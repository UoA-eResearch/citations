# Preregistration: a hydrological noise floor for volcanic-unrest detection under Auckland — ambient-noise dv/v across the Auckland Volcanic Field, 2013–2026

Lead: `auckland-nz-avf-dvv-hydrological-baseline` (Auckland/NZ signature area). Written 2026-10-23, before any waveform
was correlated and before any rainfall series was downloaded.

**Examined beforehand (nothing estimated):**
- GeoNet's open S3 layout. For example, `waveforms/miniseed/2016/2016.100/EPAZ.NZ/2016.100.EPAZ.10-EHZ.NZ.D` is about
  12 MB.
- Download speed: about 0.4 MB/s per connection and about 7 MB/s with 32 connections.
- The FDSN channel epochs of the 11 AVF stations (`data/raw/channels.txt`).

**Novelty** (from the lead's critic, 2026-10). No dv/v monitoring of the Auckland Volcanic Field was found. New
Zealand dv/v work covers Ruapehu and Whakaari.

## 1. Data

- **Stations and channels.** Vertical channels of 11 GeoNet stations, location 10: ABAZ, AWAZ, EPAZ, ETAZ, HBAZ,
  KBAZ, MBAZ, MKAZ, RVAZ, WIAZ and WTAZ. Each is EHZ, except MKAZ, which is HHZ.
- **Period:** 2013-01-01 to 2026-09-30. Day files are streamed from S3, correlated, and deleted.
- **Segments.** A station's record is continuous across channel epochs that keep the same location code and sensor
  description and are separated by at most 7 days. Any other boundary starts a new segment: a new sensor or
  location, or a gap of more than 7 days. From the epochs above, the segment holding 2021-01-01 ends at:
  - ABAZ: 2023-07-28;
  - KBAZ: 2023-11-21;
  - MBAZ: 2025-03-11;
  - RVAZ: 2022-05-18;
  - WIAZ: 2024-10-09;
  - WTAZ: 2022-05-17;
  - all others continue to 2026-09-30.
- **Forcing.** Open-Meteo's ERA5 archive (no key) at the field's centre (36.90° S, 174.78° E), 2012-01-01 to
  2026-09-30: daily precipitation sum and daily mean 2 m temperature. ERA5 underestimates local extremes; the model
  uses cumulative diffusion of rainfall, not peaks.

## 2. Correlations and dv/v

- **Preprocessing, per station-day:**
  1. merge; skip the day if less than 20 h of data;
  2. demean and detrend;
  3. anti-alias and decimate to 20 Hz;
  4. bandpass 0.3–5 Hz;
  5. spectral whitening over 0.3–5 Hz;
  6. temporal normalisation by running absolute mean (2 s window).
- **Transient mask.** In 30-minute windows, any window whose pre-normalisation RMS exceeds 5 times the day's median
  window RMS is dropped, from both stations of every pair.
- **Daily correlations.** For all 55 vertical–vertical pairs, the 30-minute cross-correlations (lags ±100 s) are
  stacked linearly per day. A pair-day needs at least 24 windows.
- **dv/v by stretching:**
  - band 0.5–2 Hz;
  - coda window from t₁ = max(5 s, 2d / 1.5 km s⁻¹) to t₁ + 20 s, on the causal and acausal sides averaged, where d is
    the inter-station distance;
  - current = 10-day centred moving stack;
  - reference = mean of the segment's 2013–2020 daily correlations;
  - stretching factor grid ±2% in 0.01% steps, dv/v = −ε at the best correlation coefficient (the coherence).
- **Smoothing.** dv/v is smoothed with a 30-day centred running mean, on days with a valid current stack.

## 3. Model and test

For each pair, 30-day dv/v (%) = Σ segment constants + a · P_τ(t) + b₁ sin(2πt/365.25) + b₂ cos(2πt/365.25) + c · t.

- **P_τ** is rainfall diffused to depth: P_τ(t) = Σ over days i before t of rᵢ · erfc(√(τ / (t − tᵢ))). This is the 1-D
  pore-pressure response at depth z, with τ = z²/4D.
- **τ** is chosen from {1, 2, 5, 10, 20, 50, 100, 200, 500} days by the best training fit. Everything else is ordinary
  least squares.
- **Training:** 2013-01-01 to 2020-12-31.
- **Held-out:** 2021-01-01 to the end of the segment holding 2021-01-01 for either station of the pair. No parameter or
  offset is fitted on held-out data (the critic's design fix).
- **Pairs scored:** mean training coherence of at least 0.5, and at least 180 held-out days.

**H1 (the hydrological model explains most of the held-out dv/v).** The test statistic is the median held-out R²
(1 − SS_res/SS_tot about the held-out mean) across scored pairs, with a 95% interval from a bootstrap over pairs
(B = 2,000, seed 20261023).
- **Supported** if the median is at least 0.5 and the lower bound at least 0.4.
- **Refuted** if the upper bound is below 0.5.
- **Inconclusive** otherwise, or if fewer than 5 pairs qualify.

## 4. Secondary analyses (reported, not confirmatory)

1. **Noise floor:** twice the standard deviation of held-out residuals, as a median across pairs, against 0.05%.
2. **The March 2020 lockdown:** mean training residual over the 30 days from 2020-03-26, minus the 30 days before,
   against twice the residual standard deviation.
3. **The record-wet January–February 2023:** held-out residuals and observed dv/v in those months, for pairs whose
   held-out window covers them.
4. **Segment-break sensitivity:** every epoch boundary treated as a segment break, so held-out windows end earlier.
5. **Temperature:** ERA5 daily mean temperature (lag fitted from 0–90 days in training) in place of the sinusoid.
6. **Results by pair type:** borehole–borehole pairs (AWAZ, EPAZ, ETAZ, HBAZ, RVAZ, KBAZ, MBAZ at 93–383 m) against
   pairs with a surface sensor.

## 5. Limits stated in advance

- Urban noise sources change. Coda coherence at 0.5–2 Hz may be weak over 5–40 km, so few pairs may qualify.
- Rainfall stands in for groundwater in fractured basalt aquifers. Auckland Council's groundwater bores are not used,
  because their portal has click-through terms.
- Vertical components only. The lead's single-station cross-components are not computed.

## 6. Care note

The maunga of the Auckland Volcanic Field are taonga of Ngā Mana Whenua o Tāmaki Makaurau, co-governed by the Tūpuna
Maunga Authority. This is a methods baseline, not a hazard assessment, and it is reported as such. Results belong with
the Authority, Auckland Emergency Management and GeoNet, which the lab cannot engage directly.

## 7. Outputs

- `results/tables/`: `pairs.csv`, `dvv_daily.parquet` (by pair), `fit.json`, `primary.json`.
- `results/figures/`.
- `deviations.md` records changes before the results they affect.
