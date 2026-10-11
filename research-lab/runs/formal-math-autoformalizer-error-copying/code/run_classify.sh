#!/bin/bash
# Plan section 5: classify each model's samples in Lean as soon as its sampling has finished (no rates printed here).
cd "$(dirname "$0")/.."
PY=../formal-math-certified-contamination-did/venv/bin/python
for m in kimina goedel herald dsp_v2 qwen; do
  until grep -q "^$m SAMPLING DONE" logs/gpu_main.log || grep -q "owner vllm restarted" logs/gpu_main.log; do sleep 60; done
  if grep -q "^$m SAMPLING DONE" logs/gpu_main.log; then
    VAC_TOOLCHAIN=v49 taskset -c 4-27 $PY code/classify.py $m 22 > logs/classify_$m.log 2>&1
  else
    echo "$m: sampling did not finish" > logs/classify_$m.log
  fi
done
echo "CLASSIFY ALL FINISHED $(date)" > logs/classify_done.log
