# Can earlier milestones forecast New Zealand's 24-month immunisation coverage?

*A preregistered rolling-origin backtest of a cohort-cascade forecast of Health NZ's 24-month coverage measure,
2012-2026, for 20 districts and Māori and Pacific children, with forecasts for the next releases frozen and hashed
before publication.*

Run directory: `research-lab/runs/auckland-nz-immunisation-cascade-forecast` · Preregistration: [`plan.md`](plan.md)
(commit 691a47e) · Departures from it: [`deviations.md`](deviations.md) (D1) · Frozen forecasts:
[`results/forecasts_frozen.csv`](results/forecasts_frozen.csv) (commit eb53bc6, sha256 e19d0d63…) · 7 October 2026,
draft for independent review

## In plain terms

Health NZ reports every quarter how many children are fully immunised at 6, 8, 12, 18 and 24 months. The 24-month
figure is the official health target, and it trails the others: the children who will be counted at 24 months next
year were already counted at 12 months this year. We asked whether linking the same children across milestones gives
a better year-ahead forecast than simple rules.

**A year ahead, it does not.** Across 50 quarters of history (2012-2026), forecasts for each district, and for Māori
and Pacific children, built from the same children's 12-month coverage were no better than assuming nothing changes.
Before 2020 they were clearly better, cutting the error by about a fifth. After the 2020 schedule change and the
2023-24 move to a new immunisation register, the link between 12-month and 24-month coverage shifted. Recent catch-up
between those ages has outpaced anything earlier cohorts showed.

**A quarter or two ahead, it works.** Using the same children's 18-month coverage, forecasts were 20-32% more
accurate than either simple rule.

We have frozen and published forecasts for the next two releases, July-September and October-December 2026. Nationally
they put 24-month coverage at about 85%. No district reaches 95%, and Māori coverage is forecast at about 73%. These
forecasts will be scored when Health NZ publishes the figures, expected around December 2026 and March 2027.

## What was done

**Data.** Every quarterly coverage file Health NZ and the Ministry of Health have published since April 2009 was
collected:

- 54 archived files, recovered from the Internet Archive;
- 12 current files, to June 2026.

They were parsed into one table of quarter × milestone × district × ethnic group, with eligible and fully immunised
counts (66 quarters; 2009Q3, 2022Q2 and 2023Q2 have no file). The parse reproduces the published headline for
January-March 2026: 6-month coverage of 66.6% nationally and 48.5% for Māori. District counts sum to the national
total within 1.5%, the remainder being children with no district. Suppressed cells were left missing and never
back-calculated.

**The cascade (M1).** The children who reach 24 months in a quarter reached 12 months four quarters earlier, and 18
months two quarters earlier.

- **Year-ahead forecasts (3-4 quarters):** start from the cohort's 12-month coverage on the logit scale and add the
  average 12-to-24-month change of the latest four cohorts in the same district and group.
- **Short-horizon forecasts (1-2 quarters):** the same, from 18-month coverage.

Intervals come from standardised past errors.

**Baselines.**

- **Persistence (B1):** the latest published 24-month value.
- **Linear trend (B2):** a line through the last eight published values.

**Test (H1, preregistered).** At a 4-quarter horizon, over the 20 districts × Total, Māori and Pacific, M1's mean
absolute error must be at least 30% below each baseline's, with a one-sided Diebold-Mariano p < 0.05 against each.
The backtest uses 50 origins from 2012Q2 to 2025Q2. It is Refuted if, against either baseline, the upper end of the
block-bootstrap 95% CI for the error reduction is below 30%.

## Results

**H1: Refuted.** 4-quarter horizon, 2,471 district-group-quarter cells:

| | Mean absolute error | Error reduction by the cascade (95% CI) | Diebold-Mariano p |
|---|---|---|---|
| Cohort cascade (M1) | 4.19 pp | | |
| Persistence (B1) | 4.00 pp | −4.7% (−20.4% to +13.4%) | 0.76 |
| Linear trend (B2) | 4.80 pp | +12.8% (+4.6% to +22.6%) | 0.0009 |

The cascade is significantly better than a linear trend, but by far less than 30%, and no better than persistence.
Its preregistered 80% intervals covered only 61% of outcomes.

![Backtest error by horizon and period](results/figures/backtest_errors.png)

**What changed.** The cascade worked until the 2020 schedule change and failed after it. Mean absolute error at a
4-quarter horizon:

| Target years | Cascade | Persistence | Linear trend | Reduction against persistence |
|---|---|---|---|---|
| 2013-2016 | 2.06 pp | 2.48 pp | 3.03 pp | 17% |
| 2017-2019 | 2.22 pp | 2.85 pp | 3.19 pp | 22% |
| 2020-2022 | 5.83 pp | 5.83 pp | 6.34 pp | 0% |
| 2023-2026 | 8.07 pp | 5.70 pp | 7.79 pp | −42% |

- **The schedule change.** From 1 October 2020 the first MMR dose moved to 12 months and the pneumococcal booster from
  15 to 12 months. So the "12-month" milestone began counting different vaccines, and its relationship to 24-month
  coverage changed.
- **The new register.** Then came the move from the National Immunisation Register to the Aotearoa Immunisation
  Register.
- **Catch-up outran the model.** In 2024-25, low 12-month coverage implied 24-month coverage near 70%. The published
  figure recovered to about 83% instead, as catch-up between 12 and 24 months surged.

Excluding the target quarters most affected (2020Q3-2022Q2 and 2023Q3-2024Q2) still leaves the cascade 5% worse than
persistence.

![Published coverage, backtest and frozen forecasts](results/figures/series.png)

**Secondary results.**

- **Horizon.** Short-horizon forecasts from 18-month coverage are much better than both baselines:

  | Horizon | Cascade | Persistence | Linear trend | Reductions (DM p < 0.001) |
  |---|---|---|---|---|
  | 1 quarter | 2.30 pp | 2.88 pp | 2.94 pp | 20%, 22% |
  | 2 quarters | 2.43 pp | 3.28 pp | 3.55 pp | 26%, 32% |

  Their 80% intervals covered 77% and 76% of outcomes. At 3 quarters, the cascade is again no better than
  persistence.
- **Groups (4 quarters):**

  | Group | Cascade | Persistence |
  |---|---|---|
  | Total | 3.18 pp | 2.97 pp |
  | Māori | 4.83 pp | 4.76 pp |
  | Pacific | 4.94 pp | 4.58 pp |

  The cascade does not help any group a year ahead.
- **Regression cascade (M2).** It adds 6-month coverage and fits intercepts by district and group. On the 2,351
  cells where M1, M2 and persistence all forecast, it reaches 3.78 pp, against 4.11 pp for M1 and 3.92 pp for
  persistence. That is a 3.5% improvement on persistence, far from the 30% bar.
- **National total.** The cascade (3.20 pp) is worse than persistence (2.38 pp). Its intervals are far too narrow for
  large cells (26% coverage), because they scale with sampling noise while national errors are systematic.

## Frozen forecasts (H2, pending)

The cascade was refitted on data to June 2026, and forecasts for July 2026 to June 2027 were frozen on 7 October 2026:
279 district-group-quarter cells, sha256 e19d0d63…, committed in eb53bc6 and pushed.

**National, 24-month coverage:**

| Quarter | Total (80% interval) | Māori | Pacific | Asian | European or Other |
|---|---|---|---|---|---|
| Jul-Sep 2026 | 85.4% (84.9-86.0) | 73.4% | 86.2% | 96.4% | 86.9% |
| Oct-Dec 2026 | 85.3% (84.8-86.0) | 73.4% | 86.8% | 96.0% | 86.4% |

The latest published value (April-June 2026) is 83.7%. No district is forecast to reach 95% in October-December 2026.
Two reach 90%: Capital and Coast, and Auckland. Northland's forecast is lowest, at 69.3%.

![Frozen forecasts by district](results/figures/districts_2026q4.png)

**Scoring (preregistered).** When Health NZ publishes the two files, `code/score.py` checks the frozen file's hash
and scores the 40 district-Total cells. H2 is Supported if both of these hold:

- the mean absolute error is at most 2.5 pp;
- 70-90% of cells fall inside the preregistered 80% intervals.

The backtest gives reason for caution on both counts.

- **Error.** For district Totals at 1-2 quarters, the error was 1.7-1.9 pp overall, but about 3 pp for 2023-2026
  targets.
- **Interval coverage.** Coverage was 73-76% overall, but about 60% for 2023-2026.
- **A second interval, added after the backtest (D1).** It is calibrated on the latest eight quarters and frozen
  alongside the preregistered one. It would have covered 72-76% in 2023-2026, but that figure is post hoc. H2 is
  scored on the preregistered interval.

The forecasts for 2027Q1 and 2027Q2 use 12-month inputs, which the backtest shows are currently unreliable. They are
reported for completeness only.

## Caveats

- **A forecasting method, not an explanation.** The failure after 2020 is consistent with the schedule change, the
  register migration and the surge in catch-up. The backtest cannot separate them.
- **Definitions move.** What "fully immunised for age" means at each milestone follows the schedule. The 12-month
  milestone in particular changed meaning in October 2020. Any cohort-linked model must be re-anchored after such a
  change, and the cascade's four-cohort window takes a year to do so.
- **Published files only.** Health NZ holds individual-level register data and could project coverage far more
  precisely. The value of this work is an independent, open check, not a replacement.
- **Small cells.** Pacific and Asian cells are often suppressed in smaller districts, so those groups are forecast
  only where Health NZ publishes them. District intervals for small populations are wide.
- **Three quarters have no file** (2009Q3, 2022Q2, 2023Q2). Forecasts needing those inputs were not made.

## Data and Māori data sovereignty

The study uses only aggregate counts that Health NZ publishes, under the Te Mana Raraunga principles:

- suppressed cells are never reverse-engineered;
- results for Māori and Pacific children describe how far immunisation services are reaching them, not
  characteristics of their families;
- the district forecasts are offered as a tool for Health NZ, Iwi-Māori Partnership Boards and Pacific providers to
  plan catch-up and measles readiness, not as a ranking of communities.

## Deviations (summary)

D1, logged before freezing: a second, recent-window 80% interval was added to the frozen forecasts as a labelled
secondary, after the backtest showed the preregistered intervals undercovering since 2023. The preregistered
interval remains the one H2 is scored on. Nothing else departs from the plan.
