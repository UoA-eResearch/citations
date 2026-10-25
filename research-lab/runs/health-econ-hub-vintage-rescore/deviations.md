# Deviations from plan.md

## D1 — 2026-10-25 03:44 NZDT — the COVID-19 Forecast Hub secondary is not run

The archived `reichlab/covid19-forecast-hub` repository is 13.8 GB. Clones from GitHub ran at roughly 0.3–3 MB/s
today, so it could not be obtained within the run. As the plan allows, plan §1's secondary and §3.4 are logged as not
run. No other change; the primary FluSight analysis is as planned.

## Pre-review gate (G5, G6, plus a G3 point) — 2026-10-25 22:59 NZDT, after all results (wording and attribution only)

The lab's METHODS.md gates were run before this draft's review. No number changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - the title's "top model changed" now notes it happens in about half of bootstrap resamples;
  - "the top-ranked team changed" became "model", since one change is between two variants of the same team;
  - "leaderboards mostly reflect forecasting skill" became "mostly not an artefact of data revisions", as skill was
    not measured.
- **G3 point.** 2022–23 also had heavy revisions (27% of location-weeks revised by more than 10%) but no net bias and
  0.7% reversals. The revisions bullet and the closing sentence now say that the downward bias of first reports, not
  the size of revisions, goes with reversals.
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 3 claims, passes): Mathis et al. 2024 (Nat. Commun.)
  resolves.
