#!/bin/bash
# D17 ablation chain (2026-09-11): after chain2 has finished (remaining fits, mocks, mock statistics, diagnostics,
# figures), fit the four single-ingredient ablations of the LVK configuration on the GPU, then redo diagnostics and
# figures so the final tables include them. Idempotent; restarts vllm at the end.
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
LOG=$RUN/logs/run_all_full_gpu.out
PY=$RUN/venv/bin/python
MODELS=abl_plp_m2taper_both,abl_plp_lvkspin_both,abl_bpl2p_sharedtaper_both,abl_bpl2p_plpspin_both
echo "=== $(date) chain3: waiting for run_gpu_chain2.sh to exit" >> $LOG
while pgrep -f "run_gpu_chain2.sh" > /dev/null; do sleep 60; done
echo "=== $(date) chain3: fitting ablations $MODELS" >> $LOG
$PY run_all.py --mode full --stages fit --models $MODELS --skip-nuts >> $LOG 2>&1
RC=$?
echo "=== $(date) chain3: ablation fits exit rc=$RC" >> $LOG
$PY run_all.py --mode full --stages diagnostics,figures --force >> $LOG 2>&1
echo "=== $(date) chain3: diagnostics/figures exit rc=$?" >> $LOG
echo "=== $(date) CHAIN3 EXIT rc=$RC" >> $LOG
docker inspect -f '{{.State.Running}}' vllm | grep -q true || { echo "=== vllm down after chain3; starting" >> $LOG; docker start vllm >> $LOG 2>&1; }
exit $RC
