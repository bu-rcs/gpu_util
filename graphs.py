#%%
# List of implemented graphs:
# 1. Batch vs. Interactive (OOD or qrsh) GPU jobs
# 2. Batch vs. Interactive (OOD or qrsh) jobs: CPU wallclock hours
#
#--------------------------------------------------------------

#%%
import pandas as pd
import seaborn as sns
from matplotlib import style
import matplotlib.pyplot as plt

# import functions from other python files
from graphs_util import *
from graph_plot import *


import sys,importlib
importlib.reload(sys.modules['graphs_util'])
importlib.reload(sys.modules['graph_plot'])
from graphs_util import *
from graph_plot import *
#--------------------------------------------------------------

#%%
# Specify the file path to the CSV file
file_path = '/projectnb/rcsmetrics/gpu_util/data/010124_112524.txt'

# Example usage:
df = load_csv(file_path)

# ToDo: Get the following automatically
time_period = "January 1 - November 25, 2024"

#--------------------------------------------------------------

#%%

# Set the display option to show all columns
pd.set_option('display.max_columns', None)

#Explore the input file (can be taken out later)
print(df.columns)
#print(df.head())
#print(df.tail())
#freq_table = df["job_name"].value_counts()
#print(freq_table.head(10))

#--------------------------------------------------------------

#%%
# Split Job column into 3 columns

# Total number of jobs
# Josh's file has multiple records for the same job (as many as there are GPUs)
# The first field if "job". It includes 3 values
# 1. job ID (also in column "job_number")
# 2. task ID (no in the current input file)
# 3. Date: yy-mm 
df = split_string_to_columns(df, "job", ["job_id", "task_id", "date"])

# Convert job_id and task_id to integer
df["job_id"] = df["job_id"].astype(int)
df["task_id"] = df["task_id"].astype(int)
#--------------------------------------------------------------

#%%

# Group by job_id and task_id and calculate the number of unique pairs of
# job_id and task_id
print(df.groupby(['job_id','task_id']).ngroups)
# This should be equal to the total number of jobs (the above)
print(df['job'].nunique())

#--------------------------------------------------------------

#%%

#Explore the input file (can be taken out later)
print(df.columns)
#print(df.head())
#print(df.tail())
#freq_table = df["job_id"].value_counts()
#print(freq_table.head(10))
#--------------------------------------------------------------

#%%
# Get values from Josh's slide # 4
# 192,000 jobs, 1.4 million GPU hours
# 1051 users, 380 projects
# 81 hosts, 47 queues
#print(" Total number of records", f'{len(df):,}' )
#print(" Total number of jobs", f'{len(df['job'].groupby(level=0).count()):,}' )
#--------------------------------------------------------------
#%%

# Number of records in input file
print(" Number of records in input file", f'{len(df):,}' )

# Number of GPU jobs
print(" Total number of GPU jobs", f'{df.groupby(['job_id','task_id']).ngroups:,}')

# Number of unique users
print(" Total number of unique users", f'{df['owner'].nunique():,}' )

# Number of unique projects
print(" Number of unique projects", df['project'].nunique())

# number of unique GPU nodes used
print(" Number of GPU nodes", df['hostname'].nunique())

# Number of unique queues (probably not useful)
print(" Number of unique GPU queues", df['qname'].nunique())

#--------------------------------------------------------------

#--------------------------------------------------------------
#%%
# For this task, we only need a single record per job
df_first = df.groupby(['job_id','task_id']).first().reset_index()

#--------------------------------------------------------------


#%%
# Calculate the number of batch and interactive jobs
job_class = job_classification(df_first["job_name"])
counts = job_class.value_counts()
# print("Counts of True and False values:")
# print(counts)

# Split the original dataframe into two
df_interactive = df_first[job_class]  # DataFrame where the condition is True
df_batch = df_first[~job_class] 


# Graph1: Display Interactive vs batch GPU jobs "count"
plot_job_classification(counts, 
            title="Batch vs. Interactive (OOD or qrsh) GPU jobs",
            subtitle = time_period )

#--------------------------------------------------------------

#%%
# Compute the total wallclock time for the batch jobs vs. interactive
int_time = round(df_interactive['ru_wallclock'].sum()/3600)
batch_time = round(df_batch['ru_wallclock'].sum()/3600)

# Graph2: Display Interactive vs batch GPU jobs by wallclock time
jobs_time = pd.Series([batch_time,int_time])
plot_job_time_classification(jobs_time, 
            title="Batch vs. Interactive (OOD or qrsh) jobs: \nWallclock hours",
            subtitle = time_period,
            y_title="Wallclock Time, hours" )

#--------------------------------------------------------------
#%%
# Calculate the CPU-hours of the GPU jobs
# Compute the total wallclock time for the batch jobs vs. interactive
int_time = round((df_interactive['ru_wallclock'] /
                       3600 * df_interactive['slots']).sum())
batch_time = round((df_batch['ru_wallclock'] /
                       3600 * df_batch['slots']).sum())

# Graph3: Display Interactive vs batch GPU jobs using CPU hours
jobs_time = pd.Series([int_time, batch_time])
plot_job_time_classification(jobs_time, 
            title="Batch vs. Interactive (OOD or qrsh) jobs: \nCPU - hours",
            subtitle = time_period ,
            y_title="CPU-hours")


#--------------------------------------------------------------

#%%
# Calculate the GPU-hours of the GPU jobs
# Compute the total wallclock time for the batch jobs vs. interactive
int_time = round((df_interactive['ru_wallclock'] /
                       3600 * df_interactive['n_gpu']).sum())
batch_time = round((df_batch['ru_wallclock'] /
                       3600 * df_batch['n_gpu']).sum())

# Graph4: Display Interactive vs batch GPU jobs using GPU-hours
jobs_time = pd.Series([int_time, batch_time])
plot_job_time_classification(jobs_time, 
            title="Batch vs. Interactive (OOD or qrsh) jobs: \nGPU - hours",
            subtitle = time_period,
            y_title="GPU-hours" )


# %%
# Calculate the number/percentage of jobs that did not 
# use GPU at all
# 'idle_start', 'idle_end', 'idle_mid', 'comp_tot',
# 'comp_active', 'comp_time', 'comp_frac', 'comp_std'
# Note: this needs to be re-calculated as there are multiple records for each job

print("Number and percentage of jobs that did not utilized GPU at all")
print( "     Overall: ", sum(df['comp_tot'] == 0), " (", round(100* sum(df['comp_tot'] == 0)/len(df)), "%)" )
print( "     Batch: ", sum(df_interactive['comp_tot'] == 0), " (", round(100* sum(df_batch['comp_tot'] == 0)/len(df_batch)), "%)" )
print( "     Interactive: ", sum(df_batch['comp_tot'] == 0), " (", round(100* sum(df_interactive['comp_tot'] == 0)/len(df_interactive)), "%)" )


# %%
