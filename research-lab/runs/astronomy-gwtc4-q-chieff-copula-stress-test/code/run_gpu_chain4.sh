#!/bin/bash
# Final chain (2026-09-13, D18): after chain2 exits, fit whatever is still missing from the full model set (the four
# D17 ablations; copula_indep_splm1 has been dropped), then the mock arm (stages 04-05), then diagnostics and figures
# with --force so every table includes every fitted model. Restarts vllm at the end. Idempotent.
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
LOG=$RUN/logs/run_all_full_gpu.out
PY=$RUN/venv/bin/python
echo "=== $(date) chain4: waiting for run_gpu_chain2.sh to exit" >> $LOG
while pgrep -f "run_gpu_chain2.sh" > /dev/null; do sleep 20; done
echo "=== $(date) chain4: fit (ablations) + mocks + mockstats" >> $LOG
$PY run_all.py --mode full --stages fit,mocks,mockstats --skip-nuts >> $LOG 2>&1
RC=$?
echo "=== $(date) chain4: fit/mocks/mockstats exit rc=$RC" >> $LOG
$PY run_all.py --mode full --stages diagnostics,figures --force >> $LOG 2>&1
echo "=== $(date) chain4: diagnostics/figures exit rc=$?" >> $LOG
echo "=== $(date) CHAIN4 EXIT rc=$RC" >> $LOG
docker inspect -f '{{.State.Running}}' vllm | grep -q true || { echo "=== vllm down after chain4; starting" >> $LOG; docker start vllm >> $LOG 2>&1; }
exit $RC
