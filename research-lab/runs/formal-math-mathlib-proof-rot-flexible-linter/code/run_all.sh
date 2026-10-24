#!/bin/bash
# labelling then replays (plan sections 2-3); stops at the first failure
set -e
cd "$(dirname "$0")/.."
export WORKERS=${WORKERS:-14}
for step in "label O_2504" "label O_2510" "replay O_2504 N_2604" "replay O_2504 O_2510" "replay O_2510 N_2610"; do
  echo "== $step $(date +%H:%M:%S)"
  venv/bin/python -I code/rot.py $step
done
echo "== done $(date +%H:%M:%S)"
