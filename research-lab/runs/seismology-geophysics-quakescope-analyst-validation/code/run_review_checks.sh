#!/bin/bash
# Review-requested analyses (deviations.md D5). Each job logs to logs/review_<job>.log ending in "<job> DONE" or "<job> FAILED".
R=/mnt/citations/research-lab/runs/seismology-geophysics-quakescope-analyst-validation
cd $R
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONUNBUFFERED=1
job() { name=$1; (./venv/bin/python code/review_checks.py $name > logs/review_$name.log 2>&1 && echo "$name DONE" >> logs/review_$name.log || echo "$name FAILED" >> logs/review_$name.log) & }
job zero
job weights
job misc
job misses
job falsepick
wait
(./venv/bin/python code/review_checks.py table > logs/review_table.log 2>&1 && echo "table DONE" >> logs/review_table.log || echo "table FAILED" >> logs/review_table.log)
echo "REVIEW CHECKS FINISHED $(date)" > logs/review_all.log
