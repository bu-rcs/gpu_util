# Main links:
- Mike's files: `/project/scv/dugan/gpustats/data`

# Plans
* Preliminarily: output format CSV (unless output gets very large)
* Visualization of results
  * What kinds of visualization
  * May be different for different users (queue owners, RCS staff, individual users)
* Interactive visualization
* Inputs: (User, queue, compute node), time period, multi-GPU, OOD (interactive) vs batch, fully idle jobs

# Meeting notes

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

# Reference
- Josh's original presentation: https://docs.google.com/presentation/d/1qy-anZATVVVB5fv80usWPAIZHH-HZffbzkc7xP058xs/edit#slide=id.g2cade5c334c_0_102
