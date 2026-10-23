#!/bin/bash
# run_cv.sh : D5, the Common Voice replication (Whisper-small, FP16 and GPTQ-W3 x 3 compositions x 3 seeds),
# started after the large-v3 pipeline has released the GPU
cd "$(dirname "$0")/.." || exit 1
export HF_HOME=/mnt/data/asr-accent-parity/hf
while pgrep -x -f "/bin/bash code/run_large.sh" > /dev/null; do sleep 60; done
test -s data/manifest/cv_segments.csv || { echo "cv manifest missing"; exit 1; }
code/run_queue.sh small cv fp16 gptq_w3_us_s0 gptq_w3_balanced_s0 gptq_w3_worst_s0 gptq_w3_us_s1 gptq_w3_balanced_s1 gptq_w3_worst_s1 gptq_w3_us_s2 gptq_w3_balanced_s2 gptq_w3_worst_s2
venv/bin/python -I code/score.py analyze small cv > logs/analyze_small_cv.log 2>&1
echo "cv pipeline done $(date '+%H:%M:%S')"
