#!/bin/bash
# Post-outcome diagnostics (deviations.md D4). Each job logs to logs/checks_<job>.log and ends with "<job> DONE" or "<job> FAILED".
R=/mnt/citations/research-lab/runs/seismology-geophysics-quakescope-analyst-validation
cd $R
job() { name=$1; shift; (./venv/bin/python code/checks.py "$@" > logs/checks_$name.log 2>&1 && echo "$name DONE" >> logs/checks_$name.log || echo "$name FAILED" >> logs/checks_$name.log) & }
job vb1 vb 1 BFGS
job vb2 vb 2 BFGS
job vb3 vb 3 BFGS
job vb1l vb 1 L-BFGS-B
job misc misc
job falsepick falsepick
# the AGHQ fits and h2x were moved to code/run_aghq.sh (first attempt too slow; see deviations.md D4)
wait
echo "ALL CHECKS FINISHED" > logs/checks_all.log
