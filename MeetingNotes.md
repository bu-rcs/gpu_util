
# Meeting notes

*2025-03-10*
Present: Katia & Ryan
1. Ryan completed the standard read python function and created pull request for RCShelpers_py repo (into main branch)
2. Pull request for gpu_util (into ryan branch)
3. Ryan's Todo:
      - Try to find GPUs jobs that are longer than a month (there are some in 2024) and see if they are not lost in the "year" analysis
      - One more time interval to handle: from date to date (vs particular year or a month)
      - Other items from Katia's list [https://github.com/bu-rcs/gpu_util/blob/katia/Questions.md]
4. Katia's todo: Check with Mike on "short" lines in gpustats file

*2025-02-24*
Present: Katia & Ryan

1. Generic Python functions that reads all three types of accounting file and returns a list
   - leave read_csv function returning a "generator". ; Write an example of using this function and a) "time it" and also separately convert to a list and print the number of records (the length of the list)
   - create a similar function for the regular accounting file (no extension)
   - read_feather:
   - investigate why csv file is smaller.
   - Do pull request into https://github.com/bu-rcs/rcshelpers_py repo
   - email/slack katia when you time all 3 as batch jobs.
2. For the read gpu recrods only
   - read_gpu_records _with _grep should go to the repo https://github.com/bu-rcs/gpu_util
   - Just for a test: read_gpu records from feather file and see if the number of records is the same if you use your read_gpu_recrods_with grep() function;
3. For the handling GPU taks:
   - JOsh's file /projectnb/rcsmetrics/gpu_util/data/010124_112524.txt
   - In addition to Josh's columns, could you make JobID and JobTask as separate integer columns
   - Create several functions: create "merged" filed
       a) merge everything for a particular year
       b) merge everything for a particular month
       c) merge everything for a particular month for a specific list of projects
       d) start creating text and visual reports : wallclocktime (in hours), wallclock in GPU-hours; also try to split them by "interactive" vs "batch jobs": job_name.str.startswith("ood") | (job_name == "QRLOGIN")
     e) Shared GPU utilization over the year; Buy-in utilization over the year; All utilization over the year;Katia's file: /projectnb/scv/utilization/katia/queue_info.csv

     

*2025-02-10*
1. Josh ToDo: Add "Task ID" column to the "input" (for Katia) file
2. Katia ToDo: Process the "input" file correctly to make sure records are not assumed to be jobs, as each recrods correspond to a GPU (so for 4 GPU-job there are 4 records)
3. Katia: Ask Ryan Gilbert to create a Python function that reads in accounting file as fast as possible.
4. Josh: Find a "problematic" GPUstats file with missing data/column

*2025-01-13*

- Katia: fix the calculation of the number and % of jobs that do not use GPUs. Need to use comp_tot column
- Josh: Finalize the names of the columns in the file
- Katia: for the wallclock (batch vs. interactive) GPU job graphs, add the number of GPUs:
      - one graph can be stacked (by the number of GPUs used )
      - the other graph can have y axis gpu-hours (based on the number of GPUs used for the jobs
- Note for Katia: number of hosts is not the same as the number of GPUs!

*12/9/24*
- Discuss with Charlie what other statistics we need for the Mike's files:
    - memory usage (and probably total memory so it is easier)
    - temperature ?
    - power?
 
 - Created Questions.md file to start collecting questions we want to answer.
 - We should now think about what kind of files we want to generate, where to store them and disscuss the naming conventions for them:
   - For the files that are about RCS resource utilization we will generate monthly files (with the naming convention similar to Mike) and this can be used by the Shiny App
   - For the User/queue/project utilization we will (at least for now) will generate a static report - given the start and end date and the information about username, project name or queue name.

*11/25/24*
- Naming convention for the file names (including intermediate csv); Do we give period of time (start day-end day) or month name.
- Josh and Katia will create branches and will be working within them

*11/18/24*  
Schedule
- Monday 10am-12:30pm every other week
- Josh schedule meeting
- Starting on 11/25 <br>
"Beta" MATLAB version of GPU util output here: /projectnb/rcsmetrics/gpu_util/data  
Repo  
- For not just code, but project docs and meeting notes
Intern
- Join January or February

