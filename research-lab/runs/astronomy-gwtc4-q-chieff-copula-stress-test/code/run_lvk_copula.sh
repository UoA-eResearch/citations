#!/bin/bash
# D24: E1 inside the LVK configuration. Waits for the D22 mass-binned scan to release the GPU, fits the Frank and
# Gaussian copulas on the LVK parametric marginals, then refreshes diagnostics and figures on the CPU.
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
LOG=$RUN/logs/run_all_full_lvk_copula.out
PY=$RUN/venv/bin/python
echo "=== $(date) waiting for e2_rho_scan_mbin.py" >> $LOG
while pgrep -f "analysis/e2_rho_scan_mbin.py" > /dev/null; do sleep 15; done
echo "=== $(date) fitting copula_frank_lvk, copula_gauss_lvk" >> $LOG
$PY run_all.py --mode full --stages fit --models copula_frank_lvk,copula_gauss_lvk --skip-nuts >> $LOG 2>&1
RC=$?
echo "=== $(date) fits exit rc=$RC" >> $LOG
$PY run_all.py --mode full --stages diagnostics,figures --force --backend cpu >> $LOG 2>&1
echo "=== $(date) diagnostics/figures exit rc=$?" >> $LOG
docker inspect -f '{{.State.Running}}' vllm | grep -q true || { echo "=== vllm down; starting" >> $LOG; docker start vllm >> $LOG 2>&1; }
echo "=== $(date) LVK-COPULA EXIT rc=$RC" >> $LOG
