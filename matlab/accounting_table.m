function T = accounting_table(year)
my_path = '/projectnb/rcsmetrics/accounting/data/scc/';
year = 2024-year;

% List all CSV files in the directory
csvFiles = dir(fullfile(my_path, '*.csv'));
the_file = fullfile(csvFiles(end-year).folder, csvFiles(end-year).name);
opts = detectImportOptions(the_file);
opts.VariableTypes([5, 17]) = {'char'};
opts.VariableTypes([6:8, 11:13]) = {'int32'};
opts.VariableTypes(9:10) = {'uint8'};
opts.VariableTypes(16) = {'int16'};
opts.VariableTypes(21) = {'int64'};

T = readtable(the_file,opts);
end