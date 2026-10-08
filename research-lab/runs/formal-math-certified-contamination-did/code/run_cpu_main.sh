#!/bin/bash
# CPU work alongside the main GPU run: (1) finish the secondary-benchmark certification and its recheck (D3b);
# (2) verify each prover's samples as soon as its GPU sampling is done.
cd "$(dirname "$0")/.."
for b in bench_putnam bench_proofnet bench_minif2f_v2c; do
  VAC_TOOLCHAIN=v49 taskset -c 4-27 ./venv/bin/python code/certify.py leaks $b 22
  VAC_TOOLCHAIN=v415 taskset -c 4-27 ./venv/bin/python code/certify.py leaks $b 22
  VAC_TOOLCHAIN=v49 taskset -c 4-27 ./venv/bin/python code/recheck.py $b 22
  VAC_TOOLCHAIN=v415 taskset -c 4-27 ./venv/bin/python code/recheck.py $b 22
  echo "$b certified $(date)"
done
for p in dsp_v2:v49 goedel_v2:v49 kimina:v415 stp:v49; do
  name=${p%%:*}; tc=${p#*:}
  until grep -q "^$name done" logs/gpu_main.log logs/gpu_stp.log 2>/dev/null && [ -s data/samples/$name.jsonl ]; do sleep 60; done
  VAC_TOOLCHAIN=$tc taskset -c 4-27 ./venv/bin/python code/verify.py $name 22
  echo "$name verified $(date)"
done
echo "cpu main done $(date)"
