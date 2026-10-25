# Deviations from the preregistration

No analysis choice was changed. These are recorded for completeness.

## Technical — 2026-10-23 20:03 NZDT

- **pyproj** (used by `dvv.py` for inter-station distances) was missing from the venv, and the first `dvv.py` run
  stopped on import. It was installed after the correlation job had finished, and `dvv.py` was re-run unchanged.
- **The import path.** `model.py` could not import `dvv` under `python -I`, which drops the script directory, so the
  directory was added to `sys.path`. No logic changed.

## Post hoc checks — 2026-10-23 20:03 NZDT, after the primary result was read

These are labelled post hoc in the report and do not change H1.
- **`code/posthoc_drift.py`:** held-out R² with the linear drift held at its end-of-training value instead of
  extrapolated.
- **`code/posthoc_kernel.py`:** the preregistered erfc kernel, which tends to 1 at long lags, so rain never drains,
  is replaced by a draining exponential kernel exp(−lag/τ) over the same τ grid.

## Pre-review gate (G5, G6) — 2026-10-25 19:11 NZDT, after all results (wording and attribution only)

The lab's METHODS.md gates were run before this draft's review. No number changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - the title said "Rainfall and season do not predict"; it now says "A rainfall-and-season model does not predict",
    as the report already states that hydrology's effect is not excluded;
  - the plain-terms sentence about predicting worse than the average now says it holds for 25 of the 32 pairs.
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 12 claims, passes):
  - the lead's 0.05% target, attributed to Brenguier et al. (2008), is not in that paper's abstract or preprint
    text, which reports detectable perturbations as small as 0.1%;
  - the verdict now compares the 0.14% noise floor with that 0.1% and notes the unsupported 0.05% target.
  - All six cited DOIs resolve exactly in OpenAlex, and none is retracted.

## D1 — 2026-10-25 23:26 NZDT — fixes after independent review (POST-RESULT)

The Fable review (`review/review.md`, "fix first") found processing faults that changed the numbers but not the
verdict. All changes were made after every result had been seen. The first-version tables and figures are in
`results/tables/v1_pre_review/` and `results/figures/v1_pre_review/`.

1. **Segments (dvv.py).** Segments now also break on a change of sensor dip (polarity) and on station data gaps of
   more than 7 days, the plan's own "gap" wording, which the metadata-only rule missed. KBAZ splits at 2014-08-25
   (dip +90 to −90) and at 2018-03-21 (a 3.5-year data gap). Segments are written to `results/tables/segments.csv`
   and used by every downstream script.
2. **Dead channel and polarity checks (G2).**
   - Pair-days with zero coda energy are removed from references and stacks: 852, including the 52-day KBAZ block of
     2018-08-22 to 2018-10-31, which had entered the table as +2.05%.
   - Days whose stack correlates negatively with the reference at zero stretch are dropped (959).
   - All drops are counted in `results/tables/coverage.json`.
3. **Interpolation.** The stretched trace is evaluated with a cubic spline instead of linear interpolation on the
   20 Hz lag grid, which had banded low-SNR series. The 0.05%/0.005% grid, which replaced the plan's 0.01% grid
   without a deviation entry, is now stated.
4. **Secondary 4** recomputes dv/v with every-epoch segments (`RULE=every_epoch`). It previously only truncated
   held-out windows.
5. **Floors.**
   - Beside the preregistered residual floor, the report gives the held-out dv/v's own 2 SD about its mean and a
     season-only model's residual.
   - The title no longer leads with the failed model's residual.
6. **Lockdown.** The windows get a 15-day guard against the 30-day smoother (both reported).
7. **Post hoc coherence breakdown.** The median zero-stretch correlation of the 11-day stack with its reference is
   stored, and the scored pairs with a median of 0.7 or more are reported separately.
8. **Attribution (G6) corrected.**
   - The pre-review gate's claim that Brenguier et al. (2008) does not contain 0.05% was wrong. The published
     abstract gives decreases of order 0.05%; the gate had read only the arXiv preprint. Ledger A2 and the report are
     corrected.
   - A5's role and claim are fixed: background on ocean noise, with cultural noise attributed to A6.
   - METHODS.md G6 now requires checking the version of record.
9. **G3.** `results/plausibility.md` and `code/handtrace.py` (three pair-days recomputed from raw correlations:
   two exact, one within a fine-grid step).

**Result.** The median held-out R² is −0.27 (−0.35 to −0.15) on 31 scored pairs, still Refuted. The floors are
0.076% (residual), 0.074% (no model) and 0.067% (season-only), against v1's −0.12 and 0.136%.

### D1 addendum — 2026-10-26 03:58 NZDT — after the confirmation pass

- **The confirmation pass found that the 7-day data-gap rule split records at routine outages.** MKAZ had 16
  segments and WIAZ/RVAZ 7; held-out windows ended at outages, and 15 of 31 scored pairs rested on under two years of
  training.
- **The data-gap threshold is now 90 days**, which still separates KBAZ's 3.5-year gap. The dip rule and the
  per-day drops are unchanged.
- **The 7-day version is kept as a sensitivity** (`GAP=7`, `secondary_gap7.json`: −0.27, 31 pairs).
- **Final primary:** median held-out R² −0.08 (−0.19 to −0.01), 33 scored pairs, 24 negative. Still Refuted.
- **Floors:** residual 0.088%, no model 0.077%, season-only 0.075%.
- **Coverage:** 186,439 of 200,667 pair-days measured.
- The v1 `dvv_daily.parquet` is in git history at commit 35e9d7a, not duplicated in `v1_pre_review/`.
