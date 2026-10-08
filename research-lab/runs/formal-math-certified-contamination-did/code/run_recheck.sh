#!/bin/bash
cd "$(dirname "$0")/.."
VAC_TOOLCHAIN=v49 taskset -c 2-27 ./venv/bin/python code/recheck.py bench_minif2f 24
VAC_TOOLCHAIN=v415 taskset -c 2-27 ./venv/bin/python code/recheck.py bench_minif2f 24
echo "recheck done $(date)"
