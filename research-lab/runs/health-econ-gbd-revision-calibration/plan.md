# Do GBD uncertainty intervals anticipate the next revision? A country-by-cause calibration audit of GBD 2021 against GBD 2023

Preregistration · lead `health-econ-gbd-revision-calibration` · written 12 October 2026, before any GBD 2021 interval
has been compared with any GBD 2023 estimate.

## What has been seen before writing (disclosure)

**Novelty check (11-12 October 2026).**

- **Closest prior work.** Zavalis, Pezzullo and Ioannidis, *JAMA Health Forum*, 13 March 2026 (medRxiv
  10.1101/2025.11.14.25340145). It compares later GBD point estimates with earlier rounds' 95% UIs for GBD 2019, 2021
  and 2023, but only for **global** deaths and DALYs **attributable to risk factors**. It does not look at
  cause-specific deaths by country and does not relate miscoverage to data quality.
- **Searches** for country-level, cause-specific cross-round coverage, and for any link to vital-registration quality,
  found nothing else.

**Data access and probes (structure only).**

- **GBD 2019 is no longer downloadable.** The current GBD Results tool serves GBD 2023 only (version 8352, released 29
  October 2025). An archived tool serves GBD 2021 (version 8016). The GBD 2019 tool URL returns 404.
- **Download limit.** Each release allows a registered user about 100,000 rows. IHME does not raise limits for
  papers that present estimates for "all or most countries", so the data were cut down to fit the standard allowance
  instead of requested in bulk.
- **What was downloaded.** The lab owner ran the downloads through their own IHME account; links and checksums are in
  `data/raw/ihme/SOURCES.tsv`. All files cover 204 countries and territories, deaths (number), all ages, both sexes:

  | Release | Causes | Years |
  |---|---|---|
  | GBD 2021 | 139 level-3 causes | 2019, 2021 |
  | GBD 2023 | 140 level-3 causes | 2019 |
  | GBD 2023 | all 298 causes | 2021 |

  Plus population (all ages, both sexes) from each release for 2019 and 2021.
- **Checks run on each file separately:** row counts, one row per cell, no missing values, and the share of estimates
  inside their own interval.
  - Zero-width intervals: 1,795 rows in the GBD 2023 2021-year file and 3,586 in the GBD 2021 file. Nearly all are
    zero deaths; the rest are COVID-19 and conflict deaths entered as fixed counts.
  - Estimates outside their own interval: 6 rows in the GBD 2023 file (rounding of fixed counts) and 5 in the GBD
    2021 file (tiny eating-disorder counts and San Marino COVID-19 in 2021).
- **Cause lists.** 137 level-3 causes have the same cause ID in both releases. "Other digestive diseases" and "Other
  unintentional injuries" changed IDs, and GBD 2023 adds "Electrocution".
- **Panel built** (`code/build.py`): 55,896 cells, 204 countries × 137 causes × 2 years, joined with no missing values.
  No coverage or revision statistic has been computed.
- **Synthetic tests** (`tests/synthetic_test.py`) used only the GBD 2021 values for scale and interval widths; every
  GBD 2023 value was replaced by simulation.

**Data-quality sources** (Section 4): WHO GHE 2021 methods report, and the GBD 2021 and 2023 causes-of-death appendices
(PMC11126520, PMC12535838).

## 1. Question and hypotheses

**Question.** When GBD revises a country's cause-specific death estimate, does the new estimate usually fall within the
uncertainty the previous release stated? Does that depend on how good the country's death registration data are?

**Why a naive test is not enough.** Even if both releases' intervals were perfectly calibrated, a later *estimate*
(not the truth) falls inside an earlier 95% interval less than 95% of the time, because both estimates carry error.
With independent errors of equal size the expected share is 83%. In the synthetic test, which uses GBD 2021's actual
interval widths and a later release with intervals 20% narrower, a perfectly calibrated world gives 86-88%. The share
rises towards 100% if the two releases' errors are correlated, as they will be, since they share data and models. The
lead's hypotheses (H1, H2) are tested as written, but the headline rests on H3 and H4, which allow for both releases'
uncertainty.

**H1 (lead, part 1).** Fewer than 95% of GBD 2023 estimates fall inside the GBD 2021 95% UI (C1 < 0.95).

**H2 (lead, part 2).** C1 is below 0.80 in countries with poor or no vital registration and above 0.90 in countries
with high-quality vital registration.

**H3 (calibration).** Revisions are larger than the two releases' stated uncertainty allows: C2 < 0.95 (Section 5).

**H4 (calibration gradient).** C2 is at least 5 percentage points lower in countries with poor or no vital
registration than in countries with high-quality vital registration.

**Headline verdict.**

| Headline | Condition |
|---|---|
| **Supported** | H3 and H4 both Supported |
| **Refuted** | H4 Refuted (no gradient of 5 points or more), whatever H3 shows; H3 is stated alongside |
| **Inconclusive** | Anything else |

## 2. Departures from the lead, decided now (before outcomes)

| Lead | This plan | Why |
|---|---|---|
| GBD 2017 / 2019 / 2021 rounds | GBD 2021 intervals against GBD 2023 estimates | GBD 2017 and 2019 results are no longer served; GBD 2023 is the current release. |
| All years | 2019 and 2021 | Download limit. 2019 is the last pre-pandemic year; 2021 is the last year GBD 2021 estimated. |
| Level-2 and level-3 causes; number and rate; all ages and age-standardised | Level-3 causes; deaths (number), all ages, both sexes; all-age rates from each release's own population as a secondary | Download limit. |
| GBD star ratings | WHO GHE 2021 vital-registration quality class (primary); GBD's own garbage-code shares (secondary) | GBD publishes country star ratings only as a colour map (appendix Figure S5), not a table. WHO's class rests on the same idea: completeness × share of usable cause codes. |
| Raw WHO Mortality Database validation in high-quality countries | Dropped | Mapping ICD codes to 137 GBD causes for each country-year is a separate project. Stated as a limitation. |
| Hierarchical logistic regression as the main model | Bootstrap shares (primary); mixed logistic model (secondary) | Shares with cluster-bootstrap intervals map directly onto the hypotheses. |

## 3. Data

**Panel.** Built by `code/build.py`.

- **Cells:** country × cause × year, for 204 countries, the 137 level-3 causes with the same cause ID in both releases,
  and the years 2019 and 2021 (55,896 cells).
- **Per cell:** from each release r ∈ {21, 23}, the point estimate p_r (IHME's mean of draws) and the 95% UI
  [L_r, U_r] (the 2.5th and 97.5th percentiles of the draws). Each release's population is also kept.
- **Excluded causes:** the two causes whose IDs changed (and Electrocution) are left out of the panel. They are
  listed in `data/cause_map.csv`.

**Use of IHME data.** Raw files stay in `data/`, which git ignores. Only derived statistics are published, which are
shares and counts of cells; no GBD estimate is reproduced. IHME and the GBD Collaborative Network are cited.

## 4. Data-quality groups (fixed now)

**Primary: the WHO class.** WHO GHE 2021 methods report, Table 4.1, gives each country's vital-registration quality
class: high, medium, low or very low. Countries missing from the table have no vital-registration data in the WHO
Mortality Database and are classed `none`. Names are matched to GBD location names in `code/quality.py`, with the
crosswalk saved to `data/quality_crosswalk.csv`.

The WHO classes are defined in its Table 8.1 by usability, which is completeness × (1 − share of ill-defined codes),
since 2010:

| WHO class | Rule |
|---|---|
| high | ≥ 5 years of data and usability ≥ 80% |
| medium | ≥ 5 years and usability ≥ 60% |
| low | ≥ 1 year and usability ≥ 40% |
| very low | anything else, or data unavailable |

For the hypotheses the classes are grouped as follows:

| Group | WHO classes | Countries |
|---|---|---|
| **high** | high | 59 |
| **medium** | medium | 28 (reported, not used in H2 or H4) |
| **low** | low, very low, none | 22 + 10 + 85 = 117 |

**Secondary measures.**

- **GBD garbage-code share.** The mean share of registered deaths redistributed from garbage codes over 2010-2021, read
  from GBD 2021 appendix 1, pages 76-78, for 130 countries. Grouped into tertiles, plus "no vital registration in the
  GBD table".
- **The five WHO classes,** reported separately.

## 5. Outcomes

**C1, naive coverage.**

- **Covered:** L21 ≤ p23 ≤ U21.
- **Eligible:** U21 > L21, which excludes zero-width intervals (3,586 cells, nearly all zero deaths).

**C2, combined calibration.**

- **Scale:** s_r = (ln U_r − ln L_r) / (2 × 1.96), the log-scale SD implied by each release's interval.
- **Score:** z = (ln p23 − ln p21) / √(s21² + s23²).
- **Covered:** |z| ≤ 1.96.
- **Eligible:** p and L are positive in both releases and U > L in both.
- **Why it works:** if both releases' intervals are calibrated, approximately log-normal, and their errors are not
  negatively correlated, P(|z| ≤ 1.96) ≥ 0.95. A C2 clearly below 0.95 therefore means that at least one release's
  intervals are too narrow for the revisions that happen.

**E1, a benchmark for C1.** The C1 expected if both releases were calibrated with independent errors:
Φ((ln U21 − ln p21)/sd) − Φ((ln L21 − ln p21)/sd), with sd = √(s21² + s23²), averaged over cells eligible for both.

## 6. Primary analysis (code committed before any real coverage is computed)

**Estimates.** C1 and C2 are pooled over both years: the share of eligible cells covered, overall and by quality group.

**Intervals.** A two-way (country × cause) pigeonhole bootstrap:

- **Each replicate** resamples countries (within each group) and causes with replacement, and weights each cell by the
  product of the two multiplicities.
- **Draws:** B = 2,000, seed 20261012; the 2.5th-97.5th percentiles give the interval.
- **Group differences** use the same cause draw for both groups in each replicate.

**Decision rules.** CI means that 95% interval.

| | Supported | Refuted | Otherwise |
|---|---|---|---|
| **H1** | upper bound of C1 < 0.95 | lower bound ≥ 0.95 | Inconclusive |
| **H2** | C1(low) upper bound < 0.80 and C1(high) lower bound > 0.90 | C1(low) lower bound ≥ 0.80, or C1(high) upper bound ≤ 0.90, or the CI of C1(high) − C1(low) has upper bound ≤ 0 | Inconclusive |
| **H3** | upper bound of C2 < 0.95 | lower bound ≥ 0.95 | Inconclusive |
| **H4** | for D = C2(high) − C2(low): lower bound > 0 and D ≥ 0.05 | upper bound of D < 0.05 | Inconclusive |

## 7. Secondary analyses (labelled secondary)

**Variants of C1 and C2.**

- **Interval method:** a country-only bootstrap, as a sensitivity check.
- **By year:** 2019 and 2021 separately.
- **All-age death rates:** each release's estimate and interval divided by its own population. This removes revisions
  that come only from population estimates.
- **By level-1 cause group:** communicable, maternal, neonatal and nutritional; non-communicable; injuries.
- **Excluding COVID-19.**
- **Cells with at least 10 deaths** in GBD 2021.
- **By other quality measures:** the five WHO classes, and the GBD garbage-code tertiles.

**Diagnostics.**

- **E1 against C1,** overall and by group.
- **Direction of misses:** among C1 misses, the share with p23 above U21.
- **Interval widths:** the median ratio s23 / s21, overall and by group, as a check on the assumptions behind C2.

**Mixed model.** miss(C2) ~ quality group + year + level-1 group, with country and cause variance components, fitted by
variational Bayes (`BinomialBayesMixedGLM.fit_vb`). It reports the odds ratios for low and medium against high, and
both variance components. The optimiser's convergence flag is reported but not relied on; it has been unstable across
runs in this lab.

**Descriptive tables.** C1 and C2 by country and by cause (`by_country.csv`, `by_cause.csv`). These contain shares
only, no GBD estimates.

## 8. Validation before analysis

`tests/synthetic_test.py` keeps the real panel structure and the GBD 2021 values, and simulates every GBD 2023 value.
Error SDs carry country and cause heterogeneity (log-normal multipliers, SD 0.3).

| Scenario | C1 | C2 | H4 |
|---|---|---|---|
| **A, calibrated** | 0.881 (E1 0.862) | 0.946 [0.933, 0.956] | Refuted, D = −0.003 [−0.023, 0.015] |
| **B, low-group intervals 2× too narrow** | 0.741 | C2(low) 0.743, C2(high) 0.947 | Supported, D = 0.204 [0.174, 0.234] |

In scenario A, H1 is Supported even though both releases are calibrated. That is why H1 is not the headline.

## 9. Power and precision (before outcomes)

From scenario A's bootstrap intervals:

- **H3** has a half-width of 1.1 points, so it is decidable unless C2 lies within about 1 point of 0.95.
- **H1** has a half-width of 1.7 points.
- **The H4 difference** has a half-width of 1.9 points (SE ≈ 0.010). The minimum detectable difference (80% power,
  two-sided α = 0.05) is about 2.7 points, below the 5-point threshold.

If the real heterogeneity is larger than assumed, the intervals will be wider. The half-widths are reported with the
results.

## 10. Limitations stated in advance

- **A later estimate is not the truth.** C2 tests whether the releases' intervals are consistent with each other's
  revisions, not accuracy against reality.
- **Assumptions behind C2:** the log-normal approximation, and errors that are not negatively correlated.
- **"Rounds are not comparable."** IHME argues that methods and data change between releases. GBD's UIs claim to
  include model-choice uncertainty, so revisions from methods changes are part of what the intervals should cover.
  The by-cause table shows where revisions concentrate.
- **Scope:** two years, level-3 causes, both sexes and all ages only, and no age-standardised rates.
- **The quality measure is WHO's,** not GBD's own star rating.

---

*Erratum added after the independent review (12 October 2026; deviations.md D3). In section 4, "Countries missing from
the table have no vital-registration data in the WHO Mortality Database" is wrong. Table 4.1 covers only countries in
WHO's GHE scope. 17 of the 85 `none` countries have GBD vital-registration data for 2010-2021, and 9 have WHO Mortality
Database data since 2010. The preregistered grouping is kept, and alternatives are reported.*
