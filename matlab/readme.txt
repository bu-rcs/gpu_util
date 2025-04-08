This uses a MATLAB script to read the accounting file and the gpustats 
files, computes derived GPU job info and then joins them together 
based on job ID, task ID, and start date.

Relevant functions:
combine_stats -  Top-level script that combines accounting and GPU job info

gpustats_table - Reads in all the gpustats files for every folder for 
	every compute node

compute_stats - Takes the time series data read in by gpustats_table and
	computes dervied aggregate measures
	
accounting_table - Reads in accounting file and formats it accordingly
