#!/bin/bash
# Final GPU queue (2026-09-25, D27/D28). Waits for the D24 LVK-copula chain, then keeps vllm stopped for the whole
# queue (restarted by the EXIT trap, also on failure or kill): nuisance-integrated rho scan on the validated v3b mocks,
# then repeat-seed nautilus fits for the ablation configurations (two extra seeds each).
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
LOG=$RUN/logs/run_gpu_final.out
PY=$RUN/venv/bin/python
echo "=== $(date) waiting for run_lvk_copula.sh" >> $LOG
while pgrep -f "run_lvk_copula[.]sh" > /dev/null; do sleep 20; done
restore() { docker inspect -f '{{.State.Running}}' vllm | grep -q true || { echo "=== $(date) starting vllm" >> $LOG; docker start vllm >> $LOG 2>&1; }; }
trap restore EXIT
echo "=== $(date) stopping vllm for the queue" >> $LOG
docker stop vllm >> $LOG 2>&1
sleep 10
echo "=== $(date) D27 integrated rho scan on v3b mocks" >> $LOG
$PY analysis/e2_rho_scan_int.py --mock-dir $RUN/data/mocks/v3 --backend gpu >> $LOG 2>&1
echo "=== $(date) D27 scan exit rc=$?" >> $LOG
MODELS=baseline_plp_both,lvk_bpl2p_both,abl_plp_lvkspin_both,abl_bpl2p_plpspin_both
for S in 2 3; do
  echo "=== $(date) D28 seed $S: $MODELS" >> $LOG
  SEED_TAG=$S $PY run_all.py --mode full --stages fit --models $MODELS --skip-nuts --backend gpu >> $LOG 2>&1
  echo "=== $(date) D28 seed $S exit rc=$?" >> $LOG
done
echo "=== $(date) FINAL QUEUE DONE" >> $LOG
