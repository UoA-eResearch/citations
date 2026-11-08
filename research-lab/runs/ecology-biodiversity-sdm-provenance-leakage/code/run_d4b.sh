#!/bin/bash
# D4 re-run, from the removals step on (the first attempt stopped at an import error)
set -e
cd "$(dirname "$0")/.."
PY="venv/bin/python -I"
$PY code/rf.py removals > logs/d4_removals.log 2>&1
$PY code/rf.py fit 12 > logs/d4_fit.log 2>&1
$PY code/analyse.py > logs/d4_analyse.log 2>&1
echo "== d4 pipeline done $(date)" >> logs/d4_fit.log
