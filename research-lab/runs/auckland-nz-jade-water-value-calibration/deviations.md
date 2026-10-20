# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-20 22:47 NZDT — data coverage, usability rules and the storage measure

Recorded as each item was found. Items 1 to 5 were settled before any exceedance rate was computed; item 6 was
added after the results, and is descriptive only.

1. **152 weekly runs, not the 103 the lead estimated** — 52 in 2023, 52 in 2024 and 48 in 2025. All 152 are
   usable: none was excluded.
2. **The number of inflow sequences varies.** The lead and the plan both say 91. In the published runs the
   stage-2 count is 91 in 101 runs, 90 in 43, 89 in 7 and 80 in 1. The analysis therefore uses whatever sequences
   a run carries and requires at least 50 (`MIN_SIMS`); no run fell below that, so the rule excluded nothing. The
   validation reports the distribution rather than asserting 91.
3. **A complete settled week is required.** A run is scored only if its stage-2 week has seven days of settled
   prices and at least 330 half-hour periods (`MIN_PERIODS`); a full week is 336, or 334 and 338 in the weeks the
   clocks change. This was added after a smoke test on partial data produced a week with 33 periods. No run in
   the final data fell below it.
4. **December 2025 was assembled from daily files.** The Authority publishes that month's consolidated file only
   as `202512_FinalEnergyPrices_incomplete.csv`. The 31 daily files for December 2025 are all published, so the
   month was built from those instead and checked: 31 days, 48 periods each.
5. **National storage is measured in energy, and the preregistered split covers 104 of 152 runs.** Volumes cannot
   be added across lakes, so each lake's active storage is converted with its own GWh-per-Mm3 ratio from the
   hydrological dataset's derived capacity series before summing (10 lakes, daily from 1980-01-01). That dataset
   ends 2024-12-31, so the storage percentile exists for the 2023 and 2024 runs only. Both groups still clear the
   plan's ten-run minimum (20 low, 84 other), so H2 is scored on them. A sensitivity covering all 152 runs uses
   JADE's own run-start reservoir sum with two seasonal harmonics removed, flagging the bottom fifth of residuals;
   it agrees with the primary split.
6. **Spread statistics added after the results.** The preregistered tests are one-sided, but the realised price
   fell *below* the simulated 10th percentile in 28% of weeks as well as above the 90th in 59%. Statistics
   describing the width of the simulated band against the spread of realised prices were added to report that
   two-sided failure honestly. They are descriptive and carry no verdict.
