#!/bin/bash
# D5: STP sampling with the fixed tokenizer configuration, after the main GPU run; same restart guarantee.
cd "$(dirname "$0")/.."
RUN=$(pwd)
until grep -q "owner vllm restarted" logs/gpu_main.log; do sleep 60; done
trap 'docker stop fr-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "owner vllm restarted $(date)"' EXIT
docker stop vllm
docker run --rm -d --gpus all --name fr-gen -v $RUN/data/models:/models -p 8001:8000 vllm/vllm-openai:latest \
  --model /models/STP_model_Lean_0320 --served-model-name stp --max-model-len 4096 --gpu-memory-utilization 0.92 --max-num-seqs 256 --enable-prefix-caching
for i in $(seq 1 120); do curl -sf localhost:8001/v1/models >/dev/null && break; sleep 10; done
echo "stp up $(date)"
./venv/bin/python code/sample.py stp http://localhost:8001 stp
docker stop fr-gen
echo "stp done $(date)"
