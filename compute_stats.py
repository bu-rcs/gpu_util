import pandas as pd
import numpy as np

def compute_stats(G, util_par):
    interval = 5  # minutes per record
    under_util = G['util'].astype(float) <= util_par


	# Find where the job ID changes, this will give the index for the last
	# measurement for that job
	# Next, get the indices for these job endpoints and add in the end of
	# the final job and the "end" of the zeroth job so our index math works
    job_changes = G['job'].ne(G['job'].shift())
    bounds = job_changes[job_changes].index.to_list()
    bounds.append(len(G))  # add the end of the final job
    bounds = [0] + bounds  # include start of first job

    stats_list = []

    for i in range(len(bounds)-1):
        bnd_1 = bounds[i]
        bnd_2 = bounds[i+1] - 1
		# If the GPU is always under utilized, we won't be able to find a
		# start to the computation. Instead set the comp start/end equal to
		# the bounds of the whole job
		# By convention we set all idle values to 0
        if under_util[bnd_1:bnd_2+1].all():
            idle_start = idle_end = idle_mid = 0
            comp_start = bnd_1
            comp_end = bnd_2
        else:
            util_change = np.diff(under_util[bnd_1:bnd_2+1].astype(int))
            # If the job is never under-utilized, find(util_change) will be empty
            idle_start = 0
            idle_end = 0
            
			# Find when the under_util first/last changes from 0 to 1 or 1 to 0
			# An idle start/end starts/ends with under_util=1
			# If our period actually isn't idle, then the computed value will be 0
            if under_util.iloc[bnd_1]:
                first_change = np.argmax(util_change != 0)
                idle_start = (first_change + 1) * interval if util_change.any() else 0

            if under_util.iloc[bnd_2]:
                reversed_change = np.argmax(util_change[::-1] != 0)
                idle_end = (bnd_2 - bnd_1 + 1 - reversed_change - 1) * interval if util_change.any() else 0

			# Find the start and end of the computation by looking for when
			# we are first/last not under-utilizing the GPU
			# Remember that we need to add these offsets to the whole job
			# start bound
            comp_start = under_util[bnd_1:bnd_2+1].idxmin()
            comp_end = under_util[bnd_1:bnd_2+1][::-1].idxmin()
            idle_mid = under_util[comp_start:comp_end+1].sum() * interval

        tot_time = (bnd_2 - bnd_1 + 1) * interval
        comp_time = (comp_end - comp_start + 1) * interval

        util_slice = G['util'].iloc[comp_start:comp_end+1].astype(float)
        under_util_slice = under_util.iloc[comp_start:comp_end+1]

        comp_tot = util_slice.sum() / 100 * interval
        comp_active = (util_slice * (~under_util_slice)).sum() / 100 * interval
        comp_frac = comp_tot / comp_time if comp_time else 0
        comp_std = util_slice.std() / 100
		
		# Set up the table that holds the GPU usage stats
        stats_list.append({
            "idle_start": idle_start,
            "idle_end": idle_end,
            "idle_mid": idle_mid,
            "comp_tot": comp_tot,
            "comp_active": comp_active,
            "comp_time": comp_time,
            "comp_frac": comp_frac,
            "comp_std": comp_std
        })

	# Generate job names including task IDs to match the format of the
	# accounting file
	# We also include GPU index so that we can disambiguate when a job uses
	# multiple GPUs. We have stats on a per job per GPU basis.
    job_names = G['job'].iloc[np.array(bounds[:-1])]
    job_split = job_names.str.split('.', expand=True)
    job_split[1] = job_split[1].replace('undefined', '0')
    rundates = G['rundate'].iloc[np.array(bounds[:-1])] # starting rundate for each job; we need this to distinguish between identical jobids that occured in past years
    job_ids = job_split[0] + '.' + job_split[1] + '.' + rundates

    bus_ids, _ = pd.factorize(G['bus'].iloc[np.array(bounds[:-1])])

    job_table = pd.DataFrame({'job': job_ids, 'bus': bus_ids})
    stats_df = pd.DataFrame(stats_list)

    return pd.concat([job_table, stats_df], axis=1)
