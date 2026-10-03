#!/bin/bash
# Process all three epochs sequentially (each step waits for the previous; no pgrep loops).
cd "$(dirname "$0")/.."
for ep in 2016 2013 2024; do
  echo "$(date '+%F %T') start $ep"
  ./venv/bin/python code/process_tiles.py $ep 64 > data/cells_$ep.log 2>&1
  echo "$(date '+%F %T') done $ep: $(tail -1 data/cells_$ep.log)"
done
echo "$(date '+%F %T') ALL DONE"
