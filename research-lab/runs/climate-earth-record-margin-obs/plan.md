# Preregistration: are heat records being broken by growing margins in station observations?

Lead: `climate-earth-record-margin-obs` (research-lab/leads.json). Written 2026-10-01 and committed to git before any
station temperature data were downloaded or examined. Probes made before writing:

- the GHCN-Daily inventory and station lists (element coverage by year only, no values);
- the AWS and NCEI file layouts and freshness;
- a download-speed test on one station file, whose values were not inspected;
- a literature search.

Every later departure goes to `deviations.md` with a timestamp taken from `date`.

## 1. Background and gap

- **The prediction.** Fischer, Sippel & Knutti (2021, Nature Climate Change) showed in large model ensembles that
  warming makes "record-shattering" extremes more likely: new records that beat the previous one by a large margin.
  The probability depends on the rate of warming, not only its level.
- **Observations so far measure frequency.** Observational work quantifies how *often* records fall; a 2025 Nature
  Reviews Earth & Environment review reports 300–350% more daily hot records in 2016–2024 than a stationary climate
  would give. Regional studies (Spain, Australia) do the same.
- **The gap.** Model and reanalysis studies (e.g. Thompson et al.) treat margins. A global station-based test of record
  *margins* against explicit null models was not found. Such a test must separate three things:
  - what any warming implies;
  - what the local mean warming implies;
  - margins beyond both.

## 2. Hypotheses

Notation:

- X_t is a station's annual maximum of daily maximum temperature (TXx) in year t.
- m_t = X_t − max(X_{t−30}, …, X_{t−1}) is the **30-year record margin**, in units of σ_s, the station's detrended
  interannual standard deviation of TXx.
- A year is **record-shattering** when m_t > 1.
- The look-back is fixed at 30 years, so under a stationary climate the distribution of m_t does not depend on t. This
  removes the "older records are harder to beat" artefact of all-time records.

Hypotheses:

- **H1 (primary).** In 2003–2025, the pooled frequency of record-shattering years exceeds the expectation under a
  **stationary null** (detrended series, years block-resampled). Estimand: ratio R1 = observed / null frequency.
- **H2 (primary, the non-trivial test).** In 2003–2025 the frequency also exceeds a **trend-preserving null**: the
  station's smooth warming trend plus its own detrended variability, block-resampled. Estimand: R2 = observed /
  trend-null frequency. R2 > 1 means margins grow beyond what mean warming at unchanged variability implies. R2 ≈ 1
  means mean warming explains them.
- **H3 (rate dependence).** Across stations, the excess shattering frequency over the stationary null in 2003–2025
  increases with the local warming rate.
- **H4 (acceleration).** The record-shattering frequency is higher in 2003–2025 than in 1981–2002 (ratio R4).

## 3. Data (open)

- **Temperatures.** NOAA GHCN-Daily per-station files (NCEI `by_station/*.csv.gz`, current release), element TMAX.
  Values with a non-empty quality flag are dropped.
- **Candidates.** The 4,020 stations whose inventory TMAX coverage spans 1951 to 2025 or longer.
- **Metadata.** `ghcnd-stations.txt` (coordinates; HCN/CRN and GSN flags).
- **External warming rate (H3).** Berkeley Earth gridded land temperature trend at the station's location, if
  available. Otherwise the station's own smooth-trend slope, labelled as a deviation.

## 4. Definitions

- **Warm season.** May–September north of the equator, November–March south of it; for the south, a season is
  assigned to the year in which it ends.
- **Valid year.** At least 90% of warm-season days have a valid TMAX. Only then is TXx computed.
- **Qualifying station.**
  - At least 60 valid years in 1951–2025;
  - at least 20 valid years in each 30-year look-back window used;
  - valid in at least 80% of the years in each era.
- **Margin.** m_t is computed only when at least 25 of the 30 look-back years are valid.
- **σ_s.** The standard deviation of TXx residuals after removing a LOESS trend (span 30 years), over 1951–2025.
- **Eras.** E1 = 1981–2002 (look-back from 1951), E2 = 2003–2025.
- **Secondary variable.** TX7x: the annual maximum of the 7-day running mean of TMAX, same rules (Fischer's
  week-long heat).
- **Thresholds.** Shattering at m_t > 1 (primary). Secondary thresholds: m_t > 0 (any new 30-year record) and
  m_t > 2.

## 5. Null models and statistics

- **Stationary null.** Per station:
  - take the TXx residuals from the LOESS trend and add them to the station's 1951–1980 mean;
  - resample years in blocks of 3, to keep short-range dependence;
  - recompute m_t;
  - repeat 500 times.

  The expected frequency per era is the surrogate mean.
- **Trend-preserving null.** The same, but the resampled residuals are added back to the LOESS trend. Residual
  resampling is within the whole record, so variability is stationary by construction.
- **Pooling and uncertainty.** Frequencies are pooled over station-years. 95% intervals come from a **spatial block
  bootstrap**: 1,000 resamples of 5°×5° grid cells, with each cell's stations kept together. Ratios R1, R2 and R4 are
  computed within each bootstrap resample.
- **H3.** Station-level excess (observed minus stationary-null shattering frequency in E2) is regressed on the local
  warming rate (°C per decade, 1981–2025). The slope is estimated with the spatial block bootstrap.

**Decision rules.**

- **H1 / H2 / H4.** Supported if the lower bound of the 95% interval of R1, R2 or R4 exceeds 1; contradicted if the
  upper bound is below 1; otherwise inconclusive.
- **H3.** Supported if the 95% interval of the slope excludes 0 on the positive side.

**Robustness (reported regardless of outcome):**

- TX7x instead of TXx;
- thresholds 0 and 2;
- the HCN / GSN-flagged high-quality subset;
- excluding the United States (half the stations);
- block length 1 and 5.

## 6. Known limitations (a priori)

- **Homogeneity.** GHCN-Daily is not homogenised. Station moves and instrument changes can create steps that look like
  shattering records. The high-quality subset and the within-station null partly address this.
- **Spatial coverage.** Stations are concentrated in the US, Europe, Russia and East Asia; the tropics and the southern
  hemisphere are sparse.
- **One observed realisation.** There is a single realisation of climate, so power is limited. Pooling over stations
  helps but stations are spatially correlated, hence the grid-cell bootstrap.
- **Local detrending.** The trend-preserving null takes the station's own LOESS trend as "mean warming". Any
  low-frequency variability it absorbs is treated as trend.
