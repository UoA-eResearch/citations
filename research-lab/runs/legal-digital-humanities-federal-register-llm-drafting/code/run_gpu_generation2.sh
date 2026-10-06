#!/bin/bash
# GPU stage for the D2 generators: wait for the downloads, stop the user's vllm container (authorised for GPU stages),
# serve Gemma 4 31B-it then gpt-oss-120b from a temporary container, generate, and ALWAYS restart the user's vllm
# container at the end (trap), even on failure.
cd "$(dirname "$0")/.."
RUN=$(pwd)
trap 'docker stop fr-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "user vllm restarted $(date)"' EXIT
DL=$(cat logs/download_models2.pid)
while kill -0 $DL 2>/dev/null; do sleep 30; done
echo "downloads done $(date)"
docker stop vllm
for spec in "gemma:gemma-4-31B-it:4096" "gptoss:gpt-oss-120b:8192"; do
  IFS=: read label dir mlen <<< "$spec"
  docker run --rm -d --gpus all --name fr-gen -v $RUN/data/models:/models -p 8001:8000 vllm/vllm-openai:latest \
    --model /models/$dir --served-model-name $label --max-model-len $mlen --gpu-memory-utilization 0.92 --max-num-seqs 64
  up=0
  for i in $(seq 1 120); do curl -sf localhost:8001/v1/models >/dev/null && up=1 && break; sleep 10; done
  if [ $up = 0 ]; then echo "$label server FAILED to start $(date)"; docker logs --tail 40 fr-gen; docker stop fr-gen; sleep 10; continue; fi
  echo "$label server up $(date)"
  ./venv/bin/python code/generate.py $label http://localhost:8001 $label 4000
  docker stop fr-gen; sleep 15
  echo "$label done $(date)"
done
