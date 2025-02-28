import subprocess
import pandas as pd
from io import StringIO

def read_gpu_records(filepath):
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
        result = subprocess.run(["grep", "-e", "gpus=", filepath], capture_output=True, text=True, check=True)

        # Extract header from the first row of the file
        with open(filepath, 'r', encoding='utf-8') as file:
            header = next(file).strip().split(',')

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
        return pd.DataFrame(columns=header)  # Return empty DataFrame if no matches are found
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=header)  # Handle case where grep returns no valid data

def extract_task_id_from_file(filename):
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
    df["task_id"] = df["job"].astype(str).str.split('.').str[1]
    
    return df

def clean_gpu_data(filepath):
    """
    Reads and processes GPU usage data while handling missing values and misaligned JobID.

    The function categorizes GPU usage scenarios based on job assignment:
    - Scenario 0: GPU unassigned and unused.
    - Scenario 1: Job ID exists, but user and project are missing (GPU in use).
    - Scenario 2: Job ID exists, but user and project are marked as "-", indicating idle GPU.
    - Scenario 3: Job ID appears in the user column due to misalignment.

    Parameters:
        filepath (str): Path to the GPU usage data file.

    Returns:
        pd.DataFrame: A DataFrame containing cleaned GPU usage records.
    """
    data = []

    with open(filepath, 'r', encoding='utf-8') as file:
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
            data.append([int(time), bus, float(util), float(mem_throughput), user, proj, job_id, scenario])

    # Create a DataFrame
    columns = ["time", "bus", "util", "memory_throughput", "user", "project", "job_id", "scenario"]
    return pd.DataFrame(data, columns=columns)
