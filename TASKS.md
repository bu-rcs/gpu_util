### Post 4/7/25 meeting
1. x Report by queue - added to report gen
2. x Page 8: Add values for each bar, i.e. 56 (32%)
3. x Page 9: Add only percentages for the top portion of each bar( you can place them to the middle right). Use only one digit after a period.
4. x Page 10: see if you can add a table to the upper-right corner to specify number of jobs for each count of GPUs.
5. (SWITCHED ALL TO class_user) The last 2 pages and page 8: To split on buy-in  vs shared resources, use the column that is "shared" for "*-pub* queues.
6. -
7. x For all graphs starting from page 5 use "class-user" from Katia's file to diff. between shared vs. buy-in
8. x Fix README file to list the right python script name.

- integrate new gpu util file parser, test & compare to prev
   - working for old files -> generates same output for default vals
SOME OUTPUTS:
=========
python reportgenerator.py -y=25 -m=04
Skipping missing or corrupted file: /project/scv/dugan/gpustats/data/scc-e04/2504
Skipping missing or corrupted file: /project/scv/dugan/gpustats/data/scc-e02/2504

broken line!!!:
1743424803 Unable to determine the device handle for GPU3: 0000:3D:00.0: Unknown Error   0.0   0.0 -        - 3322342.undefined
=========

python reportgenerator.py -y 25 -m 03
Skipping missing or corrupted file: /project/scv/dugan/gpustats/data/scc-e04/2503
Skipping missing or corrupted file: /project/scv/dugan/gpustats/data/scc-e02/2503
Skipping missing or corrupted file: /project/scv/dugan/gpustats/data/scc-306/2503  <----- WHY IS THIS BROKEN???



### Post 3/31/25  
Ryan's notes todo:  
- x rename reserved
- x rename second chart to gpu hours 
- x top users/projects for shared/buyin
- x repeat low 5% for shared
- x add numbers on top of bars (done for n gpu, is it really needed for others?)
- x proportions for squashed chart doesnt look great
- x gpu hist numbers
- x Utilization graph over only shared nodes
- x sahares vs buyin last graph
- x quick stats undefined task id, truncate decimals
- x refine descriptions throughout, removing bboxes
- x output duplicates warning
- x FIGURE OUT jobid RECYCLE! Fillforward user/project? might fix issue and allow for join in jobid and user! - removes a bunch of missings, but not all
- x PANDAS MERGE WILL CREATE MULTIPLE ROWS, WE CAN THEN FILTER THESE BY SUBMISSION TIME AND END TIME AND GPU UTIL TIME TO KEEP ONLY GOOD ONES
- x explore this issue: python reportgenerator.py -y 24 -m 12 pandas.errors.IntCastingNaNError: Cannot convert non-finite values (NA or inf)
- x function to save merged dataset from date to date -> NOTE already done basically with process_gpu_data_range
- x CHECK old function on new month data, does new columns mess with logic? YES, IT DOES, NEED TO GET NEW FUNCTION BUILT IN!!!
- x explore this issue: python reportgenerator.py -y 25 -m 03  
         Skipping missing or corrupted file: /project/scv/dugan/gpustats/data/scc-e02/2503  
         Skipping missing or corrupted file: /project/scv/dugan/gpustats/data/scc-306/2503  


### Post 3/18/25
1. grep ,4086404 /projectnb/rcsmetrics/accounting/data/scc/2024.csv -> scc-ye2 has no gpu, but recorded  
2. added node name. did not add username to merge since it can be missing for many values. alternative?  
3. added nan percent warning to visuals.ipynb. can be also included in the helper function or pdf generation  
4. created pdf file, what other things to add?  
5. update function to support old + new mike gpu util files  
6. todo: fix branch, new PR  
7. can generate report for specific year month, project (optional), user (optional), "Quick Stats" page generated if specified

Questions:  
- How to tell if a gpu belongs to shared vs buyin? When idle no qname: Katia node file
- Jobname recycle, how to tell what user since missing for many?: find jobids that are less, these are recycled, these are sep dates. fill in user/owner by looking at same month node file to find it, correction algorithm only on recycled job ids
- Duplicate values? whats going on? 2024-01-21 22:58:02 weird merging time event? - get code to reproduce
- some nans when grouping over entire 2024 year...exploring this 153847 vs 137830: 505 jobs?, 3 users
   - year_2024_01[year_2024_01['owner']=='allenjb']['options'].values
   - causes some issues with generating report for whole year  
- one user requested 4 gpus and held an interactive session open for 48 hours 4 times last month! maybe this can be monitored!

### 3/10/25

- [x] Try to find GPUs jobs that are longer than a month (there are some in 2024) and see if they are not lost in the "year" analysis
- [x] Update yearly function to merge entire year rather than iterate over months -> **EQUAL BUT SLOWER!**
- [ ] Check cross year for yearly, or cross month for monthly
- [x] One more time interval to handle: from date to date (vs particular year or a month)
- [ ] Other items from Katia's list [https://github.com/bu-rcs/gpu_util/blob/katia/Questions.md]
- [x] CLI tool with python to get all useful information for a user, see qaccct -j \<jobid\>
- [ ] Show util for user, gpu memory usage
- [ ] Data viz should show gpu util based on used/total over time
- [ ] Shared vs buy in, <5% util, etc. fixes  


## Findings:  
- merging all files at once for yearly has same dataframe but is much slower
- investigating missing values: since using util as main table and merging accounting, we miss info for jobs that finish after the month
- some issues using job id + task id together for merge, how else can tasks be in options? using -t to check if undefined isnt great
- changed logic to ~(gpu_jobs["options"].str.contains("-t") | gpu_jobs['task_number'] != 0), mostly reduced nans from 130k to 200 ish
- job id 4086404 has gpu usage, specified "no_gpu=TRUE" in batch job options, does avg=TRUE nodes only have gpus? grep ,4086404 /projectnb/rcsmetrics/accounting/data/scc/2024.csv
- looking at "scc-techinfo -w=scc-ye2" no gpu available???
- other jobs: 4102432, 4093245, 4102429, 4102431: doesnt exist...?, 
- qacct -j 4102431: error: job id 4102431 not found
- 4102436 also no_gpu=TRUE

- 