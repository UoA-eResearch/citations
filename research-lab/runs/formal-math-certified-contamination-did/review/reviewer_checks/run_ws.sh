#!/bin/bash
S=/tmp/claude-1001/-mnt-citations/14121cdb-aa2a-421c-926d-b1c71589d0e4/scratchpad
cd /mnt/citations/research-lab/runs/formal-math-certified-contamination-did
export PYTHONUNBUFFERED=1
until grep -q "CHAIN DONE" $S/chain.log; do sleep 30; done
VAC_TOOLCHAIN=v49 taskset -c 0-3 ./venv/bin/python $S/reverify_ws.py goedel_v2 4 $S/ws_goedel.jsonl
VAC_TOOLCHAIN=v49 taskset -c 0-3 ./venv/bin/python $S/reverify_ws.py dsp_v2 4 $S/ws_dsp.jsonl
echo "WS DONE $(date)"
