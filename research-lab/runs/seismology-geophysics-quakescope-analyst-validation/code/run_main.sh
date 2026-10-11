#!/bin/bash
# After the downloads: parse -> covariates (waveforms only) -> match -> analysis (all code committed in ac2ad99).
cd "$(dirname "$0")/.."
R=$(pwd)
export PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
while kill -0 3901360 2>/dev/null; do sleep 60; done
grep -q "FETCH DONE" $R/logs/fetch.log || { echo "fetch did not finish cleanly $(date)"; exit 1; }
grep -q "Traceback" $R/logs/fetch.log && { echo "fetch log has a traceback $(date)"; exit 1; }
./venv/bin/python code/parse.py && echo "parse done $(date)" || exit 1
./venv/bin/python code/covariates.py 12 > logs/covariates.log 2>&1 && echo "covariates done $(date)" || { echo "covariates failed"; exit 1; }
./venv/bin/python code/match.py > logs/match.log 2>&1 && echo "match done $(date)" || { echo "match failed"; exit 1; }
./venv/bin/python code/analysis.py > logs/analysis.log 2>&1 && echo "analysis done $(date)" || { echo "analysis failed"; exit 1; }
echo "MAIN DONE $(date)"
