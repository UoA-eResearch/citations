#!/bin/bash
S=/tmp/claude-1001/-mnt-citations/14121cdb-aa2a-421c-926d-b1c71589d0e4/scratchpad
cd /mnt/citations/research-lab/runs/formal-math-certified-contamination-did
export PYTHONUNBUFFERED=1
VAC_TOOLCHAIN=v49  taskset -c 0-3 ./venv/bin/python $S/review_lean.py neg 4 $S/neg_v49.jsonl
echo "neg v49 done $(date)"
VAC_TOOLCHAIN=v415 taskset -c 0-3 ./venv/bin/python $S/review_lean.py neg 4 $S/neg_v415.jsonl
echo "neg v415 done $(date)"
VAC_TOOLCHAIN=v49  taskset -c 0-3 ./venv/bin/python $S/review_lean.py free 4 $S/free_v49.jsonl
echo "free done $(date)"
VAC_TOOLCHAIN=v49  taskset -c 0-3 ./venv/bin/python $S/review_lean.py rejected 4 $S/rejected_v49.jsonl
VAC_TOOLCHAIN=v415 taskset -c 0-3 ./venv/bin/python $S/review_lean.py rejected 4 $S/rejected_v415.jsonl
echo "rejected done $(date)"
echo "CHAIN DONE $(date)"
