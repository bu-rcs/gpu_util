# Questions

1. For a specific GPU/queue/GPU-type/All Shared GPU/All Buyin GPU/All GPU queues/: total GPU utilization - time GPU jobs ran/all time (regardless whether job used GPUs or did not)
    
2. Actual `%%` utilization of gpus over the time:
   - can come solely from Mike's file `/project/scv/dugan/gpustats/data` as it lists the job for every period of time
   - we will distinguish 3 types of utilization: job running vs no running; gpu is used vs. gpu is not used; true gpu utilization;

3. How many OOD vs. batch jobs (accounting file is needed);
4. What percentage of jobs has not used GPU at all 
5. Per job (per OOD and per batch) - per user, per project, per queue, overall:
   - average time before GPU utilization starts
   - average time at the end of the job GPU is not longer utilized
   - %% of time GPU(s) are used over the length of the job
   - medium/mean/max utilization value during the job
6. Distribution of jobs requesting 1 GPU vs. 2 GPUs or more
7. GPU memory usage analyzis - can only be done when/if Mike adds additional inormation to his files


## RCS Resource utilization questions

### Machine Utilization questions (low priority)

## Queue utilization questions

## Project utilization questuions

## User-related questions
