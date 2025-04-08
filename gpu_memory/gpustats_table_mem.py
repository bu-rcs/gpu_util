import os
import pandas as pd

def gpustats_table(parent_folder, start_date, dtypes):
    skip_links = 3

    # List entries in the parent folder
    all_entries = sorted(os.listdir(parent_folder))
    all_entries = all_entries[skip_links:]  # skip '.', '..', and any fixed number of initial entries

    # Keep only files that are >= start_date (compare as ints)
    files = [f for f in all_entries if f.isdigit() and int(f) >= int(start_date)]

    G_list = []

    for file in files:
        full_path = os.path.join(parent_folder, file)

        # Read with pandas, no header, custom dtypes as available
        G_temp = pd.read_csv(full_path, header=None, delim_whitespace=True, dtype=str)

        # Rename temporary columns to Var1...Var7 for clarity
        G_temp.columns = [f'Var{i}' for i in range(1, len(G_temp.columns)+1)]

        # Keep only rows with assigned job IDs (Var7 != '-')
        mask = G_temp['Var7'] != '-'
        if mask.sum() == 0:
            continue

        G_filtered = G_temp[mask].copy()
        G_filtered['rundate'] = file  # add rundate column (from filename)
        G_list.append(G_filtered)

    if not G_list:
        return pd.DataFrame(columns=["time", "bus", "util", "mem", "user", "proj", "job", "rundate"])

    G = pd.concat(G_list, ignore_index=True)

    # Rename columns
    G.columns = ["time", "bus", "util", "mem", "user", "proj", "job", "rundate"]

	# Catch small parsing bug where (under some circumstances TBD) job ID is put in the wrong column when GPU had running process that then ended
	# Fix columns to revert bug
    mask = G['job'] == ''
    G.loc[mask, 'job'] = G.loc[mask, 'user']
    G.loc[mask, 'user'] = '-'
    G.loc[mask, 'proj'] = '-'

    # Fix even rarer bug where we are missing column data, but also there is no job assigned
    G = G[G['job'] != '-']

    # SSort by busID to make jobs contiguous
    G = G.sort_values(by='bus').reset_index(drop=True)

    return G
