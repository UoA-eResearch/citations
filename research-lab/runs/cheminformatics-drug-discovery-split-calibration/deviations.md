# Deviations from plan.md

The study ran as planned; the first draft recorded no deviations. The ChEMBL download needed a resumable fetcher,
because EBI throttles this host, but that changed no analysis choice.

## D1 — 2026-11-06 — edits after the independent review (verdict: publish with edits)

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
