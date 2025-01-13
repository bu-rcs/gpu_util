#%%
import pandas as pd
import seaborn as sns
from matplotlib import style
import matplotlib.pyplot as plt


#%%
def load_csv(file_path):
    """
    Loads a CSV file into a pandas DataFrame.

    Parameters:
        file_path (str): The path to the CSV file.

    Returns:
        pd.DataFrame: The loaded DataFrame if successful.
        None: If the file is not found or another error occurs.
    """
    try:
        data = pd.read_csv(file_path)
        print("CSV file loaded successfully!")
        print(data.head())  # Display the first few rows of the DataFrame
        return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None




def job_classification(job_name):
    """
    Checks if a job is "Interactive" or "Batch": 
    check if the job_name starts with the prefix 'ood-' or
    is equal to QRLOGIN .

    Parameters:
        job_name (pd.Series): String with the names of jobs.

    Returns:
        bool: True if the job_name starts with 'ood-' or is equal to QRLOGIN, 
              False otherwise.
    """
    return job_name.str.startswith("ood") | (job_name == "QRLOGIN")

#%%