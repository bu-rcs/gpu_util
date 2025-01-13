import os

base_path = '/project/scv/dugan/gpustats/data/'

skip_list = [
    'c02', #defunct
    'ea1','ea2','ea3','ea4','eb1','eb2','eb3','eb4','ec1','ec2','ec3','ec4', #defunct
    'fa1','fa2','fa3','fa4','fb1','fb2','fb3','fb4','fc1','fc2','fc3','fc4', #defunct
    'ha1','ha2','hb1','hb2','hc1','hc2','hd1','hd2','he1','he2', #defunct
    'ja1','ja2','jb1','jb2','jc1','jc2','jd1','jd2','je1','je2', #defunct
    'c01','c04','c05','sc1','sc2'] #K40M

# Loop over each sub-directory
for subdir in os.listdir(base_path):
    subdir_path = os.path.join(base_path, subdir)
    
    # Check if the sub-directory name is in the skip_list
    if subdir in skip_list:
        continue
    
    # Loop over each file in the sub-directory
    for filename in os.listdir(subdir_path):
        file_path = os.path.join(subdir_path, filename)
        
        # Read the file
        with open(file_path, 'r') as f:
            lines = f.readlines()

# Identify all folders belonging to nodes of interest
# Choose a specific gpustats file as an example to get import options from

# Loop through all folders and compute derived GPU stats node by node
for i = 1:length(folders)
    folder = fullfile(base_path, folders{i});
    G = gpustats_table(folder, start_date
    stats{i} = compute_stats(G, util_par);

# stats = vertcat(stats{:});
# Read in accounting file and generate a derived job "name" that 
# matches the format also used in G
B = accounting_table(2024);
rundate = char(datetime(B.ux_start_time, 'ConvertFrom', 'posixtime','TimeZone','America/New_York','Format','yyMM'));
B.task_number=strcat(B.job_number,'.',B.task_number,'.',rundate);

S = innerjoin(stats,B,'LeftKeys',1,'RightKeys',17);
