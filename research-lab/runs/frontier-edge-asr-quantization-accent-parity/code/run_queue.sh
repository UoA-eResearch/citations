#!/bin/bash
# run_queue.sh MODEL SPLIT COND... : decode conditions one after another (shared calibration-text cache)
cd "$(dirname "$0")/.." || exit 1
export HF_HOME=/mnt/data/asr-accent-parity/hf
m=$1; s=$2; shift 2
for c in "$@"; do
  echo "$(date '+%H:%M:%S') start $m $c $s"
  venv/bin/python -I code/decode.py "$m" "$c" "$s" 2>&1 | grep -vE "max_new_tokens|generation_config|attention mask|clean_up_tokenization" > "logs/${m}_${c}_${s}.log"
  echo "$(date '+%H:%M:%S') done  $m $c $s: $(tail -1 logs/${m}_${c}_${s}.log | cut -c1-200)"
done
