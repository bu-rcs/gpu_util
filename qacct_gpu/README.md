# qacct_gpu

`qacct` plus GPU usage for SCC batch jobs. It takes job records from SGE
accounting and adds utilization, idle time and peak memory from the
per-node `gpustats` logs.

```bash
qacct_gpu -j 6964876                      # one job (one block per task for array jobs)
qacct_gpu -o someuser                     # summary of that user's GPU jobs
qacct_gpu --csv -o someuser -d 30 > x.csv # one CSV row per record
qacct_gpu -f /usr/local/sge/sge_root/default/common/accounting.2025 -j 2343372   # last year's job

qacct_gpubatch.sh jobids.txt > report.txt               # many ids: one block each, in file order
qacct_gpubatch.sh --csv jobids.txt -b 2610010000 > r.csv # narrow the scan: much faster
```

Every option except `--csv` goes straight to `qacct`, so filters like `-o`, `-h`, `-q`, `-d`,
`-b/-e` and `-f` all work. For `qacct_gpubatch.sh`, put the job-id file first and any `qacct`
options after it. The script supplies `-j` itself.

## Files

| file | what |
|---|---|
| `qacct_gpu.sh` | The command. `/projectnb/scv/jbevan/qacct_gpu` is a symlink to it. |
| `qacct_gpubatch.sh` | Same output for a list of job ids, from one `qacct` scan instead of one per id. |
| `qacct_gpu_lib.sh` | Code shared by both (sourced, not run). **Must stay in the same directory**: the scripts find it via `readlink -f`, which works through the symlink. |
| `acct.pl` | Older Perl reader of the raw accounting file (date range, `-o` = OnDemand cell). Not used by the above. |
| `notes.txt` | Old scratch notes/links. |

Each script's header documents its usage and output. The metric definitions are in `qacct_gpu.sh`.

## Before you edit: this directory is live

- **The symlink serves this working tree directly.** Any saved edit is instantly what everyone running
  `qacct_gpu` gets, and checking out another branch here switches the tool. So develop and test in a
  copy (e.g. a scratch dir holding all three `.sh` files), then `cp` the files in. Copying onto an
  existing file keeps its permissions. The directory is setgid `rcsmetrics`.
- **Git:** remote is `github.com/bu-rcs/gpu_util`, and the work lives on the personal branch
  `josh`. The local `josh` branch's upstream is `origin/main` (that's why `git status` says
  "ahead of origin/main"), so **push explicitly**: `git push origin josh:josh`. A bare `git push` may
  target `main`. Other people have their own branches (`katia`, `ryan`).
- **Known consumer:** the `audit-gpu` Claude skill (`~jbevan/.claude/skills/audit-gpu/audit_gpu.py`)
  parses the text output as `name value` blocks between `=====` lines. It parses `start_time`/`end_time`
  in qacct's own format (`%a %b %d %H:%M:%S %Y`). That's why ISO dates are CSV-only, so don't change
  the text-mode time format or the label names without checking it. Besides those, it reads `owner`,
  `qname`, `jobnumber`, `taskid`, `exit_status`, `num_gpus`, `gpu_avg_util`, `gpu_idle`, `peak_vram`,
  `gpu_type`, and `wallclock` (only if the times won't parse). It does not read `gpu_time`,
  `gpu_util_each`, `gpu_idle_each`, `gpu_mem` or `job_type`, and ignores labels it doesn't know.
- **Known CSV consumer:** `/projectnb/jbrcs/aicr/gpu_user_summary.py` reads columns by name, including
  `gpu_util_each`, `gpu_idle_each` (";"-separated, one value per GPU), `gpu_mem` and `job_type`. New columns go at the
  end of the row so positional readers of the older columns keep working.

## How it works

1. **Stage 1 (per script)** gets `qacct -l gpu_c=6.0 ... -j` output and splits it on the `=====`
   separators. Meanwhile `qg_gpukeys` lists the records that requested GPUs, and afterwards
   `qg_gpu_only` drops the rest (CPU-only jobs on GPU nodes; see "SGE accounting" below). Using the awk helpers in `QG_AWK`, it writes three files into a temp dir:
   - `recs`: the displayed lines of each record.
   - `plan`: one line per record, with its host, the `<jobnumber>.<taskid>` key, the months it spans,
     and its start and end times (epoch).
   - `need`: one line per needed `(host, month)` log, with the latest job end time among the
     records that need it.

   `qacct_gpubatch.sh` reads every GPU record once and keeps those whose job number is in the list.
2. **Stage 2:** one `qhost -F gpu_type` call gives each host's GPU model.
3. **Stage 3:** finds each needed log once. It uses the central archive in place if its copy already
   covers the job (see below). Otherwise it `scp`s the month's file from the node, up to `$NSLOTS`
   at a time (1 if unset), and deletes failed or partial copies. If the node is unreachable, it falls
   back to the archive and warns that later samples are missing.
4. **Stage 4:** one gawk pass reads each log file once and aggregates per
   `(host, month, <jobnumber>.<taskid>)` for only the keys some record wants. It then prints text,
   CSV, or the summary (whose averages are computed in `bc`).

Only stage 1 differs between the scripts. Everything else is in `qacct_gpu_lib.sh` (`QG_FIELDS`,
`QG_AWK`, `qg_report`).

## Data sources

### SGE accounting / qacct

- **qacct reads the whole accounting file on every call**, whatever the filter. The cost is
  roughly a fixed ~4–6 s plus **~0.17 ms per record it prints** (measured Aug 2026). That's why:
  - a single job costs ~7–14 s, and no filter can get below that;
  - an unfiltered scan of all GPU records takes ~3.5 min (650k+ records, 7.5 GB file in Nov 2026);
  - **any filter that cuts the number of matches (`-b/-e`, `-d`, `-o`, `-h`) is what makes
    it fast.** None of them skip reading. Measured with batch jobs:
    | options | time |
    |---|---|
    | unfiltered | 202 s |
    | `-b 2607010000` | 98 s |
    | `-b 2611050000` | 23 s |
- **The file rotates yearly.** `accounting` is the current year, and `accounting.YYYY` holds earlier
  years (back to 2013) in `/usr/local/sge/sge_root/default/common/`. Without `-f`, last year's jobs
  are "not found". Job numbers aren't a safe key across years: pair an id with the file it came from.
  (Dec 2025 ids were ~2.34M; Jul–Nov 2026 ids ran ~6.6M–8.4M.)
- **`qacct -l` matches the queue/host a job ran on, not what the job requested.** So
  `-l gpu_c=6.0` (inherited from the original script) returns *every* job that ran on a GPU node,
  including CPU-only jobs (`-l no_gpu=TRUE`) in GPU queues. On a 1-GPU node, `-l gpus=1` matched a
  CPU job and `-l gpus=5` did not. Some users' "GPU jobs" were 100% CPU jobs (Nov 2026: 26k of 140k
  records across 67 users). Several `-l` options are ANDed (checked: `-l gpu_c=6.0 -l gpu_type=V100`
  hides a P100 job).
- **So a GPU job is one whose request contains `gpus=N`, N ≥ 1.** qacct doesn't print the request,
  but the raw accounting file has it in field 40 (`category`), e.g.
  `-l gpu_compute_capability=3.5,gpus=1,h_rt=259200 ...` vs `-l h_rt=43200,no_gpu=TRUE ...`.
  Values seen: `gpus=1`…`gpus=8` and `gpus=1.0`. `qg_gpukeys` greps the file for `gpus=` in the
  background while qacct runs (≈14 s, mostly I/O, so it adds no wall time), and `qg_gpu_only` keeps
  the qacct records that match one. Checked on 10 users: every dropped record lacked GPU samples.
- **Interactive jobs (`job_type`).** SGE adds `-I y` to the request of `qrsh`/`qlogin` jobs, so
  `qg_gpukeys` also reports that flag. Job names: plain `qrsh` sessions are `QRLOGIN`, `qlogin`
  sessions `QLOGIN`, `qrsh <command>` jobs are named after the command (`bash`, `env`, a script),
  OnDemand apps `ood-<app>` (submitted as ordinary batch jobs, never `-I y`). In 2026, 2,766 of
  10,828 QRLOGIN GPU records lacked `-I y` (cause unknown, spread over the year and many users),
  and 554 `-I y` records had other names. So `job_type` is `qrsh` if `-I y` or the name is
  QRLOGIN/QLOGIN, `ood` if the name starts with `ood-`, else `batch`.
- **Job numbers repeat within one accounting file.** `accounting.2025` has two jobs numbered 2343372:
  a CPU job of one user in January and a 2-GPU job of another in December. Match raw lines on
  job number, task **and** start time (the code allows ±1 h for DST). Raw field 36 is the task id,
  0 for a non-array job (qacct: `undefined`); field 10 is the start time in epoch seconds.
- **When nothing matches:** an unknown job id gives `error: job id N not found` and exit 1. A filter
  that excludes everything prints **nothing, with exit 0**.
- **Array jobs are the majority:** 327,826 of 593,871 GPU records (Aug 2026) were array tasks. Each
  task is its own record, with `taskid` set; non-array jobs show `taskid undefined`.
- **The separate OnDemand SGE cell** (`/usr/local/sge/sge_root/ood/common/accounting`, queue `ood`,
  its own job-number range around 456k) had **no GPU records** in the 7 days checked on 2026-11-07.
  GPU OnDemand sessions (e.g. `ood-desktop` in `onrcc-gpu`) are in the main file.

### gpustats logs (per node)

These are written by `/var/log/gpustats/gpustats.pl` (Mike Dugan) on every GPU node, every 5
minutes. Each run writes one line per GPU, appended to `/var/log/gpustats/<yymm>` (named by the
node's local date). Nodes keep about 3 years. Columns, from `gpustats.pl`:

| col | content |
|---|---|
| 1 | epoch seconds |
| 2 | PCI bus id (one per GPU) |
| 3 | GPU utilization % (`%5.1f`, always whole numbers in practice) |
| 4 | memory-controller utilization % |
| 5, 6 | user and group of a process on the GPU; `-  -` if none |
| 7 | **`<jobnumber>.<taskid>`** from SGE's `/var/spool/sge/gpu_allocation`, or `-` if unallocated |
| 8, 9 | memory total / used, MiB |
| 10 | temperature, °C |
| 11 | power draw, W |

- **Column 7 records allocation, not activity.** A GPU allocated to a job carries the job id even
  while idle, so `num_gpus` counts allocated GPUs and idle ones drag `gpu_avg_util` down.
- **Expect junk lines**, e.g. `<epoch> NVIDIA-SMI couldn't find libnvidia-ml.so ...`. They never match
  an exact column-7 key.

### Central archive

`/project/scv/dugan/gpustats/data/<host>/<yymm>`:

- **Synced weekly**, Mondays ~05:01. For complete months it's byte-identical to the node's copy
  (md5 checked).
- **Coverage:** 183 host dirs, with months back to 1608 on some hosts. A few junk month names come
  from bad node clocks (e.g. `scc-eb4/9606`) and are harmless.
- **The rule used:** the archive copy covers a job if its last line's timestamp is ≥ the job's end
  time. Samples are appended in time order (checked), so this holds. Reading it in place takes 0.007 s
  versus ~0.33 s per `scp`. Only jobs that ended since the last sync need the node.

## Things that have bitten this code

1. **awk `==` compares "numeric-looking" strings as numbers.** `$7 == key` treats `7701258.3` and
   `7701258.30` as equal, and `8265759.160` as equal to `8265759.1600`, so array tasks N and N0
   silently merged. Match through array subscripts (always string), or force a string comparison
   with `$7 "" == key ""`.
2. **An apostrophe inside a single-quoted awk program** (e.g. in a comment: `the record's`) ends the
   shell string. `QG_AWK` and the stage-4 program are single-quoted, so keep apostrophes out of them,
   and run `bash -n` after editing.
3. **Don't read a fixed number of lines per qacct record.** A record missing one field shifted every
   later record and dropped the last job. Split on the `=====` lines instead.
4. **`date --date=""` returns today.** The original script parsed `$starttime` (never set) and so
   read the current month's log for every job.
5. **Don't `grep` for a job id.** Seven-digit ids occur inside the 10-digit timestamps. Match column 7
   exactly.
6. **`qhost ... | grep $host -A 1` prefix-matches** (`scc-x0` matches `scc-x02`). Use `qhost -h host`
   or exact field matching.
7. **Summary averages are truncated by `bc` (`scale=3`), not rounded.** Numbers print with awk's
   default `%.6g`. Both were kept deliberately so outputs stay byte-comparable.
8. **Environment:** bash 4.4 (no `$EPOCHREALTIME`), gawk 4.2.1 (`-e`, `mktime`, `delete arr` are
   gawk-only). Users' CPU should be limited to `$NSLOTS` cores, which is why node copies run in
   parallel only up to `$NSLOTS`.

## Testing changes

These records are reference values for regression checks:

| record | expected |
|---|---|
| `-j 6964876` (scc-x02, P100, Jul 29 → Aug 1 2026, spans 2 months) | 1 GPU, 55.6157 %, wallclock 4320, gpu_time 2402.6, gpu_idle 1880, peak 8903 MB, ru_wallclock 259201 |
| `-j 6624759` (scc-201, V100) | 66.0328 %, wallclock 305, peak 5764 MB |
| `-j 7210786` | 99 tasks on 22 hosts; on scc-x02, tasks 27/35/51/2 have wallclock 40/50/30/0 |
| `-j 7701258`, tasks 3 and 30 (same host and month) | wallclock 35 and 30. A merging bug shows 65 for both. |
| `-j 8265759`, tasks 160 and 1600 | task 160 has no samples. A merging bug gives it task 1600's. |
| `-f …/accounting.2025 -j 2343372` | scc-e02, A6000, 2 GPUs, 6.57292 %, wallclock 720, gpu_time 94.65, peak 10285 MB, gpu_util_each 7.64583;5.5, gpu_idle_each 655;675, gpu_mem 46068 |
| `-h scc-x02 -b 2610010000 -e 2610310000` (summary) | njobs 101, ntasks 529, util 19.917, wallclock 30, idle 9, vram 914. (Before CPU jobs were dropped: 111, 642, 16.411, 25, 8, 753; the 113 records dropped, 111 by one user, had no GPU samples.) |
| `job_type`: `-j 4600826` / `4603300` / `4623092` / `2533172` / `4600139` | batch / qrsh (QRLOGIN) / qrsh (QLOGIN) / qrsh (`binary_search.sh`, only `-I y` says so) / ood (ood-jupyter). 6964876 is ood (ood-desktop). |
| `-j 5720836` (lzgan, `no_gpu=TRUE`, ran on GPU node scc-b04) | `no matching GPU job records`. Before the fix it was listed as a GPU job with zero samples. |

Techniques that worked well:

- **Get baselines from git:** run `git show HEAD:qacct_gpu/<file>` into a scratch dir, and compare
  old and new outputs with `cmp`. If a change is meant to alter output, check that only the
  intended lines differ.
- **Verify the batch script by equivalence:** its output must be byte-identical to looping
  `qacct_gpu -j ID` over the same ids. Remove the leading `=====` line from all but the first output
  (or the header row, for CSV).
- **Check CSV cell by cell against text mode** (a small Python script using `csv.DictReader`).
- **Use a stand-in `qacct`:** put a script named `qacct` that `cat`s saved real output first on
  `PATH`. It exercises the batch script in seconds instead of a 3-minute scan.
- **Use a stand-in `scp`** that only `sleep`s and then copies from the archive. It tests parallelism
  and failure handling without using CPU, and can be made to fail for chosen hosts after writing a
  partial file.
- **Use fixed `-b/-e` windows for comparisons, not `-d`.** `-d` windows move, and records keep
  appearing as recent jobs finish.
- **Watch for test artifacts:** a shell timing function whose output was redirected along with the
  command once made identical outputs look different.

## Known limitations / open questions

- The ~7–14 s `qacct` floor per call. Getting around it would mean reading the accounting file
  directly and reimplementing qacct's filters.
- Only the logs of the record's `hostname` (the master node) are read. It hasn't been checked how
  multi-node GPU jobs show up, or whether they'd be undercounted.
- `wallclock` counts 5-minute samples, so jobs under ~5 minutes show 0. Use `ru_wallclock` (exact
  seconds) for run time.
- If a node's logs are gone and the archive lacks the month, that job's stats are zeros, with a
  warning on stderr.
- A job that requested a GPU only as a soft request (`-soft -l gpus=1`) counts as a GPU job whether
  or not it got one. None were seen.
