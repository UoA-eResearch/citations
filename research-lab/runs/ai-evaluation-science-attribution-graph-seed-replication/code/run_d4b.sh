#!/bin/bash
# D4, after run_d4.sh: G3 traces (three random prompts) and the G4 rerun on the D4 prompt set. Runs on the guest A100.
cd /mnt/claude-lab/attrib
export HF_HOME=/mnt/claude-lab/hf
PY="/mnt/claude-lab/venv/bin/python -I"
until grep -q "== d4 done" logs/d4.log 2>/dev/null; do sleep 60; done
cp --update=none results/tables/g3.json results/tables/g3_v1.json; cp --update=none results/tables/g4.json results/tables/g4_v1.json
$PY code/g3.py > logs/g3_d4.log 2>&1; echo "== g3 exit $? $(date -Iseconds)" >> logs/d4.log
$PY code/g4.py > logs/g4_d4.log 2>&1; echo "== g4 exit $? $(date -Iseconds)" >> logs/d4.log
echo "== d4b done $(date -Iseconds)" >> logs/d4.log
