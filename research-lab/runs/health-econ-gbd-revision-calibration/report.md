# Do GBD's uncertainty intervals anticipate the next revision?

*A preregistered calibration audit: how often GBD 2023's cause-of-death estimates fall within the uncertainty that GBD
2021 stated, for 204 countries × 137 causes × 2019 and 2021, and whether that depends on the quality of a country's
death registration.*

Run directory: `research-lab/runs/health-econ-gbd-revision-calibration` · Preregistration: [`plan.md`](plan.md)
(commit 6b7a3e2) · Departures from it: [`deviations.md`](deviations.md) (D1-D2) · Independent review:
[`review/review.md`](review/review.md) · 12 October 2026

**Verdict: Inconclusive (preregistered headline rule).** GBD's intervals are too narrow for the revisions that follow
(H3 Supported). In about one cell in five the revision is larger than both releases' stated uncertainty together
allows; calibrated intervals would allow at most one in twenty. But the shortfall is about the same in countries with
excellent death registration as in countries with little or none: the gap is 1.2 points, with a 95% CI of −2.8 to
+5.2. The upper end misses the preregistered 5-point refutation threshold by 0.2, so H4 is Inconclusive.

## In plain terms

The Global Burden of Disease study (GBD) estimates how many people die of each cause in every country. Governments,
funders and the WHO use these numbers. Every estimate comes with a 95% uncertainty range, and every two years or so GBD
publishes a new round that revises old years.

We took GBD 2021's ranges for 2019 and 2021 and checked them against GBD 2023's revised estimates for the same years:
204 countries, 137 causes, about 52,000 comparisons. Two estimates of the same thing will never agree exactly, so the
test allows for both rounds' uncertainty. If the ranges were honest, at least 95% of revisions should fit inside that
combined allowance. **Only 81% did.**

Most revisions were of about the expected size. The problem is a minority of large jumps, some caused by method
changes and one by a bug that GBD 2023 fixed. The ranges did not allow for these.

We expected the problem to be worst in countries with poor death registration, where GBD relies most on modelling. It
was not. Countries with complete, well-coded registration had almost exactly the same shortfall (82% against 81%).

**For users:** a GBD uncertainty range understates how much the number may change in the next round, by a similar
amount everywhere. For 95% of revisions to fit, both rounds' ranges would have had to be about twice as wide (2.2×).

## The data

- **Two releases:** GBD 2021 (archived Results tool, version 8016) and GBD 2023 (current tool, version 8352, October
  2025).
- **What was downloaded:** deaths (number), all ages, both sexes, for the 204 countries and territories, for 2019 and
  2021, from each release. The 137 level-3 causes with the same cause ID in both releases are compared.
- **Why this scope:** GBD 2019 can no longer be downloaded, and each release allows about 100,000 rows per user. The
  downloads were run by the lab owner through their IHME account. File checksums are kept with the data.
- **Cells:**
  - 55,896 in total;
  - 52,310 eligible for the naive test (zero-width intervals removed, nearly all zero deaths);
  - 52,219 eligible for the calibration test (positive estimates and intervals in both releases).
- **Data-quality groups**, from the WHO Global Health Estimates 2021 methods report, Table 4.1:
  - **high:** 59 countries, at least 5 years of registration data and at least 80% "usable" (completeness × share
    of well-defined causes);
  - **medium:** 28 countries;
  - **low:** 117 countries, of which 22 are WHO "low", 10 "very low" and 85 have no data in the WHO Mortality Database.

  GBD's own star ratings are published only as a colour map, so the WHO classes stand in for them.

## Two tests

**C1, the naive test.** Is the GBD 2023 estimate inside the GBD 2021 95% interval? This is what the lead hypothesis
asked. It is not a calibration test on its own. Both releases are estimates with error, so even perfectly calibrated
intervals catch the next release's estimate less than 95% of the time. With the intervals actually published, and
independent errors, the expected share is **77.9%**.

**C2, the calibration test.** Take each release's interval as implying a log-scale standard error s. Then
z = (ln p₂₀₂₃ − ln p₂₀₂₁) / √(s₂₀₂₁² + s₂₀₂₃²). If both releases' intervals are calibrated and their errors are not
negatively correlated, |z| ≤ 1.96 holds at least 95% of the time. In practice the errors should be positively
correlated, since the releases share data and models, so 95% is a floor.

## Results

![Coverage by data-quality group](results/figures/coverage_by_group.png)

| Preregistered test | Estimate (95% CI) | Rule | Verdict |
|---|---|---|---|
| **H1** C1 < 95% | 65.9% (62.8-68.8) | upper bound < 95% | **Supported** |
| **H2** C1 < 80% in low-quality countries and > 90% in high-quality ones | low 64.9% (61.3-68.3); high 67.4% (62.8-71.8) | high's upper bound ≤ 90% refutes | **Refuted** |
| **H3** C2 < 95% | **81.4% (78.7-84.0)** | upper bound < 95% | **Supported** |
| **H4** C2 gap, high − low quality, at least 5 points | **+1.2 points (−2.8 to +5.2)**; high 82.1%, low 80.9% | Supported needs a lower bound > 0 and a gap ≥ 5; Refuted needs an upper bound < 5 | **Inconclusive** |

CIs are two-way (country × cause) cluster bootstraps, 2,000 draws.

**Headline.** The preregistered rule gives Supported only if H3 and H4 are both Supported, and Refuted if H4 is
Refuted, so the headline is **Inconclusive**.

- **What the data show:** clear miscalibration everywhere, and no detectable gradient by data quality. The gap is
  small, its CI is centred near zero, and a gradient of 5 points or more is excluded only at the margin.
- **Precision:** the H4 interval (±4.0 points) is about twice as wide as the synthetic power check predicted (±1.9).
  Real between-country and between-cause heterogeneity is larger than assumed: the mixed model puts the country SD at
  0.72 and the cause SD at 0.95 on the logit scale.

### Secondary analyses (preregistered)

| Analysis | C1 | C2 |
|---|---|---|
| Country-only bootstrap (all countries) | 65.9% (64.2-67.7) | 81.4% (80.0-82.8) |
| 2019 only: high / low quality | 71.4% / 66.2% | 85.5% / 81.5% |
| 2021 only: high / low quality | 63.3% / 63.6% | 78.7% / 80.2% |
| All-age death rates (removes population revisions): high / low | 66.6% / 64.7% | 81.5% / 80.8% |
| Communicable, maternal, neonatal and nutritional | 60.0% (54.5-65.8) | 76.0% (70.8-81.1) |
| Non-communicable diseases | 68.8% (65.2-72.4) | 83.3% (79.9-86.3) |
| Injuries | 61.8% (56.6-67.2) | 81.9% (77.5-85.9) |
| Excluding COVID-19: high / low | 67.5% / 65.0% | 82.2% / 81.0% |
| Cells with ≥ 10 deaths in GBD 2021: high / low | 71.9% / 68.0% | 85.6% / 83.8% |
| WHO class high / medium / low / very low / none | 67.4 / 67.4 / 63.8 / 67.9 / 64.8% | 82.1 / 82.3 / 77.7 / 83.6 / 81.3% |
| GBD garbage-code tertile low / mid / high / no registration data | 66.9 / 67.6 / 64.5 / 65.2% | 81.7 / 81.6 / 80.1 / 81.9% |

**Diagnostics.**

- **E1 against C1.** Over the cells eligible for both tests, C1 is 66.0% against the 77.9% expected if calibrated. By
  group: high 67.5% vs 77.0%, low 64.9% vs 78.5%.
- **Direction of misses.** Of the C1 misses, 64.5% are revisions upward, with the GBD 2023 estimate above GBD 2021's
  upper bound.
- **Interval widths.** GBD 2023's intervals are slightly wider than GBD 2021's: the median ratio of s is 1.08, and
  similar in each group. A narrowing of the later release's intervals does not explain the result.
- **Mixed model** (secondary): miss(C2) ~ group + year + cause group, with country and cause variance components.
  - The odds of a miss are 1.06 times higher in the low group than the high group (1.03-1.10).
  - The variational-Bayes interval is far narrower than the bootstrap's, as is usual for this approximation. An odds
    ratio of 1.06 corresponds to roughly a 1-point difference, in line with the bootstrap gap.

### Exploratory analyses (added after seeing outcomes; deviations.md D2)

![Calibration at several nominal levels](results/figures/calibration_levels.png)

- **X4, where the misses are.** The combined interval at nominal 50% holds 45.3% of revisions, close to nominal. At 80%
  it holds 67.9%, at 95% 81.4%, and at 99% only 87.7%. The SD of z is 3.1 (1 if calibrated), but the median |z| is
  0.77 (0.67 if calibrated). For 80%, 90% and 95% of revisions to fall within the matching band, the combined spread
  would need widening by 1.5×, 1.8× and 2.2×. The bulk of revisions are roughly the size the intervals imply. What breaks calibration
  is a heavy tail of large revisions that the intervals do not allow for.
- **X1, Other neoplasms.** It has the lowest per-cause C2 (8%). The GBD 2023 appendix (p. 361) explains the large
  increase: a fix to "an error during the CoDCorrect process that was excluding deaths in the underlying cause 'Other
  benign and in situ neoplasms' in previous cycles", and brain-tumour codes "inadvertently dropped in previous
  rounds". Excluding it, C2 is 82.0% (79.4-84.3).
- **X2, residual causes.** Excluding all 13 residual "Other …" causes, which are most exposed to cause-list
  reshuffling, C2 is 82.8% (80.6-84.7). The high − low gap is +1.7 points (−2.2 to +5.6).
- **X3, per cause.** The median cause has C2 84%, and only 7 of 137 causes reach 95%. The shortfall is broad, not
  driven by a few causes.
- **X5, by year.** The high − low C2 gap is +4.0 points in 2019 (−0.2 to +8.0) and −1.5 in 2021 (−6.0 to +2.7). A
  modest gradient may exist for a settled year and vanish in the pandemic year. In 2021, GBD 2023 added new
  registration data and a COVID-19 misclassification correction, which mostly affect well-registered countries. This
  was not preregistered and should be tested on a future release pair.
- **X6, lopsided intervals.** Using each side's own half-width instead of a symmetric log-normal spread gives
  essentially the same results: high 82.1%, low 80.7%.

![C2 by cause](results/figures/c2_by_cause.png)

![C2 by country and WHO class](results/figures/c2_by_country.png)

## What this means

**The intervals are too narrow, and not just in data-poor places.** In about 19% of country-cause-years, the GBD 2023
revision is outside what both releases' stated uncertainty allows. That is nearly four times the ≤ 5% calibrated
intervals would give.

**The shortfall is concentrated in large jumps.** The intervals describe ordinary year-to-year statistical uncertainty
reasonably well (X4). They do not cover revisions from changed methods, new data sources, recoding, or fixed errors.
GBD's own documentation shows that at least one large revision fixed an error in earlier rounds.

**IHME's likely reply.** IHME's protocol argues that releases are not directly comparable because data and methods
change. That is true, and it is the point. GBD describes its intervals as reflecting uncertainty from data, data
processing and model choice. A user reading a GBD 2021 interval in 2024 had no way to know the 2023 estimate would land
outside it about a third of the time (C1 = 66%).

**Data quality does not explain the shortfall.** We expected the opposite, so this may be the most useful finding.
Countries with complete, well-coded death registration see revisions outside the combined uncertainty about as often
as countries with no registration data. In data-rich countries, revisions come from recoding, redistribution of
garbage codes, new years of data and cause-model changes, and the intervals seem to understate those too.

## Limitations

- **A later estimate is not the truth.** C2 tests whether the releases' intervals are consistent with the revisions
  between them, not whether either release is accurate.
- **The C2 assumptions.** C2 assumes log-normal errors that are not negatively correlated. Positive correlation, the
  realistic case, would make the observed 81% look worse, not better. X6 shows the log-normal symmetry assumption is
  not driving the result.
- **Scope.** Two years, level-3 causes, all ages, both sexes, and one release pair. GBD 2019 is no longer downloadable,
  so a second pair could not be checked.
- **The quality measure** is WHO's classification, not GBD's own star rating. The secondary GBD garbage-code measure
  gives the same answer.
- **No check against raw registration counts.** The comparison with raw WHO Mortality Database counts, planned in the
  original lead, was dropped (plan section 2).
- **Same ID, different content.** The 137 causes share cause IDs across releases, but their content can still change,
  as Other neoplasms shows.

## Deviations

- **D1:** a one-line crash in the secondary-analysis code, fixed after the primary results were written. The primary
  results reproduce exactly.
- **D2:** the exploratory analyses X1-X6, added after the outcomes were seen.

See [`deviations.md`](deviations.md).

## Reproduce

```
code/run_all.sh            # build.py -> quality.py -> tests/synthetic_test.py -> analysis.py
venv/bin/python code/exploratory.py
venv/bin/python code/figures.py
```

The raw IHME files are not redistributed. `data/raw/ihme/SOURCES.tsv` lists each file's query, checksum and download
date. The tables in `results/tables/` hold only derived shares, never GBD estimates.

## Data and citations

- Global Burden of Disease Collaborative Network. *Global Burden of Disease Study 2021 (GBD 2021) Results.* Seattle,
  United States: Institute for Health Metrics and Evaluation (IHME), 2022. https://vizhub.healthdata.org/gbd-results/
- Global Burden of Disease Collaborative Network. *Global Burden of Disease Study 2023 (GBD 2023) Results.* Seattle,
  United States: IHME, 2024. https://vizhub.healthdata.org/gbd-results/
- GBD 2021 Causes of Death Collaborators. *Lancet* 2024;403:2100-32, appendix 1 (PMC11126520). GBD 2023 Causes of
  Death Collaborators. *Lancet* 2025;406:1811-72, appendix 1 (PMC12535838).
- World Health Organization. *WHO methods and data sources for country-level causes of death 2000-2021* (Global
  Health Estimates Technical Paper), Table 4.1 and Table 8.1.
- Zavalis EA, Pezzullo AM, Ioannidis JPA. Instability of Global Burden of Disease estimates of deaths and DALYs from
  major risk factors: a meta-epidemiological analysis. *JAMA Health Forum*, 2026.

Used under IHME's non-commercial terms. Results are derived statistics only.
