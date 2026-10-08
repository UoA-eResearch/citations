#!/bin/bash
# Resume after the NuminaMath-LEAN crash (duplicate ids): miniF2F x NuminaMath-LEAN (Lean 4.15) first, then the
# secondary benchmarks (the v49 putnam results already written are kept; run_rows-style resume skips done keys).
cd "$(dirname "$0")/.."
VAC_TOOLCHAIN=v415 taskset -c 4-27 ./venv/bin/python code/certify.py leaks bench_minif2f 22
echo "bench_minif2f numina done $(date)"
for b in bench_putnam bench_proofnet bench_minif2f_v2c; do
  VAC_TOOLCHAIN=v49 taskset -c 4-27 ./venv/bin/python code/certify.py leaks $b 22
  VAC_TOOLCHAIN=v415 taskset -c 4-27 ./venv/bin/python code/certify.py leaks $b 22
  echo "$b done $(date)"
done
echo "certification done $(date)"
