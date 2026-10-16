#!/bin/bash
# GPU stage: stop the user's vllm container (authorised for GPU stages), serve each audited model in turn from a
# temporary vLLM container, generate the pilot and main sets, and ALWAYS restart the user's vllm at the end (trap).
cd "$(dirname "$0")/.."
RUN=$(pwd)
trap 'docker stop lc-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "user vllm restarted $(date)"' EXIT
docker image inspect vllm/vllm-openai:latest --format '{{.Id}} {{.Created}}' > logs/vllm_image.txt
docker stop vllm
for spec in "qwen3-32b:Qwen3-32B" "olmo2-13b:OLMo-2-1124-13B-Instruct" "mistral-small-24b:Mistral-Small-24B-Instruct-2501"; do
  IFS=: read label dir <<< "$spec"
  docker run --rm -d --gpus all --name lc-gen -v $RUN/data/models:/models -p 8002:8000 vllm/vllm-openai:latest \
    --model /models/$dir --served-model-name $label --max-model-len 6144 --gpu-memory-utilization 0.92 \
    --max-num-seqs 64 --seed 0
  up=0
  for i in $(seq 1 120); do curl -sf localhost:8002/v1/models >/dev/null && up=1 && break; sleep 10; done
  if [ $up = 0 ]; then echo "$label server FAILED $(date)"; docker logs --tail 60 lc-gen; docker stop lc-gen; sleep 10; continue; fi
  echo "$label up $(date)"
  for set in pilot main; do ./venv/bin/python code/generate.py $label http://localhost:8002 $label $set; done
  docker stop lc-gen; sleep 15
  echo "$label done $(date)"
done
