#!/bin/bash
# Final GPU window for all three models (deviations D2, D3), with max_tokens 1,100 for every model. Context per model:
# OLMo-2 4,096 (its limit; longest prompt 2,969 + 1,100 fits), Qwen3 and Mistral 6,144. Waits for a free GPU before
# each server, stops waiting if a container exits, and captures each container's log.
cd "$(dirname "$0")/.."
RUN=$(pwd)
trap 'docker stop lc-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "user vllm restarted $(date)"' EXIT
docker image inspect vllm/vllm-openai:latest --format '{{.Id}} {{.Created}}' > logs/vllm_image_mistral.txt
docker stop vllm
for spec in "qwen3-32b:Qwen3-32B:6144" "mistral-small-24b:Mistral-Small-24B-Instruct-2501:6144" "olmo2-13b:OLMo-2-1124-13B-Instruct:4096"; do
  IFS=: read label dir mlen <<< "$spec"
  for i in $(seq 1 60); do used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1); [ "$used" -lt 2000 ] && break; sleep 10; done
  docker run --rm -d --gpus all --name lc-gen -v $RUN/data/models:/models -p 8002:8000 vllm/vllm-openai:latest \
    --model /models/$dir --served-model-name $label --max-model-len $mlen --gpu-memory-utilization 0.92 \
    --max-num-seqs 64 --seed 0
  (docker logs -f lc-gen > logs/lc-gen-$label.log 2>&1 &)
  up=0
  for i in $(seq 1 360); do curl -sf localhost:8002/v1/models >/dev/null && up=1 && break; [ -z "$(docker ps -q -f name=lc-gen)" ] && echo "$label container exited early" && break; sleep 10; done
  if [ $up = 0 ]; then echo "$label server FAILED $(date)"; docker logs --tail 60 lc-gen; docker stop lc-gen; sleep 10; continue; fi
  echo "$label up $(date)"
  for set in pilot main; do ./venv/bin/python code/generate.py $label http://localhost:8002 $label $set; done
  docker stop lc-gen; sleep 15
  echo "$label done $(date)"
done
