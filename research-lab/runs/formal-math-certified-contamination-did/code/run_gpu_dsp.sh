#!/bin/bash
# D7: DeepSeek-Prover-V2 resampled with the fixed tokenizer configuration; same restart guarantee for the owner's vLLM.
cd "$(dirname "$0")/.."
RUN=$(pwd)
trap 'docker stop fr-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "owner vllm restarted $(date)"' EXIT
docker stop vllm
docker run --rm -d --gpus all --name fr-gen -v $RUN/data/models:/models -p 8001:8000 vllm/vllm-openai:latest \
  --model /models/DeepSeek-Prover-V2-7B --served-model-name dsp_v2 --max-model-len 12288 --gpu-memory-utilization 0.92 --max-num-seqs 256 --enable-prefix-caching
for i in $(seq 1 120); do curl -sf localhost:8001/v1/models >/dev/null && break; sleep 10; done
echo "dsp_v2 up $(date)"
./venv/bin/python code/sample.py dsp_v2 http://localhost:8001 dsp_v2
docker stop fr-gen
echo "dsp_v2 done $(date)"
