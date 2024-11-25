#%%
import pandas as pd
import seaborn as sns
from matplotlib import style
import matplotlib.pyplot as plt



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



def plot_job_classification(counts, title, subtitle):
    # Create a plot

    # parameters
    plt.rcParams['font.family'] = "roboto"
    style.use('fivethirtyeight')
    sns.set(style="whitegrid")
    ax = sns.barplot(x=counts.index.astype(str), 
                 y=counts.values, 
                 palette="Set2", 
                 hue=counts.index.astype(str), 
                 legend=False)
  
    # Add text labels to each bar
    for i, value in enumerate(counts.values):
        ax.text(i, value + 0.05, str(value), ha='center', va='bottom', fontsize=12)

        plt.ylim(0, counts.values.max()*1.1)

    # Set the main title
    plt.suptitle(
        title,  
        fontsize=18,  # Set the font size
        color="black",  # Set the color
        x=0.51,  # Adjust this to align with the subtitle
        y=1.01,  # Adjust this to align with the subtitle
    )

    # Set the subtitle
    plt.title(
        subtitle,  
        fontsize=14,  # Set the font size
        color="grey",  # Set the color
    )

    plt.xlabel("Type of Job")
    plt.ylabel("Count")
    plt.xticks([0, 1], labels=['Batch', 'Interactive'])  # Labeling True and False explicitly
    plt.show()



# Specify the file path to the CSV file
file_path = '/projectnb/rcsmetrics/gpu_util/data/010124_112524.txt'

# Example usage:
df = load_csv(file_path)

print(df.head())
print(df.tail())


freq_table = df["job_name"].value_counts()
print(freq_table.head(10))

job_class = job_classification(df["job_name"])
counts = job_class.value_counts()
print("Counts of True and False values:")
print(counts)

# Split the original dataframe into two
df_interactive = df[job_class]  # DataFrame where the condition is True
df_batch = df[~job_class] 



plot_job_classification(counts, 
            title="Batch vs. Interactive (OOD or qrsh) job",
            subtitle = "January 1 - November 25, 2024" )


# %%
