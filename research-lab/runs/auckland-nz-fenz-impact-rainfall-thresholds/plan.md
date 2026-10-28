# Plan (preregistration): do flood callouts track how rare the rain is for a place, rather than how deep it is?

Lead: `auckland-nz-fenz-impact-rainfall-thresholds`. Written before any FENZ outcome row was read.

**Seen before this plan:**
- **The lead's text,** including scout counts of flood-coded rows per year.
- **The FENZ incident files' column names and metadata PDF.** One record per exposure; locations at suburb level;
  NaturalDisasterType includes "Flood"; an action category "Water removal: … weather related floods". Five
  StartDateTime values were read to learn the format: local civil time, no zone.
- **The NZ Gazetteer's feature types** (Suburb, Locality, Town and others, with coordinates).
- **Rain-gauge series and HIRDS v4 depths from this lab's HIRDS lead** (`auckland-nz-hirds-out-of-sample-exceedance-audit`):
  - 443 council gauges in eight regions, water years 1995/96–2025/26, with that lead's completeness and quality
    rules (its D2, D3, D5);
  - HIRDS point depths at each gauge.

  That lead's rainfall maxima and exceedances have been analysed, but never against any FENZ record.

## 0. Hypothesis

**Unit:** a suburb-day (NZST calendar day), July 2017 to June 2025, for suburbs with a usable rain gauge within
10 km.

**Outcome:** at least one FENZ exposure with NaturalDisasterTypeName "Flood" starting that day in that suburb.

**Rain:** the day's maximum 6-hour rainfall at the assigned gauge (section 2), as either:
- depth, *d* (mm); or
- rarity, *r* = *d* / *M*, where *M* is the gauge's HIRDS v4 6-hour depth at a 2-year ARI (AEP 0.5). That is
  HIRDS's own index variable, the median annual maximum, so *r* is its index-flood standardisation of depth.

**Two models,** identical except for the rain term:
- **(D)** a natural cubic spline (4 df) in log(1 + *d*);
- **(R)** the same spline in log(1 + *r*).

**Shared terms:**
- antecedent rain: log(1 + 72-hour total before the day);
- month (12 levels) and weekend;
- region (council) fixed effects;
- suburb activity: log of the suburb's mean daily count of non-flood FENZ exposures in the training years.

Logistic regression; train FY2017/18–2023/24, test FY2024/25 (held out, evaluated once).

**Statistics:**
- D_LL = held-out mean log-loss(D) − mean log-loss(R). Positive favours rarity.
- S = (LL0 − LL_R) / (LL0 − LL_D), where LL0 is the same model with no 6-hour rain term (antecedent rain kept).

**H1 (the lead's claim): rarity predicts flood callouts better than depth.**
- **Supported** if all three hold:
  - D_LL > 0, with a 95% storm-day block bootstrap interval excluding 0;
  - S ≥ 1.05;
  - (R) beats (D) in a majority of regions under leave-one-region-out cross-validation (section 3).
- **Refuted** if either:
  - D_LL's interval lies wholly below 0; or
  - the interval includes 0, S < 1, and (R) wins in fewer than half the regions.
- **Inconclusive** otherwise.

**Bootstrap:** held-out days are resampled with replacement; all suburbs of a day move together, so a storm stays
one unit. 2,000 resamples, seed 20261028.

## 1. FENZ records

- All eight files, FY2017/18–2024/25. Column-name differences between years (e.g. RC_ID in 2024/25) are mapped.
- **Time.** StartDateTime is treated as New Zealand civil time and converted to NZST (UTC+12, the gauges' time
  base) with the Pacific/Auckland zone rules.
- **Outcome variants** (sensitivities):
  - **V1:** add exposures whose action is "Water removal: domestic, commercial, weather related floods";
  - **V2:** add exposures whose ICAD event type starts "NAT" (natural disaster).
- **Suburb geocoding.**
  - FENZ Suburb is matched to NZ Gazetteer points (feature types Suburb, Locality, Town, City, Village, and others
    that match) by normalised name.
  - A name with several gazetteer points takes the one nearest the centroid of the suburbs uniquely matched in the
    same TLA.
  - Unmatched suburbs are dropped and counted (G2).
  - The lead's LINZ suburb polygons need an account the lab cannot create, so points replace polygons. This is
    stated as a limit: distances are to a suburb's gazetteer point, not its area.

## 2. Rain

- **Gauges.** The HIRDS lead's series: Hilltop servers for Northland, Hawke's Bay, Wellington, Marlborough,
  Tasman, Taranaki and the West Coast, plus Auckland Council.
- **Quality.**
  - 1xx (missing) and 3xx (synthetic) records count as unknown time.
  - **2xx (unverified) is kept in the primary.** Impact forecasting runs on operational data, and the unaudited
    recent years would otherwise remove Auckland's 2021–2023 record.
  - **Sensitivity Q:** 2xx excluded.
- **Gauge-day completeness.** A gauge-day is usable if:
  - at least 90% of the 30 hours from 6 hours before the day to its end is known (the HIRDS lead's D2 rules:
    unresolved rain, outages in dense-logging years, quality exclusions); and
  - the gauge-year's median wet interval is no more than 15 minutes (its D3).
- **Assignment.** Each suburb-day takes the nearest gauge within 10 km that is usable that day. If none is usable,
  the suburb-day is dropped and counted.
- **Rain values.**
  - *d* = the maximum sliding 6-hour total among windows ending in the day (5-minute bins, as in the HIRDS lead's
    maxima.py).
  - Antecedent rain = the 72-hour total ending at the day's start.
  - *M* comes from the HIRDS lead's `data/hirds_depths.parquet`.

## 3. Secondary analyses (reported, not confirmatory)

- **Leave-one-region-out** (part of H1's rule). For each region with at least 20 flood suburb-days, (D) and (R) are
  fitted on the other regions' training years and scored by mean log-loss on that region's held-out year. A win is
  a lower log-loss for (R).
- **The same comparison at 1 hour and 24 hours,** with *M* at those durations.
- **An AEP form.** log ARI by log-interpolating each gauge's HIRDS 6-hour depth–ARI curve where *d* is at least the
  1.58-year depth, joined to *r* below it.
- **Onset thresholds.** For each region, the rarity and the depth at which (R)'s and (D)'s fitted callout
  probability first exceeds 10 times the region's dry-day rate.
- **Auckland.** Auckland's curve, with 27 January 2023 placed on it.
- **Sensitivities:** V1, V2, Q, nearest gauge within 5 km, and the inverse-distance mean of up to three gauges.

## 4. Leakage audit (G1)

- The test year (FY2024/25) is not used in fitting, feature construction or model choice. Suburb activity uses
  training years only and excludes flood exposures.
- HIRDS depths are ESNZ's, untouched. *M* is a fixed per-gauge constant, not fitted to callouts.
- Gauge assignment uses distance and data availability only, never callouts.
- The rain-callout relationship is not inspected before this plan is committed. The evaluation code is committed
  before it is run on the test year.
- No LLM or agent labels any unit.

## 5. Other gates

- **G2:** `results/tables/coverage.json`, covering:
  - FENZ rows, then flood rows, then geocoded, then within 10 km of a gauge, then gauge-day usable;
  - suburbs and suburb-days at each step.
- **G3:** `results/plausibility.md`, tracing three storm days (27 Jan 2023 in Auckland, 14 Feb 2023 in Hawke's Bay,
  late June 2025 in Nelson–Tasman) from FENZ rows and gauge series to model predictions.
- **G4:**
  - **geocoding audit:** for every matched suburb, whether its nearest gauge's council matches the FENZ record's
    regional council, with the mismatch rate reported;
  - **window audit:** 30 random suburb-days' *d* recomputed independently from raw records.
- **G5 and G6:** at write-up.
- **G7:** does not apply (no human labels).

## 6. Limits stated in advance

- **Callouts are not damage.** They reflect drainage, exposure, reporting and FENZ capacity as well as rain;
  capacity saturation on extreme days caps counts.
- **Gauges cover eight regions,** so the result is for those regions.
- **Points, not polygons,** for suburbs. A gauge within 10 km of a suburb's point may still miss a convective cell.
- **Logistic GLM, not the lead's GLMM.** Suburb random effects are replaced by the suburb-activity covariate, for
  cost on several million suburb-days.
- **Care note (Te Mana Raraunga).** FENZ records include suburbs with high Māori populations that are of iwi interest
  after Cyclone Gabrielle. The study uses no ethnicity or iwi data, does not stratify by ethnicity, and reports
  service-design results in aggregate.
