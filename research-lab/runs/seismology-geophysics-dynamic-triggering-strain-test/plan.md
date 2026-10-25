# Plan (preregistration): is remote dynamic triggering in the western US real and strain-dependent?

Lead: `seismology-geophysics-dynamic-triggering-strain-test`. Written before any pick was counted around any trigger.

**Seen before this plan:**
- Hardebeck et al. 2025 (JGR, doi:10.1029/2025JB031566) and Guo, Brodsky & Miyazawa 2025 (JGR,
  doi:10.1029/2024JB030004): abstracts only.
  - Hardebeck et al.: false positives explain the apparent triggering after about 70% of global M ≥ 6 events in
    southern California, except El Mayor-Cucapah.
  - Guo et al.: PhaseNet picks at 239 southern California stations map triggering intensity, with no false-positive
    null or strain-dose test.
- The QuakeScope 2026 western catalogue (anonymous Parquet, `s3://quakescope-picks-2026/western/`):
  - its listing: 580,407 pick files, 55.3 GB, 121 networks, 1986–2026, last modified between 3 September and
    9 October 2026;
  - the schema: `tid, cha, pha, start, peak, end, conf, amp, amp_vel, rid`;
  - two locally cached partitions (from the analyst-validation lead), which showed exact duplicate picks across
    processing runs: 1.3% and 9.2% of rows; same station, channel, phase, time and confidence; different run id.
- From the analyst-validation lead: 91% recall of analyst P picks within 0.5 s. 59% of P picks with confidence ≥ 0.5
  are isolated single-station detections, probably noise.

No pick has been counted in any trigger or baseline window.

## 0. Question and hypotheses

Large distant earthquakes are said to set off small local earthquakes as their surface waves pass. Real triggering
should grow with the strain the waves impose; chance coincidences should not.

**Unit:** a station × trigger pair.

**Significant:** the station's local-event count in the 24 hours after the wave train exceeds its 7-day pre-trigger
baseline at β ≥ 2 (section 3).

**Excess:** for each station × trigger, I(significant) − p0_s, where p0_s is the station's significant rate at its
own matched pseudo-trigger times (section 4).

**Quintiles** of estimated peak dynamic strain are taken over all station × trigger pairs (section 5).

- **H1 (primary: strain dependence).** The top-quintile excess E5 is positive and at least 3 times the bottom
  quintile's E1, and E1 is consistent with zero.
  - **Supported** if E5's 95% lower bound is above 0, E5 − 3·E1 has a 95% lower bound above 0, and E1's 90% interval
    includes 0.
  - **Refuted** if the 95% upper bound of E5 − 3·E1 is below 0, or the 95% upper bound of E5 is at most 0.
  - **Inconclusive** otherwise.
- **H2 (secondary: existence).** The mean excess over all station × trigger pairs is positive.
  - **Supported** if its 95% lower bound is above 0.
  - **Refuted** if its 95% upper bound is below 0.005 (half a percentage point).
  - **Inconclusive** otherwise.
- **Intervals:** a two-way bootstrap over triggers and stations, resampled independently with pairs kept in the
  product (2,000 resamples, seed 20261026).

## 1. Data

- **Picks.** The QuakeScope 2026 western catalogue: all networks, picks dated 2002-01-01 to 2025-12-31.
  - The listing (key, ETag, size, last modified) is frozen when the download starts.
  - Columns read: `tid, cha, pha, peak, conf`.
- **Cleaning:**
  1. Keep confidence ≥ 0.5.
  2. Drop exact duplicates of (tid, cha, pha, peak).
  3. Per station (`tid`) and phase, merge picks within 0.5 s across channels, keeping the highest confidence.
- **Stations:** `western/stations.parquet`, with coordinates and operating dates.
  - Analysed stations are those in US states (the catalogue also lists stations in British Columbia, Alberta,
    Saskatchewan and Mexico).
  - Canadian and Mexican stations may still serve as coincidence neighbours.
  - Availability comes from `western/availability/` (station-days with status `loaded`).
- **Triggers:** USGS ComCat, global M ≥ 7.0, 2002–2025. A trigger is dropped if it lies within 1,000 km of any
  analysed station; this drops El Mayor-Cucapah, Ridgecrest and nearby Mexican and Pacific Northwest offshore events.
- **Masking catalogue:** ComCat global M ≥ 4.5, 2002–2025, for teleseismic phase masking.
- **Local-sequence catalogue:** ComCat, region 25–55°N, 135–100°W, M ≥ 3.5.
- **Proxy validation catalogue:** ComCat M ≥ 1.0 events in the same region.

## 2. Local-event proxy (catalogue-free)

1. **P–S pairs at a station:** each P pick paired with the first S pick 0.8–8.0 s later at the same station, with no
   other P pick between them.
2. **Origin-time estimate:** t0 = tP − 1.37·(tS − tP), assuming Vp/Vs = 1.73.
3. **A local-event pair** is a pair with at least 2 other stations within 50 km having a pair whose t0 lies within
   ±2.5 s of it (at least 3 stations in all).
4. **Masking:** picks within ±60 s of the predicted P arrival (TauP, iasp91) of any ComCat global M ≥ 4.5 event more
   than 1,000 km from the station are removed before pairing.
5. **Proxy counts:** the station's local-event pairs per hour.
- **Analysable stations:** stations with at least 2 other stations within 50 km that have catalogue picks.

## 3. Per station × trigger test

- **Arrivals:** with Δ the epicentral distance, the surface-wave train runs from origin + Δ/4.5 km/s to origin +
  Δ/2.5 km/s.
- **Windows:**
  - post window: from the end of the wave train + 2 h, for 24 h;
  - baseline: the 7 days before the origin time.
- **Statistic:** β = (N_post − N·f) / sqrt(N·f·(1 − f)), with N = N_post + N_base and f = T_post / (T_post +
  T_base). If N = 0, β = 0. Significant if β ≥ 2.
- **A pair enters the population if:**
  - the station is analysable;
  - every station-day touching both windows is `loaded` in the availability table;
  - the station has at least one local-event pair in the 30 days before the baseline;
  - no ComCat M ≥ 3.5 event lies within 100 km of the station during the baseline window.

## 4. Empirical null

- **Pseudo-triggers:** for each station, 500 pseudo-triggers (seed 20261026).
  - Each takes a randomly chosen real trigger time and shifts it by a whole number of days, k ∈ [−45, 45] plus 365·y
    with y ∈ [−12, 12], keeping it within 2002–2025.
  - Hour of day is therefore matched exactly and season within 45 days.
  - Each inherits the real trigger's Δ-based windows.
  - It is rejected if within 10 days of any global M ≥ 7.0 or within 3 days of any global M ≥ 6.5.
- **The same rules apply as for real pairs:** availability, activity in the prior 30 days, the baseline local-sequence
  exclusion, masking and the β test.
- **p0_s** is the significant share among the station's valid pseudo-triggers. Stations with fewer than 100 valid
  pseudo-triggers are dropped, and counted.

## 5. Peak dynamic strain

- **Estimated strain:** from the surface-wave magnitude relation (Lay & Wallace),
  log10(A/T [µm/s]) = M − 1.66·log10(Δ°) − 3.3, with M = min(Mw, 8.3);
  PGV = 2π·A/T, and ε = PGV / 3.5 km/s.
- **Quintiles** are taken over all population pairs. Only ranks matter, so constants do not affect H1.
- **Secondary check of the strain proxy:**
  - 40 broadband stations with LHZ data, drawn with seed 20261026 from analysable stations, weighted toward
    geographic spread (one per 2° cell first);
  - every population trigger at those stations: peak velocity, bandpassed 15–60 s, in the surface-wave window, from
    EarthScope FDSN;
  - report the Spearman correlation with estimated PGV, and the quintile agreement.

## 6. Secondary and robustness (reported, not confirmatory)

- **Excess by quintile.** All five quintiles, and the excess against estimated strain in deciles.
- **Expected false positives.** The expected number of false positives (Σ p0_s) against observed significant pairs,
  overall and by trigger.
- **Proxy validation.** Recall of ComCat M ≥ 1.0 events within 30 km of analysable stations, on 100 random quiet days
  (seed 20261026): the share with a local-event pair at the nearest analysable station within ±10 s of the predicted
  t0.
- **Robustness of H1 and H2:**
  - S−P of 0.8–5 s;
  - confidence ≥ 0.7;
  - a 24 h baseline instead of 7 days;
  - post window from the end of the wave train + 6 h;
  - geothermal and volcanic areas excluded (The Geysers, Coso, Salton Sea, Long Valley and Yellowstone: boxes of
    ±0.3°, fixed now);
  - triggers above M 8.0 excluded.
- **Instantaneous triggering (exploratory).** Local-event pairs during the surface-wave train itself, against the same
  null.
- **Map.** Station-level excess (observed significant rate − p0_s), with geothermal and injection areas marked.

## 7. Leakage audit (G1)

Fields that correlate with high strain, and how the design handles them:
- **Bigger, nearer triggers have more teleseismic aftershocks** whose phases reach the station. These are removed by
  masking ComCat M ≥ 4.5 arrivals.
- **Long surface-wave codas** from big triggers can produce false PhaseNet picks.
  - The post window starts 2 h after the slowest surface waves (6 h in robustness).
  - The 3-station coincidence and S−P ≤ 8 s requirements reject most single-station noise.
- **Time of day and season:** pseudo-triggers are matched in hour of day and within 45 days of season. Picking noise
  varies by day and season.
- **Station churn:** p0_s is per station, so a station's own detection level is compared with itself.
- **Local sequences:** an M ≥ 3.5 sequence already under way inflates or deflates β. The same baseline exclusion
  applies to real and pseudo triggers.
- **The strain estimate uses only M and Δ** (catalogue values). It is never fitted to pick counts.
- No LLM or agent judges any unit, so no order-swap probe is needed.

## 8. Other gates

- **G2:** coverage at every step (`results/tables/coverage.json`): files, picks, stations, station × trigger pairs
  and pseudo-triggers, with every drop reason.
- **G3:** `results/plausibility.md`: the proxy validation, three station × trigger pairs traced by hand from raw picks,
  and invariants.
- **G5, G6:** at write-up.
- **G4 and G7 do not apply:** there is no classifier or labelling. The proxy's recall check is reported as validation
  with its denominator.

## 9. Limits stated in advance

- **The proxy** counts pick pairs, not located earthquakes. Its recall of small events and its false-coincidence rate
  vary by station density.
- **Strain** comes from a magnitude–distance relation, without site amplification or radiation pattern.
- **The catalogue was re-processed in September–October 2026.** The frozen listing fixes which version is used.
- **Areas without dense networks** (much of Nevada, eastern Oregon) contribute few analysable stations.
- **A null result** may mean triggering is too rare for this proxy to detect, not that it never happens.
