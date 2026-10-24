# Plan (preregistration): how robust is procyclical US mortality? A specification curve over the state panel, 1976–2023

Lead: `health-econ-procyclical-mortality-multiverse`. Written before any mortality outcome is assembled into a panel
or any model is fitted. Raw files are being downloaded while this is written. Only their availability and column
names have been checked, not their values.

## 0. Question and hypotheses

Ruhm (2000) found that US state mortality falls when unemployment rises (a procyclical relationship). Ruhm (2015)
found that it weakened after 1990, and that drug-poisoning deaths moved the other way. This study asks how much the
sign and significance depend on defensible analytic choices.

- **H1.** Across the specification multiverse in §3 for total mortality, the coefficient on economic weakness is
  negative and significant (two-sided p < 0.05, primary inference) in fewer than half of specifications.
  - **Supported** if that share S1 is below 0.40.
  - **Refuted** if S1 is above 0.60.
  - **Inconclusive** otherwise.
- **H2.** In post-2010 windows, drug-poisoning mortality responds countercyclically: positive and significant in a
  majority of the specifications in §4.
  - **Supported** if that share S2 is above 0.60.
  - **Refuted** if S2 is below 0.40.
  - **Inconclusive** otherwise.

Every specification counts equally. Specifications whose outcome is undefined in a window are excluded and counted
(§3).

## 1. Data

Units are the 50 states and DC, by calendar year. Deaths are by state of residence unless noted.

- **Total deaths.** The sources are spliced, and the overlap years serve only for validation.
  - **1976–1998: NBER Multiple Cause of Death microdata.** Records are counted by state of residence; foreign
    residents and records without a US state are excluded. Age at death is recoded to the 11 NCHS age groups for
    age adjustment.
  - **1999–2017: CDC "NCHS – Leading Causes of Death: United States"** (`bi63-dtpu`), "All causes": deaths and the
    age-adjusted rate (2000 standard). NBER microdata for 1999–2004 is used only to validate this splice.
  - **2018–2023: CDC weekly counts by state** (`3yf8-kanr` for 2014–2019, `muzy-jte6` for 2020–2023), "All Cause".
    - These are by jurisdiction of **occurrence**.
    - Each MMWR week's deaths are apportioned to calendar years by the share of its seven days falling in each year.
    - Each state's 2018–2023 series is multiplied by exp(mean log(Leading Causes / weekly)) over 2014–2017, which
      calibrates occurrence to residence.
    - New York City is added to New York State.
    - The 2014–2017 fit is reported.
- **Age-adjusted total rate.** For 1976–1998 it is computed from the NBER deaths by age group and SEER population,
  using the 2000 US standard population (11 groups). For 1999–2017 it is the CDC rate, and the overlap 1999–2004
  validates the computed rate. It is not available for 2018–2023.
- **Drug-poisoning deaths.**
  - **1999–2018:** CDC "NCHS – Drug Poisoning Mortality by State" (`44rk-q6r2`; both sexes, all ages, all races).
  - **2019–2023:** CDC "VSRR Provisional Drug Overdose Death Counts" (`xkb8-kh2a`), "Number of Drug Overdose Deaths",
    12 months ending December. The 2015–2018 overlap is reported.
- **Population:** SEER US population estimates 1969–2024 (adjusted, 19 age groups, by state, race and sex).
- **Economic weakness:**
  - **(a) Unemployment rate:** BLS LAUS annual average, `LAUST{fips}0000000000003A` via FRED, in percentage points.
  - **(b) Negative employment-to-population ratio:** −100 × LAUS annual employment (`…005A`) / SEER population aged
    15+. It is in percentage points, signed so that higher means weaker in both cases.
- **Demographic controls (SEER):** the population shares under 5, 65 and over, 85 and over, and Black.

## 2. Model

The outcome y_st is a function of mortality in state s and year t, and U_st is economic weakness. Every
specification is a linear model:

- **TWFE:** y_st = β U_st [+ β₁ U_s,t−1] + X_st γ + α_s + λ_t [+ state trends] + e_st.
- **First differences (FD):** Δy_st = β ΔU_st [+ β₁ ΔU_s,t−1] + ΔX_st γ + λ_t + e_st. The trend options become a
  state intercept (linear trends) or a state intercept plus a state slope (quadratic trends).
- **Division × year:** TWFE with Census-division × year effects instead of year effects.

With a lag, the reported coefficient is the cumulative effect β + β₁, estimated directly by reparametrising. The
first year of each window is dropped in lag and FD specifications. Weighted specifications use SEER state population
of the year (for FD, the mean of the two years).

**Inference:**
- **Primary:** a wild cluster restricted bootstrap by state, Rademacher weights, 9,999 draws, the null β = 0 imposed,
  with a symmetric two-sided p from the CR1 t-statistic.
- **Secondary:** CR1 cluster-robust standard errors by state with t(G−1) critical values, reported alongside.

## 3. The H1 multiverse (total mortality)

| dimension | options |
|---|---|
| outcome | log crude rate; log age-adjusted rate; crude rate (deaths per 100,000) |
| economic weakness | unemployment rate; negative employment-to-population ratio |
| weighting | population; none |
| trends | none; state linear; state quadratic |
| lags | contemporaneous; cumulative with one lag |
| window | 1976–2017; 1976–1991; 1992–2005; 2006–2017; 1976–2019; 1976–2023 |
| estimator | TWFE; FD; division × year |
| controls | none; demographic shares |

- **Size:** 3 × 2 × 2 × 3 × 2 × 6 × 3 × 2 = 5,184 combinations.
- **Exclusions:** the log age-adjusted outcome is undefined in windows that include 2018 or later, which removes
  2 × 2 × 3 × 2 × 2 × 3 × 2 = 288 combinations, leaving 4,896.
- **The canonical Ruhm specification:** log crude rate, unemployment rate, population weights, no trends,
  contemporaneous, TWFE, demographic controls. It is reported for every window.

## 4. The H2 multiverse (drug poisoning, post-2010)

| dimension | options |
|---|---|
| outcome | log crude rate; crude rate |
| economic weakness | unemployment rate; negative employment-to-population ratio |
| weighting | population; none |
| trends | none; state linear; state quadratic |
| lags | contemporaneous; cumulative with one lag |
| window | 2011–2019; 2011–2023 |
| estimator | TWFE; FD; division × year |
| controls | none; demographic shares |

That gives 576 specifications. A state-year with zero drug-poisoning deaths would make the log undefined. If any
occurs, that outcome uses log(deaths + 1) − log(population), and the count is reported.

## 5. Secondary analyses (labelled as such)

1. **Specification curves** for H1 and H2: estimates sorted, with 95% intervals and a panel of the choices.
2. **What drives the sign.** The share of negative-significant results within each option of each dimension, and the
   share of variance in β̂ (standardised by the outcome's SD in the window) explained by each dimension: the sums of
   squares of a main-effects ANOVA, in standard deviations.
3. **A joint test** (Simonsohn, Simmons and Nelson 2020).
   - 500 null datasets per specification, with one Rademacher draw per state shared across specifications, each
     built from that specification's restricted residuals.
   - The share of specifications negative-significant under CR1 in each null dataset forms the null distribution of
     S1 (CR1). The observed S1 (CR1) is compared with it.
4. **A pre-2011 contrast for drug poisoning:** the H2 multiverse with window 1999–2010.
5. **Splice validation:**
   - NBER against CDC total deaths and computed against CDC age-adjusted rates, 1999–2004;
   - weekly against Leading Causes, 2014–2017;
   - VSRR against NCHS drug poisoning, 2015–2018.
6. **The canonical specification by window**, with both inference methods.

## 6. What would change the plan

- If a source cannot be obtained, the affected windows or outcomes are dropped, logged as a deviation before the
  multiverse is run, and the specification counts recomputed. The decision thresholds are unchanged.
- **Splice bias.** If the 1999–2004 NBER–CDC median absolute log difference in total deaths exceeds 2%, the cause is
  investigated and logged before any estimation. The splice rule above stays unless the cause is a coding error.
- Code is tested on synthetic data with a known β, and the WCR p-values are checked against CR1 on simulated
  clusters, before the real panel is used.

## 7. Limits stated in advance

- **No new identification.** The design is the established state-year panel. It does not add exogenous variation
  in unemployment. Heterogeneity-robust continuous-treatment estimators are not in the multiverse.
- **Uneven sources.** Occurrence-to-residence calibration for 2018–2023 and the provisional status of recent counts
  are limits.
- **2020–2023** are dominated by COVID-19. They enter only through the 1976–2023 and 2011–2023 windows.
- **Equal weights.** The share of specifications depends on the multiverse chosen. Each specification counts
  equally, and the decomposition (§5.2) shows how the share moves with each choice.
