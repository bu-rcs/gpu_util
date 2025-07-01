# Usage:
# $ qacct_gpu <jobnumber>
# Example:
# $ qacct_gpu 5078528
# This prints selected information from qacct along with some basic GPU usage info

# Create a temp directory to work out of
out_dir=$(mktemp -d)
cd $out_dir

# Relevant fields from qacct we want to display, or info we need to get GPU logs
fields="qname|hostname|owner|jobnumber|start_time|end_time|exit_status|cpu"
nfields=8

# We always need job level info to get gpu stats, but want to replicate
# qacct behavior of generating a summary when "-j" is omitted
# If the user omits "-j" we set a summary flag and add the "-j" back in
if [[ $* == *"-j"* ]]; then
	qacct $* | grep -E $fields > output
	summary=false
else
	qacct -j $* | grep -E $fields > output
	summary=true
fi
njobs=$(grep "jobnumber" output | wc -l)

# Need to loop here for each `jobnumber` found in output
# Also need to split output so only current job is being worked on

# SPACE FOR CODE/LOOP

# Grab GPU logs from compute node where it ran.
# Note this needs to copy the info from the host itself, since logs are
# only centralizaed once a week.
host=$(awk '/hostname/ {split($2, a, "."); print a[1]}' output)
scp -rq $host:/var/log/gpustats .

# Currently this ignores the possibility of a job that take place over three distinct months
startdate=$(awk '/start_time/ {$1=""; print $0}' output)
startdate=$(date --date="$starttime" "+%y%m")
enddate=$(awk '/end_time/ {$1=""; print $0}' output)
enddate=$(date --date="$enddate" "+%y%m")

# Now collect the relevant month(s) of logs so we can parse after
if [ $startdate -eq $enddate ]; then
	cat gpustats/$startdate > logs
else
	cat gpustats/$startdate gpustats/$enddate > logs
fi
grep $1 logs > job

ngpus=$(awk '{print $2}' job | sort | uniq | wc -l)
avg_util=$(awk '{sum+=$3; n++}END{print sum/n;}' job)
idle_time=$(awk '$3 <1.0 { count++ } END { print count*5 }' job)
peak_vram=$(awk 'NR == 1 || $9 > max { max = $9 } END { print max }' job)
gpu_type=$(qhost -F gpu_type | grep scc-211 -A 1 | grep gpu_type | cut -d= -f2)

if [ "$summary" = true ]
	n_rows=$(cat job | wc -l)
	integ_util=$(awk '{sum+=$3; n++}END{print sum;}' job)
	idle_time=$(awk '$3 <1.0 { count++ } END { print count }' job)
fi

cat output
echo "num_gpus    " $ngpus
echo "gpu_avg_util" $avg_util %
echo "gpu_idletime" $idle_time mins
echo "peak_vram   " $peak_vram MB
echo "gpu_type    " $gpu_type

rm -rf $out_dir
