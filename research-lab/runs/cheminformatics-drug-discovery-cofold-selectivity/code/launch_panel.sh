#!/bin/bash
# Wait until (a) no boltz process is on the GPU - three concurrent shards already saturate it at ~49 GB and
# 100% utilisation, so a second arm starting underneath would risk OOM - and (b) every MSA the panel needs
# exists, which build_inputs.py checks by raising. Then run the remaining arms in the preregistered order.
set -u
cd "$(dirname "$0")/.."
while true; do
  n=$(pgrep -fc "boltz predict" || echo 0)
  if [ "$n" -eq 0 ] && ./venv/bin/python code/build_inputs.py panel >> logs/build_panel.log 2>&1; then
    break
  fi
  sleep 60
done
echo "[$(date +%H:%M:%S)] panel inputs ready and GPU free, launching arms"
NS=3 bash code/run_all.sh panel sampling promisc
