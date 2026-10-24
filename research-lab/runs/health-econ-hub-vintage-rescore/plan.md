# Plan (preregistration): do flu forecast leaderboards change when forecasts are scored against the data available at the time?

Lead: `health-econ-hub-vintage-rescore`. Written before any forecast is scored or any truth vintage is compared.

**Seen before this plan:**
- the repository sizes;
- the FluSight hub's `target-data/` file list;
- that `target-hospital-admissions.csv` has weekly commits.

## 0. Question and hypotheses

Forecast hubs score forecasts against "finalised" surveillance data. Hospital admission counts are revised after
first report, while forecasters only ever saw first reports. If revisions are large and uneven, leaderboards may
partly reward luck with revisions.

- **H1.** Re-scoring against first-reported values instead of finalised values reverses at least 20% of within-season
  pairwise model orderings by mean WIS.
  - **Supported** if the 95% lower bound of the reversal share is at least 0.20.
  - **Refuted** if the upper bound is below 0.20.
  - **Inconclusive** otherwise.
- **H2.** The best non-ensemble model changes identity in at least one season × horizon.
  - **Supported** if the point estimates differ in at least one season × horizon *and* identities differ in at least
    half of the bootstrap resamples for that season × horizon.
  - **Refuted** if no season × horizon differs in the point estimate.
  - **Inconclusive** otherwise.

**Intervals:** a bootstrap over reference dates within each season (B = 500), recomputing both scorings on each
resample.

## 1. Data

- **Forecasts.** FluSight weekly incident influenza hospital admissions for US states, DC, Puerto Rico and the US:
  - 2022–23 from `cdcepi/Flusight-forecast-data` (horizons 1–4 weeks);
  - 2023–24 and 2024–25 from `cdcepi/FluSight-forecast-hub` (horizons 0–3).
  - Quantile forecasts only (23 levels). Each season runs over its official reference dates as listed in the hubs.
- **Truth vintages.** The git history of each hub's truth file: `data-truth/truth-Incident Hospitalizations.csv` and
  `target-data/target-hospital-admissions.csv`.
  - **First report:** for each location × target week, the value in the earliest commit whose file contains that
    week.
  - **Finalised:** the value in the latest commit, as cloned on 2026-10-25. For 2022–23, that is the last version in
    the old repository.
- **Secondary (only if obtainable within the run).** The COVID-19 Forecast Hub (`reichlab/covid19-forecast-hub`,
  2020–2023, archived, 13.8 GB) with the same design for incident deaths, using its JHU-CSSE truth history. If it
  cannot be obtained, this is logged as not run.

## 2. Scoring and rankings

- **Score.** WIS from the 23 quantiles (Bracher et al. 2021), per model × reference date × location × horizon, under
  each truth.
- **Pairwise orderings.**
  - Within each season × horizon, every pair of models with at least 100 common forecasts (location × reference
    date) is compared by mean WIS over their common set, under each truth.
  - A **reversal** is a change of which model has the lower mean WIS.
  - The reversal share pools all pairs over all season × horizons.
- **Best non-ensemble model.**
  - Relative WIS is the geometric mean, over all other models, of pairwise mean-WIS ratios on common sets (Cramer
    et al. 2022).
  - It is taken among models covering at least 80% of the season × horizon's location × reference-date cells,
    excluding ensembles and baselines (model names containing "ensemble" or "baseline", plus the hub's designated
    ensemble).
  - The best model is the one with the lowest relative WIS.

## 3. Secondary (labelled as such)

1. **Revision size:** first report minus finalised, by season, horizon-independent, as % of finalised; the share of
   location-weeks revised by more than 10%.
2. **Rank agreement:** the Spearman correlation of relative WIS between the two truths, per season × horizon.
3. **Which models gain:** each model's change in relative WIS, against the size of revisions in the locations it
   forecasts.
4. **COVID-19 Forecast Hub:** the same design for deaths, if obtained (§1).

## 4. Limits stated in advance

- **"First report" approximates what forecasters saw.** Forecasters may also have used other sources.
- **Finalised values are still subject to later revision.** For 2022–23, the old repository's last version is taken
  as final.
- **Pair thresholds change which models are compared;** they are fixed here.
- **Reporting changes.** NHSN reporting changed during 2024 (a voluntary period from May to October 2024). Seasons
  are analysed separately as well as pooled.
