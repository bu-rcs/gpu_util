#%%
import pandas as pd
import seaborn as sns
from matplotlib import style
import matplotlib.pyplot as plt

# import functions from other python files
from graphs_util import *
from graph_plot import *


#%%
# Specify the file path to the CSV file
file_path = '/projectnb/rcsmetrics/gpu_util/data/010124_112524.txt'

# Example usage:
df = load_csv(file_path)

# ToDo: Get the following automatically
time_period = "January 1 - November 25, 2024"

#%%
#Explore the input file (can be taken out later)
print(df.columns)
print(df.head())
print(df.tail())
freq_table = df["job_name"].value_counts()
print(freq_table.head(10))

#%%
# Get values from Josh's slide # 4
# 192,000 jobs, 1.4 million GPU hours
# 1051 users, 380 projects
# 81 hosts, 47 queues

# Total number of jobs
print(" Total number of jobs", f'{len(df):,}' )

# Number of unique users
print(" Total number of unique users", f'{df['owner'].nunique():,}' )

# Number of unique projects
print(" Number of unique projects", df['project'].nunique())

# number of unique GPU nodes used
print(" Number of GPU nodes", df['hostname'].nunique())

# Number of unique queues (probably not useful)
print(" Number of unique GPU queues", df['qname'].nunique())






#%%
job_class = job_classification(df["job_name"])
counts = job_class.value_counts()
# print("Counts of True and False values:")
# print(counts)

# Split the original dataframe into two
df_interactive = df[job_class]  # DataFrame where the condition is True
df_batch = df[~job_class] 


# Graph1: Display Interactive vs batch GPU jobs "count"
plot_job_classification(counts, 
            title="Batch vs. Interactive (OOD or qrsh) job",
            subtitle = time_period )

#%%
# Compute the total wallclock time for the batch jobs vs. interactive
int_WC_time = round(df_interactive['ru_wallclock'].sum()/3600)
batch_WC_time = round(df_batch['ru_wallclock'].sum()/3600)

# Graph2: Display Interactive vs batch GPU jobs by wallclock time
jobs_WC = pd.Series([batch_WC_time,int_WC_time])
plot_job_time_classification(jobs_WC, 
            title="Batch vs. Interactive (OOD or qrsh) job by time",
            subtitle = time_period )



# %%
