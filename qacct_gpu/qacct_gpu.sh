# Usage:
# $ qacct_gpu <usual "qacct" parameters/options>
# This prints selected information from qacct along with some basic GPU 
# usage info
# The format is meant to mimic qacct

cum_avg=0
cum_wall=0
cum_idle=0
cum_vram=0

# Create a temp directory to work out of
out_dir=$(mktemp -d)
cd $out_dir

# Relevant fields from qacct we want to display, or info we need to get GPU logs
fields="qname|hostname|owner|jobnumber|start_time|end_time|exit_status|cpu"
nfields=8 #  IF THIS IS CHANGED, SET LOOP BOUNDS BELOW

# We always need job level info to get gpu stats, but want to replicate
# qacct behavior of generating a summary when "-j" is omitted
# If the user omits "-j" we set a summary flag and add the "-j" back in
if [[ $* == *"-j"* ]]; then
	qacct -l gpu_c=6.0 $* | grep -E $fields > output
	summary=false
else
	qacct -l gpu_c=6.0 -j $* | grep -E $fields > output
	summary=true
fi
njobs=$(grep "jobnumber" output | wc -l)

# Need to loop here for each `jobnumber` found in output
# Also need to split output so only current job is being worked on
echo "=============================================================="

while :; do
#=== BEGIN WHILE LOOP OVER EACH JOB ====
record=()
# MODIFY LOOP BOUNDS IF "nfields" CHANGES ABOVE
for i in {1..8}; do
IFS= read -r line || break 2
record+=("$line")
done
rec=$(printf "%s\n" "${record[@]}")

# Grab GPU logs from compute node where it ran.
# Note this needs to copy the info from the host itself, since logs are
# only centralizaed once a week.
host=$(awk '/hostname/ {split($2, a, "."); print a[1]}'  <<<"$rec")
jobid=$(awk '/jobnumber/ {print $2}' <<<"$rec")
scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -rq $host:/var/log/gpustats .

# Currently this ignores the possibility of a job that take place over three distinct months
startdate=$(awk '/start_time/ {$1=""; print $0}'  <<<"$rec")
startdate=$(date --date="$starttime" "+%y%m")
enddate=$(awk '/end_time/ {$1=""; print $0}'  <<<"$rec")
enddate=$(date --date="$enddate" "+%y%m")

# Now collect the relevant month(s) of logs so we can parse after
if [ $startdate -eq $enddate ]; then
	cat gpustats/$startdate > logs
else
	cat gpustats/$startdate gpustats/$enddate > logs
fi
grep $jobid logs > job

# Get col 2 (bus ID) and count unique buses
ngpus=$(awk '{print $2}' job | sort | uniq | wc -l)

# Need to catch the case where the job is too short for it to be recorded
# in gpustats
zero_test=$(wc -l < job)
if [ $zero_test -eq 0 ]; then
	avg_util=0
	ngpus=1
else
	# Add col 3 (util) and divide by number of rows to get avg
	# Note if there is more than 1 GPU this averages them together
	avg_util=$(awk '{sum+=$3; n++}END{print sum/n;}' job)
fi

# Wallclock based on "gpustats" rows
wallclock=$(cat job | wc -l)
wallclock=$(echo 5*$wallclock/$ngpus | bc)
# This is a total across ALL GPUs, and therefore could exceed "wallclock"
idle_time=$(awk '$3 <1.0 { count++ } END { print count*5 }' job)
peak_vram=$(awk 'NR == 1 || $9 > max { max = $9 } END { print max }' job)
gpu_type=$(qhost -F gpu_type | grep $host -A 1 | grep gpu_type | cut -d= -f2)

if [ "$summary" = false ]; then
	cat<<<"$rec"
	echo "num_gpus    " $ngpus
	echo "gpu_avg_util" $avg_util %
	echo "wallclock   " $wallclock mins
	echo "gpu_idletime" $idle_time mins
	echo "peak_vram   " $peak_vram MB
	echo "gpu_type    " $gpu_type
	echo "=============================================================="
elif [ "$summary" = true ]; then
	cum_avg=$(echo "scale=3;$cum_avg+$avg_util" | bc)
	cum_wall=$(echo "$cum_wall+$wallclock" | bc)
	cum_idle=$(echo "$cum_idle+$idle_time" | bc)
	cum_vram=$(echo "$cum_vram+$peak_vram" | bc)
fi

rec=""
done < output
#=== END WHILE LOOP OVER EACH JOB ====

if [ "$summary" = true ]; then
	echo "GPU Job Summary:"
	echo "njobs            " $njobs
	echo "average util     " $(echo "scale=3;$cum_avg/$njobs" | bc) %
	echo "average wallclock" $(echo "$cum_wall/$njobs" | bc) mins
	echo "average idletime " $(echo "$cum_idle/$njobs" | bc) mins
	echo "average peak_vram" $(echo "$cum_vram/$njobs" | bc) MB
fi

rm -rf $out_dir
