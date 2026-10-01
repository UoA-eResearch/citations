#!/bin/bash
# GPU window (plan.md sec 7): stop the shared vLLM server, run the AIFS forecasts, and ALWAYS restart vLLM afterwards.
set -u
LOG=${1:-gpu_window.log}
restart() {
  echo "$(date '+%F %T') restarting vllm" >> "$LOG"
  docker start vllm >> "$LOG" 2>&1
  for i in $(seq 1 60); do
    if curl -s -o /dev/null -w "%{http_code}" --max-time 5 localhost:8000/v1/models | grep -q 200; then
      echo "$(date '+%F %T') vllm serving again" >> "$LOG"; return; fi
    sleep 10
  done
  echo "$(date '+%F %T') WARNING: vllm not answering after 10 min" >> "$LOG"
}
trap restart EXIT
echo "$(date '+%F %T') stopping vllm" >> "$LOG"
docker stop vllm >> "$LOG" 2>&1
sleep 5
nvidia-smi --query-gpu=memory.used --format=csv,noheader >> "$LOG"
cd "$(dirname "$0")/.."
venv/bin/python code/run_forecasts.py >> "$LOG" 2>&1
echo "$(date '+%F %T') forecasts finished with exit code $?" >> "$LOG"
