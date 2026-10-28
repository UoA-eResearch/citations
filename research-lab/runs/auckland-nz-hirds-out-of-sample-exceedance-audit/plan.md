# Plan (preregistration): are New Zealand's HIRDS v4 design rainfalls exceeded more often than stated since they were fitted?

Lead: `auckland-nz-hirds-out-of-sample-exceedance-audit`. Written before any rainfall value or HIRDS depth was
read.

**Seen before this plan:**
- **The HIRDS v4 report** (NIWA client report 2018022CH, 2018), §2.2–2.3 and §3.1:
  - fitting data end in 2016 (national climate database), 2015 (hydrology archive) and early 2017 (Auckland
    Council);
  - 3,404 stations in total, 1,353 of them sub-daily;
  - annual maxima are true (sliding-window) maxima, from series at least ten times finer than the duration;
  - daily-data adjustment factors.
- **The public HIRDS grid metadata list** (DataHub): 2,304 v4 "Historical" grids, 12 durations × 12 return periods
  × 16 regions, 2 km resolution. No v5 or climate-scenario grids exist, although the catalogue's filters offer them.
- **Council rain-gauge site lists only** (names and coordinates, no values), from open Hilltop servers: Northland
  253, Hawke's Bay 235, Wellington 233, Marlborough 188, Tasman 170, Taranaki 140, West Coast 54. Auckland
  Council's Environment Auckland portal responds.
- No rainfall series and no HIRDS depth has been read.

## 0. Hypotheses

**Unit:** a gauge-water-year (July–June).

**Out of sample:** water years 2017/18 onward, which lie after every HIRDS v4 fitting record.

**Exceedance.** A gauge-year exceeds when its annual-maximum rainfall for duration d is greater than the HIRDS v4
historical depth for d at the gauge's location.

- **Expected count:** AEP × gauge-years. HIRDS's return periods are annual-maximum ones, so AEP = 1/ARI and the
  10-year grid is 10% AEP. The alternative convention, 1 − e^(−1/ARI) = 9.5%, is a sensitivity.
- **O/E** is the observed count divided by the expected count, pooled over all qualifying gauges.

- **H1 (the lead's claim).** For d = 6 hours at 10% AEP, out of sample, O/E ≥ 1.3.
  - **Supported** if O/E ≥ 1.3 and its 95% interval's lower bound exceeds 1.0.
  - **Refuted** if the interval's upper bound is below 1.3.
  - **Inconclusive** otherwise.
- **Interval:** a water-year block bootstrap. Water years are resampled with replacement, and every gauge's value
  for a year moves together, which preserves the spatial dependence of single storms (2,000 resamples, seed
  20261028).
- **Sanity control (must hold for the test to mean anything):** the same O/E over in-sample water years (up to
  2014/15) should have an interval that includes 1.0. If it does not, HIRDS and this harvest disagree even where
  HIRDS was fitted, and the out-of-sample result is reported as uninterpretable.

## 1. Gauges

- **Sources (open, no account):**
  - council Hilltop servers: Northland, Hawke's Bay, Wellington, Marlborough, Tasman, Taranaki, West Coast;
  - Auckland Council's Environment Auckland portal. Its terms allow published derived results but not
    redistribution of raw data, so raw series stay out of git;
  - any further council server found before rainfall values are read, added with a dated note.
- **Resolution.** The 6-hour test needs native resolution of 15 minutes or finer (HIRDS's rule: at least ten times
  finer than the duration). The 1-hour secondary needs 5 minutes or finer; the 24-hour one, hourly or finer.
  Event (tip) records qualify.
- **Quality.** Council quality codes where served: values coded as missing, synthetic or unverified are excluded
  and counted (G2).
- **Complete water years:** at least 90% of the year's time covered by data.
- **Inclusion:** at least 8 complete out-of-sample water years. For the sanity control, at least 10 complete
  in-sample years.
- **Duplicates.** Co-located duplicates (within 100 m, overlapping records) keep the longer record.
- **Target:** at least 250 gauges. If fewer qualify, the count is reported and the intervals widen. The test still
  runs if at least 100 qualify.

## 2. Annual maxima and HIRDS depths

- **Annual maxima.** Series are accumulated to 5-minute totals (or the native interval if coarser and allowed). For
  each water year, the maximum of the sliding d-hour sum, d = 1, 6, 24.
- **HIRDS depths.** Read from the v4 historical grids (ordered on DataHub and downloaded through its API) at each
  gauge's coordinates, by bilinear interpolation between 2 km cell centres. The grids are a 2 km model surface, not
  the point tables, and this is stated as a limit.

## 3. Secondary analyses (reported, not confirmatory)

- The same O/E at 1 and 24 hours, and at 2% AEP (50-year grid).
- **Strata:** Auckland region; by council.
- **Without January–February 2023,** the period that motivated the lead.
- **Storm-cluster bootstrap:** exceedances within 72 hours of each other, across gauges, are one storm; storms are
  resampled. A cross-check on the water-year bootstrap.
- **Year-by-year O/E,** to show whether any excess is spread out or concentrated in a few events.
- **Regional GEV refit:** a GEV fitted per region to pre-2017 annual maxima, then refitted with the out-of-sample
  years, giving the shift in the 10% AEP 6-hour depth. This is descriptive and independent of HIRDS.
- **Dropped from the lead:** the climate-adjusted HIRDS depths, because no such grids exist on DataHub.
- **A possible extension, not a hypothesis:** if ESNZ publishes HIRDS v5 (fitted to data through 2024) before
  write-up, report how far v5 moved each gauge's depth from v4, and whether it moved in the direction the v4
  exceedances imply.

## 4. Leakage audit (G1)

- The test years are after every HIRDS v4 fitting record. The cut-off is fixed here from the HIRDS report, not from
  the data.
- Gauge inclusion uses record completeness, resolution and quality codes only, never rainfall values or
  exceedances.
- HIRDS depths come from ESNZ's grids, untouched.
- The lead was motivated by Auckland 2023, so:
  - the confirmatory test is national;
  - it does not oversample Auckland;
  - the without-2023 sensitivity is declared here.
- Many gauges also contributed to HIRDS v4's fit (council archives fed its hydrology data). That is intended: the
  question is whether the stated probabilities hold at those places after the fit. The in-sample control measures
  any agreement inflated by that overlap.
- No LLM or agent labels any unit.

## 5. Other gates

- **G2:** `results/tables/coverage.json`, covering sites listed, series fetched, quality-excluded values,
  incomplete years, gauges failing each inclusion rule, and HIRDS depths found per gauge.
- **G3:** `results/plausibility.md`, with three gauges traced from raw series to annual maxima to exceedance, and
  the in-sample control.
- **G4:** a hand check of 30 annual maxima, sampled at random, against the raw series, for the windowing code.
- **G5 and G6:** at write-up.
- **G7:** does not apply (no human labels).

## 6. Limits stated in advance

- **Councils are not a random sample.** Open servers cover some regions much better than others, so the result is
  for the regions covered, which is reported.
- **Grid, not point.** HIRDS's 2 km grid depths can differ from its point tables, especially in steep terrain.
- **Non-independence across gauges.** It is handled by the year-block bootstrap, which with about nine
  out-of-sample years gives wide intervals.
- **Low power at 2% AEP.**
- **Provisional data.** Recent council data may be provisional and revised later.
