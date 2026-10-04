#!/bin/bash
# Secondary corpora (plan.md section 2), started after the main STP run finishes.
cd "$(dirname "$0")/.."
W=${W:-12}; CORES=${CORES:-16-27}
while kill -0 "$(cat logs/main.pid)" 2>/dev/null; do sleep 60; done
for c in workbook dsp1 sftv2; do
  taskset -c $CORES ./venv/bin/python code/run_rows.py data/samples/$c.parquet results/rows/$c.jsonl $W
done
VAC_TOOLCHAIN=v415 taskset -c $CORES ./venv/bin/python code/run_rows.py data/samples/numina.parquet results/rows/numina.jsonl $W
