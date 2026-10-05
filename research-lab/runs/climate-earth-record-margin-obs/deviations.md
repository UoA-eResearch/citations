# Deviations log: record-shattering margins deep dive

Every departure from `plan.md`, with a timestamp (NZDT) taken from `date`. Newest last.

### D1. Preregistration (2026-10-01 02:19:17)
`plan.md` committed as 448f69c before any station temperature values were downloaded or examined.

### D2. External warming-rate period (2026-10-01 02:24)
The Berkeley Earth gridded file (Complete_TAVG_LatLong1.nc, last modified 2025-01-10) ends in December 2024, so the H3
external warming rate is the 1981-2024 trend rather than the planned 1981-2025. The station-trend version (1981-2025,
the plan's fallback) is reported alongside it.

### D3. Preregistered results and the failed null validation (2026-10-01 03:30-03:32)
Preregistered analysis (`code/analyze.py`; `results/tables/pooled.csv`, `h3.csv`): 2,013 qualifying stations in 270
grid cells. Primary (TXx, threshold 1, block 3): R1 = 1.67 [1.27, 2.20], R2 = 1.02 [0.82, 1.26], R4 = 0.80 [0.55, 1.14];
observed record-shattering frequency in 2003-2025 0.66% of station-years, stationary null 0.39%, trend-preserving null
0.65%. H3 with the station trend: slope +0.011 per degC/decade [0.007, 0.015]. At threshold 0, R2 = 0.71 [0.65, 0.78].
Because R2 < 1 at threshold 0 looked like a null-model artefact, the nulls were validated (exploratory,
`code/validate_nulls.py`, `results/tables/null_validation.csv`): each qualifying station's pipeline was run on synthetic
series with a known answer -- its own LOESS trend plus stationary AR(1) noise (station sd and lag-1 autocorrelation;
median phi ~0), 3 replicates, and a no-trend world. Result: the nulls are NOT calibrated. In the no-trend world R1 =
1.23 [1.20, 1.26] (threshold 0) and 1.27 [1.17, 1.41] (threshold 1) instead of 1; in the trend world R2 = 0.91
(threshold 0) and 1.16 [1.09, 1.24] (threshold 1) instead of 1. Cause: the 30-year LOESS absorbs part of the
interannual variability, so the resampled residuals (both nulls) are too calm, and the fitted "trend" carries noise
wiggles into the trend-preserving null. The biases (10-25%) are as large as the effects. The preregistered numbers are
reported as preregistered but cannot be read at face value. Remedy (exploratory, D4): a low-flexibility trend (hinge:
flat to 1980, linear after; 3 parameters) validated on the same synthetic test before use.

### D4. Null-model bug found by validation; corrected analysis (exploratory; 2026-10-01 03:32-03:35)
Root cause of D3: the preregistered surrogates resample residuals WITH replacement (circular block bootstrap). For record
statistics this is wrong: duplicated extreme values cannot be strictly exceeded, so surrogates produce too few records
(in the no-trend synthetic world the null gave 2.7% new 30-year records against the true 1/31 = 3.2%). Detrending was a
secondary issue: switching LOESS to a hinge trend alone did not fix it (no-trend R1 1.23 / 1.17 at thresholds 0 / 1).
Fix: block PERMUTATION without replacement (`block_permute`: residuals cut into consecutive blocks of L with a random
phase, block order shuffled; every value used once). Unit check: permuted iid surrogates give 3.17% records (theory
3.23%). Validation of the fixed nulls (`results/tables/null_validation_*_permute*.csv`, 3 replicates x 2,013 stations):
- hinge detrending (flat to 1980, linear after; 2 parameters): no-trend world R1 = 0.99 [0.96, 1.02] / 1.02 [0.93, 1.12]
  (thresholds 0 / 1); trend world R2 = 0.99 [0.97, 1.01] / 0.98 [0.92, 1.05] -- calibrated.
- LOESS detrending: no-trend R1 at threshold 1 still 1.12 [1.02, 1.24] (variance absorption) -- not used.
- misspecification check (truth with the curved LOESS trend, analysed with the hinge): trend-world R2 = 1.05 [1.02,
  1.08] / 1.03 [0.97, 1.11] -- a small upward bias at most.
Corrected analysis (`code/analyze.py hinge permute`; `results/tables/pooled_hinge_permute.csv`, `h3_hinge_permute.csv`):
primary R1 = 1.19 [0.89, 1.59] (inconclusive), R2 = 0.80 [0.63, 1.02] (inconclusive, below 1), R4 = 0.77 [0.53, 1.12];
threshold 0: R1 1.11 [0.94, 1.31], R2 0.80 [0.73, 0.88] (contradicted); TX7x: R1 1.37 [1.03, 1.85], R2 0.91; outside
the US: R1 1.92 [1.36, 2.56], R2 0.75 [0.56, 0.98]; H3 (station hinge slope) +0.0099 [0.0065, 0.0133]. Note that
observed frequencies differ between the two analyses because the shattering threshold is in units of each station's
residual sd, which is larger under the hinge. The report presents the corrected analysis as primary evidence and the
preregistered numbers alongside, with this log as the reason.

### D5. H3 with the preregistered external covariate (2026-10-01 03:36)
`code/h3_external.py` (Berkeley Earth 1-degree TAVG trend 1981-2024 at each station; `results/tables/h3_external_*.csv`):
slope of the station excess shattering frequency (2003-2025, observed minus stationary null) on the external warming
rate = +0.0017 [-0.014, +0.018] per degC/decade (hinge/permute; 1,989 stations, 258 cells); loess/bootstrap +0.0002
[-0.017, +0.017]. H3 is NOT supported with the preregistered primary predictor. The station-own-trend version
(+0.0099 [0.0065, 0.0133]) is circular -- a station that happens to end on warm years gets both a steeper fitted trend
and more records from the same data -- and is reported only as a secondary, confounded estimate. Berkeley TAVG trend and
the station TXx hinge slope correlate at r = 0.50.

### D6. Revisions after the independent review (2026-10-01 03:52-04:08)
An independent reviewer (a separate Fable 5.1 agent with the plan, log, code and draft) returned FIX FIRST. Changes:

1. **Plausibility screen** (`analyze.screen`, applied in `stage1`). A station is dropped if any valid seasonal value is
   more than 8 robust standard deviations (MAD x 1.4826) from its median, or its TXx is below 10 degC at |latitude| < 60.
   Flagged: 11 candidate stations for TXx and 5 for TX7x, of which 4 qualified in each case (e.g. RSM00023986, with
   values off by a factor of 10). Qualifying stations 2,013 -> 2,009. Ratios change by less than 0.015. Screened
   results are cached as `*_screened.parquet`; the preregistered cache is untouched.
2. **Two-way bootstrap** (`analyze.pooled_twoway`, 5,000 draws). It resamples 5x5-degree cells and, independently,
   3-year blocks of years within each era. Large heatwaves set records at hundreds of stations in the same year, and
   the preregistered cell-only bootstrap ignores that dependence. The two-way interval is now primary
   (`*_lo`/`*_hi`); the cell-only interval is kept as `*_lo_cell`/`*_hi_cell`. H3 gets the same treatment
   (`h3_external.py`: cells plus 3-year blocks of 2003-2025, station excess recomputed per draw).
3. **Coverage check** (`code/validate_coverage.py`; `results/tables/coverage_validation*.csv`). Setup:
   - 30 synthetic worlds x {steady warming, no warming}; the true ratio is 1 in every world;
   - the full pipeline on each world, with 200 surrogates per station.

   Two dependence models were measured from the hinge residuals. The results:

   | Dependence model | Cell-only coverage | Two-way coverage |
   |---|---|---|
   | Nested: a 20-degree regional year effect (39% of variance) plus a 5-degree cell effect (20%) | 63-83% | 97-100% |
   | Distance kernel: corr = 0.78 exp(-d / 819 km), fitted to station-pair correlations of 0.56 at 0-500 km, 0.33 at 500-1000 km, 0.18 at 1000-1500 km and ~0 beyond 2000 km | 33-80% | R2: 100% / 97% (thresholds 0 / 1); R1: 83% / 93% |

   Under the distance kernel, which is the more realistic model:
   - The two-way interval is conservative for R2: its width is about 1.5x the spread of estimates across worlds.
   - It is slightly narrow for R1 at threshold 0.
   - In no-warming worlds, R1 averages 1.06 (threshold 0) and 1.13 (threshold 1). Spatially correlated chance alone
     produces R1 of about 1.1.
4. **Results with two-way intervals** (`results/tables/pooled_hinge_permute.csv`).

   | Analysis | R1 | R2 | R4 |
   |---|---|---|---|
   | Primary | 1.19 [0.64, 1.98] | 0.80 [0.45, 1.34] | 0.77 [0.37, 1.63] |
   | Threshold 0 | 1.11 [0.80, 1.46] | 0.80 [0.59, 1.02] | 1.00 [0.63, 1.51] |
   | TX7x | 1.38 [0.60, 2.53] | | |
   | Non-US | 1.92 [1.00, 3.15] | | |
   | Non-US, threshold 0 | 1.78 [1.17, 2.48] | | |
   | US only, threshold 0 | 0.82 [0.47, 1.23] | 0.72 [0.41, 1.07] | |

   - H3 (external rate): +0.0017 [-0.041, +0.036].
   - Only non-US threshold-0 H1 excludes 1.
   - The earlier "supported" (TX7x, non-US threshold 1) and "contradicted" (R2 at threshold 0) verdicts came from the
     too-narrow cell-only intervals and are withdrawn.
   - The R2 upper bound at threshold 0 depends on Monte Carlo noise at 1,000 draws (0.997 at seed 0; 1.015-1.023 at
     5,000 draws for seeds 0-2; 1.05-1.09 with 2-, 4- and 5-year blocks). Hence 5,000 draws.
5. **Where the H2 shortfall comes from** (`code/explore_h2.py`; `h2_breakdown.csv`, `h2_by_year.csv`). At threshold 0:
   - R2 is 0.72 [0.41, 1.07] at US stations and 0.91 [0.60, 1.25] elsewhere.
   - In 17 of the 23 years of 2003-2025, fewer new records were set than the steady-warming null expects.
   - Three heatwave years (2012, 2003, 2021) hold 28% of the observed new records, against 13% of the expected ones.
   - Without those three years R2 is 0.67; without the three largest-deficit years it is 0.89.

   The shortfall is therefore broad across years. It is partly offset by a few very large regional heatwaves rather
   than caused by them.
6. **The early baseline** (`code/explore_baseline.py`; `baseline_residuals.csv`).
   - The hinge assumes a flat climate until 1980, but the mean hinge residual in 1951-55 is +0.78 degC at US stations
     (the 1950s drought heat) and +0.24 degC elsewhere.
   - Sensitivity check: a 3-parameter continuous piecewise-linear trend with its own 1951-80 slope (`detrend(..., "pw")`).
     The pw nulls pass the same synthetic validation: steady-warming world R2 0.98 / 0.99, no-warming world R1 1.00 / 1.07
     (thresholds 0 / 1; `null_validation_pw_permute.csv`).
   - Results are essentially unchanged (`pooled_pw_permute.csv`): primary R1 1.27, R2 0.79, R4 0.79; threshold 0 R2
     0.77 [0.57, 0.98]; non-US threshold 0 R1 1.77 [1.16, 2.46]. The 1951-55 US residual falls only to +0.56 degC,
     because the 1950s heat is a multi-year episode rather than a trend.
7. **Disclosures added to the report.**
   - The hinge knot is fixed at 1980 (not tuned).
   - sigma_s is the standard deviation of the station's hinge residuals with ddof = 2 (the number of trend parameters),
     so "margin > 1" means beating the previous 30-year maximum by more than one residual standard deviation.
     Threshold 0 (any new record) does not depend on sigma and is the most robust statistic.
   - The preregistered LOESS used no robustness iterations (it = 0).
   - The null validation (D4) targets the 2003-2025 ratios R1 and R2. R4 is a ratio of observed frequencies and needs
     no null.
   - H3 is underpowered: the two-way interval spans +/-0.04 per degC/decade, against the ~0.003 slope the reviewer
     estimated a model-like rate dependence would give at these warming rates.
8. **Log correction.** D3 said the hinge has 3 parameters; the code has always used 2 (intercept and post-1980 slope).
   D3 now says so and points here.

## Correction after publication (2026-10-06 02:34 NZDT)

The lab's self-audit (`research-lab/paper/`) found a rounding error. For the steady-warming world at threshold 1,
the lower bound of the H2 ratio is 0.9149 in `results/tables/null_validation_hinge_permute.csv`. The report and D4
above printed it as 0.92, rounding twice. The report now reads 0.98 [0.91, 1.05]. D4 is left as written, and this
entry corrects it. No conclusion changes.
