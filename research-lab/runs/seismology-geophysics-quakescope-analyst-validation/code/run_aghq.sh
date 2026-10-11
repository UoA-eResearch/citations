#!/bin/bash
# AGHQ maximum-likelihood fits (deviations.md D4), then the H2 exploratory analyses that use the ML station effects.
R=/mnt/citations/research-lab/runs/seismology-geophysics-quakescope-analyst-validation
cd $R
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
for K in 1 15; do for S in vb zero; do
  (./venv/bin/python code/checks.py aghq $K $S > logs/checks_aghq_K${K}_$S.log 2>&1 && echo "aghq DONE" >> logs/checks_aghq_K${K}_$S.log || echo "aghq FAILED" >> logs/checks_aghq_K${K}_$S.log) &
done; done
wait
(./venv/bin/python code/checks.py h2x > logs/checks_h2x.log 2>&1 && echo "h2x DONE" >> logs/checks_h2x.log || echo "h2x FAILED" >> logs/checks_h2x.log)
echo "AGHQ AND H2X FINISHED" > logs/checks_aghq_all.log
