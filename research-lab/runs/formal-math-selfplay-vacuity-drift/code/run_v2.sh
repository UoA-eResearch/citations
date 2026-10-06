#!/bin/bash
# D7 rerun after the independent review: v2 certificate (elaborated in the original statement's context), STP's own
# verifier environment (`import miniF2F`), an all-of-Mathlib fallback for rows that do not re-verify under miniF2F, the
# split-repair sensitivity, and the four other corpora in their own environments. Outputs go to results/rows_v2/.
cd "$(dirname "$0")/.."
W=${W:-22}; CORES=${CORES:-4-27}
O=results/rows_v2; mkdir -p $O
PY="taskset -c $CORES ./venv/bin/python"
export VAC_HEADER=minif2f
$PY code/run_rows.py data/samples/stp_conjecture.parquet $O/stp_conjecture.jsonl $W --trivial-iters 1-9,38-47 --filter "(iteration <= 9) or (iteration >= 38)"
$PY code/run_rows.py data/samples/stp_conjecture.parquet $O/stp_conjecture.jsonl $W --trivial-iters 1-9,38-47
$PY code/run_rows.py data/samples/stp_statement.parquet $O/stp_statement.jsonl $W
for c in stp_conjecture stp_statement; do
  ./venv/bin/python -c "
import json
ids = [r['row_id'] for r in map(json.loads, open('$O/$c.jsonl')) if r.get('parsed') and not r.get('foreign_imports') and r.get('reverify') is False]
open('$O/${c}_fallback_ids.txt', 'w').write('\n'.join(map(str, ids)))
print('$c fallback rows:', len(ids))"
  VAC_HEADER=mathlib $PY code/run_rows.py data/samples/$c.parquet $O/${c}_mathlib.jsonl $W --ids $O/${c}_fallback_ids.txt --trivial-iters 1-9,38-47
done
$PY code/repair_split.py data/samples/stp_conjecture.parquet $O/stp_conjecture.jsonl $O/stp_conjecture_repair.jsonl $W
echo "repair done $(date)"
unset VAC_HEADER
for c in workbook dsp1 sftv2; do
  $PY code/run_rows.py data/samples/$c.parquet $O/$c.jsonl $W
done
VAC_TOOLCHAIN=v415 $PY code/run_rows.py data/samples/numina.parquet $O/numina.jsonl $W
echo "all done $(date)"
