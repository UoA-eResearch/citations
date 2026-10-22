#!/bin/bash
# run_measure.sh : measure every atoll once its scene lists exist (Sentinel-2 and Collection 1 Landsat in parallel)
cd "$(dirname "$0")/.." || exit 1
for a in funafuti tarawa majuro kwajalein penrhyn kapingamarangi kanton kiritimati; do
  until [ -e "data/scenes/${a}_s2.parquet" ] && [ -e "data/scenes/${a}_ls.parquet" ]; do sleep 60; done
  [ -e "data/scenes/${a}_l1.parquet" ] || venv/bin/python -I code/gcp_scenes.py >> logs/gcp_scenes.log 2>&1
  echo "$(date '+%H:%M:%S') start $a"
  venv/bin/python -I code/measure.py "$a" s2 --threads 40 > "logs/measure_${a}_s2.log" 2>&1 &
  p1=$!
  venv/bin/python -I code/measure.py "$a" l1 --threads 24 > "logs/measure_${a}_l1.log" 2>&1 &
  p2=$!
  wait $p1 $p2
  echo "$(date '+%H:%M:%S') done $a: $(tail -1 logs/measure_${a}_s2.log) | $(tail -1 logs/measure_${a}_l1.log)"
done
