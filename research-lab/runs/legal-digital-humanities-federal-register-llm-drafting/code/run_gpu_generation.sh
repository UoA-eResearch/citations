#!/bin/bash
# GPU stage of plan section 3: after the Nemotron run (user's server) finishes, stop the user's vllm container
# (authorised for GPU stages), serve Qwen2.5-32B and OLMo-2-32B in turn from a temporary container, generate, and
# ALWAYS restart the user's vllm container at the end (trap), even on failure.
cd "$(dirname "$0")/.."
RUN=$(pwd)
trap 'docker stop fr-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "user vllm restarted $(date)"' EXIT
while kill -0 2837127 2>/dev/null; do sleep 30; done
echo "nemotron done $(date)"
docker stop vllm
for spec in "qwen:Qwen2.5-32B-Instruct" "olmo:OLMo-2-0325-32B-Instruct"; do
  label=${spec%%:*}; dir=${spec#*:}
  docker run --rm -d --gpus all --name fr-gen -v $RUN/data/models:/models -p 8001:8000 vllm/vllm-openai:latest \
    --model /models/$dir --served-model-name $label --max-model-len 4096 --gpu-memory-utilization 0.92 --max-num-seqs 64
  for i in $(seq 1 120); do curl -sf localhost:8001/v1/models >/dev/null && break; sleep 10; done
  echo "$label server up $(date)"
  ./venv/bin/python code/generate.py $label http://localhost:8001 $label 4000
  docker stop fr-gen; sleep 15
  echo "$label done $(date)"
done
