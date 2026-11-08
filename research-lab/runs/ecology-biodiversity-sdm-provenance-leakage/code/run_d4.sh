#!/bin/bash
# D4 re-run with the amended provenance flags (post hoc). Logs in logs/d4_*.log
set -e
cd "$(dirname "$0")/.."
PY="venv/bin/python -I"
$PY code/cells.py records > logs/d4_records.log 2>&1
$PY code/cells.py support > logs/d4_support.log 2>&1
$PY code/audit.py > logs/d4_audit.log 2>&1
$PY code/rf.py removals > logs/d4_removals.log 2>&1
$PY code/rf.py fit 12 > logs/d4_fit.log 2>&1
$PY code/analyse.py > logs/d4_analyse.log 2>&1
echo "== d4 pipeline done $(date)" >> logs/d4_fit.log
