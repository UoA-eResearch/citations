# Deviations and implementation details

The plan (plan.md) was committed in 691a47e at 2026-10-07 08:43 NZDT, and the backtest code in e1a51b0 before its
first run. Entries are timestamped with `date`.

## D1. A secondary, recent-window prediction interval added after the backtest; forecasts frozen (2026-10-07 08:46 NZDT)

**What the backtest showed.** The preregistered 80% intervals for M1 calibrate errors over an expanding window that
starts in 2012. For district Totals at h = 1-2 they covered 73-76% of outcomes over the whole backtest, but only
59-62% for targets in 2023-2026. In that period errors were larger and mostly positive: 24-month coverage rose faster
than the cascade predicted.

**Change.** The frozen forecasts carry, as a labelled secondary, a second 80% interval (`lo80_recent`,
`hi80_recent`). It calibrates the standardised errors of the latest 8 target quarters only, with at least 6.

- In the backtest its coverage over 2023-2026 would have been 72-76%. That is a post hoc figure, from the same
  period that motivated the change.
- **H2 is scored on the preregistered interval** (`lo80`, `hi80`). The recent-window interval is reported
  alongside.
- The point forecasts and every preregistered element are unchanged.

**Frozen forecasts.** `results/forecasts_frozen.csv` holds 279 rows: origin 2026Q2, h = 1-4, 20 districts plus the
national total, five groups. Its sha256 is

  e19d0d63c19ed56e34629a9c0f93953c5e8c2beba7517ed09688bc62b0d547df

It is committed now, before Health NZ publishes the Q1 2026/27 file (July-September 2026, expected about December
2026). Scoring will use `code/score.py`, to be written without changing `backtest.py` or the frozen file.

## D2. Independent review (fix first): corrections, implementation details and scoring safeguards (2026-10-07 09:18 NZDT)

The review (`review/review.md`) re-ran the pipeline from the raw files and reproduced every results file byte for
byte. It confirmed H1 = Refuted and the frozen file's hash. It asked for corrections to the interpretation and to
D1, plus the following. **None of this touches `results/forecasts_frozen.csv` or the H1 computation.**

**Amendments to D1.**

- **The comparison was not like-for-like.** The recent-window interval needs 6 of the latest 8 target quarters, and
  2022Q2 and 2023Q2 have no file, so it exists for only half of the 2023-2026 district-Total cells (80 of 160 at h = 1,
  100 of 200 at h = 2) and for no 2024 target. On the cells where both intervals exist, coverage is:
  - preregistered interval: 65% (h = 1) and 64% (h = 2);
  - recent-window interval: 76% and 72%.

  The figures given in D1 compared different cells.
- **The frozen recent interval at h = 1 breaks D1's own rule.** At origin 2026Q2 it is calibrated on 5 target
  quarters, not 6. It is reported, but marked as not meeting D1's minimum. `backtest.py` now applies the guard, for
  any future run.
- **Calibration stops at origin 2025Q2.** Both the preregistered and the recent h = 1-2 intervals use errors only up to
  that origin, the H1 origin range. So the latest 2-3 available short-horizon errors (targets 2025Q4-2026Q2) were not
  used. This is a limitation of the frozen intervals.

**Implementation details not stated in the plan.**

- **The national total is in the interval pool.** `backtest.py` puts its errors into each group's pooled z
  percentiles, while the plan says "pooled across districts". Without it, primary-cell coverage in the backtest is
  76.7% (h = 1) and 59.5% (h = 4), against 77.4% and 61.3% with it. The frozen intervals include it.
- **B2 works on the coverage scale.** It fits and clips a line on coverage, as the plan's B2 paragraph specifies,
  although the plan's preamble says all models work on the logit scale.

**Safeguards for scoring** (`score.py`, before any target release).

- `backtest.py` no longer overwrites `forecasts_frozen.csv`: a re-run writes `forecasts_rerun.csv`.
- `score.py` reads the frozen hash from D1's sentence.
- It asserts 40 district-Total cells once both releases are in.
- It reports interval coverage for the seven largest districts separately. This is secondary, because the backtest
  shows the intervals too narrow for large cells.
- **Parse-only edits are allowed.** `parse.py` may be edited only to read a new file layout. Every edit is logged
  here, and the historical rows (to 2026Q2) must be unchanged. `score.py` checks them against the

  historical rows hash  b1a8bb046ae82646dc608bf2713ccfe10b2935fee92d5606dc8036d975cd8c50

  (the sha256 of the sorted historical rows as CSV). For reference, `data/coverage.parquet` currently has sha256
  21926040746157261327bbacb8ee1dd9172cb5872c67f2a00394c11c323d9c8c.

**Traceability.** `code/post_review.py` writes the tables behind every number the revised report quotes. They are
`results/tables/post_review*.{json,csv}`: short horizons by period, D1 like-for-like, coverage by cell size, the
noise floor, milestone changes around October 2020, and the cohort gap and denominators.

**District figure.** The districts are now listed alphabetically rather than ranked by forecast.
