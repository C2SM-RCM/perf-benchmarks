#!/bin/bash

# Check alteration of the YUSPECIF file from OWM as compared to the benchmark
# Generate a warning and send mail if the diff between the YUSPECIF from owm
# and the current YUSPECIF is different than a reference diff (check line count)
#

# Author       Xavier Lapillonne
# Date         15.05.2017
# Mail         xavier.lapillonne@meteoswiss.ch

# Set variables
# checktool_dir="../checktools"
checktool_dir="../perf-benchmarks/checktools"
recipients="xavier.lapillonne@meteoswiss.ch carlos.osuna@meteoswiss.ch"

diff -bitw ./owm_YUSPECIF ./YUSPECIF > tmp_diff_YUSPECIF_owm_vs_benchmark.txt
status=$?
# check if diff fail (missing file ...), status 1 is ok
if [ $status -gt 1 ]; then
    echo "Error with diff command in yuspecif_owm_check.sh"
    echo "diff ./YUSPECIF ./owm_YUSPECIF > tmp_diff_YUSPECIF_owm_vs_benchmark.txt"
    echo `pwd`
    exit 1
fi

#compare length of diff
nl_ref=`wc -l < reference_${REAL_TYPE}/diff_YUSPECIF_owm_vs_benchmark.txt`
nl_bench=`wc -l < tmp_diff_YUSPECIF_owm_vs_benchmark.txt`

if [ "$nl_ref" -ne "$nl_bench" ]; then
    echo "! Warning : New differences with owm_YUSPECIF:" |tee -a tmp_mail.txt
    echo `pwd` |tee -a tmp_mail.txt
    echo "diff tmp_diff_YUSPECIF_owm_vs_benchmark.txt diff_YUSPECIF_owm_vs_benchmark.txt :"
    diff tmp_diff_YUSPECIF_owm_vs_benchmark.txt reference_${REAL_TYPE}/diff_YUSPECIF_owm_vs_benchmark.txt |tee -a tmp_mail.txt
    cat tmp_mail.txt | mail -s "COSMO-ORG - benchmark: changes against owm_YUSPECIF" "$recipients"
    rm tmp_mail.txt
fi
rm tmp_diff_YUSPECIF_owm_vs_benchmark.txt

exit 0



