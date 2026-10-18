# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 14:24 NZDT — larger token budget for 64 extraction failures (before any extraction was validated or used)

The first pass extracted 1,766 of 1,830 abstracts. For 58 of the 64 failures the reasoning model spent its whole
4,096-token budget reasoning and returned no answer; the other 4 returned truncated JSON. Those 64 are retried with a
16,384-token budget (`MAX_TOKENS=16384`). The prompt, schema and temperature are unchanged. Papers still failing are
reported as extraction failures and stay in the denominator of papers processed.

## D2 — 2026-10-18 15:00 NZDT — the extraction check failed; one prompt and schema revision, re-validated on a fresh sample (before any signal was recomputed)

**Round 1 result** (`code/validation_adjudication.py`, `results/tables/extraction_validation.{csv,json}`):
- 272 papers sampled (seed 20261019); 44 yielded candidate signals (a ROR with estimate and CI, lower bound > 1, a window).
- Precision was 115/147 = 0.78 on candidates, and 51/71 = 0.72 on fully eligible signals (single RxNorm ingredient, a FAERS PT).
- Recall was complete: the 11 missed candidate-level signals were all class, SOC, combination or grouped-event estimates,
  none of them eligible.
- Errors on eligible signals (20):
  - 10 window: one paper's "June 2023" was read as 2023Q4.
  - 5 non-FAERS database: JADER and EudraVigilance estimates.
  - 2 misattributed drug: a regimen subgroup estimate attributed to one component.
  - 1 each: a non-disproportionality factor (dose per body weight), an HLT split into its PTs, and an IC025 copied as the ROR CI.

Precision is below the 0.90 bar, so plan §5 applies: the prompt and schema are revised once.

**Revision (prompt and schema v2, in `code/extract_signals.py`):**
- An explicit month-to-quarter rule with worked examples. The window is null unless the FAERS period's start and end are
  both stated.
- Per-signal `database` (FAERS / other / unclear) and `comparison` (all drugs / subgroup / comparator / interaction /
  unclear).
- The drug is the drug, class, regimen or combination the estimate belongs to, never one component of it.
- Grouped event names stay whole.
- A reported bound only (ROR025, IC025) gives a null estimate, and a CI is never borrowed from another measure.
- Adjusted RORs count as ROR.
- The token budget is 16,384 from the start (D1).
- Temperature, model and server are unchanged.

**Eligibility, added to plan §2:**
- the signal's `database` is FAERS;
- its `comparison` is not `interaction`.

As preregistered (§7), subgroup and comparator-restricted estimates stay in the primary set. A sensitivity analysis keeps
only `comparison` = all drugs.

**Re-validation:**
- A fresh random sample of 272 papers (15%), drawn from the extracted papers not in round 1 (seed 20261020), fixed
  before any v2 output exists. It is adjudicated by the same rules.
- Precision on fully eligible signals must be at least 0.90. If it is not, the study reports extraction as the finding
  and does not run the recalibration.
- The round-1 sample is re-extracted with v2 as a development check only; it does not count towards the decision.
- The v2 extraction then replaces v1 for every paper (`data/extract/signals_raw_v2.jsonl`).
- The accuracy of the `comparison` label is reported separately; it affects only the sensitivity analysis.
