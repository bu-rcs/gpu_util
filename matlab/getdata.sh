#/bin/bash -l

# This is necessary because cron doesn't know about the the scheduler

export SGE_ROOT=/usr/local/sge/sge_root
/usr/local/bin/qsub /projectnb/rcsmetrics/gpu_util/getdata.qsub
