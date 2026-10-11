#!/bin/bash
# D9 fixes after the independent review: Lean Workbook re-extracted, retrieved and certified; recheck with the witness and
# negation guards for every benchmark and corpus; benchmark vacuity / automation-provability; spacing-insensitive
# re-check of "changed statement" rejections; tiers rebuilt. 8 workers on cores 4-27.
cd "$(dirname "$0")/.."
taskset -c 4-27 ./venv/bin/python code/extract.py lean_workbook
for b in bench_minif2f bench_putnam bench_proofnet bench_minif2f_v2c; do
  taskset -c 4-27 ./venv/bin/python code/retrieve.py $b lean_workbook
  mv data/certify/${b}__lean_workbook.jsonl data/certify/lean_workbook_buggy/ 2>/dev/null
  VAC_TOOLCHAIN=v49 taskset -c 4-27 ./venv/bin/python code/certify.py leaks $b 8
done
mv data/certify/recheck_bench_*.jsonl data/certify/recheck_D3b/
for b in bench_minif2f bench_putnam bench_proofnet bench_minif2f_v2c; do
  VAC_TOOLCHAIN=v49 taskset -c 4-27 ./venv/bin/python code/recheck.py $b 8
  VAC_TOOLCHAIN=v415 taskset -c 4-27 ./venv/bin/python code/recheck.py $b 8
  echo "$b rechecked $(date)"
done
VAC_TOOLCHAIN=v49 taskset -c 4-27 ./venv/bin/python code/benchcheck.py 8
export VERIFY_MAX_CMDS=40
for p in dsp_v2:v49 goedel_v2:v49 kimina:v415 stp:v49; do
  VAC_TOOLCHAIN=${p#*:} taskset -c 4-27 ./venv/bin/python code/reverify_ws.py ${p%%:*} 4
done
for b in bench_minif2f bench_putnam bench_proofnet bench_minif2f_v2c; do
  taskset -c 4-27 ./venv/bin/python code/tiers.py $b
done
echo "fix chain done $(date)"
