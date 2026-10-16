#!/bin/bash
# Second GPU window for the two models the first window missed (deviations D2): OLMo-2-13B, whose server crashed at
# start-up (probably because the stopped Qwen container had not yet released GPU memory), and Qwen3-32B, whose
# 62 GB took ~20 minutes to load from the HDD, the first window's whole timeout. Here: a 60-minute timeout, a wait
# for the GPU to be free before each server starts, and the container's log captured to a file.
# GPU stage: stop the user's vllm container (authorised for GPU stages), serve each audited model in turn from a
# temporary vLLM container, generate the pilot and main sets, and ALWAYS restart the user's vllm at the end (trap).
cd "$(dirname "$0")/.."
RUN=$(pwd)
trap 'docker stop lc-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "user vllm restarted $(date)"' EXIT
docker image inspect vllm/vllm-openai:latest --format '{{.Id}} {{.Created}}' > logs/vllm_image_qwen.txt
docker stop vllm
for spec in "olmo2-13b:OLMo-2-1124-13B-Instruct" "qwen3-32b:Qwen3-32B"; do
  IFS=: read label dir <<< "$spec"
  for i in $(seq 1 60); do used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1); [ "$used" -lt 2000 ] && break; sleep 10; done
  docker run --rm -d --gpus all --name lc-gen -v $RUN/data/models:/models -p 8002:8000 vllm/vllm-openai:latest \
    --model /models/$dir --served-model-name $label --max-model-len 6144 --gpu-memory-utilization 0.92 \
    --max-num-seqs 64 --seed 0
  (docker logs -f lc-gen > logs/lc-gen-$label.log 2>&1 &)
  up=0
  for i in $(seq 1 360); do curl -sf localhost:8002/v1/models >/dev/null && up=1 && break; sleep 10; done
  if [ $up = 0 ]; then echo "$label server FAILED $(date)"; docker logs --tail 60 lc-gen; docker stop lc-gen; sleep 10; continue; fi
  echo "$label up $(date)"
  for set in pilot main; do ./venv/bin/python code/generate.py $label http://localhost:8002 $label $set; done
  docker stop lc-gen; sleep 15
  echo "$label done $(date)"
done
