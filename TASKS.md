### Post 3/18/25
1. grep ,4086404 /projectnb/rcsmetrics/accounting/data/scc/2024.csv -> scc-ye2 has no gpu, but recorded  
2. added node name. did not add username to merge since it can be missing for many values. alternative?  
3. added nan percent warning to visuals.ipynb. can be also included in the helper function or pdf generation  
4. created pdf file, what other things to add?  
5. update function to support old + new mike gpu util files  
6.

Questions:  
- How to tell if a gpu belongs to shared vs buyin? When idle no qname
- Jobname recycle, how to tell what user since missing for many?
- Duplicate values? whats going on? 2024-01-21 22:58:02 weird merging time event?
- some nans when grouping over entire 2024 year...exploring this

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