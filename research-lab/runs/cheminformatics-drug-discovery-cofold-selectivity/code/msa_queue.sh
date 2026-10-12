#!/bin/bash
# Fetch the remaining MSAs in the order the arms need them: the 8 promiscuity-probe kinases first (that arm
# runs before the post-cutoff one), then the 61 kinases of the post-cutoff arm. One sequence per request.
set -u
cd "$(dirname "$0")/.."
while pgrep -f "boltzrun.py msa data/msa_seqs_main.json" > /dev/null; do sleep 30; done
./venv/bin/python code/boltzrun.py msa data/msa_seqs_promisc.json
./venv/bin/python code/boltzrun.py msa data/msa_seqs_postcut.json
echo "[$(date +%H:%M:%S)] all MSAs fetched"
