#!/bin/bash
# Leak certification for miniF2F (primary), then the secondary benchmarks; Lean 4.9 corpora then NuminaMath-LEAN (4.15).
cd "$(dirname "$0")/.."
for b in bench_minif2f bench_putnam bench_proofnet bench_minif2f_v2c; do
  VAC_TOOLCHAIN=v49 taskset -c 4-27 ./venv/bin/python code/certify.py leaks $b 22
  VAC_TOOLCHAIN=v415 taskset -c 4-27 ./venv/bin/python code/certify.py leaks $b 22
  echo "$b done $(date)"
done
echo "certification done $(date)"
