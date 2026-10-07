#!/bin/bash
# Certify R1/R2 against the originals in both prover environments (cores 0-3, alongside the leak certification).
cd "$(dirname "$0")/.."
VAC_TOOLCHAIN=v49 taskset -c 0-3 ./venv/bin/python code/reform.py certify 4
VAC_TOOLCHAIN=v415 taskset -c 0-3 ./venv/bin/python code/reform.py certify 4
echo "reforms done $(date)"
