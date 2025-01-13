
# Meeting notes

*2025-01-13*

- Katia: fix the calculation of the number and % of jobs that do not use GPUs. Need to use comp_tot column
- Josh: Finalize the names of the columns in the file
- Katia: for the wallclock (batch vs. interactive) GPU job graphs, add the number of GPUs:
      - one graph can be stacked (by the number of GPUs used )
      - the other graph can have y axis gpu-hours (based on the number of GPUs used for the jobs

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

