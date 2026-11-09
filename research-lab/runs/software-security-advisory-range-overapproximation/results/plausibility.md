# Plausibility (G3)

Hand traces (`code/handtrace.py`, `results/tables/handtrace.json`; D4). One seeded-random advisory per class. Releases
are re-downloaded with plain urllib, fix files are matched to release files by hand-written suffix matching (not
`presence.py`), and the fix's deleted lines in non-test files are counted by plain substring search on
whitespace-stripped text:
- **Tight** (GHSA-q326-jhw3-699g, ipython): the earliest in-range release (3.0.0) contains 32 of 32 deleted lines;
  pipeline s = 1.0, present.
- **Over-approximated** (GHSA-hvfh-5mj3-5f3j, chainlit): release A (2.4.0rc0) contains 41% of the lines by hand
  against s = 0.32 (both undetermined); the first absent release (2.7.1) contains none, but its artefact has **no
  source files at all**, the empty-extraction case of the review's finding 8; the first present release (2.11.0)
  contains 98% (s 0.98). 2.7.1 is its only absent release, so this is the one advisory the recheck reclassifies
  undetermined (`release_recheck.csv`).
- **Undetermined** (GHSA-r4gj-5m52-g5wh, axios): 65% by hand against s = 0.61, between the thresholds.

The first traces (three chosen advisories, using the pipeline's own path matching) are kept as
`results/tables/handtrace_v1_chosen.json`.

Invariants, asserted in `code/posthoc_d4.py`:
- 800 sampled advisories, 800 rows in `classes.csv`; 411 classified (308 over-approximated, 103 tight).
- Tight advisories are present at index 0.
- Corrected pairs never exceed declared pairs, under every reading (pipeline, strict, earlier starts).
- Coverage reconciles: 800 = 411 classified + 300 undetermined + 79 no signature + 10 no diff.

Recheck (`code/recheck_d4.py`): the stored presence share reproduces exactly for every re-downloaded deciding release
(307 of 307 absent, 411 of 411 present).
