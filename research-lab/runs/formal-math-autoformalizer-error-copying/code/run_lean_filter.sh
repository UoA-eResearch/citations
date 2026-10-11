#!/bin/bash
# Plan 2.2: Lean filters on the candidate pairs, v49 then v415 for items not settled in v49.
cd "$(dirname "$0")/.."
PY=../formal-math-certified-contamination-did/venv/bin/python
VAC_TOOLCHAIN=v49 taskset -c 4-27 $PY code/candidates.py lean v49 22 > logs/lean_v49.log 2>&1
VAC_TOOLCHAIN=v415 taskset -c 4-27 $PY code/candidates.py lean v415 22 > logs/lean_v415.log 2>&1
echo "LEAN FILTER FINISHED $(date)" > logs/lean_filter_done.log
