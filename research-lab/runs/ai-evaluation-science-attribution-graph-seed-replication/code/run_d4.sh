#!/bin/bash
# D4 (after the independent review): rebuild the arithmetic prompts with the digit as target, reselect, build their
# graphs for every set, extend the own-effects files, rematch every pair into data/match_d4/ (candidate effects stored,
# deduplicated subspace, nulls), then the fidelity diagnostics. Runs on the guest A100.
set -e
cd /mnt/claude-lab/attrib
export HF_HOME=/mnt/claude-lab/hf
PY="/mnt/claude-lab/venv/bin/python -I"
LOG=logs/d4.log
echo "== d4 start $(date -Iseconds)" >> $LOG
if ! grep -q '"i":' results/tables/prompts.jsonl; then                    # selection not yet redone
  [ "$(md5sum < results/tables/prompts.jsonl | cut -c1-32)" = "936de71da16992bbe84955299ed8523f" ] || { echo "prompts.jsonl is not the frozen v1" >> $LOG; exit 1; }
  cp --update=none results/tables/prompts.jsonl data/prompts_v1_frozen.jsonl
  $PY code/prompts.py >> $LOG 2>&1
  $PY code/select_prompts.py > logs/select_d4.log 2>&1
  echo "== select exit $? $(date -Iseconds)" >> $LOG
fi
# the first run's arithmetic graphs (space-token target) are moved aside; their indices are no longer used
$PY - <<'EOF' >> $LOG 2>&1
import json, shutil
from pathlib import Path
old = [n for n, l in enumerate(open("data/prompts_v1_frozen.jsonl")) if json.loads(l)["family"] == "arithmetic"]
moved = 0
for S in ["A", "B", "C", "D", "public"]:
    dst = Path("data/graphs_v1_arith") / S
    dst.mkdir(parents=True, exist_ok=True)
    for i in old:
        for suf in (".json", "_active.pt"):
            f = Path("data/graphs") / S / f"{i:03d}{suf}"
            if f.exists():
                shutil.move(str(f), dst / f.name); moved += 1
print("moved", moved, "files of", len(old), "first-run arithmetic prompts")
EOF
for S in A B C D public; do
  echo "== graphs $S start $(date -Iseconds)" >> $LOG
  $PY code/graphs.py build $S > logs/graphs_d4_$S.log 2>&1
  echo "== graphs $S exit $? $(date -Iseconds)" >> $LOG
done
$PY code/match.py > logs/match_d4.log 2>&1
echo "== match exit $? $(date -Iseconds)" >> $LOG
$PY code/fidelity_d4.py > logs/fidelity_d4.log 2>&1
echo "== fidelity_d4 exit $? $(date -Iseconds)" >> $LOG
echo "== d4 done $(date -Iseconds)" >> $LOG
