#!/bin/bash
# Usage:
# $ qacct_gpubatch.sh [--csv] JOBID_FILE [qacct options] > report.txt
# Examples:
# $ qacct_gpubatch.sh jobids.txt > report.txt
# $ qacct_gpubatch.sh --csv jobids.txt > report.csv
# $ qacct_gpubatch.sh jobids.txt -b 2610010000 > report.txt   # jobs started since Oct 1
# $ qacct_gpubatch.sh jobids.txt -f /usr/local/sge/sge_root/default/common/accounting.2025
#
# JOBID_FILE holds one job id per line (blanks, junk and repeats are skipped).
# Prints exactly what "qacct_gpu -j ID" (or "qacct_gpu --csv -j ID") prints
# for each id, concatenated in the order the ids appear in the file, with one
# header row for CSV. An array job gives one block per task, as it does there.
# Ids with no GPU accounting record are listed on stderr along with progress,
# so redirecting stdout gives a clean report. See qacct_gpu.sh for what the
# fields mean.
#
# Why not just loop over qacct_gpu? Every qacct call reads the whole
# accounting file (~7-14 s), so hundreds of ids would take an hour or more.
# This makes ONE pass over all GPU records and keeps the requested ones.
# That pass takes a few minutes, but it does not grow with the length of the
# list.
#
# Arguments after JOBID_FILE go to that one qacct scan (anything but -j,
# which this script supplies). Filters that narrow it -- a start-time window
# (-b/-e YYMMDDhhmm), -d days, -o owner, -h host, -q queue, -l attr=val --
# can make it many times faster: qacct reads the whole file either way, but
# most of its time goes into printing the records it matches. Ids the filters
# exclude are reported as missing. qacct reads only the current year's
# accounting file unless given -f, e.g. for last year's jobs:
#   -f /usr/local/sge/sge_root/default/common/accounting.2025
#
# Only stage 1 is specific to this script; the rest is shared with
# qacct_gpu.sh in qacct_gpu_lib.sh, which must sit next to this script.
#
# Requires gawk.

here=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
. "$here/qacct_gpu_lib.sh" || { echo "${0##*/}: cannot load $here/qacct_gpu_lib.sh" >&2; exit 1; }

usage() {
	echo "Usage: ${0##*/} [--csv] JOBID_FILE [qacct options]" >&2
	exit 2
}

# "--csv" is ours, wherever it appears. The first other argument is the id
# file, and everything after it goes to qacct.
csv=false
idfile=
qargs=()
for a in "$@"; do
	if [ "$a" = "--csv" ]; then
		csv=true
	elif [ -z "$idfile" ]; then
		idfile=$a
	else
		qargs+=("$a")
	fi
done
[ -n "$idfile" ] || usage
case $idfile in
	-*) echo "${0##*/}: the job id file comes first, then any qacct options" >&2; usage ;;
esac
for a in "${qargs[@]}"; do
	if [ "$a" = "-j" ]; then
		echo "${0##*/}: don't pass -j: the job ids come from '$idfile'" >&2
		exit 2
	fi
done
[ -r "$idfile" ] || { echo "${0##*/}: cannot read '$idfile'" >&2; exit 1; }

# Create a temp directory to work out of, and always clean it up
out_dir=$(mktemp -d) || exit 1
trap 'rm -rf "$out_dir"' EXIT

# Clean the id list: strip whitespace and leading zeros, keep digits only,
# drop repeats, and preserve the file's order
gawk '{gsub(/[[:space:]]/, ""); sub(/^0+/, "")} /^[0-9]+$/ && !seen[$0]++' "$idfile" > "$out_dir/ids"
nids=$(wc -l < "$out_dir/ids")
[ "$nids" -gt 0 ] || { echo "${0##*/}: no job ids found in '$idfile'" >&2; exit 1; }

#=== 1. ONE pass over every GPU record, keeping the requested jobs ============
# Writes the usual recs/plan/need files (see qacct_gpu_lib.sh), with the
# records put in id-list order, plus
#   missing  ids that had no GPU accounting record
if [ ${#qargs[@]} -gt 0 ]; then
	echo "${0##*/}: $nids job ids -- reading GPU records matching: ${qargs[*]}" >&2
else
	echo "${0##*/}: $nids job ids -- reading every GPU record (a few minutes; qacct options after the file, e.g. -b YYMMDDhhmm, narrow it)..." >&2
fi
acct=$(qg_acct_file "${qargs[@]}")
qg_gpukeys "$acct" > "$out_dir/gpukeys" 2>"$out_dir/gpukeys_err" &
gk_pid=$!
qacct -l gpu_c=6.0 "${qargs[@]}" -j 2>"$out_dir/qacct_err" |
	gawk -v idfile="$out_dir/ids" -v fields="$QG_FIELDS" -v recs="$out_dir/recs" \
	     -v plan="$out_dir/plan" -v need="$out_dir/need" -v missing="$out_dir/missing" \
	     -e "$QG_AWK" -e '
	BEGIN {
		qg_init(fields)
		while ((getline id < idfile) > 0) { want[id] = 1; order[++nid] = id }
	}
	/^=+$/ { keep(); next }
	{ qg_line() }
	END {
		keep()
		printf "" > missing
		for (i = 1; i <= nid; i++) {
			id = order[i]
			if (!(id in nrec)) { print id > missing; continue }
			for (j = 1; j <= nrec[id]; j++) {
				rec = R[id, j]; host = HO[id, j]; jn = id
				task = TK[id, j]; st = ST[id, j]; et = ET[id, j]
				flush()
			}
		}
		qg_finish()
	}
	# Hold on to a requested record; they are written out in id-list order at
	# the end. (Array jobs keep their tasks in qacct order.)
	function keep(   c) {
		if (rec != "" && (jn in want)) {
			c = ++nrec[jn]
			R[jn, c] = rec; HO[jn, c] = host; TK[jn, c] = task; ST[jn, c] = st; ET[jn, c] = et
		}
		rec = host = jn = task = st = et = ""
	}'

# Drop CPU-only jobs that ran on GPU nodes (see qg_gpukeys); an id left
# with no records joins the missing list, in id-file order
wait "$gk_pid"
if [ $? -gt 1 ] || [ -s "$out_dir/gpukeys_err" ]; then
	cat "$out_dir/gpukeys_err" >&2
	echo "${0##*/}: cannot tell GPU jobs from CPU jobs: failed to read $acct" >&2
	exit 1
fi
qg_gpu_only "$out_dir" || exit 1
cut -f4 "$out_dir/plan" | sort -u > "$out_dir/kept"
gawk -v kept="$out_dir/kept" 'BEGIN { while ((getline k < kept) > 0) K[k] = 1 } !($0 in K)' \
	"$out_dir/ids" > "$out_dir/missing"

nrec=$(wc -l < "$out_dir/plan")
nmiss=$(wc -l < "$out_dir/missing")
echo "${0##*/}: matched $((nids - nmiss)) of $nids ids ($nrec records)" >&2
if [ "$nmiss" -gt 0 ]; then
	if [ ${#qargs[@]} -gt 0 ]; then
		why="not a GPU job (no gpus= request), or not matched by: ${qargs[*]}"
	else
		why="not a GPU job (no gpus= request), or older than the current accounting file"
	fi
	echo "${0##*/}: no GPU accounting record ($why) for $nmiss id(s):" >&2
	fmt -w 76 "$out_dir/missing" | sed 's/^/  /' >&2
fi
if [ "$nrec" -eq 0 ]; then
	cat "$out_dir/qacct_err" >&2
	exit 1
fi
echo "${0##*/}: locating $(wc -l < "$out_dir/need") gpustats log file(s)..." >&2

#=== 2-4. GPU types, logs, stats, output (qacct_gpu_lib.sh) ====================
qg_report "$out_dir" false "$csv"

echo "${0##*/}: done -- $nrec records" >&2
