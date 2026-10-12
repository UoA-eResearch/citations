#!/bin/bash
# Run the arms in the preregistered order (plan.md §5.7) with the preregistered settings, sharded across
# NS concurrent boltz processes. Resumable: boltz skips any pair that already has an affinity JSON in its
# out_dir, and collect() de-duplicates on (arm, pair_id) keeping the last row.
#
#   NS=3 bash code/run_all.sh panel decoy sampling promisc postcut
set -u
cd "$(dirname "$0")/.."
PY=./venv/bin/python
NS=${NS:-3}

run_arm () {
  arm=$1; shift
  $PY code/shard.py "$arm" "$NS"
  pids=()
  for i in $(seq 0 $((NS - 1))); do
    nohup $PY code/boltzrun.py run "data/inputs_${arm}_s$i" "out/${arm}_s$i" --seed $((20261013 + i)) "$@" \
      > "logs/${arm}_s$i.log" 2>&1 &
    pids+=($!)
  done
  echo "[$(date +%H:%M:%S)] $arm: $NS shards running (pids ${pids[*]})"
  wait "${pids[@]}" || echo "[$(date +%H:%M:%S)] $arm: a shard exited non-zero"
  for i in $(seq 0 $((NS - 1))); do
    $PY code/boltzrun.py collect "out/${arm}_s$i" "$arm" results/predictions.jsonl
  done
  echo "[$(date +%H:%M:%S)] $arm: collected $(grep -c "\"arm\": \"$arm\"" results/predictions.jsonl) rows"
}

for arm in "$@"; do
  case $arm in
    panel|decoy|promisc) $PY code/build_inputs.py "$arm" && run_arm "$arm" ;;
    sampling)            $PY code/build_inputs.py sampling \
                           && run_arm sampling --sampling_steps_affinity 400 --diffusion_samples_affinity 9 ;;
    postcut)             $PY code/postcutoff.py yaml && run_arm postcut ;;
    *) echo "unknown arm $arm"; exit 1 ;;
  esac
done
echo "[$(date +%H:%M:%S)] all requested arms done"
