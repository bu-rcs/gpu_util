import os
import pandas as pd
from datetime import datetime
from gpustats_table import gpustats_table
from accounting_table import accounting_table
from compute_stats import compute_stats

# This script reads the accounting file and the gpustats files, computes
# derived GPU job info and then joins them together based on job ID, 
# task ID, and start date

base_path = '/project/scv/dugan/gpustats/data/'
util_par = 5  # Percent utilization a job is considered underutilized
start_date = '2401'  # yyMM
skip_list = [
    'c02',
    'ea1','ea2','ea3','ea4','eb1','eb2','eb3','eb4','ec1','ec2','ec3','ec4',
    'fa1','fa2','fa3','fa4','fb1','fb2','fb3','fb4','fc1','fc2','fc3','fc4',
    'ha1','ha2','hb1','hb2','hc1','hc2','hd1','hd2','he1','he2',
    'ja1','ja2','jb1','jb2','jc1','jc2','jd1','jd2','je1','je2',
    'c01','c04','c05','sc1','sc2'
]
skip_list = [f'scc-{node}' for node in skip_list]
skip_links = 3  # Ignore '.', '..' and initial non-data folders

# List valid folders
all_folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
folders = [f for f in all_folders if f not in skip_list][skip_links:]

# Detect import options manually from example file
example_file = os.path.join(base_path, 'scc-202', '2402')
example_dtypes = {
    0: 'int32',  # Assuming 0-indexed column for first variable
    1: 'str',    # 2nd column (MATLAB's index 2)
    6: 'str'     # 7th column (MATLAB's index 7)
}

# Process GPU stats from each folder
stats = []
for folder_name in folders:
    folder_path = os.path.join(base_path, folder_name)
    G = gpustats_table(folder_path, start_date, example_dtypes)
    stats.append(compute_stats(G, util_par))

stats_df = pd.concat(stats, ignore_index=True)

# Read accounting data
B = accounting_table(2024)
B['ux_start_time'] = pd.to_datetime(B['ux_start_time'], unit='s')
B['rundate'] = B['ux_start_time'].dt.strftime('%y%m')
B['task_number'] = B['job_number'].astype(str) + '.' + B['task_number'].astype(str) + '.' + B['rundate']

# Join GPU stats with accounting table
# Assuming the first column of `stats_df` matches the 'task_number' in B
merged_df = pd.merge(stats_df, B, left_on=stats_df.columns[0], right_on='task_number', how='inner')

# Output to CSV
date_str = datetime.today().strftime('%m%d%y')
merged_df.to_csv(f"data/010124_{date_str}.csv", index=False)
