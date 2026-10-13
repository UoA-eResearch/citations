#!/bin/bash
# After the crash (D7) the post-cutoff arm is the only one left to predict, and it waits on two things:
# its 61 MSAs, which the public ColabFold server has been serving slowly (about 18 min each), and a free
# boltz lane. The GPU now holds the owner's vLLM container (71 GB) plus the resumed panel affinity pass
# (9 GB), so one boltz process at a time is all that fits -- hence a third lane that waits rather than
# the two concurrent lanes of D6.
set -u
cd "$(dirname "$0")/.."
PY=./venv/bin/python
N_PC=61

# The fetcher only requests what is missing, so re-invoking it is both safe and the retry: a dropped
# connection to the public server leaves the other alignments in place.
for try in 1 2 3 4 5 6; do
  have=$(ls data/msa/*_pc.a3m 2>/dev/null | wc -l)
  echo "[$(date +%H:%M:%S)] postcut MSAs: $have of $N_PC (attempt $try)"
  [ "$have" -ge "$N_PC" ] && break
  while pgrep -f "boltzrun.py msa data/msa_seqs_postcut.json" > /dev/null; do sleep 120; done
  $PY code/boltzrun.py msa data/msa_seqs_postcut.json >> logs/msa_postcut2.log 2>&1
done

have=$(ls data/msa/*_pc.a3m 2>/dev/null | wc -l)
if [ "$have" -lt "$N_PC" ]; then
  echo "[$(date +%H:%M:%S)] giving up with $have of $N_PC MSAs; post-cutoff arm not run"
  exit 1
fi

while pgrep -f "boltzrun.py run data/inputs_panel" > /dev/null; do sleep 120; done
echo "[$(date +%H:%M:%S)] panel lane free, starting post-cutoff"
$PY code/postcutoff.py yaml >> logs/build_postcut.log 2>&1 \
  && $PY code/boltzrun.py run data/inputs_postcut out/postcut > logs/postcut_run.log 2>&1 \
  && $PY code/boltzrun.py collect out/postcut postcut results/predictions.jsonl >> logs/collect.log 2>&1
echo "[$(date +%H:%M:%S)] postcut done, $(find out/postcut -name 'affinity*.json' | wc -l) read-outs"
echo "lane 3 done"
