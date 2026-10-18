# Preregistration: does the major-event-day rule hide the outage trend it is meant to normalise?

Lead: `energy-outage-major-event-day-ratchet` (Energy). Written 2026-10-18, before any outage series was built.

**Examined beforehand (no index computed):**
- the EAGLE-I figshare record (CC BY 4.0, outages 2014–2025, 15-minute county snapshots, 11.6 GB);
- its MCC customer counts, its coverage history and its DQI file;
- the first rows of two outage files, for format. The timestamps are UTC, and 2014 starts in November.
- 32 of 56 states and territories have at least 80% customer coverage in every coverage-history year (2018–2022).

**Novelty** (search 2026-10-18). Known critiques of the IEEE 1366 2.5β method:
- zero-SAIDI days (IEEE 2013);
- log-normal tail misfit (IEEE 2011);
- a CPUC technical session (2025) warning that rising thresholds can hide localised problems.

No study was found that quantifies, across a national panel, how much of the outage trend the rolling threshold
removes, or what detection power alternative normalisation policies have.

## 1. Definitions

**System.** A US state (or DC) with stable EAGLE-I coverage (§2). Utilities' service territories cannot be mapped
from the open data. States are the systems, and this is stated as a limitation.

**Daily SAIDI.** For each state s and local day d, in the state's predominant time zone:

  SAIDI_{s,d} = Σ_{counties, 15-minute snapshots} customers_out × 15 min / customers_s.

customers_s is the MCC 2022 customer count, summed over the state's counties. Days with no recorded outage are 0.

**IEEE 1366 2.5β.** For year Y:
- **Window:** the non-zero daily SAIDI of years Y−5 to Y−1, including their major event days (MEDs), as the
  standard specifies.
- **α and β:** the mean and standard deviation of ln(SAIDI) over that window.
- **Threshold:** T_Y = exp(α + 2.5β).
- **MEDs:** the days of Y with SAIDI > T_Y.
- **Annual indices:**
  - all-events SAIDI_Y = Σ_d SAIDI_{s,d};
  - MED-excluded SAIDI_Y = Σ_{d not MED} SAIDI_{s,d}.
- **Years.** Data from 2015 (2014 is partial) give thresholds and indices for 2020–2025.

**Policies compared:**
- (a) rolling 2.5β (the standard);
- (b) frozen 2.5β, with the threshold computed once from 2015–2019;
- (c) a 10-year rolling window, where available (2025 only, with 2015–2024), reported descriptively;
- (d) a fixed quantile: days above the state's 2015–2019 99th percentile of daily SAIDI are excluded;
- (e) no normalisation (all events).

## 2. Data and inclusion

**Data:**
- EAGLE-I outages 2015–2025, county by 15 minutes;
- MCC 2022 customers;
- the coverage history (2018–2022);
- EIA-861 reliability (PUDL, 2015–2024: SAIDI with and without MEDs, by utility and state), for validation.

**Inclusion.** A state is included if both hold:
- its maximum covered share is at least 0.80 in every coverage-history year;
- in every year 2015–2025, its number of distinct counties reporting any outage is within ±15% of its 2018–2022
  median. This guards against coverage changes outside the coverage-history years.

Territories are excluded.

## 3. Hypotheses

The trend measure is the pooled log-linear annual trend over 2020–2025:
- a state panel regression of ln(annual index + 1 minute) on year, with state fixed effects;
- intervals from a state-cluster bootstrap (2,000 resamples, seed 20261018);
- the trend expressed in % per year.

- **H1 (masking).** The MED-excluded index under the rolling 2.5β rule grows at less than half the rate of the
  all-events index.
  - The measure is the ratio of the two trends.
  - If the all-events trend's interval includes 0, H1 is Inconclusive (no trend to mask).
  - Otherwise: Supported if the ratio's upper bound is < 0.5; Refuted if its lower bound is ≥ 0.5.
- **H2 (ratchet).** The rolling threshold removes more of the trend than a frozen threshold.
  - The measure is the MED-excluded trend under (a) minus that under (b).
  - Supported if the difference's upper bound is < 0; Refuted if its lower bound is > 0; Inconclusive otherwise.
- **H3 (detection power).** In simulated systems where normal-operations severity grows by 3% a year and storms are
  unchanged, the rolling 2.5β index detects the trend at most half as often as an oracle index that knows which days
  are storms.
  - **Detection:** a one-sided p < 0.05 for a positive log-linear trend over the final 6 years.
  - Supported if the power ratio's upper bound is < 0.5; Refuted if its lower bound is ≥ 0.5.

## 4. The Monte Carlo (`code/simulate.py`)

**Calibration.** The daily severity process is fitted to the included states' 2015–2019 data as a mixture:
- the probability of a zero day;
- a log-normal body;
- a generalised Pareto tail above the state's 95th percentile.

Each simulated system takes the parameters of a randomly drawn included state.

**Scenarios** (2,000 systems each, 11 years each):
- **A.** The body grows 3% a year; the tail is unchanged.
- **B.** The tail's frequency and scale grow 5% a year; the body is unchanged.
- **C.** No trend.

**Outputs, for each policy (a)–(e) and the oracle:**
- detection rates;
- the false-positive rate (scenario C, and scenario B for normal-operations indices);
- years to first detection.

Power intervals are binomial (Wilson). The power ratio's interval comes from a bootstrap over systems.

## 5. Decomposition and validation

**Decomposition.** For each state, the change in all-events SAIDI from 2020 to 2025 is split three ways:
- non-MED growth;
- MED growth at a fixed (2020) classification;
- reclassification (days changing class as the threshold moves).

A sequential decomposition is used, with Shapley averaging over the order. It is summarised across states.

**Validation of the proxy** against EIA-861 state totals:
- **EIA side:** utility SAIDI with MEDs, customer-weighted within the state, for IEEE-method utilities.
- **EAGLE-I side:** all-events SAIDI.
- **Statistic:** Spearman correlation over state-years 2018–2024.

If it is below 0.6, the proxy is reported as not validated. H1 and H2 then stand only as statements about the EAGLE-I
proxy, and the report says so.

## 6. Threats and care

- **Coverage drift** can create spurious trends. The inclusion rule and a sensitivity analysis address it: the
  analysis is repeated normalising by the covered customers in the coverage-history years.
- **States are not utilities.** Real 2.5β thresholds are computed per utility. State aggregation smooths daily SAIDI
  and lowers β, so MED counts will differ from the utilities' own.
- **Six annual points per state** give modest power per state. Inference pools across states.
- **The NZ external check named in the lead** (Commerce Commission data) is descoped: the open NZ data are annual
  per-EDB disclosures, not daily microdata.
