#!/bin/bash
# Usage:
# $ qacct_gpu [--csv] <usual "qacct" parameters/options>
# Examples:
# $ qacct_gpu -j 6964876          # one job, full detail
# $ qacct_gpu -o jbevan           # summary over all that user's GPU jobs
# $ qacct_gpu --csv -o jbevan > jobs.csv
# This prints selected information from qacct along with some basic GPU
# usage info. The format is meant to mimic qacct.
#
# We always need job level info to get gpu stats, but want to replicate
# qacct behavior of generating a summary when "-j" is omitted.
# If the user omits "-j" we set a summary flag and add the "-j" back in.
#
# Besides the qacct fields (ru_wallclock is qacct's exact run time, in
# seconds), each record gets these, from the nodes' gpustats logs, which
# sample every GPU every 5 minutes:
#   num_gpus      GPUs the job has samples on
#   gpu_avg_util  mean utilization over all its samples on all its GPUs, %
#   wallclock     minutes the job was sampled for; in 5-minute steps, so a job
#                 under ~5 minutes shows 0
#   gpu_time      busy GPU-minutes: utilization/100 x 5 minutes per sample,
#                 summed over its GPUs (so it can exceed wallclock)
#   gpu_idle      GPU-minutes under 1% utilization, summed over its GPUs
#   peak_vram     most GPU memory in use in any one sample, MB
#   gpu_type      from qhost
#   gpu_util_each gpu_avg_util for each GPU separately, joined with ";" in
#                 PCI bus ID order (one value per GPU; empty with no samples)
#   gpu_idle_each gpu_idle for each GPU separately, same format
#   gpu_mem       the card's total memory, MB (largest seen, from gpustats)
#
# --csv prints CSV instead: a header row, then one row per record (or a single
# summary row). Columns are named as above, values carry no units, and times
# are written as 2026-07-29 14:15:47.
#
# How it runs: one pass over qacct's output (stage 1, below), then stages 2-4,
# shared with qacct_gpubatch.sh in qacct_gpu_lib.sh, which must sit next to
# this script. Logs are read from the central archive when its weekly copy
# already covers the job, otherwise copied from the node, up to $NSLOTS at a
# time. qacct itself reads the whole accounting file on every call (~7-14 s),
# whatever filter it is given.
#
# Requires gawk.

here=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
. "$here/qacct_gpu_lib.sh" || { echo "${0##*/}: cannot load $here/qacct_gpu_lib.sh" >&2; exit 1; }

usage() {
	echo "Usage: ${0##*/} [--csv] <qacct options>   (e.g. -j JOB_ID, or -o USER)" >&2
	exit 2
}

# "--csv" is ours (qacct options all start with a single dash); everything
# else is passed to qacct untouched
csv=false
args=()
for a in "$@"; do
	if [ "$a" = "--csv" ]; then
		csv=true
	else
		args+=("$a")
	fi
done

[ ${#args[@]} -gt 0 ] || usage

# Create a temp directory to work out of, and always clean it up
out_dir=$(mktemp -d) || exit 1
trap 'rm -rf "$out_dir"' EXIT

# Match "-j" as a whole argument. A substring test on "$*" also fires on
# things like "-o alice-jones", which would wrongly suppress the summary.
summary=true
for a in "${args[@]}"; do
	if [ "$a" = "-j" ]; then
		summary=false
		break
	fi
done

[ "$summary" = true ] && args=(-j "${args[@]}")

#=== 1. ONE pass over qacct's output ===========================================
# Records are split on the "=====" separators, so a record missing a field
# can't knock the following records out of step.
qacct -l gpu_c=6.0 "${args[@]}" 2>"$out_dir/qacct_err" |
	gawk -v fields="$QG_FIELDS" -v recs="$out_dir/recs" -v plan="$out_dir/plan" \
	     -v need="$out_dir/need" -e "$QG_AWK" -e '
	BEGIN { qg_init(fields) }
	/^=+$/ { flush(); next }
	{ qg_line() }
	END { flush(); qg_finish() }'

if [ ! -s "$out_dir/plan" ]; then
	# Surface qacct's own complaint ("job id N not found", etc.)
	cat "$out_dir/qacct_err" >&2
	echo "${0##*/}: no matching GPU job records" >&2
	exit 1
fi

#=== 2-4. GPU types, logs, stats, output (qacct_gpu_lib.sh) ====================
qg_report "$out_dir" "$summary" "$csv"
