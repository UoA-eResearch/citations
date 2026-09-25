#!/bin/bash
# D27c: once the v3c mocks exist, validate them and rerun both E2 statistics against them.
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
V=$RUN/venv/bin/python
LOG=$RUN/logs/run_v3c_followup.out
echo "=== $(date) waiting for v3c mocks" >> $LOG
for t in rho+0.00 rho-0.60 rho-0.40 rho-0.20 rho+0.20 width mean; do
  until [ -f $RUN/data/mocks/v3c/mocks_full_$t.h5 ]; do sleep 20; done
done
echo "=== $(date) v3c complete; starting validation, tau and the integrated scan" >> $LOG
SETS=v3c JAX_PLATFORMS=cpu $V analysis/validate_mocks.py > $RUN/logs/validate_v3c.log 2>&1 &
P1=$!
JAX_PLATFORMS=cpu $V analysis/e2_tau.py --mock-dir $RUN/data/mocks/v3c --workers 12 > $RUN/logs/e2_tau_v3c.log 2>&1 &
P2=$!
$V analysis/e2_rho_scan_int.py --mock-dir $RUN/data/mocks/v3c --shared-gpu --chunk 77 > $RUN/logs/e2_rho_scan_int_v3c.log 2>&1 &
P3=$!
wait $P1; echo "=== $(date) validation rc=$?" >> $LOG
wait $P2; echo "=== $(date) e2_tau v3c rc=$?" >> $LOG
wait $P3; echo "=== $(date) integrated scan v3c rc=$?" >> $LOG
