#!/bin/bash
# Run the arms one after another, one boltz process each (D4: one process already saturates the A100).
# Resumable: boltz skips any pair that already has an affinity JSON in that arm's out dir. An arm whose
# MSAs are not all present raises in build_inputs.py and is skipped with a message, to be run later.
set -u
cd "$(dirname "$0")/.."
PY=./venv/bin/python

arm_run () {
  arm=$1; shift
  nohup $PY code/boltzrun.py run "data/inputs_$arm" "out/$arm" "$@" > "logs/${arm}_run.log" 2>&1
  rc=$?
  $PY code/boltzrun.py collect "out/$arm" "$arm" results/predictions.jsonl
  echo "[$(date +%H:%M:%S)] $arm finished (exit $rc), $(grep -c "\"arm\": \"$arm\"" results/predictions.jsonl) rows collected"
}

for arm in "$@"; do
  case $arm in
    panel|decoy|promisc)
      if $PY code/build_inputs.py "$arm" >> logs/build_$arm.log 2>&1; then arm_run "$arm"
      else echo "[$(date +%H:%M:%S)] $arm skipped: $(tail -1 logs/build_$arm.log)"; fi ;;
    sampling)
      if $PY code/build_inputs.py sampling >> logs/build_sampling.log 2>&1; then
        arm_run sampling --sampling_steps_affinity 400 --diffusion_samples_affinity 9
      else echo "[$(date +%H:%M:%S)] sampling skipped: $(tail -1 logs/build_sampling.log)"; fi ;;
    postcut)
      if $PY code/postcutoff.py yaml >> logs/build_postcut.log 2>&1; then arm_run postcut
      else echo "[$(date +%H:%M:%S)] postcut skipped: $(tail -1 logs/build_postcut.log)"; fi ;;
    *) echo "unknown arm $arm"; exit 1 ;;
  esac
done
echo "[$(date +%H:%M:%S)] all requested arms done"
