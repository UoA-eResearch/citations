# Plausibility gate (G3)

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| median prospective RMSE (RF, pChEMBL) | 1.07 | QSAR regression errors on held-out ChEMBL data commonly near 1 log unit; random-split RMSE here 0.68 | yes | |
| random split optimistic | −0.37 log units | Sheridan 2013: random selection too optimistic (ledger L1) | yes | partly confirmatory |
| time split near unbiased | +0.01 | Sheridan 2013: time split closest to prospective (L1) | yes | within-release document years |
| cluster split | −0.05 (not pessimistic) | Sheridan's leave-class-out was pessimistic | partly | Butina clusters at 0.65 distance are smaller than his classes |
| prospective-noise floor for median absolute bias | about 0.045 | normal-theory SE of RMSE, RMSE/√(2n) | yes | observed 0.16–0.22 |

## 2. Three targets traced end to end (`code/plausibility_check.py`, `results/tables/plausibility_traces.json`)

The RF was refitted independently of run.py's loop on all ChEMBL 33 compounds of the target (500 trees, seed
20261026), then predicted on the primary prospective set.

| target | train / prospective compounds | prospective RMSE recomputed | stored | retrospective RMSE (random / scaffold / document / time) | notes |
|---|---|---|---|---|---|
| CHEMBL2899 (smallest, 101) | 101 / 69 | 1.388 | 1.388 | 0.34 / 0.40 / — / 0.47 | cluster and document repeats dropped (no 15–25% draw), counted in coverage |
| CHEMBL221 (median, 746) | 746 / 61 | 1.113 | 1.113 | 0.75 / 0.86 / 1.04 / 1.06 | |
| CHEMBL1163125 (90th percentile, 3,295) | 3,295 / 768 | 0.823 | 0.823 | 0.56 / 0.66 / 0.87 / 1.37 | author infeasible (one component holds >80%), counted |

In all three, the random and scaffold estimates fall below the prospective RMSE. The provenance estimates are
closer, on either side.

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| strict prospective compounds are absent from ChEMBL 33 (InChIKey) | select.py; selection.json | yes, by construction |
| fit units: ok + planned drops = attempted | coverage.json `fits` | yes (37,600 + 425 + 145 = 38,170) |
| every target has the primary prospective set and the RF fit | bias_long.csv | yes (250 targets) |
| recomputed RF prospective RMSE equals the stored value | plausibility_traces.json | yes (3 of 3, to 4 decimals) |
