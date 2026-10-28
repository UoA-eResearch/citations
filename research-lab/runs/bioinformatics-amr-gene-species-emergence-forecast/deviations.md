# Deviations from plan.md

## D1 — 2026-10-29 00:07 NZDT — the AMR catalog is not fixed across the corpus; candidate genes are restricted to the oldest catalog in use. Before any candidate table, model or result

**The problem.** Plan section 3 (G1) assumed "the reference catalog and AMRFinderPlus version are fixed", so that a
catalog update could not create a new pair in one period only. The isolate metadata shows otherwise: calls were made
with five reference-database versions, 2025-12-03.1 to 2026-08-07.1 (and five older ones, 15 isolates in all). A
symbol added to the catalog in 2026 can only be called on isolates processed after that, so its "first observation"
is partly an artefact of reprocessing.

**How large.**
- The version mix is nearly flat across collection years (the 2026-08-07.1 share runs from 0.37 in 2017 to 0.23 in
  2025), so a newly catalogued gene's carriers are spread over all collection years rather than recent ones.
- Even so, genes never called under a version before 2026-03 are 8.5% of 2023–2025 emergent pairs against 3.1% of
  pairs established by 2022, a 2.8-fold enrichment. Part of that is rarity rather than catalog age, but it is not
  negligible.

**The fix** (decided before any candidate table was built):
- **Candidate genes are restricted to symbols present in the 2025-12-03.1 Reference Gene Catalog**, the oldest
  version in use. Every retained isolate was screened with a catalog containing all of them, so catalog growth
  cannot manufacture an emergence.
- **Isolates processed with a version older than 2025-12-03.1 are dropped** (15 of 1.62 million).
- Cost: 4,250 of 4,417 observed symbols are kept (97.9% of calls) and 1,116 of 1,160 emergent pairs in 2023–2025.
- The excluded genes are reported, and a sensitivity keeps them.

## D2 — 2026-10-29 07:20 NZDT — hyperparameter selection, and post hoc diagnosis of the primary result

1. **Hyperparameters** (decided before the model was fitted). plan.md section 0 says they are "chosen on that
   split's 2022 slice", which is ambiguous for a task whose horizon is 2020–2022. They are instead chosen inside the
   training task by gene-grouped 2-fold cross-validation over three settings, then refitted on all of it. No test
   candidate is involved.
2. **Post hoc, after the primary result** (`code/posthoc.py`): score saturation, the carried-over against
   newly-eligible split, within-period cross-validation on the test task, and the H1 statistic for the
   no-embedding model (the H2 comparison model, which is a preregistered ablation). These diagnose why the
   preregistered model loses to the null; none of them changes H1 or H2.
