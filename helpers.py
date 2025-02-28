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