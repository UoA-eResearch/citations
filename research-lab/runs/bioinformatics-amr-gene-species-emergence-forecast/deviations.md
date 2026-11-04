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

## D3 — 2026-11-04 00:30 NZDT — fixes after the independent review (verdict: fix first)

The review found that four load-bearing numbers were artefacts and two labels did not follow the plan's own rules.
Everything below was run after the review, so all of it is post hoc except where it implements the preregistered
quantity exactly (item 1) or a preregistered secondary that had not been run (item 6).

1. **The null, computed exactly** (finding 1). 1 − Binomial(≤1; n, f) saturates at exactly 1.0 in double precision
   for 4,727 primary-task candidates, and the stable sort then took the first 100 rows of that tie block. All 100 were
   *A. baumannii*, because candidates are written in alphabetical species order. The null is now computed in log
   space (`binom.logsf`). Genes with equal counts still tie within a species even in log space, so every
   precision@k is now the exact expectation under random order within ties (`d3_fixes.topk`). The null's
   precision@100 is **0.033**, not 0.08. Under random tie order the old saturated score gives 0.028 (row order
   gave 0.08).
2. **Seed stability** (finding 2). The preregistered hyperparameters were refitted with ten seeds, the preregistered
   one first. The model's precision@100 is 0.00 at the preregistered seed and 0.10–0.19 at the other nine. Its
   average precision is 0.075–0.090 at every seed, against the null's 0.016.
3. **H1 by the plan's rule** (finding 5), with the exact null at the preregistered seed. The ratio is 0 with an
   interval of 0 to 0.97, so it is *Refuted* by the rule (upper bound below 2). The exact null is never 0, so no
   bootstrap draw is undefined. At the other nine seeds the point ratio is 3.0–5.7. The report therefore states the
   preregistered verdict alongside its fragility.
4. **H2 by the plan's rule** (finding 4). The interval (−0.0128 to +0.0009) is neither below 0 nor within ±0.005,
   so H2 is *Inconclusive*. The code had refuted on the upper bound alone; `analyse.py` now applies the plan's rule
   and `primary.json` is relabelled. Across seeds the embedding's gain in average precision is positive at 7 of 10.
5. **Withdrawn: "the embedding is what breaks the model"** (finding 3). It described one seed.
6. **Preregistered secondaries now run** (finding 7):
   - the at-least-three-isolates variant: model 0.12 against null 0.024;
   - the D1 sensitivity with all genes (`KEEP_ALL_GENES`): 0.19 against 0.033;
   - recall at matched list sizes (`d3.json`);
   - the Europe PMC literature check (`epmc.csv`).

   **Gene × country was not run.** It needs a second candidate construction and feature set at country level, so it
   is a new study rather than a variant, and is recorded as not done.
7. **Deposit dates** (finding 6). 45% of isolates collected by 2022 were deposited after 2022, so the 2022 "cutoff"
   uses data that were not public in 2022. The design is retrospective by collection date, not a real-time
   forecast. Of the 847 primary-rule emergences, 705 had a carrier collected by 2022 but only 316 (37%) had one
   deposited by 2022 (`hindsight.json`). "Deposited" means a target_creation_date in or before 2022; the reviewer's
   rule, the earlier of target_creation_date and sra_release_date, gives 39.2% and 341 of 847. The report's "83% already observed" becomes "83% already collected, 37%
   already public".
8. **G4** (finding 8). `g4_check.py` recomputes 30 random pairs' first-observation years and two-BioProject years
   from the raw metadata independently of `build.py`; 30 of 30 match on both.
9. **G3 and G2** (findings 9, 10, 12):
   - the null's calibration by decile: its top decile predicts 0.47 against an observed 0.011;
   - the coverage double count of 135 rows is removed;
   - the embedding zero-vector fallback is recorded (one gene, 156 test rows, 2 positives);
   - a plausibility count is corrected.
10. **D1 was not blind** (finding 11). The catalog restriction was decided after 2023–2025 emergence counts had been
    seen. Its sensitivity (item 6) shows it does not drive the result.

## D3b — 2026-11-05 13:00 NZDT — fixes from the confirmation pass (verdict: fix first)

1. **The null still saturated** (C1). log P(≥2) from `binom.logsf` rounds to exactly 0.0 wherever P(≥2) is within
   about 1e-16 of 1, the same candidates whose probability saturated at 1.0. `d3_fixes.log_null` now ranks by
   −log P(≤1) (`binom.logcdf`), the same order without saturation: 798 distinct scores in the top 1,000.
   - **Null precision@100:** 0.073 (primary), 0.152 (first isolate), 0.053 (three isolates), 0.072 (all genes).
   - **H1 at the preregistered seed:** ratio 0, interval 0–0.46, Refuted.
   - **Other seeds:** the ratio is 1.4–2.6, with five of nine at 2 or more.
   - **Average precision:** the model is 4.1–4.9 times the null at every seed.
2. **Model metrics carried over** (`d3c_null.py`). The model fits are deterministic: the second D3 run reproduced the
   first run's per-seed values before it was stopped, and the reviewer reproduced them bit for bit. So the model
   metrics are carried over and only null-dependent quantities are recomputed, plus one model fit for the H1
   bootstrap.
3. **Wording** (C2–C5). The ratios, title and plain terms are corrected, and the first-appearance result now leads.
   The baseline mechanism is described correctly: exact ties plus row order, with 0.08 nearer the truth than 0.033.
   The "null cannot order large species" claim is withdrawn, the preregistered fit is labelled correctly, and the
   recall range is corrected.
4. **Records** (C6–C8). `primary.json` carries a superseded-null note, the report has a Coverage line, the embedding
   fallback is labelled UNPLANNED, and the deposit-date rule is stated beside the reviewer's.
