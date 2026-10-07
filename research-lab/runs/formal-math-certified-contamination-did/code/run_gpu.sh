#!/bin/bash
# GPU stage (plan section 6): stop the lab owner's vllm container (authorised for GPU stages), serve each prover in turn
# from a temporary vllm container, sample, and ALWAYS restart the owner's container at the end (trap), even on failure.
# Usage: run_gpu.sh pilot|main
cd "$(dirname "$0")/.."
RUN=$(pwd)
MODE=${1:-pilot}
trap 'docker stop fr-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "owner vllm restarted $(date)"' EXIT
docker stop vllm
for spec in "dsp_v2:DeepSeek-Prover-V2-7B" "goedel_v2:Goedel-Prover-V2-8B" "kimina:Kimina-Prover-Distill-8B"; do
  name=${spec%%:*}; dir=${spec#*:}
  docker run --rm -d --gpus all --name fr-gen -v $RUN/data/models:/models -p 8001:8000 vllm/vllm-openai:latest \
    --model /models/$dir --served-model-name $name --max-model-len 12288 --gpu-memory-utilization 0.92 --max-num-seqs 256 \
    --enable-prefix-caching
  up=0
  for i in $(seq 1 120); do curl -sf localhost:8001/v1/models >/dev/null && up=1 && break; sleep 10; done
  if [ $up = 0 ]; then echo "$name server FAILED $(date)"; docker logs --tail 40 fr-gen; docker stop fr-gen; sleep 10; continue; fi
  echo "$name up $(date)"
  if [ "$MODE" = pilot ]; then
    ./venv/bin/python code/sample.py $name http://localhost:8001 $name 20
  else
    ./venv/bin/python code/sample.py $name http://localhost:8001 $name
  fi
  docker stop fr-gen; sleep 15
  echo "$name done $(date)"
done
