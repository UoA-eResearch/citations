#!/bin/bash
# Resumed full run (2026-09-11): model unit tests on the current config, then the GPU stages.
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
LOG=$RUN/logs/run_all_full_gpu.out
PY=$RUN/venv/bin/python
N=$($PY -c "import json;print(json.load(open('$RUN/data/processed/sample_summary_full.json'))['n_included'])")
echo "=== $(date) sample n_included=$N; running model tests" >> $LOG
[ "$N" = "153" ] || { echo "=== SAMPLE CHECK FAILED ($N != 153)" >> $LOG; exit 2; }
$PY run_all.py --mode full --stages test >> $LOG 2>&1 || { echo "=== $(date) MODEL TESTS FAILED; not starting GPU stages" >> $LOG; exit 1; }
echo "=== $(date) starting fit,mocks,mockstats,diagnostics,figures" >> $LOG
$PY run_all.py --mode full --stages fit,mocks,mockstats,diagnostics,figures >> $LOG 2>&1
RC=$?
echo "=== $(date) CHAIN EXIT rc=$RC" >> $LOG
docker inspect -f '{{.State.Running}}' vllm | grep -q true || { echo "=== vllm down after chain; starting" >> $LOG; docker start vllm >> $LOG 2>&1; }
exit $RC
