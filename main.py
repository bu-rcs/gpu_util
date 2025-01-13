# Loop over all files in parent_folder, skipping the first 2 items which
# are the '.' and '..' "files"
# We only process folders with date names that are at least as new as
# start_date
# These are read in one by one, pre-processed, and then concated
# together into a single big table
files = dir(parent_folder);
files = {files.name};
files = files(skip_links:end);
daterange = cellfun(@(x)str2num(x),files) >= str2double(start_date);
files = files(daterange);

G = cell(length(files), 1);

for i = 1:length(files)
    file = files{i};
    myfile = fullfile(parent_folder, file);

    G_temp = readtable(myfile, opts, ReadVariableNames=false);
    mask = ~strcmp(G_temp.Var7,'-'); # If no job ID is listed the job is not assigned
    rundate = repmat({file},sum(mask),1);
    G{i} = [G_temp(mask,:), table(rundate)]; # Remove rows where the GPU is not assigned, add in a column for the YYMM of running date

end