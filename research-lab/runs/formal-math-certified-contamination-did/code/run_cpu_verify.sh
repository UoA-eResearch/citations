#!/bin/bash
# Verification chain restarted with lower memory use (10 workers; REPL restart every 40 commands): finish Goedel-Prover-V2
# (resumable), then Kimina and STP as soon as their sampling is done.
cd "$(dirname "$0")/.."
export VERIFY_MAX_CMDS=40
VAC_TOOLCHAIN=v49 taskset -c 4-27 ./venv/bin/python code/verify.py goedel_v2 10
echo "goedel_v2 verified $(date)"
for p in kimina:v415 stp:v49; do
  name=${p%%:*}; tc=${p#*:}
  until grep -q "^$name done" logs/gpu_main.log logs/gpu_stp.log 2>/dev/null && [ -s data/samples/$name.jsonl ]; do sleep 60; done
  VAC_TOOLCHAIN=$tc taskset -c 4-27 ./venv/bin/python code/verify.py $name 10
  echo "$name verified $(date)"
done
echo "cpu verify done $(date)"
