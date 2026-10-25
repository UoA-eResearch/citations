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
