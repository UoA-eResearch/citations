#!/bin/bash
# NuminaMath-LEAN secondary corpus on cores 0-11 in parallel with run_other.sh (D6); run_rows.py is resumable, so
# run_other.sh skips these rows when it reaches Numina.
cd "$(dirname "$0")/.."
VAC_TOOLCHAIN=v415 taskset -c 0-11 ./venv/bin/python code/run_rows.py data/samples/numina.parquet results/rows/numina.jsonl 10
