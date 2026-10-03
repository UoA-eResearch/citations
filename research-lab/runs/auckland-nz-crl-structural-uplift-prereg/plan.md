# Preregistration: is the City Rail Link's ridership jump structural or a novelty effect?

Lead: `auckland-nz-crl-structural-uplift-prereg` (research-lab/leads.json). Written 2026-10-03 and committed to git
before any post-opening data beyond 20 September 2026 exist. Auckland Transport's (AT) daily file currently ends on
20 Sep 2026.

## What was seen before writing (disclosure)

- **By the lead scout** (2026-10-03, during scouting): AT daily boardings from 1 Jul 2023 to 20 Sep 2026, including the
  first post-opening week. The scout reported a weekday rail/bus ratio of about 0.307 in the first full week after City
  Rail Link (CRL) public services began on 13 Sep 2026, against monthly medians of 0.209–0.232 before.
- **By me** (writing this plan):
  - The structure and date coverage of the daily files (FY2023/24 to FY2026/27; the current file runs 1 Jul to 20 Sep
    2026).
  - The structure of the monthly-by-route file (FY2026/27 columns, filled to Aug 2026).
  - The current AT GTFS feed's station list, reported by the lead critic: the three new stations Te Waihorotiu,
    Karanga-a-Hape and Maungawhau are present.
  - No boardings values after 10 Sep 2026.
- **The confirmatory window (16 Feb to 25 Mar 2027) is in the future.** No one has seen it.

Every later departure goes to `deviations.md` with a timestamp taken from `date`.

## 1. Question and gap

- **The project.** The CRL (NZ$5.5 billion) opened on 13 Sep 2026: underground through-running rail under central
  Auckland with three new stations.
- **The gap.** No independent evaluation after opening exists; there are only AT's 2015 business-case forecasts and
  commentary. Early jumps on new rail lines often fade, the novelty or ramp-up question of Shinn & Voulgaris (TRR 2019),
  or come from riders who switched from buses.
- **This study** fixes the test before the outcome data exist.

## 2. Data

- **AT daily boardings by mode** (bus, train, ferry; HOP, contactless and train line-to-line transfers). The yearly
  files FY2023/24 to FY2026/27 come from at.govt.nz ("How many people are taking buses, trains and ferries"), and later
  releases of the FY2026/27 and FY2027/28 files will be added.
- **AT monthly boardings by route** (FY2025/26 and FY2026/27 files).
- **The current AT GTFS static feed** (gtfs.at.govt.nz/gtfs.zip), used only for bus route shapes and stop locations.

## 3. Outcome and day filters (H1)

- **Outcome.** The daily ratio R_d = train boardings / bus boardings.
- **Days used:**
  - Tuesdays, Wednesdays and Thursdays only;
  - excluding NZ public holidays;
  - excluding disrupted days, where train or bus boardings fall below 60% of the median of that mode on the same
    weekday over the preceding 8 weeks. The rule is symmetric and fixed now; it catches strikes, closures and storms.
- **Windows.** W_y = 16 Feb to 25 Mar of year y. 2027 Easter (Good Friday 26 Mar) falls outside it.

## 4. Primary hypothesis H1 and decision rule

- **Baseline.** R_pre = the mean of the three window means R(W_2024), R(W_2025), R(W_2026).
- **Confirmatory value.** R_post = the mean of R_d over W_2027.
- **Uplift.** U = R_post / R_pre − 1.
- **Calibration (placebo error), computed now from pre-opening data only.** For every 38-day window starting between 1
  Feb 2025 and 1 Aug 2026 (ending before 11 Sep 2026), compute the same statistic: that window's mean ratio over the mean
  of the same calendar window in all earlier available years. The empirical distribution of these placebo uplifts is the
  no-intervention error distribution. q05 and q95 are its 5th and 95th percentiles.
- **Bounds.** L = U − q95 and H = U − q05.

| H1 verdict | Condition |
|---|---|
| Supported | U ≥ 0.20 and L > 0.10 |
| Contradicted | H < 0.20 |
| Inconclusive | otherwise |

## 5. Secondary analyses

- **Persistence.**
  - U_open = the opening-week uplift: the mean R over Tue to Thu 15–17 Sep 2026 against the same weekdays of the
    corresponding week in 2023, 2024 and 2025.
  - P = U / U_open is descriptive. The lead's prediction is P ≥ 0.55.
- **Each mode against its own baseline.** Train and bus boardings in W_2027 relative to their W_2024–2026 means, with
  the same placebo calibration. This separates a rail gain from a bus loss.
- **H2 (bus substitution), route-level difference in differences:**
  - **Exposed bus routes:** any GTFS shape (current feed) passes within 800 m of Te Waihorotiu, Karanga-a-Hape or
    Maungawhau station. Sensitivity radii: 400 m and 1,200 m.
  - **Outcome:** each route's boardings, Oct 2026 to Mar 2027 against Oct 2025 to Mar 2026. Routes present in only one
    period are excluded and counted.
  - **Estimate:** the ratio of ratios, exposed (post/pre) over unexposed (post/pre), with a route-cluster bootstrap.
  - **Verdict:** supported if the ratio ≤ 0.95 and its 95% upper bound < 1; contradicted if the 95% lower bound > 0.95.
- **H3 (job accessibility) is conditional.** It needs a pre-opening GTFS feed. None is archived on the Wayback Machine,
  and the Mobility Database needs an account, which will not be created without the lab owner's agreement. H3 runs only
  if a pre-opening feed is obtained; otherwise it is reported as not run.

## 6. Timeline and interim reporting

- **Now.**
  - Freeze this plan.
  - Compute the placebo calibration and the route-exposure classes, neither of which uses post-opening outcomes.
  - Publish an interim status.
- **About 6 weeks after opening.** An optional descriptive update with no hypothesis test.
- **Confirmatory analysis.** When AT's daily file covers 25 Mar 2027 (expected around early April 2027), and the
  monthly route file covers Mar 2027 (expected around April–May 2027).

## 7. Validity threats (fixed now)

- **Counting artefact.** Train boardings include line-to-line transfers, and through-running changes transfer
  patterns. Reported as a limitation, with the mode-specific series as a partial check.
- **Concurrent changes.** Bus network changes, fares or events. The same-calendar-window baseline and the disruption
  filter mitigate these; known changes will be listed.

## 8. Review and reporting

- An independent reviewer agent checks code and the confirmatory analysis before any verdict.
- The report opens with an "In plain terms" section.
- Derived tables are committed.
