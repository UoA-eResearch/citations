# Deviations from plan.md

The study ran as planned; the first draft recorded no deviations. The ChEMBL download needed a resumable fetcher,
because EBI throttles this host, but that changed no analysis choice.

## D1 — 2026-11-05 — edits after the independent review (verdict: publish with edits)

All additions are post hoc and labelled so in the report.

1. **The noise floor** (finding 1). `code/noise_check.py` now adds the retrospective estimate's standard error (the
   standard deviation of the five repeats' RMSEs over √5, from `data/fits`) to the prospective one, in quadrature.
   The expected median absolute bias from noise is 0.065–0.069 for the provenance and cluster splitters, against the
   observed 0.16–0.22. The report's "about 0.05" becomes "about 0.07, a lower bound".
2. **The bars** (finding 2). H2's and H3's preregistered bars are stated against what was achievable. The verdicts are
   unchanged.
3. **Model spread** (finding 3). `code/posthoc_review.py`: per target, the five families' prospective RMSEs span a
   median of 0.49; the MLP's median is 1.41, against 1.04–1.09 for the others.
4. **Artefacts** (finding 4):
   - the time splitter's coverage share is noted as uninformative in `primary.json` (one repeat, zero-width
     interval);
   - group splitters' median test fractions (15–17%, against 20%) are stated.
5. **InChIKey skeletons** (finding 5). The review's check, 0.86% sharing a skeleton block, is cited.
6. **The G4 delta audit** (finding 6) is described as a document-year tabulation that cannot detect 2023+
   republication of older data.
7. **The lenient set** (finding 7): its size per target is stated.
8. **Smaller points** (finding 8):
   - dropped repeats concentrate on small targets (median 196 compounds against 789);
   - this file now exists;
   - in `bias_long.csv`, `nn_sim_median` is the prospective set's similarity on every row, retrospective rows
     included. That is by design for stratification, and is noted here rather than renamed.

## D2 — 2026-11-07 — edits after the confirmation pass (verdict: publish with edits)

The numbers below come from the confirming reviewer's checks, recorded in `review/review.md`.

1. **The H3 model-spread inference is replaced.** The 0.49 spread is driven by the MLP. Every split correctly ranks
   the MLP last (81–98% of targets), and no split orders the other four families, which sit within a median 0.20 of
   each other (τ 0.12–0.18 over those four).
2. **H3's bar** is now justified by the within-release noise ceiling: two single repeats agree at τ 0.40–0.55,
   against 0.30–0.37 for a single repeat against the future. This replaces the "steps of 0.2" remark.
3. **H2's bar.** A true per-target miss of up to about 0.08 would usually pass (the confirmation pass's
   simulation), so the bar was achievable. This replaces "near zero".
4. **Coverage.** Dropped repeats fall on 13 small targets; the 29 infeasible author graphs fall on larger targets
   (median 1,152 against 730).
5. **Corrections:** the document splits' retrospective SE is 0.068, and D1's date is fixed.
