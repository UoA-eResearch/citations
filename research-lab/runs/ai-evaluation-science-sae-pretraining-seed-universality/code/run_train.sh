#!/bin/bash
# Plan section 3: one sparsify run per model trains its six SAEs (layers 4 and 8 x SAE seeds 0-2) on the same token
# stream (data/train_tokens.bin, fixed order). Usage: NSEQ=<sequences> SAVE=<dir> run_train.sh <model> [<model> ...]
cd "$(dirname "$0")/.."
PY=venv/bin/python
NSEQ=${NSEQ:-97657}
SAVE=${SAVE:-data/sae}
for m in "$@"; do
  if [ -f $SAVE/$m/DONE ]; then echo "$m already trained"; continue; fi
  echo "$m start $(date)"
  $PY -m sparsify data/raw/models/$m data/train_tokens.bin --ctx_len 2048 --max_examples $NSEQ \
    --layers 4 8 --init_seeds 0 1 2 --k 32 --num_latents 32768 --batch_size 32 \
    --nolog_to_wandb --save_dir $SAVE --run_name $m > logs/train_$m.log 2>&1 \
    && touch $SAVE/$m/DONE && rm -f $SAVE/$m/optimizer_*.pt && echo "$m done $(date)" || echo "$m FAILED $(date)"
done
echo "TRAIN BATCH FINISHED $(date)"
