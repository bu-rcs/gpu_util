import subprocess
import pandas as pd
from io import StringIO
import os
from joblib import Parallel, delayed


def read_gpu_records(filepath: str) -> pd.DataFrame:
    """Extracts rows containing 'gpus=' from a CSV file and loads them into a DataFrame.

    This function uses the `grep` command to filter rows containing 'gpus=' from the
    specified file, extracts the header from the first line, and loads the filtered data
    into a Pandas DataFrame.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        pd.DataFrame: A DataFrame containing only rows with 'gpus=', preserving the original headers.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        PermissionError: If the file cannot be accessed due to permission issues.
        subprocess.CalledProcessError: If an error occurs while executing the grep command.
        pd.errors.EmptyDataError: If no matching data is found.

    Example:
        gpu_jobs_2024 = read_gpu_records("/projectnb/rcsmetrics/accounting/data/scc/2024.csv")
        print(gpu_jobs_2024.head(10))
    """
    try:
        # Run grep command to filter lines containing 'gpus='
        result = subprocess.run(
            ["grep", "-e", "gpus=", filepath],
            capture_output=True,
            text=True,
            check=True,
        )

        # Extract header from the first row of the file
        with open(filepath, "r", encoding="utf-8") as file:
            header = next(file).strip().split(",")

        # Convert grep output to a file-like object and read into pandas
        df = pd.read_csv(StringIO(result.stdout), names=header, quotechar='"')

        # Ensure 'gpus=' is actually in the 'options' column
        df = df[df["options"].astype(str).str.contains("gpus=", na=False)]

        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except PermissionError:
        raise PermissionError(f"Permission denied: {filepath}")
    except subprocess.CalledProcessError:
        return pd.DataFrame(
            columns=header
        )  # Return empty DataFrame if no matches are found
    except pd.errors.EmptyDataError:
        return pd.DataFrame(
            columns=header
        )  # Handle case where grep returns no valid data


def extract_task_id_from_file(filename: str) -> pd.DataFrame:
    """
    Reads a CSV file and extracts the task ID from the 'job' column.

    Args:
        filename (str): The path to the CSV file.

    Returns:
        pd.DataFrame: The dataframe with a new 'task_id' column extracted from 'job'.

    Example:
        josh_df = extract_task_id_from_file('/projectnb/rcsmetrics/gpu_util/data/010124_112524.txt')
        print(josh_df.head())
    """
    # Read the file into a DataFrame
    df = pd.read_csv(filename)

    # Ensure 'job' column exists
    if "job" not in df.columns:
        raise ValueError("The file does not contain a 'job' column.")

    # Extract task ID (second part of the job column)
    df["task_id"] = df["job"].astype(str).str.split(".").str[1]

    return df


def clean_gpu_data(filepath: str) -> pd.DataFrame:
    """
    Reads and processes GPU usage data while handling missing values and misaligned JobID.

    The function categorizes GPU usage scenarios based on job assignment:
    - Scenario 0: GPU unassigned and unused. NOTE: MAY BE MINOR USAGE - IDLE DRAW?
    - Scenario 1: Job ID exists, but user and project are missing (GPU in use).
    - Scenario 2: Job ID exists, but user and project are marked as "-", indicating idle GPU.
    - Scenario 3: Job ID appears in the user column due to misalignment.

    Parameters:
        filepath (str): Path to the GPU usage data file.

    Returns:
        pd.DataFrame: A DataFrame containing cleaned GPU usage records.
    """
    data = []

    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.split()
            scenario = 0  # Default scenario: GPU unassigned, unused

            # Extract core metrics
            time, bus, util, mem_throughput = parts[:4]

            if len(parts) == 5:
                # Scenario 3: Job ID misaligned to user column
                user, proj = "Missing Values", "Missing Values"
                job_id = parts[4]
                scenario = 3
            else:
                user, proj, job_id = parts[4:7]

                if user == "-" and proj == "-" and job_id != "-":
                    # Scenario 2: Job ID exists but user/project missing (idle GPU)
                    user, proj = "Missing Values", "Missing Values"
                    scenario = 2
                elif job_id != "-":
                    # Scenario 1: Job ID exists, GPU is actively in use
                    scenario = 1

            # Append cleaned record
            data.append(
                [
                    int(time),
                    bus,
                    float(util),
                    float(mem_throughput),
                    user,
                    proj,
                    job_id,
                    scenario,
                ]
            )

    # Create a DataFrame
    columns = [
        "time",
        "bus",
        "util",
        "memory_throughput",
        "user",
        "project",
        "job_id",
        "scenario",
    ]
    return pd.DataFrame(data, columns=columns)


def process_gpu_data(year: str, month: str) -> pd.DataFrame:
    """
    Processes GPU usage data for a given year and month by merging job records with node statistics
    in parallel using joblib.

    Parameters:
        year (str): Two-digit year string (e.g., "25" for 2025).
        month (str): Two-digit month string (e.g., "01" for January).

    Returns:
        pd.DataFrame: A merged DataFrame containing job and GPU usage records.
    """
    # Validate year format
    if not isinstance(year, str) or not year.isdigit() or len(year) != 2:
        raise ValueError(
            f"Invalid year format: {year}. Expected a two-digit string (e.g., '25' for 2025)."
        )

    # Validate month format
    if not isinstance(month, str) or not month.isdigit() or len(month) != 2:
        raise ValueError(
            f"Invalid month format: {month}. Expected a two-digit string (e.g., '01' for January)."
        )

    # Load job records
    gpu_jobs = read_gpu_records(
        f"/projectnb/rcsmetrics/accounting/data/scc/20{year}.csv"
    )
    gpu_jobs["task_string"] = gpu_jobs["task_number"].astype(str)
    gpu_jobs.loc[~(gpu_jobs["options"].str.contains("-t")), "task_string"] = "undefined"
    gpu_jobs["job_task"] = (
        gpu_jobs["job_number"].astype(str) + "." + gpu_jobs["task_string"].astype(str)
    )

    # Get file paths for the specified month
    nodes = os.listdir("/project/scv/dugan/gpustats/data/")
    files = [
        f"/project/scv/dugan/gpustats/data/{node}/{year}{month}"
        for node in nodes
        if os.path.exists(f"/project/scv/dugan/gpustats/data/{node}/{year}{month}")
    ]

    # Determine the number of parallel jobs to use based on NSLOTS environment variable
    n_jobs = int(os.environ.get("NSLOTS", 1))  # Default to 1 if NSLOTS is not set
    print(f"Processing in parallel with {n_jobs} cores")

    # Define a function to process each file individually
    def process_file(file_name):
        try:
            gpu_records = pd.DataFrame(clean_gpu_data(file_name))
            merged_df = pd.merge(
                gpu_records, gpu_jobs, left_on="job_id", right_on="job_task", how="left"
            )
            return merged_df
        except Exception as e:
            print(f"Skipping missing or corrupted file: {file_name}")
            return pd.DataFrame()  # Return an empty DataFrame if an error occurs

    # Use joblib to process files in parallel
    all_merged_dfs = Parallel(n_jobs=n_jobs)(
        delayed(process_file)(file_name) for file_name in files
    )

    # Return the final concatenated DataFrame
    return pd.concat(all_merged_dfs, ignore_index=True) if all_merged_dfs else pd.DataFrame()


def aggregate_gpu_data(year: str) -> pd.DataFrame:
    """
    Aggregates GPU usage data for all months in a given year.

    Parameters:
        year (str): Two-digit year string (e.g., "25" for 2025).

    Returns:
        pd.DataFrame: A concatenated DataFrame containing job and GPU usage records for all months.
    """
    # Validate year format
    if not isinstance(year, str) or not year.isdigit() or len(year) != 2:
        raise ValueError(
            f"Invalid year format: {year}. Expected a two-digit string (e.g., '25' for 2025)."
        )

    all_months_df = []
    for month in [f"{m:02d}" for m in range(1, 13)]:  # Generate "01" to "12"
        print(f"Processing {year}-{month}...")
        monthly_df = process_gpu_data(year, month)
        if not monthly_df.empty:
            all_months_df.append(monthly_df)

    # Return the final concatenated DataFrame
    return (
        pd.concat(all_months_df, ignore_index=True) if all_months_df else pd.DataFrame()
    )


def process_projects_gpu_data(year: str, month: str, projects: list) -> pd.DataFrame:
    """
    Processes GPU usage data for a given year, month, and filters by specified projects.

    Parameters:
        year (str): Two-digit year string (e.g., "25" for 2025). Must be a two-digit numeric string.
        month (str): Two-digit month string (e.g., "01" for January). Must be a valid two-digit numeric string from "01" to "12".
        projects (list): List of project names to filter the data.

    Returns:
        pd.DataFrame: Filtered DataFrame containing job and GPU usage records for the specified projects.

    Raises:
        ValueError: If year or month are not properly formatted, or if projects is not a list.
    """
    # Validate year format
    if not isinstance(year, str) or not year.isdigit() or len(year) != 2:
        raise ValueError(f"Invalid year format: {year}. Expected a two-digit string (e.g., '25' for 2025).")

    # Validate month format
    if not isinstance(month, str) or not month.isdigit() or len(month) != 2 or not (1 <= int(month) <= 12):
        raise ValueError(f"Invalid month format: {month}. Expected a two-digit string from '01' to '12'.")

    # Validate projects parameter
    if not isinstance(projects, list) or not all(isinstance(proj, str) for proj in projects):
        raise ValueError("Projects must be a list of strings.")

    # Process GPU data for the given year and month
    full_df = process_gpu_data(year, month)

    # Filter the DataFrame to include only rows where the 'project' column matches the given projects
    filtered_df = full_df[full_df["project_x"].isin(projects)]

    return filtered_df
