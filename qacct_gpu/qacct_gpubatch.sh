#!/bin/bash
# Usage:
# $ qacct_gpubatch.sh JOBID_FILE > report.txt
# Example:
# $ qacct_gpubatch.sh jobids.txt > report.txt
# $ qacct_gpubatch.sh --csv jobids.txt > report.csv
#
# JOBID_FILE holds one job id per line (blanks, junk and repeats are skipped).
# Prints exactly what "qacct_gpu -j ID" prints for each id, concatenated in
# the order the ids appear in the file; an array job gives one block per task,
# as it does there. Ids with no GPU accounting record are listed on stderr
# along with progress, so redirecting stdout gives a clean report.
# --csv gives the same as "qacct_gpu --csv -j": a header row, then one row per
# record.
#
# Why not just loop over qacct_gpu? Every qacct call reads the whole
# accounting file (~7-14 s), so hundreds of ids would take an hour or more.
# This makes ONE pass over all GPU records and keeps the requested ones.
# That pass takes a few minutes (qacct's time goes mostly into printing the
# ~650k records it matches), but it does not grow with the length of the list.
#
# Only stage 1 differs from qacct_gpu.sh. Stages 2-4 are copied from it
# unchanged, so keep them in sync when either script changes.
#
# Requires gawk (mktime, "delete array").

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

# Per-job detail output, as with "qacct_gpu -j"
summary=false

# Clean the id list: strip whitespace and leading zeros, keep digits only,
# drop repeats, and preserve the file's order
gawk '{gsub(/[[:space:]]/, ""); sub(/^0+/, "")} /^[0-9]+$/ && !seen[$0]++' "$idfile" > "$out_dir/ids"
nids=$(wc -l < "$out_dir/ids")
[ "$nids" -gt 0 ] || { echo "${0##*/}: no job ids found in '$idfile'" >&2; exit 1; }

# Relevant fields from qacct we want to display, and in this order the first
# CSV columns (same as qacct_gpu.sh)
fields="qname|hostname|owner|jobname|jobnumber|taskid|start_time|end_time|exit_status|cpu"

#=== 1. ONE pass over every GPU record, keeping the requested jobs ============
# Writes the same recs/plan/need files as stage 1 of qacct_gpu.sh, with the
# records put in id-list order, plus
#   missing  ids that had no GPU accounting record
echo "${0##*/}: $nids job ids -- reading every GPU record (a few minutes)..." >&2
qacct -l gpu_c=6.0 -j 2>"$out_dir/qacct_err" |
	gawk -v idfile="$out_dir/ids" -v fields="$fields" -v recs="$out_dir/recs" \
	     -v plan="$out_dir/plan" -v need="$out_dir/need" -v missing="$out_dir/missing" '
	BEGIN {
		while ((getline id < idfile) > 0) { want[id] = 1; order[++nid] = id }
		fre = "^(" fields ")$"
		split("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec", mn, " ")
		for (i = 1; i <= 12; i++) mon[mn[i]] = i
	}
	/^=+$/ { keep(); next }
	{
		if ($1 ~ fre) rec = rec $0 "\n"
		if ($1 == "hostname") { split($2, a, "."); host = a[1] }
		else if ($1 == "jobnumber") jn = $2
		else if ($1 == "taskid") task = $2
		else if ($1 == "start_time") st = $0
		else if ($1 == "end_time") et = $0
	}
	END {
		keep()
		printf "" > plan
		printf "" > need
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
		for (k in maxend) print k, maxend[k] > need
	}
	# Hold on to a requested record; they are written out in id-list order at
	# the end. (Array jobs keep their tasks in qacct order.)
	function keep(   c) {
		if (rec != "" && (jn in want)) {
			c = ++nrec[jn]
			R[jn, c] = rec; HO[jn, c] = host; TK[jn, c] = task; ST[jn, c] = st; ET[jn, c] = et
		}
		rec = host = jn = task = st = et = ""
	}
	# "start_time   Wed Jul 29 14:15:47 2026" -> "2607"; "" if unparsable (e.g. "-/-")
	function yymm(line,   f) {
		if (split(line, f, " ") < 6 || !(f[3] in mon) || f[6] !~ /^[0-9][0-9][0-9][0-9]$/) return ""
		return sprintf("%02d%02d", f[6] % 100, mon[f[3]])
	}
	# Same line -> epoch seconds (local time, as qacct prints it); -1 if unparsable
	function epoch(line,   f, t) {
		if (split(line, f, " ") < 6 || !(f[3] in mon) || split(f[5], t, ":") != 3) return -1
		return mktime(f[6] " " mon[f[3]] " " f[4] " " t[1] " " t[2] " " t[3])
	}
	function flush(   sm, em, y, m, ye, me, months, nm, ms, j, k, e) {
		if (rec != "") {
			n++
			printf "\001\n%s", rec > recs
			# qacct reports "undefined" for non-array jobs, which is also what
			# gpustats records, so no special-casing is needed
			if (task == "") task = "undefined"
			# Every month from start to end inclusive. (Previously only the start
			# and end months were read, missing the middle of a 3+ month job.)
			sm = yymm(st); em = yymm(et); months = ""
			if (host != "" && sm != "" && em != "") {
				y = substr(sm, 1, 2) + 0; m = substr(sm, 3, 2) + 0
				ye = substr(em, 1, 2) + 0; me = substr(em, 3, 2) + 0
				if (y * 12 + m > ye * 12 + me)
					months = sm " " em
				else
					while (y * 12 + m <= ye * 12 + me) {
						months = months (months == "" ? "" : " ") sprintf("%02d%02d", y, m)
						if (++m > 12) { m = 1; y++ }
					}
			}
			print n "\t" host "\t" jn "." task "\t" jn "\t" months > plan
			# An unparsable end time forces a fresh copy from the node
			e = epoch(et); if (e < 0) e = 9999999999
			nm = split(months, ms, " ")
			for (j = 1; j <= nm; j++) {
				k = host " " ms[j]
				if (!(k in maxend) || e > maxend[k]) maxend[k] = e
			}
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

#=== 2. GPU type of every host, in one qhost call =============================
qhost -F gpu_type 2>/dev/null | gawk '
	/^[^ \t-]/ { h = $1; next }
	/gpu_type=/ { split($0, a, "gpu_type="); sub(/[[:space:]]+$/, "", a[2]); print h, a[2] }' > "$out_dir/types"

#=== 3. Locate each needed (host, month) log file, once each ==================
# The central archive is a weekly copy of each node's /var/log/gpustats. Its
# copy covers a job if its last sample is at or after the job's end time
# (samples are appended in time order), so use it in place when it does --
# no network, no copy. Otherwise the job ended since the last sync, and the
# node's own copy is the only complete one.
central=/project/scv/dugan/gpustats/data
: > "$out_dir/logmap"
while read -r host mon maxend; do
	c=$central/$host/$mon
	last=
	if [ -f "$c" ]; then
		last=$(tail -n 1 "$c")
		last=${last%% *}
		if [[ $last =~ ^[0-9]+$ ]] && [ "$last" -ge "$maxend" ]; then
			echo "$host $mon $c" >> "$out_dir/logmap"
			continue
		fi
	fi
	dest=$out_dir/gpustats/$host
	mkdir -p "$dest"
	if scp -o StrictHostKeyChecking=no -q "$host:/var/log/gpustats/$mon" "$dest/$mon" 2>/dev/null; then
		echo "$host $mon $dest/$mon" >> "$out_dir/logmap"
	elif [ -f "$c" ]; then
		# Better than nothing, but samples after the last sync are missing
		echo "$host $mon $c" >> "$out_dir/logmap"
		if [[ $last =~ ^[0-9]+$ ]]; then
			echo "warning: $host unreachable; central archive for $host/$mon only runs to $(date -d "@$last" '+%F %R'), later samples missing" >&2
		else
			echo "warning: $host unreachable; used central archive for $host/$mon, may be incomplete" >&2
		fi
	else
		echo "warning: no gpustats for $host/$mon (node unreachable, not in archive)" >&2
	fi
done < "$out_dir/need"

#=== 4. Aggregate the logs and print, in ONE pass ==============================
gawk -v summary="$summary" -v csv="$csv" -v fields="$fields" \
     -v plan="$out_dir/plan" -v logmap="$out_dir/logmap" \
     -v types="$out_dir/types" -v recs="$out_dir/recs" -v bcf="$out_dir/bc" '
BEGIN {
	while ((getline line < types) > 0) {
		sp = index(line, " ")
		if (sp) gtype[substr(line, 1, sp - 1)] = substr(line, sp + 1)
	}

	while ((getline line < plan) > 0) {
		split(line, p, "\t")
		i = p[1] + 0; N = i
		H[i] = p[2]; K[i] = p[3]; M[i] = p[5]
		if (!(p[4] in seenjob)) { seenjob[p[4]] = 1; njobs++ }
		nm = split(p[5], ms, " ")
		for (j = 1; j <= nm; j++) want[p[2], ms[j], p[3]] = 1
	}

	# Read every log file once, keeping running totals per
	# (host, month, <jobnumber>.<taskid>) for just the keys some record needs.
	# Col 7 in gpustats is exactly "<jobnumber>.<taskid>", so it is matched
	# whole: matching on the job number alone merged all of an array job`s
	# tasks together, and a bare grep can hit a 7-digit id inside the
	# 10-digit timestamp in col 1.
	while ((getline line < logmap) > 0) {
		split(line, l, " ")
		h = l[1]; mo = l[2]; path = l[3]
		while ((getline row < path) > 0) {
			split(row, f, " ")
			k = h SUBSEP mo SUBSEP f[7]
			if (!(k in want)) continue
			cnt[k]++                    # rows: one per GPU per 5 min sample
			sum[k] += f[3]              # col 3: utilization %
			if (f[3] < 1.0) idle[k]++
			if (!(k in vmax) || f[9] > vmax[k]) vmax[k] = f[9]    # col 9: vram MB
			if (!((k, f[2]) in bus)) { bus[k, f[2]] = 1; buses[k] = buses[k] " " f[2] }  # col 2: bus ID
		}
		close(path)
	}

	i = 0
	while ((getline line < recs) > 0) {
		if (line == "\001") i++
		else T[i] = T[i] line "\n"
	}

	if (summary == "true")
		print "scale=3; u=0; w=0; d=0; v=0" > bcf
	else if (csv == "true") {
		# Header: the displayed qacct fields, then the GPU stats
		ncol = split(fields, col, "|")
		hdr = ""
		for (c = 1; c <= ncol; c++) hdr = hdr col[c] ","
		print hdr "num_gpus,gpu_avg_util,wallclock,gpu_time,gpu_idle,peak_vram,gpu_type"
	} else
		print "=============================================================="

	for (i = 1; i <= N; i++) {
		h = H[i]
		nm = split(M[i], ms, " ")
		n = 0; s = 0; id = 0; ng = 0; havemax = 0
		delete seen
		for (j = 1; j <= nm; j++) {
			k = h SUBSEP ms[j] SUBSEP K[i]
			if (!(k in cnt)) continue
			n += cnt[k]; s += sum[k]; id += idle[k]
			if (!havemax || vmax[k] > peak) { peak = vmax[k]; havemax = 1 }
			nb = split(buses[k], bb, " ")
			for (b = 1; b <= nb; b++)
				if (!(bb[b] in seen)) { seen[bb[b]] = 1; ng++ }
		}

		# Need to catch the case where the job is too short for it to be
		# recorded in gpustats
		if (n == 0) {
			ngpus = 1; avg = 0; gtime = 0; wall = 0; idlet = 0; peak = 0
		} else {
			ngpus = ng
			# Note if there is more than 1 GPU this averages them together
			avg = s / n
			gtime = s
			# Wallclock based on "gpustats" rows
			wall = int(5 * n / ng)
			# This is a total across ALL GPUs, and therefore could exceed "wallclock"
			idlet = id * 5
		}

		if (summary == "false" && csv == "true") {
			# Pick each field out by name, so one that is missing
			# leaves an empty cell instead of shifting the columns after it
			delete val
			nl = split(T[i], L, "\n")
			for (x = 1; x <= nl; x++)
				if (match(L[x], /^[^ ]+ +/)) {
					fv = substr(L[x], RLENGTH + 1)
					sub(/[ \t]+$/, "", fv)
					val[substr(L[x], 1, index(L[x], " ") - 1)] = fv
				}
			row = ""
			for (c = 1; c <= ncol; c++) row = row csvq(val[col[c]]) ","
			print row ngpus "," avg "," wall "," gtime "," idlet "," peak "," csvq(gtype[h])
		} else if (summary == "false") {
			printf "%s", T[i]
			print "num_gpus     " ngpus
			print "gpu_avg_util " avg " %"
			print "wallclock    " wall " mins"
			print "gpu_time     " gtime
			print "gpu_idle     " idlet " mins"
			print "peak_vram    " peak " MB"
			print "gpu_type     " gtype[h]
			print "=============================================================="
		} else {
			# Sum the printed per-job values in bc, so the averages are
			# truncated exactly as before. bc cannot read 1e-05.
			a = avg ""
			if (a ~ /e/) a = sprintf("%.10f", avg)
			print "u=u+" a "; w=w+" wall "; d=d+" idlet "; v=v+" peak > bcf
		}
	}

	if (summary == "true") {
		print "u/" N > bcf
		print "scale=0; w/" N "; d/" N "; v/" N > bcf
		close(bcf)
		cmd = "bc < \"" bcf "\""
		while ((cmd | getline r) > 0) res[++nr] = r
		close(cmd)
		if (csv == "true") {
			print "njobs,ntasks,average_util,average_wallclock,average_idletime,average_peak_vram"
			print njobs "," N "," res[1] "," res[2] "," res[3] "," res[4]
		} else {
			print "GPU Job Summary:"
			print "njobs             " njobs
			print "ntasks            " N
			print "average util      " res[1] " %"
			print "average wallclock " res[2] " mins"
			print "average idletime  " res[3] " mins"
			print "average peak_vram " res[4] " MB"
		}
	}
}
# CSV-quote a value if it contains a comma, double quote or line break
function csvq(s) {
	if (s ~ /[",\r\n]/) {
		gsub(/"/, "\"\"", s)
		return "\"" s "\""
	}
	return s
}'

echo "${0##*/}: done -- $nrec records" >&2
