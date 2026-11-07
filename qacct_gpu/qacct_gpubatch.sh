#!/bin/bash
# Usage:
# $ qacct_gpubatch.sh [--csv] JOBID_FILE > report.txt
# Examples:
# $ qacct_gpubatch.sh jobids.txt > report.txt
# $ qacct_gpubatch.sh --csv jobids.txt > report.csv
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
# That pass takes a few minutes (qacct's time goes mostly into printing the
# ~650k records it matches), but it does not grow with the length of the list.
#
# Only stage 1 is specific to this script; the rest is shared with
# qacct_gpu.sh in qacct_gpu_lib.sh, which must sit next to this script.
#
# Requires gawk.

here=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
. "$here/qacct_gpu_lib.sh" || { echo "${0##*/}: cannot load $here/qacct_gpu_lib.sh" >&2; exit 1; }

usage() {
	echo "Usage: ${0##*/} [--csv] JOBID_FILE" >&2
	exit 2
}

csv=false
idfile=
for a in "$@"; do
	if [ "$a" = "--csv" ]; then
		csv=true
	elif [ -z "$idfile" ]; then
		idfile=$a
	else
		usage
	fi
done
[ -n "$idfile" ] || usage
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
echo "${0##*/}: $nids job ids -- reading every GPU record (a few minutes)..." >&2
qacct -l gpu_c=6.0 -j 2>"$out_dir/qacct_err" |
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

nrec=$(wc -l < "$out_dir/plan")
nmiss=$(wc -l < "$out_dir/missing")
echo "${0##*/}: matched $((nids - nmiss)) of $nids ids ($nrec records)" >&2
if [ "$nmiss" -gt 0 ]; then
	echo "${0##*/}: no GPU accounting record (not a GPU job, or older than the current accounting file) for $nmiss id(s):" >&2
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
