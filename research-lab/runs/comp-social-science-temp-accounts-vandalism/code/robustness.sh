#!/bin/bash
# Preregistered robustness variants (plan.md sec 4-5): 24-hour window, 10% treatment threshold, excluding enwiki,
# and leave-one-cohort-out (cohorts by treatment month, from the primary run's treatment dates).
set -u
cd "$(dirname "$0")/.."
PY=venv/bin/python
$PY code/analysis.py --window 24 --tag window24
$PY code/analysis.py --thresh 0.10 --tag thresh10
$PY code/analysis.py --exclude enwiki --tag no_enwiki
$PY code/analysis.py --weight edits --tag edit_weighted
for c in 2024-11 2025-06 2025-09 2025-11 2026-03; do
  ex=$(awk -F, -v c=$c 'NR>1 && substr($2,1,7)==c {print $1}' results/tables/treatment_dates_primary.csv | paste -sd,)
  $PY code/analysis.py --exclude "$ex" --tag "drop_$c"
done
echo ROBUSTNESS_DONE
