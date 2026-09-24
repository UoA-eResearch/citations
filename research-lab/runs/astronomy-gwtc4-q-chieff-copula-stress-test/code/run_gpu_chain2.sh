#!/bin/bash
# Continuation of the full run after the D16 trim (2026-09-11 19:xx): waits for the LVK follow-up to finish its
# GPU fits, then runs the remaining stages. Finished models are skipped by the fit stage; diagnostics and figures
# are forced so the final tables include every model (the follow-up's interim diagnostics are superseded).
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
LOG=$RUN/logs/run_all_full_gpu.out
PY=$RUN/venv/bin/python
echo "=== $(date) chain2: waiting for run_lvk_followup.sh to exit" >> $LOG
while pgrep -f "run_lvk_followup.sh" > /dev/null; do sleep 30; done
echo "=== $(date) chain2: starting fit (remaining models), mocks, mockstats, diagnostics, figures" >> $LOG
$PY run_all.py --mode full --stages fit,mocks,mockstats >> $LOG 2>&1
RC=$?
echo "=== $(date) chain2: fit/mocks/mockstats exit rc=$RC" >> $LOG
if [ $RC -eq 0 ]; then
  $PY run_all.py --mode full --stages diagnostics,figures --force >> $LOG 2>&1
  echo "=== $(date) chain2: diagnostics/figures exit rc=$?" >> $LOG
fi
echo "=== $(date) CHAIN EXIT rc=$RC" >> $LOG
docker inspect -f '{{.State.Running}}' vllm | grep -q true || { echo "=== vllm down after chain2; starting" >> $LOG; docker start vllm >> $LOG 2>&1; }
exit $RC
