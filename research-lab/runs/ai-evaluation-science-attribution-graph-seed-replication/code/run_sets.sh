#!/bin/bash
# Train the four transcoder sets in sequence (plan section 0): A, B, C differ only in init seed; D only in data order.
cd /mnt/claude-lab/attrib
export HF_HOME=/mnt/claude-lab/hf
for spec in "A 0 0" "B 1 0" "C 2 0" "D 0 1"; do
  set -- $spec
  if [ -f "data/sets/$1/progress.json" ] && grep -q '"step": 73242' "data/sets/$1/progress.json"; then echo "skip $1"; continue; fi
  echo "== $1 start $(date -Is)"
  /mnt/claude-lab/venv/bin/python -I code/train_transcoders.py "$1" "$2" "$3" > "logs/train_$1.log" 2>&1
  echo "== $1 exit $? $(date -Is)"
done
echo "== all done $(date -Is)"
