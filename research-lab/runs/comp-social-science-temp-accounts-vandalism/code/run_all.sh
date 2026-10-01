#!/bin/bash
# Full re-run after re-extraction (deviations.md D5): primary, robustness, extra models, placebo checks, figures.
set -u
cd "$(dirname "$0")/.."
PY=venv/bin/python
$PY code/analysis.py --tag primary
code/robustness.sh
$PY code/extra_models.py
$PY code/placebo_checks.py
$PY code/make_figures.py primary
echo RUN_ALL_DONE
