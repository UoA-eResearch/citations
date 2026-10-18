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

## D2 outcome — 2026-10-18 15:27 NZDT — the revised extraction passes the re-validation (before any signal was recomputed)

Source: `results/tables/extraction_validation_round2.{csv,json}`, from `code/validation_adjudication.py 2`.

- **Sample.** 272 fresh papers; 35 yielded candidate signals.
- **Precision.** 97/106 = 0.92 on candidates. On fully eligible signals it is 68/71 = 0.96, above the 0.90 bar, so
  the study proceeds on the v2 extraction.
- **Remaining errors on candidates (9):**
  - 6 in one paper whose drug-approval years (2014–2021) were read as its FAERS window;
  - 3 within-drug sex or indication contrasts, labelled "subgroup" where "interaction" was meant.
- **Recall.** No candidate-level signal was missed.
- **The `comparison` label** is right for 103/106 candidates (0.97).
- **Not counted towards the decision:** one non-candidate window ("2006Q1-2021Q3" read as null).
- **Pipeline changes (D2):**
  - `code/eligible.py` now reads the v2 file and applies the FAERS and non-interaction rules.
  - `code/analysis.py` adds the all-drugs-only sensitivity, and reports how many windows start before 2004Q1.
    Those windows are recomputed from 2004Q1, the first quarter in the public files.

## D3 — 2026-10-18 18:12 NZDT — two implementation errors found after the first analysis; corrected, as-run results kept

The first analysis ran (as-run results are kept in `results/asrun/` and `data/recomputed_asrun.csv`):
- H1 survival 0.724 (95% CI 0.663–0.782), Refuted;
- H2 median published/recomputed ROR 1.079 (1.018–1.162), Refuted.

Checking why 279 of the 659 capped signals had no FAERS PT found two errors in the code, not in the plan:

1. **The cap came before rule 4.** The plan (§2) caps at 5 *eligible* signals per paper, and eligibility includes rule 4
   (the event is a FAERS PT). The code capped first and checked rule 4 later, inside the recomputation. Papers with
   non-PT signals among their 5 random picks therefore lost eligible signals.
2. **The spelling map broke two UK spellings.** "esophag" → "oesophag" and "estrogen" → "oestrogen" also fired on
   words already in UK spelling, giving "ooesophagitis".

**Correction.**
- `code/eligible.py` now checks rule 4 against the FAERS reaction table before the cap. The two map entries no longer
  fire after an "o". The map is otherwise unchanged, so US spellings it does not list (e.g. "hyperprolactinemia",
  "gynecomastia") still fail rule 4. This is a stated limitation.
- Result: 495 fully eligible signals, 406 after the cap, from 142 papers.
  - 337 of the 406 were already computed in the as-run pass and are reused, since the computation is deterministic.
  - 69 are new. 43 as-run signals are no longer drawn, because the draw now runs over a different eligible set.

**Status.** The corrected analysis implements the preregistered text, so it is primary. These errors were found
after the as-run results were seen, so the report gives both, with the as-run numbers beside the corrected ones.
