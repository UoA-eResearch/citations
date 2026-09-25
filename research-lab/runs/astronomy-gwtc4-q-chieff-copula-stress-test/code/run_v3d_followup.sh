#!/bin/bash
# D29d: once the v3d mocks exist, validate them and rerun the E2 statistics and the prior-shift PPC against them.
RUN=/mnt/citations/research-lab/runs/astronomy-gwtc4-q-chieff-copula-stress-test
cd $RUN/code
V=$RUN/venv/bin/python
LOG=$RUN/logs/run_v3d_followup.out
echo "=== $(date) waiting for v3d mocks" >> $LOG
for t in rho+0.00 rho-0.60 rho-0.40 rho-0.20 rho+0.20 width mean; do
  until [ -f $RUN/data/mocks/v3d/mocks_full_$t.h5 ]; do sleep 20; done
done
echo "=== $(date) v3d complete" >> $LOG
SETS=v3d JAX_PLATFORMS=cpu $V analysis/validate_mocks.py > $RUN/logs/validate_v3d.log 2>&1
echo "=== $(date) validation rc=$?" >> $LOG
JAX_PLATFORMS=cpu $V analysis/e2_tau.py --mock-dir $RUN/data/mocks/v3d --workers 12 > $RUN/logs/e2_tau_v3d.log 2>&1
echo "=== $(date) e2_tau v3d rc=$?" >> $LOG
JAX_PLATFORMS=cpu $V analysis/qmedian_dispersion_ppc.py --mock-dir $RUN/data/mocks/v3d > $RUN/logs/qmedian_ppc_v3d.log 2>&1
echo "=== $(date) qmedian ppc v3d rc=$?" >> $LOG
while pgrep -f "[e]2_rho_scan_mbin.py" > /dev/null; do sleep 20; done
$V analysis/e2_rho_scan_int.py --mock-dir $RUN/data/mocks/v3d --shared-gpu --chunk 77 > $RUN/logs/e2_rho_scan_int_v3d.log 2>&1
echo "=== $(date) integrated scan v3d rc=$?" >> $LOG
