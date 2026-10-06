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
