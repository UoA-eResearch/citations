# Deviations from plan.md

## D1 — 2026-10-28 13:17 NZDT — HIRDS depths from the point API; before any annual maximum or exceedance was computed

The owner supplied a key for ESNZ's HIRDS public API (`api.niwa.co.nz/hirds`, header `x-apikey`). A
`POST /report` with a latitude and longitude returns HIRDS v4's own tables at that exact point. One test point was
read (Auckland Airport, not a selected gauge), to learn the format. Changes:

- **Depths come from the point API at each gauge's coordinates,** not from the 2 km grids (plan section 2). This
  removes the "grid, not point" limit: the values are the ones HIRDS's point tables give.
- **AEP = 1/ARI is confirmed,** not inferred: the API's table lists the 10-year ARI as AEP 0.100, and 1.58 years as
  0.633. The 1 − e^(−1/ARI) sensitivity is dropped.
- **The climate-adjusted secondary is restored.** The API returns RCP2.6/4.5/6.0/8.5 depths for 2031–2050 and
  2081–2100. The lead's secondary uses RCP4.5 2031–2050, and RCP8.5 2031–2050 is added for range. These are
  descriptive comparisons, not hypotheses.
- **HIRDS's standard errors** (the API's "Depth standard error" table) are carried as a sensitivity: the O/E is also
  computed against depth minus and plus one standard error.
- **HIRDS's site list** (`GET /sites`, 3,344 sites, with the years each contributed and its data source):
  - **G1 check:** any selected gauge matched to a HIRDS site (within 100 m) whose listed coverage runs past the
    2016/17 water year has its out-of-sample start moved after that coverage. This is decided from the listed years
    alone.
  - **Secondary:** O/E for gauges that were among HIRDS's fitting sites against gauges that were not.
- **The grid order on DataHub is no longer needed.**

## D2 — 2026-10-28 13:39 NZDT — how completeness, resolution and quality codes are read; before any annual maximum

Fixed from the structure of the fetched series only: time stamps, whether a record is zero, and quality codes
(`code/structure.py`, `results/tables/series_structure.csv`). No annual maximum, exceedance or HIRDS depth had been
computed or read for any gauge.

**What the data are.**
- **Hilltop "incremental" series:** each record's value is the rain since the previous record.
- **No explicit gap markers.** The servers mark no gaps; a test request showed that their own aggregation spreads a
  long interval's total evenly across it.
- **Two logging styles.**
  - Some gauge-years log a record at least hourly in dry weather (1,486 of 4,862 gauge-years spend under 0.5% of
    their time in 1-hour to 7-day silences).
  - Others log only around rain (1,608 spend over 40% of their time in such silences).
  - In the second kind, a silence closed by a zero is, by the councils' convention, a dry spell. An outage closed
    the same way cannot be told apart from one.
- **Any filter on silences is biased.** A completeness filter that treats such silences as missing removes dry
  years preferentially. That would inflate exceedance rates, so silences are bracketed, not filtered.

**Rules (all durations).**
1. **Quality** (plan section 1). Records coded 1xx (missing), 2xx (not verified) or 3xx (synthetic), by the NEMS
   hundreds digit, are excluded. Their interval counts as unknown time. Code 0 (no code assigned; most of
   Wellington's archive) and 4xx–6xx are kept.
2. **Resolution** (plan section 1's limits).
   - A wet interval (value > 0) is resolved for duration d if it is no longer than 15 minutes (6 h), 5 minutes
     (1 h) or 60 minutes (24 h).
   - Resolved rain is spread evenly over 5-minute bins.
   - Unresolved rain counts as unknown time for d. For the point estimate it is spread evenly over its interval,
     as the councils' own aggregation does.
3. **Dry intervals** (value 0).
   - In a "dense" gauge-year (no more than 2% of its time in 1-hour to 7-day silences), any interval over 60 minutes
     is an outage: unknown time.
   - In other gauge-years it is dry, by the councils' convention.
4. **Complete water year:** at least 90% of its time is known for d (plan).
5. **Exceedance.** The annual maximum is the point estimate (rule 2). An upper bound adds, to each window, the full
   amount of every unresolved interval that overlaps it.
   - A gauge-year is "undetermined" if the point estimate is below the HIRDS depth and the upper bound is not.
   - The primary counts it as not exceeding.

**Sensitivities, reported beside the primary.**
- **S1:** undetermined gauge-years counted as exceedances (an upper bound on O/E).
- **S2:** zero-closed silences over 14 days are unknown time in every gauge-year. This brackets hidden outages from
  the other side.
- **S3:** 2xx (not verified) data are kept. This adds most of the West Coast's record and the provisional recent
  years.
- **S4:** code 0 and 4xx (poor) are excluded as well.
