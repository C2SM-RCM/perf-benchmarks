#!/bin/bash

# COSMO CHECK script
#
# This script run severals check (see testsuite checkers for more info)
# It is expected to be called from the COSMO run directory using single precision executable
# The script prints TEST RESULT : OK and return 0 or TEST RESULT : FAIL and return 1

# Author       Xavier Lapillonne
# Date         26.06.2015
# Mail         xavier.lapillonne@meteoswiss.ch

# Set variables
checktool_dir=$(dirname $(realpath -s $0))
status=0

# set environment variables for the checkers
export TS_RUNDIR="."
export TS_LOGFILE="run.out"
export TS_LOGFILE_SLURM="slurm.log"
export TS_VERBOSE=1
export TS_REFOUTDIR="./reference_${REAL_TYPE}"
export TS_NAMELISTDIR="."
export TS_TOLERANCE="TOLERANCE_${REAL_TYPE}"
export TS_TIMINGS="TIMINGS_${REAL_TYPE}.cfg"
export TS_BASEDIR="."
export TS_FORCEMATCH="TRUE"


#run checkers
${checktool_dir}/run_success_check.py
if [ $? -gt 15 ]; then
    echo "run_success_check : fail"
    status=1
else
   echo "run_success_check : success"
fi

${checktool_dir}/output_tolerance_check.py
if [ $? -gt 15 ]; then
   echo "output_tolerance_check : fail"
   status=1
else
   echo "output_tolerance_check : success"
fi

${checktool_dir}/timing_check.py -f $1
if [ $? -gt 15 ]; then
    echo "timing_check : fail"
    status=1
else
   echo "timing_check : success"
fi


if [ ${status} == 0 ]; then
    echo TEST RESULT: OK
else
    echo TEST RESULT: FAIL
fi

# Check if there are changes with respect to owm YUSPECIF
# This will send a warning if not (but won't change the exit status)
${checktool_dir}/yuspecif_owm_check.sh

exit $status




