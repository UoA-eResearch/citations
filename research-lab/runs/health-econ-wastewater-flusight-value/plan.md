# Preregistration: does influenza wastewater data improve state-level flu hospitalisation forecasts?

Lead: `health-econ-wastewater-flusight-value` (research-lab/leads.json). Written 2026-10-01 and committed to git before
any hospital admission data were downloaded or examined.

Probes made before writing:

- **A literature search** (§1).
- **Wastewater data, covariate only:**
  - the data.cdc.gov catalogue and schema of the NWSS influenza A datasets;
  - a download of the sample-level influenza A data (ymmh-divb) and its field summaries: units, non-detects, sources,
    date ranges, and the `date_updated` field, which is a single refresh date and so carries no reporting delay;
  - state population coverage per season (`code/ww_coverage.py`, `results/tables/ww_coverage.csv`).

  No wastewater value was compared with any hospital or clinical series.
- **FluSight hub metadata:**
  - the repository layout, `hub-config/tasks.json` and the list of FluSight-ensemble reference dates;
  - `target-data/README.md` (the `as_of` vintages);
  - model metadata, where two models (MIGHTE-Base, MIGHTE-Nsemble) list national WastewaterSCAN influenza A among their
    inputs.

**Prior knowledge (disclosed).** From general knowledge, 2024–25 was a severe season and 2025–26 had an early H3N2
(subclade K) wave. No hospital admission values have been examined in this session.

Every later departure goes to `deviations.md` with a timestamp taken from `date`.

## 1. Background and gap

- **Wastewater tracks flu.** Influenza A RNA in wastewater tracks clinical flu activity (Boehm et al. 2023, JAMA;
  WastewaterSCAN). A 2025 IDWeek abstract (Open Forum Infect Dis, abstract 617) reports a two-week lead and r = 0.93
  with hospitalisations across US states. A California comparison of surveillance streams (medRxiv 2025, AJE Advances
  2026) finds wastewater strongly correlated with confirmed flu admissions.
- **Wastewater helps some COVID-19 forecasts:**
  - a retrospective multi-model study, arXiv:2512.01074;
  - EpiFlow, arXiv:2608.06671, Virginia COVID-19 only;
  - CDC CFA's wastewater-informed COVID models.
- **The gap.** No state-level, out-of-sample, probabilistic evaluation of the *marginal* value of influenza wastewater
  was found. The standard for such an evaluation is:
  - a paired model with and without wastewater, everything else identical;
  - forecasts built from data as available in real time;
  - FluSight-format quantile forecasts scored by weighted interval score (WIS) against the FluSight baseline and ensemble.

  On the FluSight hub, CFA's influenza models use hospital and ED data but not wastewater. The two MIGHTE models use a
  national wastewater series, without a published with/without comparison.
- **Why it matters.** CDC is deciding how to use wastewater in respiratory forecasting. Correlation and lead time do
  not imply forecast value once recent hospital data are already in the model.

## 2. Hypotheses

- **H1 (primary).** Adding state wastewater features to a standard quantile-regression forecaster reduces mean WIS by
  at least 5% for 1–4-week-ahead forecasts (hub horizons 0–3) of weekly confirmed influenza admissions. The panel is the
  state-seasons with at least 50% wastewater population coverage in 2023–24, 2024–25 and 2025–26. The estimate is
  relative WIS = mean WIS(with wastewater) / mean WIS(without), over the same forecast tasks.
- **H2.** The same in the wider panel: state-seasons with at least 20% coverage.
- **H3.** The gain grows with coverage. Across all state-seasons with wastewater features, the slope of the log
  state-season WIS ratio on coverage is negative.
- **H4.** Wastewater adds value on top of the FluSight ensemble. An equal-weight quantile average of the FluSight
  ensemble and the with-wastewater model has lower WIS than the same average with the no-wastewater model.
- **Descriptive (no hypothesis):**
  - relative WIS by horizon, by season, and by epidemic phase (rising or falling in the final data);
  - 50% and 95% interval coverage;
  - both models against the FluSight baseline and the FluSight ensemble.

**Decision rule** (H1, H2, H4; 95% intervals from §5).

| Verdict | Condition |
|---|---|
| Supported | point estimate ≤ 0.95 and upper bound < 1 |
| Contradicted | lower bound > 0.95: any gain is smaller than 5% |
| Inconclusive | otherwise |

An upper bound below 1 is reported as "an improvement" whatever the point estimate. For H3: supported if the slope's
upper bound < 0, contradicted if its lower bound > 0.

## 3. Data

- **Hospital admissions.** Weekly confirmed influenza admissions per state (NHSN), from the FluSight hub
  `target-data/time-series.csv` with its `as_of` vintages. Locations: the 50 states, DC and Puerto Rico; the national
  total is excluded.
  - **Real-time data** for a forecast with reference date R (a Saturday; due date D = R − 3 days, a Wednesday): the
    vintage with the latest `as_of` ≤ R when R is before 2025-07-05 (when `as_of` denotes the round), and the latest
    `as_of` ≤ D after (when `as_of` is the release date).
  - **Scoring truth** is the latest vintage.
  - If a round has no vintage, the latest earlier vintage is used, and the number of such rounds is reported.
- **Wastewater.** NWSS influenza A sample data (data.cdc.gov ymmh-divb, downloaded 1 October 2026). It covers the
  State_Territory, CDC_Verily and WastewaterSCAN sources: 330,015 samples from 1,493 sites.
  - **Real-time availability.** A sample counts as available for due date D if collected on or before D − 10 days.
    Public vintages are not available, and `date_updated` carries no delay. The 10 days assume data submitted within
    about a week of collection and posted in the weekly update before the due date.
  - **Sensitivity:** 5 and 17 days.
- **Population.** `auxiliary-data/locations.csv` from the hub.
- **Forecast dates.** The 85 FluSight-ensemble reference dates, from 2023-10-14 to 2026-05-30.
- **Comparators.** FluSight-baseline and FluSight-ensemble quantile forecasts from the hub's `model-output/`.

## 4. Models

Both variants are identical except for the wastewater features.

**Transforms and targets.**

- y_t = log((admissions_t + 1) / population × 100,000) for epiweek t.
- T is the last week with hospital data in the real-time vintage.
- The target for horizon h (0–3) is z_h = y_{T+h+1} − y_T.

**Base features:**

- y_T;
- the one-week change y_T − y_{T−1};
- the previous change y_{T−1} − y_{T−2};
- sin and cos of 2π × (MMWR week of the target week) / 52.

**Wastewater features:**

- **Site signal.** Each site × source series gets a weekly (7-day window) mean of log10 concentration
  (`pcr_target_avg_conc_lin`, as reported, including non-detects). Its anomaly is taken relative to the series' median
  over all windows available at the forecast date, requiring at least 10 windows.
- **State signal.** W_k = the population-weighted mean anomaly over series with a sample in window k. Window 0 ends at
  D − 10 days. A site sampled by several sources has its weight split between them.
- **Features:**
  - W_0;
  - W_0 − W_1;
  - W_1 − W_2.

**Fitting.** Linear quantile regression (statsmodels QuantReg) at the 23 FluSight quantile levels, one fit per horizon
and level, pooled across states.

- Refit at every forecast date on training rows built from the real-time vintage: all state-weeks since 2022-09-01
  whose target is observed and whose wastewater features exist, with features computed with the same lag.
- Both variants use the identical rows.
- Quantiles are sorted, back-transformed to counts and floored at 0.
- Where a state has no wastewater features at a forecast date, the with-wastewater forecast equals the base forecast.
  Such tasks are outside the primary panel by construction.

## 5. Evaluation

- **Score.** WIS on counts, using FluSight's definition with 23 quantiles, over horizons 0–3.
- **Relative WIS.** Ratio of mean WIS over the common tasks.
- **Secondary measure.** The geometric mean over states of state-level ratios, which weights states equally.
- **Intervals.** A two-way bootstrap: states, and independently 4-week blocks of reference dates within each season,
  both resampled; 5,000 draws; percentile 95% intervals. Epidemic waves are shared across states, and the previous deep
  dive showed that resampling places alone is too narrow.
- **Panel coverage** is computed from wastewater and census data only (`results/tables/ww_coverage.csv`):
  - at least 50%: 9, 13 and 14 states in the three seasons;
  - at least 20%: 23, 35 and 38.

## 6. Validation before any hypothesis is read

- **V1, positive control.** The wastewater features are replaced by an oracle leading indicator: next week's final
  y_{T+1} plus N(0, 0.3²) noise, fed through the same three features. The pipeline must return relative WIS < 0.9 with
  an upper bound < 1 in the primary panel. Otherwise the pipeline cannot detect a real leading signal, and is fixed
  before any hypothesis is read.
- **V2, negative control.** Each state gets another state's wastewater features (a fixed random derangement per
  season). The interval should include 1, or the ratio should exceed 1. A clear gain would mean leakage.
- **V3, leakage assertions.** Every feature uses only samples collected on or before D − 10 and hospital vintages
  ≤ the round's limit.

## 7. Sensitivity analyses

- **S1.** Wastewater availability lags of 5 and 17 days.
- **S2.** Flow- and population-normalised concentration (`pcr_target_flowpop_lin`) where a series reports it.
- **S3.** The level feature W_0 only.
- **S4.** The base model trained on all state-weeks, not only those with wastewater: "business as usual".
- **S5.** Excluding reference dates from 20 December to 10 January (holiday reporting).
- **S6.** A state signal from CDC's site-level wastewater viral activity levels (atcp-73re). Its baselines may use later
  data, so this is secondary only.
- **Per-season results.**

## 8. Independent review and reporting

- An independent reviewer agent checks code, deviations and draft before any verdict is stated.
- The report opens with an "In plain terms" section and reports every preregistered number, whatever it shows.
- All data are open. Raw data are not committed; code, tables and figures are.
