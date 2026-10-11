#!/bin/bash
S=/tmp/claude-1001/-mnt-citations/14121cdb-aa2a-421c-926d-b1c71589d0e4/scratchpad
cd /mnt/citations/research-lab/runs/formal-math-certified-contamination-did
export PYTHONUNBUFFERED=1
ONLY_CORPUS=lean_workbook VAC_TOOLCHAIN=v49 taskset -c 0-5 ./venv/bin/python $S/review_lean2.py neg 6 $S/conf_lw_neg.jsonl
echo "lw neg done $(date)"
ONLY_CORPUS=lean_workbook VAC_TOOLCHAIN=v49 taskset -c 0-5 ./venv/bin/python $S/review_lean2.py lwrej 6 $S/conf_lw_rej.jsonl
echo "lw rej done $(date)"
echo "CONF DONE $(date)"
