function G = gpustats_table(parent_folder, start_date, opts)
skip_links = 3; % this excludes the special folders "." and ".." listed by the dir command

% Loop over all files in parent_folder, skipping the first 2 items which
% are the '.' and '..' "files"
% We only process folders with date names that are at least as new as
% start_date
% These are read in one by one, pre-processed, and then concated
% together into a single big table
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
    mask = ~strcmp(G_temp.Var7,'-'); % If no job ID is listed the job is not assigned
    rundate = repmat({file},sum(mask),1);
    G{i} = [G_temp(mask,:), table(rundate)]; % Remove rows where the GPU is not assigned, add in a column for the YYMM of running date

end
A = vertcat(G{:});
G = renamevars(A, 1:7, ["time","bus","util","mem","user","proj","job"]);

mask = strcmp(G.job,''); % Catch small parsing bug where (under some circumstances TBD) job ID is put in the wrong column when GPU had running process that then ended
G.job(mask) = G.user(mask); % Fix columns to revert bug
G.user(mask) = {'-'};
G.proj(mask) = {'-'};

mask = ~strcmp(G.job,'-'); % Fix even rarer bug where we are missing column data, but also there is no job assigned
G = G(mask, :);

G = sortrows(G,2); % Sort by busID to make jobs contiguous
end