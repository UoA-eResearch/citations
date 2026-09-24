#!/bin/bash
# Full-run driver: waits for a running stage-01 fetch, re-crawls with the FAR fallback (retrying failed
# downloads once), builds the sample, verifies it is the LVK 153-BBH set and that the injection spin
# families validate, then runs the remaining stages (fit/mocks/mockstats/diagnostics/figures).
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
LOG=$RUN/logs/run_all_full_chain.out
PY=$RUN/venv/bin/python
while pgrep -f "fetch_data.py --mode full" > /dev/null; do sleep 20; done
echo "=== $(date) initial fetch ended; re-crawling with the FAR fallback (--force)" >> $LOG
$PY run_all.py --mode full --stages fetch --force >> $LOG 2>&1
if tail -80 $RUN/logs/01_fetch_data_full.log | grep -q "downloads failed"; then
  echo "=== $(date) retrying failed downloads" >> $LOG
  $PY run_all.py --mode full --stages fetch --force >> $LOG 2>&1
fi
echo "=== $(date) build + test" >> $LOG
$PY run_all.py --mode full --stages build,test >> $LOG 2>&1 || { echo "=== BUILD/TEST FAILED" >> $LOG; exit 1; }
N=$($PY -c "import json;print(json.load(open('$RUN/data/processed/sample_summary_full.json'))['n_included'])")
OK=$($PY -c "import json;print(json.load(open('$RUN/data/processed/injection_check_full.json'))['all_supported'])")
echo "=== $(date) sample n_included=$N injection all_supported=$OK" >> $LOG
if [ "$N" != "153" ] || [ "$OK" != "True" ]; then
  echo "=== SAMPLE CHECK FAILED (expected 153 / True); stopping before the GPU stages" >> $LOG
  exit 2
fi
echo "=== $(date) fit/mocks/mockstats/diagnostics/figures" >> $LOG
$PY run_all.py --mode full --stages fit,mocks,mockstats,diagnostics,figures >> $LOG 2>&1
echo "=== $(date) CHAIN EXIT rc=$?" >> $LOG
