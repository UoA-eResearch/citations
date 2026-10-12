#!/bin/bash
# Second lane: while the panel occupies one boltz process, run the other arms one after another in a second
# process. Measured: two concurrent processes give about 9.5 s per complex in aggregate against 15.1 s for
# one, and the panel itself only slows from 15.1 to 17.3 s (D6). Three processes gave no further gain.
# Each arm is still a single process with seed 20261013, so provenance stays per-arm.
set -u
cd "$(dirname "$0")/.."
PY=./venv/bin/python

wait_for_arm () {  # wait for the currently running boltz on this lane to exit
  while pgrep -f "inputs_$1" > /dev/null; do sleep 30; done
}

arm () {  # arm name, then extra boltz flags
  a=$1; shift
  $PY code/boltzrun.py run "data/inputs_$a" "out/$a" "$@" > "logs/${a}_run.log" 2>&1
  $PY code/boltzrun.py collect "out/$a" "$a" results/predictions.jsonl >> logs/collect.log 2>&1
  echo "[$(date +%H:%M:%S)] $a finished, $(grep -c "\"arm\": \"$a\"" results/predictions.jsonl) rows"
}

wait_for_arm decoy                                     # started by hand at 11:06
$PY code/boltzrun.py collect out/decoy decoy results/predictions.jsonl >> logs/collect.log 2>&1
echo "[$(date +%H:%M:%S)] decoy collected, $(grep -c '"arm": "decoy"' results/predictions.jsonl) rows"

$PY code/build_inputs.py promisc >> logs/build_promisc.log 2>&1 && arm promisc \
  || echo "[$(date +%H:%M:%S)] promisc skipped: $(tail -1 logs/build_promisc.log)"

$PY code/build_inputs.py sampling >> logs/build_sampling.log 2>&1 \
  && arm sampling --sampling_steps_affinity 400 --diffusion_samples_affinity 9 \
  || echo "[$(date +%H:%M:%S)] sampling skipped: $(tail -1 logs/build_sampling.log)"

while pgrep -f "msa_seqs_postcut" > /dev/null; do sleep 60; done   # its 61 MSAs must be in first
$PY code/postcutoff.py yaml >> logs/build_postcut.log 2>&1 && arm postcut \
  || echo "[$(date +%H:%M:%S)] postcut skipped: $(tail -1 logs/build_postcut.log)"
echo "[$(date +%H:%M:%S)] lane 2 done"
