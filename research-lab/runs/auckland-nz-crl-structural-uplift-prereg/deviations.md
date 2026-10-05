# Deviations and implementation choices

Each entry is timestamped with `date` when it was written. None of these entries used boardings from the 2027
confirmatory window, which did not exist when they were written.

## D1. Disruption rule at the start of the series (2026-10-03 20:52 NZDT)

Plan section 3 defines a disrupted day against the median of the same weekday over the preceding 8 weeks. The first 8
weeks of the series (July-August 2023) have fewer than 8 preceding values. For those days the reference is the median
of the first 8 same-weekday values. This affects only the earlier-year baselines of some placebo windows, not the
2024-2026 baseline windows or the 2027 window.

## D2. Minimum eligible days per window (first written 2026-10-03 20:52 NZDT; rewritten 2026-10-03 21:10 NZDT after review)

- **What changed.** The first version imposed no minimum and called that conservative. The reviewer showed this was
  only half true. Placebo windows over the Christmas weeks kept 1-2 eligible days and placebo uplifts of -0.54 to
  -0.22. Those windows set q05 and so lowered the Contradicted line, making the lead's hypothesis harder to contradict.
- **Rule now.** A placebo window needs at least 9 eligible days, both in the window itself and in each comparison-year
  window it uses; otherwise that comparison year, or the whole window, is dropped. 9 is half of the 18 Tue-Thu days in
  W_2027.
- **The same rule applies to W_2027.** With fewer than 9 eligible days, H1 is reported as not evaluable, and no U is
  computed.

## D3. Route matching for H2 (2026-10-03 20:52 NZDT)

- **Matching.** GTFS `route_short_name` is matched to `Route Num` in AT's monthly-by-route sheet (Mode = Bus).
- **Pre-period presence.** A route counts as present in the pre period only if it has boardings in all 6 months, Oct
  2025 to Mar 2026. The post period will use the same rule.
- **Station points.** The three new train stations are GTFS stops 131, 132 and 136, the parent "Train Station" points.
- **Radius classes.** The current feed's route distances show a natural gap between 800 m and 1,200 m: no route's
  nearest shape point falls in that band. The 800 m and 1,200 m classes are therefore identical, which the plan did not
  anticipate.

## D4. "Corresponding week" for U_open (2026-10-03 20:52 NZDT)

The plan compares 15-17 Sep 2026 with "the same weekdays of the corresponding week" in 2023-2025. This is
implemented as the Tue-Thu of ISO week 38, the week containing 15-17 Sep 2026: 19-21 Sep 2023, 17-19 Sep 2024 and
16-18 Sep 2025. All nine baseline days are eligible.

## D5. Disruption reference excludes holidays and disrupted days (2026-10-03 21:10 NZDT, after review)

- **The defect.** Plan section 3 sets the reference as "the median of that mode on the same weekday over the preceding 8
  weeks". Implemented literally, the reference for the first weeks of every 16 Feb - 25 Mar window includes the summer
  rail shutdown and the Christmas weeks. Inside those windows the 60% rule then behaved like a 14-47% rule, and real
  disruptions passed as eligible days: 17-18 Jan 2024, and 22 Jan 2026 (train at 38% of normal).
- **Why it matters for 2027.** An undetected bus disruption in W_2027 would raise the ratio and push the test toward
  Supported.
- **The rule now.** The reference is the median of the last 8 preceding same-weekday days that were neither public
  holidays nor themselves flagged as disrupted. Days are processed in date order.
- **Effect on results:**
  - No baseline-window day changes, so R_pre = 0.2218 is unchanged.
  - Three Tue-Thu days in placebo windows become ineligible.
  - Together with D2, the thresholds move: q05 -0.0658 -> -0.0572, q95 +0.0476 -> +0.0441, and the Contradicted line
    U < 0.1342 -> U < 0.1428 (ratio < 0.2515 -> < 0.2534). The Supported line stays at U >= 0.20 (ratio >= 0.2661).
- **No confirmatory data were involved.** The 2027 window does not exist; the change was made and its effect computed
  on pre-opening data only.

## D6. Disclosures about the placebo distribution (2026-10-03 21:10 NZDT)

- **Composition.** Of the 507 placebo windows, 150 have one comparison year, 325 have two and 32 have three. The
  2027 test uses three.
- **Effective sample.** The windows overlap heavily: about 13 independent 38-day blocks lie behind the quantiles.
- **Drift.** The 32 three-year windows (starts Jul-Aug 2026) are all positive (+2.0% to +3.5%). The mid-2026 ratio sat
  slightly above its three-year mean, within q95.
- **Where the details are.** results/tables/placebo_by_years.csv.

## D7. H2 caveats added before any post-opening route data (2026-10-03 21:10 NZDT)

- **Exposure uses a post-opening feed.** The feed is dated 17 Sep - 31 Dec 2026 (sha256 in data/SHA256SUMS). A route
  cut back from the city centre at opening would be classed unexposed. The reviewer found no such case among the 123
  unexposed matched routes, but it cannot be ruled out without a pre-opening feed.
- **Routes absent from the current feed.** 10 regular routes have pre-period boardings but are not in the current
  feed: 154, 172, 361, 503, 399, 933A, N10, QODTAK, Q SPEV and one "Unknown" row, together 1.3% of matched pre
  boardings. Two routes are new (42, 384), and 10 matched routes have fewer than 6 pre months (15, 17, 115, 311, 327,
  364, 37, 379, 39, 738). All are unexposed West or South network changes and are excluded under D3.
- **Feeder routes.** The unexposed group includes feeder routes to rail stations. These may gain riders from the CRL,
  which would push the ratio of ratios below 1 without any substitution on exposed routes. This caveat is reported
  alongside any H2 result.

## D8. Pinned inputs and code readiness (2026-10-03 21:10 NZDT)

- **Pinned inputs.** AT revises recent days between releases. The raw AT files used for the calibration are committed
  (force-added despite the data/ ignore rule, ~0.5 MB). Their SHA-256 sums, and the GTFS feed's, are in
  data/SHA256SUMS.
- **Month columns.** exposure.py now finds month columns by parsing their dates, and asserts that the expected
  number is present. The earlier version would silently have returned NaN for 2027 months.
- **Re-released daily files.** A re-released daily file replaces its entry in daily.DAILY rather than being added.

## Correction after publication (2026-10-06 02:34 NZDT)

The lab's self-audit (`research-lab/paper/`) found a misleading phrase in the report. "At 400 m, 37 routes (39%) are
exposed" read as if 39% were the share of routes. It is the share of pre-period boardings on those routes (0.394); 37
of 177 routes is 21%. The sentence now reads "37 routes are exposed, carrying 39% of pre-period boardings". No number
or conclusion changes.
