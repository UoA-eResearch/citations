#!/bin/bash
# Follow-up to the main full-mode chain (2026-09-11, deviations D15): once the main chain has exited, fit the
# four LVK Broken Power Law + 2 Peaks models on the GPU, then redo diagnostics and figures so the BF table,
# the second gate (gate_lvk_masses) and summary_full.md include them. Idempotent: finished models are skipped.
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
LOG=$RUN/logs/run_all_full_lvk.out
PY=$RUN/venv/bin/python
MODELS=lvk_bpl2p_both,lvk_bpl2p_null,lvk_bpl2p_mean,lvk_bpl2p_width

echo "=== $(date) waiting for the main chain (run_all.py --mode full --stages fit,...) to exit" >> $LOG
while pgrep -f "run_all.py --mode full --stages fit,mocks" > /dev/null; do sleep 30; done
echo "=== $(date) main chain gone; fitting $MODELS" >> $LOG
$PY run_all.py --mode full --stages fit --models $MODELS --skip-nuts >> $LOG 2>&1
RC=$?
echo "=== $(date) LVK fits exit rc=$RC" >> $LOG
if [ $RC -eq 0 ]; then
  echo "=== $(date) redoing diagnostics + figures with the LVK models" >> $LOG
  $PY run_all.py --mode full --stages diagnostics,figures --force >> $LOG 2>&1
  echo "=== $(date) diagnostics/figures exit rc=$?" >> $LOG
fi
docker inspect -f '{{.State.Running}}' vllm | grep -q true || { echo "=== vllm down after follow-up; starting" >> $LOG; docker start vllm >> $LOG 2>&1; }
echo "=== $(date) FOLLOW-UP EXIT rc=$RC" >> $LOG
exit $RC
