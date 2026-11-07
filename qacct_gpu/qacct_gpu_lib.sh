# qacct_gpu_lib.sh -- code shared by qacct_gpu.sh and qacct_gpubatch.sh.
# Not a command: both scripts source it from the directory they live in, so
# it has to stay next to them.
#
# Each script gets its qacct records its own way ("stage 1"), using the awk
# helpers in QG_AWK, which write three files into the script's temp dir:
#   recs  the displayed lines of each record, each record preceded by a "\001" line
#   plan  one line per record: index, host, <jobnumber>.<taskid>, jobnumber, months
#   need  one line per (host, month) log file: host, month, latest job end (epoch)
# qg_report then does everything else (stages 2-4).
#
# Requires gawk (mktime, -e, "delete array").

# Relevant fields from qacct we want to display, and in this order the first
# CSV columns. (Fields needed to find the GPU logs are read from qacct's
# output directly, so editing this is safe.)
QG_FIELDS="qname|hostname|owner|jobname|jobnumber|taskid|start_time|end_time|exit_status|ru_wallclock|cpu"

# awk helpers, loaded with:   gawk -e "$QG_AWK" -e '<program>'
# (No apostrophes in here: this is all one single-quoted shell string.)
QG_AWK='
# Call first, from BEGIN, with the fields to keep (QG_FIELDS)
function qg_init(fields,   mn, i) {
	fre = "^(" fields ")$"
	split("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec", mn, " ")
	for (i = 1; i <= 12; i++) mon[mn[i]] = i
}

# Call on every line of a qacct record: keeps the displayed lines in rec and
# picks out what is needed to find the GPU logs
function qg_line(   a) {
	if ($1 ~ fre) rec = rec $0 "\n"
	if ($1 == "hostname") { split($2, a, "."); host = a[1] }
	else if ($1 == "jobnumber") jn = $2
	else if ($1 == "taskid") task = $2
	else if ($1 == "start_time") st = $0
	else if ($1 == "end_time") et = $0
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

# Write the record held in rec/host/jn/task/st/et to recs and plan, note the
# log files it needs, then clear it. Needs -v recs=... plan=... need=...
function flush(   sm, em, y, m, ye, me, months, nm, ms, j, k, e) {
	if (rec != "") {
		n++
		printf "\001\n%s", rec > recs
		# qacct reports "undefined" for non-array jobs, which is also what
		# gpustats records, so no special-casing is needed
		if (task == "") task = "undefined"
		# Every month from start to end inclusive
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
}

# Call last, from END, after the final flush. Writes need, and makes sure plan
# and need exist even when no record named a log file (a job that never
# started has no dates), so the shell side never trips over a missing file.
function qg_finish(   k) {
	printf "" > plan
	printf "" > need
	for (k in maxend) print k, maxend[k] > need
}

# "Wed Jul 29 14:15:47 2026" -> "2026-07-29 14:15:47"; anything else unchanged
function isotime(s,   f) {
	if (split(s, f, " ") == 5 && (f[2] in mon) && f[3] ~ /^[0-9][0-9]?$/ &&
	    f[4] ~ /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]$/ && f[5] ~ /^[0-9][0-9][0-9][0-9]$/)
		return sprintf("%s-%02d-%02d %s", f[5], mon[f[2]], f[3], f[4])
	return s
}

# CSV-quote a value if it contains a comma, double quote or line break
function csvq(s) {
	if (s ~ /[",\r\n]/) {
		gsub(/"/, "\"\"", s)
		return "\"" s "\""
	}
	return s
}
'

# Stages 2-4: GPU types, find the logs, aggregate them and print.
# Usage: qg_report OUT_DIR SUMMARY CSV        (SUMMARY and CSV: true or false)
qg_report() {
	local dir=$1 summary=$2 csv=$3
	local central=/project/scv/dugan/gpustats/data
	local host mon maxend c last n

	#=== 2. GPU type of every host, in one qhost call ==========================
	qhost -F gpu_type 2>/dev/null | gawk '
		/^[^ \t-]/ { h = $1; next }
		/gpu_type=/ { split($0, a, "gpu_type="); sub(/[[:space:]]+$/, "", a[2]); print h, a[2] }' > "$dir/types"

	#=== 3. Find each needed (host, month) log file, once each ================
	# The central archive is a weekly copy of each node's /var/log/gpustats.
	# Its copy covers a job if its last sample is at or after the job's end
	# time (samples are appended in time order), so read it in place when it
	# does -- no network, no copy. Otherwise the job ended since the last
	# sync, and the node's own copy is the only complete one.
	: > "$dir/logmap"
	: > "$dir/fetch"
	while read -r host mon maxend; do
		c=$central/$host/$mon
		if [ -f "$c" ]; then
			last=$(tail -n 1 "$c")
			last=${last%% *}
			if [[ $last =~ ^[0-9]+$ ]] && [ "$last" -ge "$maxend" ]; then
				echo "$host $mon $c" >> "$dir/logmap"
				continue
			fi
		fi
		echo "$host $mon" >> "$dir/fetch"
	done < "$dir/need"

	# Copy the rest from the nodes, up to $NSLOTS at a time (1 if unset). A
	# failed copy is deleted so it can never pass for a complete one.
	n=${NSLOTS:-1}
	[[ $n =~ ^[1-9][0-9]*$ ]] || n=1
	xargs -r -P "$n" -L 1 sh -c '
		mkdir -p "$0/$1" &&
		scp -o StrictHostKeyChecking=no -q "$1:/var/log/gpustats/$2" "$0/$1/$2" 2>/dev/null ||
		rm -f "$0/$1/$2"' "$dir/gpustats" < "$dir/fetch"

	while read -r host mon; do
		c=$central/$host/$mon
		if [ -f "$dir/gpustats/$host/$mon" ]; then
			echo "$host $mon $dir/gpustats/$host/$mon" >> "$dir/logmap"
		elif [ -f "$c" ]; then
			# Better than nothing, but samples after the last sync are missing
			echo "$host $mon $c" >> "$dir/logmap"
			last=$(tail -n 1 "$c")
			last=${last%% *}
			if [[ $last =~ ^[0-9]+$ ]]; then
				echo "warning: $host unreachable; central archive for $host/$mon only runs to $(date -d "@$last" '+%F %R'), later samples missing" >&2
			else
				echo "warning: $host unreachable; used central archive for $host/$mon, may be incomplete" >&2
			fi
		else
			echo "warning: no gpustats for $host/$mon (node unreachable, not in archive)" >&2
		fi
	done < "$dir/fetch"

	#=== 4. Aggregate the logs and print, in ONE pass =========================
	gawk -v summary="$summary" -v csv="$csv" -v fields="$QG_FIELDS" \
	     -v plan="$dir/plan" -v logmap="$dir/logmap" \
	     -v types="$dir/types" -v recs="$dir/recs" -v bcf="$dir/bc" -e "$QG_AWK" -e '
	BEGIN {
		qg_init(fields)

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
		# (host, month, <jobnumber>.<taskid>) for just the keys some record
		# needs. Col 7 in gpustats is exactly "<jobnumber>.<taskid>"; as an
		# array subscript it is compared as a string, so 7701258.3 never
		# matches 7701258.30 (awk == would compare them as equal numbers).
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
				# Busy GPU-minutes: each sample stands for 5 minutes at its
				# utilization. Summed over all the job GPUs, so like gpu_idle
				# it can exceed wallclock.
				gtime = s * 5 / 100
				# Wallclock based on "gpustats" rows
				wall = int(5 * n / ng)
				# This is a total across ALL GPUs, and therefore could exceed "wallclock"
				idlet = id * 5
			}

			if (summary == "false" && csv == "true") {
				# Pick each field out by name, so one that is missing leaves
				# an empty cell instead of shifting the columns after it
				delete val
				nl = split(T[i], L, "\n")
				for (x = 1; x <= nl; x++)
					if (match(L[x], /^[^ ]+ +/)) {
						fv = substr(L[x], RLENGTH + 1)
						sub(/[ \t]+$/, "", fv)
						val[substr(L[x], 1, index(L[x], " ") - 1)] = fv
					}
				row = ""
				for (c = 1; c <= ncol; c++) {
					fv = val[col[c]]
					if (col[c] ~ /_time$/) fv = isotime(fv)
					row = row csvq(fv) ","
				}
				print row ngpus "," avg "," wall "," gtime "," idlet "," peak "," csvq(gtype[h])
			} else if (summary == "false") {
				printf "%s", T[i]
				print "num_gpus     " ngpus
				print "gpu_avg_util " avg " %"
				print "wallclock    " wall " mins"
				print "gpu_time     " gtime " mins"
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
	}'
}
