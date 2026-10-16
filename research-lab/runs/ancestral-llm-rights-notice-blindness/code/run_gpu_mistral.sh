#!/bin/bash
# Third GPU window (deviations D2): Mistral-Small-24B (in the first window generate.py failed at import: requests was
# not installed) and OLMo-2-13B (its server rejected --max-model-len 6144: OLMo-2's context is 4,096). Context set to
# 4,096 for both: the longest prompt is 2,959 OLMo tokens + 700 output, so no prompt or output is truncated.
cd "$(dirname "$0")/.."
RUN=$(pwd)
trap 'docker stop lc-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "user vllm restarted $(date)"' EXIT
docker image inspect vllm/vllm-openai:latest --format '{{.Id}} {{.Created}}' > logs/vllm_image_mistral.txt
docker stop vllm
for spec in "mistral-small-24b:Mistral-Small-24B-Instruct-2501" "olmo2-13b:OLMo-2-1124-13B-Instruct"; do
  IFS=: read label dir <<< "$spec"
  for i in $(seq 1 60); do used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1); [ "$used" -lt 2000 ] && break; sleep 10; done
  docker run --rm -d --gpus all --name lc-gen -v $RUN/data/models:/models -p 8002:8000 vllm/vllm-openai:latest \
    --model /models/$dir --served-model-name $label --max-model-len 4096 --gpu-memory-utilization 0.92 \
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
