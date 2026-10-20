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
   it agrees with the primary split (superseded: see D2 item 6, which withdraws this sensitivity as corroboration).
6. **Spread statistics added after the results.** The preregistered tests are one-sided, but the realised price
   fell *below* the simulated 10th percentile in 28% of weeks as well as above the 90th in 59%. Statistics
   describing the width of the simulated band against the spread of realised prices were added to report that
   two-sided failure honestly. They are descriptive and carry no verdict.

## D2 — 2026-10-21 12:23 NZDT — after independent review

An independent adversarial review (`review/review.md`) re-derived three runs to the cent, verified the week
alignment, and confirmed the cached data against fresh downloads. No pipeline code or result table changed; the
changes are to the reading of the results, plus analyses the review added. Each figure taken from the review was
checked against the reviewer's outputs or the Authority's files before use.

1. **The interpretation is withdrawn and replaced.** The draft said the narrow band showed that hydrological
   uncertainty accounts for about a twentieth of price variation. The runs are risk-neutral (no risk parameters are
   set in `run.csv`; JADE's default is risk neutrality), and they price the scored week at a flat long-run fuel
   assumption: in the run frozen in week 32 of 2024 the gas input is $28.31/GJ for that week and $13.20 from week
   33 onward (verified in that run's `thermal_fuel_costs.csv`). At that price the thermal stack spans about
   $128–184/MWh (recomputed here from the run's `thermal_stations.csv`, including O&M), and the cheapest next level
   is load shedding at $530. The narrow band is a property of that pricing, not of hydrology. The plan (§5 item 1)
   promised to put the point that JADE is not a price forecaster in the verdict itself; the draft did not, and the
   revision does, quoting the Authority's own description of the runs.
2. **"The range" was the wrong word.** The $25.94–$290.88 figure was the across-week 10th–90th percentile spread,
   which pools three years; realised weekly prices ran from $0.36 to $796.87. The band is now compared with three
   fairer yardsticks (forecast-error spread, week-to-week change, by year), and the share of weeks outside the entire
   envelope of inflow sequences (71.1%) is added.
3. **H2 could not have been Supported once H1 held.** With the comparison group exceeding 56% of the time, the
   largest attainable ratio is 1.79. The low-storage group is two consecutive spells, one coinciding with the 2024 gas
   shortage. The quintile table is added; "the effect is real" is withdrawn.
4. **The bootstrap understated dependence.** Lag-one autocorrelation is 0.66 (effective n about 19); longer blocks
   widen the H1 interval to about 41–79%. The verdict stands; the preregistered interval and minimum detectable
   effect are reported as understated.
5. **Bias added.** The plan (§4) promised to separate bias from spread; the draft did not. The realised price exceeds
   the simulated median in 61.2% of weeks (verified here), median ratio 1.32; a persistence baseline beats the runs'
   median.
6. **Deviations the draft did not declare:** Benmore and Otahuhu were to be reported alongside and were not scored
   (the review's alternative node mappings give 57–63%); the ratio's minimum detectable effect was not computed; and
   the all-years storage sensitivity in D1 item 5 sums JADE's run-start reservoir volumes in Mm³ across lakes — the
   operation D1 itself calls invalid — and flags the bottom fifth of three years' residuals, a different quantity
   from the preregistered percentile. Its 31 flags are a superset of the primary 20, which is why it "agreed". It is
   withdrawn as corroboration.
7. **Minor:** inflow sequences are 80 to 91, not a fixed 91 (text, captions and legend corrected); five end-of-year
   runs have a simulated 10th percentile of zero; JADE's week 52 is eight or nine days against seven realised (no
   verdict change); the HMD's two capacity files differ for Lake Taupō and the code takes the later; "no growth with
   horizon" covers stages 1–4 only.
