%% This script reads the accounting file and the gpustats files, computes
%% derived GPU job info and then joins them together based on job ID, 
% task ID, and start date

clear all
base_path = '/project/scv/dugan/gpustats/data/';
util_par = 5; % Percent utilization a job is considered underutilized
start_date = '2401'; %yyMM
skip_list = {...
    'c02',... % defunct
    'ea1','ea2','ea3','ea4','eb1','eb2','eb3','eb4','ec1','ec2','ec3','ec4',...% defunct
    'fa1','fa2','fa3','fa4','fb1','fb2','fb3','fb4','fc1','fc2','fc3','fc4',...% defunct
    'ha1','ha2','hb1','hb2','hc1','hc2','hd1','hd2','he1','he2',...% defunct
    'ja1','ja2','jb1','jb2','jc1','jc2','jd1','jd2','je1','je2',...% defunct
    'c01','c04','c05','sc1','sc2'}; %K40M

skip_list = strcat({'scc-'},skip_list);
skip_links = 3; % ignore '.' and '..' files, so the first file to consider is number skip_links
%% Identify all folders belonging to nodes of interest
folders = dir(base_path);
folders = {folders([folders.isdir]).name};
folders = folders(skip_links:end);
skip_folders = cellfun(@(x) any(strcmp(x,skip_list)), folders);
folders = folders(~skip_folders);
%% Choose a specific gpustats file as an example to get import options from
example_file = '/project/scv/dugan/gpustats/data/scc-202/2402';

opts = detectImportOptions(example_file);
opts.VariableTypes(1) = {'int32'};
opts.VariableTypes([2, 7]) = {'char'};
%% Loop through all folders and compute derived GPU stats node by node
stats = cell(length(folders), 1);

for i = 1:length(folders)
    folder = fullfile(base_path, folders{i});
    G = gpustats_table_temp(folder, start_date, opts);
    stats{i} = compute_stats(G, util_par);
end
clear G
stats = vertcat(stats{:});

%% Read in accounting file and generate a derived job "name" that 
% matches the format also used in G
B = accounting_table(2024);
rundate = char(datetime(B.ux_start_time, 'ConvertFrom', 'posixtime','TimeZone','America/New_York','Format','yyMM'));
B.task_number=strcat(B.job_number,'.',B.task_number,'.',rundate);

S = innerjoin(stats,B,'LeftKeys',1,'RightKeys',17);

writetable(S,"data/010124_"+string(datetime(date,'Format','MMddyy')))
