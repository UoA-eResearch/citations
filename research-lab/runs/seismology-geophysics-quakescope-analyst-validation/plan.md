# How trustworthy are QuakeScope's public PhaseNet picks? A station-level validation against analyst picks

Preregistration · lead `seismology-geophysics-quakescope-analyst-validation` · written 11 October 2026, before any
QuakeScope pick has been matched to an analyst pick.

## What has been seen before writing (disclosure)

**Novelty check (11 October 2026).**

- **Citing works.** OpenAlex lists 4 works citing the QuakeScope paper (Ni et al. 2025, *Seismica*,
  doi:10.26443/seismica.v4i2.1738). None validates the released picks against analyst picks.
- **The team's own benchmarks.** They publish benchmarks against analyst picks at <https://seisscoped.org/QuakeScope/>:
  - 13 curated sequences, about 100 stations;
  - a five-sequence comparison of weight sets;
  - an aftershock S-recall test on 8 stations.

  None is an archive-wide, station-level reliability map. None models station-to-station variation from instrument
  or noise attributes.
- **The retraining repository.** `Denolle-Lab/phasenet-retrain` develops a scoring engine and a calibration protocol
  for a retrained picker on curated test cases.

**Data probes (formats only, no matching).**

| What | Shown by the probe |
|---|---|
| One CI pick file (July 2019) | 3,627 picks, columns `tid, cha, pha, start, peak, end, conf, amp, amp_vel, rid` |
| `western/stations.parquet` | 26,377 station-locations |
| `western/availability/network=CI` | 5.34 M station-days with `status` and the band read |
| One run record | PhaseNet, weight `original`, P and S thresholds 0.2 |
| One SCEDC phase file (event 37265084) | The SCEDC format |
| One NCEDC monthly phase file (January 2019) | Hypoinverse archive format |
| MUSTANG metrics for four California stations | Coverage patchy (CI.PAS only to 2006, NC.KCT only 2023, CI.WBS none) |

No recall, precision or timing number has been computed.

## 1. Question and hypotheses

**Question.** How often does the QuakeScope catalogue contain a PhaseNet pick where an analyst picked a P arrival, how
much does that vary from station to station, and can the variation be predicted from what the station is?

**H1 (between-station variation).** After adjusting for magnitude and distance, P-pick recall varies between stations
with SD ≥ 0.10 on the probability scale. The SD is evaluated at a reference event of M 2.0 at 30 km epicentral
distance.

**H2 (predictability).** Station attributes alone explain at least half of that between-station variation. That means
a spatially grouped cross-validated R² ≥ 0.50 when predicting the station effects. The attributes are:

- band code;
- instrument code;
- sampling rate;
- ambient 1-10 Hz noise level.

## 2. Departures from the lead, decided now (before outcomes)

| Lead | This plan | Why |
|---|---|---|
| The 2025 archive (`wc_picks.tar.gz`, mostly `jma_wc` weights) | The 2026 `western` catalogue: PhaseNet `original` weights, thresholds 0.2, anonymous Parquet on `s3://quakescope-picks-2026` | The 2025 database is retired on 12 October 2026 (QuakeScope issue #59). The 2026 catalogue is the team's current deliverable. Selective download is possible. |
| "Which weight set" as a covariate | Dropped from H2; the 2026 western catalogue uses one weight set | Nothing to vary. If the 2025 export (`quakescope-2025/`) is published before the analysis, a within-station comparison of the two catalogues is an exploratory secondary. |
| All western networks via FDSN and ComCat | CI (SCEDC phase files) and NC and BK (NCEDC phase files), from their public S3 buckets | Bulk phase files instead of one web request per event. The other western networks are a stated limitation. |
| Cross-validation grouped by network | Grouped by 1° × 1° spatial cells | There are only three networks. |
| MUSTANG noise PSDs | Noise computed from the same data centres' continuous waveforms (Section 4) | MUSTANG coverage of CI, NC and BK stations is patchy. |

## 3. Data and sampling

**The QuakeScope snapshot.**

- **Partitions:** `western/picks/network={CI,NC,BK}/year=Y/month=M/` for the sampled months.
- **Frozen listing:** the S3 listing (key, ETag, size) of every downloaded partition is saved as
  `data/manifest_picks.csv`. The catalogue is being re-read from 8 October 2026, so the snapshot is whatever is in the
  bucket at download time, recorded by that listing.
- **Availability:** `western/availability/network={CI,NC,BK}` is downloaded once and hashed.

**Months.**

- 30 months from 2010-2024: 2 per year, drawn without replacement from that year's 12 months.
- The draw uses `numpy.random.default_rng(20261011)`, year by year in order.
- The same months are used for every network.

**Reference (analyst) picks.**

- **Sources:**
  - SCEDC `event_phases/YYYY/YYYY_DDD/<evid>.phase`, for network CI;
  - NCEDC `event_phases/YYYY/YYYY.MM.phase.Z`, for networks NC and BK.
- **Events:** local earthquakes in the sampled months with magnitude ≥ 1.5. The SCEDC event type is `eq` (local); NCEDC
  takes all events in the phase file, since quarry blasts are flagged and excluded where the format marks them.
- **Picks:** picks at stations of networks CI, NC and BK, with epicentral distance ≤ 100 km and analyst weight > 0.
- **One reference pick** per (event, station, phase). If several channels carry the same phase, the highest weight is
  kept, then the earliest time.
- **Reference time:** origin time + travel time (SCEDC). NCEDC gives the absolute arrival time.
- **What these picks are.** They come from the reviewed catalogues' phase files. Analysts reviewed them, but some
  started as automatic picks that analysts accepted or adjusted. The report calls them "analyst-reviewed picks".

**Denominator.** A reference pick counts only if:

- QuakeScope's availability table says the station-day was `loaded`;
- the station is in `western/stations.parquet`.

Picks on station-days that were never read are excluded, because a miss there is not a picker failure.

## 4. Station covariates (fixed now)

**Band and instrument code.** Taken from the analyst pick's channel. If the channel differs from the band QuakeScope
read that day, the read band is recorded too. The station's modal read band over its matched days is the covariate.

**Sampling rate.** From FDSN StationXML (SCEDC and NCEDC station services) for the read channel at the sampled dates.
The modal rate is used.

**Ambient noise.**

- **Days:** for each station, 3 days drawn at random from its `loaded` station-days in the sampled months (seed
  20261011).
- **Waveform:** the 09:00-10:00 UTC hour (01:00-02:00 local standard time), vertical component of the read band. From
  SCEDC `continuous_waveforms/` or NCEDC `continuous_waveforms/` on S3, with FDSN dataselect as fallback.
- **Processing:** instrument response removed to velocity, band-passed 1-10 Hz, RMS over 60 s windows.
- **Covariate:** log10 of the median across windows and days.
- **Missing:** stations without any usable hour get a missing value, handled natively by the gradient-boosting model.

**Secondary covariates (H2 secondary only).** Network, elevation, and the number of reference picks.

## 5. Matching and outcome

**Matching rule.**

- A reference P pick is **matched** if the catalogue has a P pick at the same network and station code, any location
  or band, with |peak − reference time| ≤ 0.5 s.
- Each catalogue pick can match at most one reference pick: greedy, closest first.

**Sensitivity tolerances:** 0.2 s and 1.0 s.

**Outcome:** matched (0/1) per reference P pick.

**S picks.** The same procedure applied to S is a secondary analysis.

## 6. Analysis (code committed before matching is run)

**Model.** A mixed logistic model, `matched ~ M + log10(distance) + (1 | station)`:

- fitted by variational Bayes (statsmodels `BinomialBayesMixedGLM.fit_vb`);
- uses stations with at least 10 reference P picks;
- `n_station` (reference picks per station) is reported.

**H1 estimand.**

- **Definition:** SD_p is the standard deviation, across a station effect u ~ N(0, σ_u²), of
  invlogit(β₀ + β_M·2.0 + β_d·log10(30) + u).
- **Computation:** by Monte Carlo (10⁵ draws), from the posterior means of β and log σ_u.
- **Interval:** a station-cluster bootstrap with 200 refits (seed 20261011), giving the 2.5-97.5 percentiles.

**H1 decision rule.**

| Verdict | Condition |
|---|---|
| **Supported** | SD_p ≥ 0.10 and the lower bound ≥ 0.05 |
| **Refuted** | The upper bound < 0.10 |
| **Inconclusive** | Anything else |

**H2 estimand.**

- **Stations:** those with at least 30 reference P picks.
- **Target:** the station effect, the posterior mean u_s, on the logit scale.
- **Model:** `sklearn.ensemble.HistGradientBoostingRegressor` with default settings and `random_state=20261011`.
- **Predictors:** the four primary covariates (Section 4); categorical codes are one-hot or native categorical.
- **Cross-validation:** grouped 5-fold, with groups being 1° × 1° cells of station latitude and longitude, assigned to
  folds by `GroupKFold`.
- **CV R²:** 1 − SSE / SST over the pooled out-of-fold predictions.
- **Interval:** a station-cluster bootstrap of the pooled out-of-fold predictions (2,000 draws) gives the 2.5-97.5
  percentiles.

**H2 decision rule.**

| Verdict | Condition |
|---|---|
| **Supported** | CV R² ≥ 0.50 and the lower bound ≥ 0.35 |
| **Refuted** | The upper bound < 0.50 |
| **Inconclusive** | Anything else |

**Secondary analyses (labelled secondary).**

- **Reliability-corrected R².** u_s carries estimation noise, so the attainable R² is below 1. The noise share comes
  from the posterior SDs of u_s.
- **Other predictors.** A linear model with the same predictors. Gradient boosting with the secondary covariates
  added.
- **Other tolerances and phases.** Recall at 0.2 s and 1.0 s; S-pick recall.
- **Timing.** The P timing residual (peak − reference) for matched picks: median and MAD, by band.
- **Subsets.**
  - Impulsive (`i`) reference picks only.
  - Excluding the busiest sampled month, if it holds more than 25% of all reference picks.
- **A station reliability table** for release: station, n, adjusted recall, interval and covariates.
- **A false-pick proxy (exploratory).** On sampled station-days, the rate of catalogue P picks with confidence ≥ 0.5
  that have no reference pick and no catalogue P pick at another station within 10 s. A rate per day.

## 7. Power and precision (before outcomes)

**H1.** With roughly 300-800 stations of 10 or more picks, the relative standard error of a between-station SD is
about 1/sqrt(2(n−1)): 3-4%, or ±0.004 at SD 0.10. The bootstrap also carries within-station binomial noise. H1 is
decidable unless the true SD sits within about 0.01 of 0.10.

**H2.** With about 300 or more stations of 30 or more picks, the sampling SE of a pooled CV R² near 0.5 is about 0.04.
The interval width needed to decide is ±0.15, so H2 is decidable unless the true R² is between about 0.42 and 0.58.

**Minimum sample.** If fewer than 100 stations have at least 30 reference P picks, both H1 and H2 are reported as
Inconclusive (insufficient stations). The months are not extended after seeing outcomes.

## 8. Order of work

1. Download availability, stations, StationXML and phase files for the sampled months. Draw the months first and
   record them in `data/months.json`.
2. Download the QuakeScope pick partitions and freeze the listing.
3. Compute the covariates. The noise step uses waveforms only, not picks.
4. Write `match.py` and `analysis.py` and test them on synthetic data with a known station SD. Commit them.
5. Run the matching, then the analysis.
6. Get an independent review, write the report, publish.

## 9. Reporting

- The verdicts follow the rules above.
- Deviations are logged with timestamps in `deviations.md`.
- The station reliability table is released as CSV.
- The report states what "analyst-reviewed" means for each data centre, and which networks are not covered.
