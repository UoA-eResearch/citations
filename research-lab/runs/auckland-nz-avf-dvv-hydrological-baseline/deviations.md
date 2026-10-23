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
