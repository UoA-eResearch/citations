#!/bin/bash
# Plan sections 4-5: match all 246 pairs at layer 4, then layer 8 (one process per layer, GPU), then the analysis.
cd "$(dirname "$0")/.."
PY=venv/bin/python
for L in 4 8; do
  $PY code/match.py $L > logs/match_L$L.log 2>&1 || { echo "MATCH L$L FAILED $(date)"; exit 1; }
done
echo "MATCH ALL DONE $(date)"
