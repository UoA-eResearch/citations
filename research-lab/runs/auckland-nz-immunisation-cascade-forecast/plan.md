# Preregistration: forecasting New Zealand's 24-month immunisation coverage from earlier milestones of the same cohort

Lead: `auckland-nz-immunisation-cascade-forecast` (research-lab/leads.json). Written 7 October 2026 and committed
before any forecast or backtest has been computed.

## What has been seen before writing (disclosure)

- **Novelty check (7 October 2026).** No open forecasting model that links birth cohorts across milestones was found
  for New Zealand. Health NZ's May 2026 Immunisation Pānui gives one national prediction, "we are predicting we will
  get to 83.9%" by 30 June, with no method. The lead's critic found no cohort-linked NZ forecasting in Europe PMC or
  Crossref for 2023-2026.
- **Data.** All files were downloaded (`code/fetch.py`, `data/raw/manifest.csv` with sha256):
  - 24 current Health NZ files (quarterly and annual, July 2023 to June 2026);
  - 54 archived quarterly files (April 2009 to March 2023);
  - 55 archived 12-month rolling files, from the Internet Archive.
- **Parsing.** `code/parse.py` reads them into `data/coverage.parquet`: quarter × milestone (6, 8, 12, 18, 24, 54
  and 60 months) × district × group (Total, Māori, Pacific, Asian, European or Other), with eligible and fully
  immunised counts.
  - 66 quarters, from 2009Q2 to 2026Q2 (quarter ends 30 June 2009 to 30 June 2026). Three quarters have no file:
    2009Q3, 2022Q2 and 2023Q2.
- **Checks already run.** These looked only at national totals and at the group values of the latest four quarters:
  - national eligible counts by quarter and milestone;
  - national coverage by milestone in every fourth quarter;
  - national coverage by group for the last four quarters;
  - district counts summing to the national total (ratio 0.985-1.000).

  The January-March 2026 6-month coverage reproduces the published headline: 66.6% nationally and 48.5% for Māori.
  No district-level series has been examined, and no forecast or backtest computed.
- **Q4 2025/26 is already published** (April-June 2026, posted before this plan). The prospective test therefore
  targets the next releases.

## 1. Question and hypotheses

Children reaching 24 months in a quarter reached 12 months four quarters earlier, and 18 months two quarters
earlier. Health NZ publishes each milestone separately. Linking them gives a forecast of the official 24-month
measure up to a year ahead.

**H1 (retrospective, rolling-origin backtest).** At a 4-quarter horizon, the cohort cascade model (M1, section 3)
forecasts district 24-month coverage with a mean absolute error at least 30% lower than each baseline:

- **B1, persistence:** the latest published 24-month coverage.
- **B2, linear trend:** an ordinary least-squares line through the last 8 observed quarters of 24-month coverage,
  extrapolated 4 quarters and clipped to [0, 1].

The error is measured over the 20 districts × {Total, Māori, Pacific}. Each improvement must also be significant by a
one-sided Diebold-Mariano test, p < 0.05.

**H2 (prospective).** Forecasts frozen and hashed now, for the district Total 24-month coverage of the next two
releases:

- Q1 2026/27 (July-September 2026, expected about December 2026);
- Q2 2026/27 (October-December 2026, expected about March 2027).

Pooled over the 40 district-release cells, they achieve a MAE of at most 2.5 percentage points, and 70-90% of cells
fall inside their 80% prediction intervals.

## 2. Data and units

**Target.** 24-month full-immunisation coverage, C24 = fully immunised / eligible, as published in each quarterly
file.

**Cells.** The 20 Health NZ districts (the former DHBs) × groups.

- **Primary groups:** Total, Māori and Pacific.
- **Secondary groups:** Asian, and European or Other. Before mid-2020, European or Other = NZ European + Other.

**District harmonisation.** Otago and Southland, which appear in the earliest files, are summed into Southern, and
the sum is missing if either part is suppressed.

**Suppression.** Suppressed cells (n/s) are missing and are never back-calculated. A cell enters an evaluation only
if the target and every input the model needs are published.

**Quarters.** Periods are labelled by quarter end. "Origin q" means data published for quarters up to and including
q.

## 3. Models (fixed now)

All models work on the logit scale. Coverage values of exactly 0 or 1 are clipped to [0.5/n, 1 − 0.5/n].

**M1, cohort cascade (primary).** For horizon h, use the latest milestone at which the target cohort has already been
observed, at lag L:

| Horizon | Latest milestone used | Lag L |
|---|---|---|
| h = 3 or 4 | 12 months, from quarter q + h − 4 | 4 |
| h = 1 or 2 | 18 months, from quarter q + h − 2 | 2 |

The forecast is

  logit Ĉ24[q+h] = logit C_m[q+h−L] + δ̂,

where δ̂ is the mean of logit C24[t] − logit C_m[t−L] over the latest 4 cohorts whose 24-month value is published at
origin q, for the same district and group. At least 2 such cohorts are needed, or the cell is not forecast.

**M2, regression cascade (secondary).** logit C24[t] = a_dg + b · logit C12[t−4] + c · logit C6[t−6], fitted by
least squares with district × group intercepts. At each origin it uses all pairs whose target is published, from the
last 20 quarters. Forecast for h = 4.

**Baselines.**

- **B1:** Ĉ24[q+h] = C24[q], the latest published value.
- **B2:** a straight line through the latest 8 published C24 values against the quarter index, extrapolated to q + h
  and clipped to [0, 1]. At least 5 points are needed.

**80% prediction intervals for M1.**

1. Standardise each past M1 error at the same horizon as z = (logit C24 − logit Ĉ24) × sqrt(n p̂ (1 − p̂)). Here n
   is the eligible count of the input milestone cell and p̂ the forecast.
2. Take the 10th and 90th percentiles of the z values from all earlier origins, pooled across districts for that
   group, as an expanding window with at least 8 origins.
3. Map back to the logit scale and invert to a coverage interval.

## 4. Backtest (H1)

- **Origins.** Every quarter q from 2012Q2 to 2025Q2 whose target q + 4 is published.
- **Horizon:** h = 4 for H1. Horizons 1-3 are secondary, and validate the M1 forms used prospectively.
- **Loss:** absolute error in percentage points.
- **MAE:** the mean over all cells with a target and forecasts from M1, B1 and B2 (a common set).
- **Reduction:** 1 − MAE(M1)/MAE(B), for each baseline.
- **Diebold-Mariano test.** For each origin, take the mean over cells of the loss differential |e_B| − |e_M1|. Test
  that series' mean against 0, one-sided, with a Newey-West variance at lag h − 1 = 3.
- **Uncertainty in the reduction:** a moving-block bootstrap over origins (block length 4, 5,000 draws) gives a 95%
  CI.

**Decision rule for H1** (primary cells: 20 districts × {Total, Māori, Pacific}):

| Verdict | Condition |
|---|---|
| **Supported** | Reduction ≥ 30% against both B1 and B2, and DM p < 0.05 against both. |
| **Refuted** | Against at least one baseline, the upper end of the reduction's 95% CI is below 30%. |
| **Inconclusive** | Anything else. |

**Power.** With about 52 origins and lag-3 autocorrelation, the effective sample size is about 52/3 ≈ 17. The DM
test then has 80% power at one-sided 5% when the mean per-origin differential exceeds about 0.6 times its standard
deviation. The 30% threshold is a substantive bar, not a statistical one. Because the outcome is historical, a
simulation-based power figure would use the data, so none is computed.

**Secondary analyses (labelled secondary).**

- MAE by group, by district and by period.
- A sensitivity excluding the target quarters affected by schedule changes:
  - 2020Q3-2022Q2: pneumococcal 3+1 → 2+1 from 1 July 2020; MMR moved to 12 and 15 months and the pneumococcal booster
    to 12 months from 1 October 2020;
  - 2023Q3-2024Q2: the move from the National Immunisation Register to the Aotearoa Immunisation Register.
- M2 against M1.
- Horizons 1-3.
- The coverage of the 80% intervals in the backtest.
- The secondary groups.

## 5. Prospective forecasts (H2)

**Freezing.** After the backtest, M1 is fitted at origin 2026Q2 (data up to June 2026) and forecasts are made for:

- h = 1 (2026Q3, Q1 2026/27) and h = 2 (2026Q4, Q2 2026/27), using the 18-month input;
- h = 3 (2027Q1) and h = 4 (2027Q2, June 2027), using the 12-month input, as secondary;

for every district and group with the inputs published.

The forecasts, with 80% intervals, are written to `results/forecasts_frozen.csv`. The file's sha256 goes into
`deviations.md` and the file is committed before Health NZ publishes the Q1 2026/27 file. The code is then not
changed for scoring.

**Scoring when each release appears.**

- **Primary scoring (H2):** district Totals at h = 1 and 2, pooled over the two releases: MAE ≤ 2.5 pp, and 70-90% of
  cells inside the 80% intervals.
  - **Supported:** both met.
  - **Refuted:** MAE > 2.5 pp, or interval coverage outside 70-90%.
- **Secondary scoring:** Māori and Pacific cells; h = 3 and 4 when those releases appear.
- **Report state until then.** The report is first published with the backtest result and the frozen forecasts,
  with H2 marked pending.

## 6. Reporting and data ethics

- **Reporting.**
  - "In plain terms" first.
  - The pre-review draft is committed.
  - The reviewer's prompt and full review are saved in `review/`.
  - Departures from this plan are logged with timestamps.
- **Māori data sovereignty (Te Mana Raraunga principles).** The study uses only aggregate counts that Health NZ
  publishes.
  - Suppressed cells are never reverse-engineered.
  - Results for Māori and Pacific groups are framed around system performance and the services' reach, not around
    deficits of families.
  - Forecasts are offered as a tool for Health NZ, Iwi-Māori Partnership Boards and Pacific providers to target
    catch-up, not as a ranking of communities.
