#!/bin/bash
# GPU stage (plan section 4): stop the lab owner's vllm container (authorised for GPU stages), serve each formalizer in
# turn from a temporary vllm container, sample, and ALWAYS restart the owner's container at the end (trap), even on failure.
# Usage: run_gpu.sh pilot|main [model ...]
cd "$(dirname "$0")/.."
RUN=$(pwd)
MODE=${1:-pilot}; shift
MODELS=${@:-"kimina goedel herald dsp_v2 qwen"}
PY=../formal-math-certified-contamination-did/venv/bin/python
DSP=$RUN/../formal-math-certified-contamination-did/data/models/DeepSeek-Prover-V2-7B
trap 'docker stop af-gen >/dev/null 2>&1; docker start vllm >/dev/null 2>&1; echo "owner vllm restarted $(date)"' EXIT
docker stop vllm
for name in $MODELS; do
  case $name in
    kimina) dir=Kimina-Autoformalizer-7B; LEN=6144;;
    goedel) dir=Goedel-Formalizer-V2-8B; LEN=20480;;
    herald) dir=Herald_translator; LEN=4096;;
    dsp_v2) dir=DeepSeek-Prover-V2-7B; LEN=6144;;
    qwen) dir=Qwen2.5-7B-Instruct; LEN=6144;;
  esac
  docker run --rm -d --gpus all --name af-gen -v $RUN/data/models:/models -v $DSP:/models/DeepSeek-Prover-V2-7B \
    -p 8002:8000 vllm/vllm-openai:latest --model /models/$dir --served-model-name $name --max-model-len $LEN \
    --gpu-memory-utilization 0.92 --max-num-seqs 256 --enable-prefix-caching --seed 20261012
  up=0
  for i in $(seq 1 120); do curl -sf localhost:8002/v1/models >/dev/null && up=1 && break; sleep 10; done
  if [ $up = 0 ]; then echo "$name server FAILED $(date)"; docker logs --tail 40 af-gen; docker stop af-gen; sleep 10; continue; fi
  echo "$name up $(date)"
  if [ "$MODE" = pilot ]; then
    $PY code/sample.py $name http://localhost:8002 6
  else
    $PY code/sample.py $name http://localhost:8002
  fi
  docker stop af-gen; sleep 15
  echo "$name done $(date)"
done
