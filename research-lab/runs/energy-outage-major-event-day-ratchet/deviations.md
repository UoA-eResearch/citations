# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 21:01 NZDT — data format and download checks (before any daily series or index was computed)

- **Integrity.** All 14 downloaded figshare files (EAGLE-I article 24237376, version 4) match the repository's sizes
  and MD5 sums. The 2014 outage file and the two R scripts were not downloaded, because the plan's indices start from
  2015 data.
- **The 2023 file names its outage column `sum`, not `customers_out`.** Its rows have the same layout and
  magnitudes as the 2022 and 2024 files (county, 15-minute snapshot, customers out), so `code/build.py` reads that
  column as customers out. The 2024 file adds a `total_customers` column, which is not used: the plan's denominator is
  MCC 2022.
- **The first build run failed on 2023 because of this.** `build.py` now processes four years in parallel and caches
  each year's state-day totals, without changing what it computes.
