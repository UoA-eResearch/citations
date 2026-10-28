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

## D3 — 2026-10-28 13:50 NZDT — a structural resolution test, earlier in-sample years, and coordinates; before any exceedance

Found while testing `code/maxima.py` on four gauges. HIRDS depths for 20 Hawke's Bay gauges had been fetched, to
test the API client, but no annual maximum had been compared with any depth.

1. **Resolution is tested on the logging, not on wet time alone.**
   - Under D2 rule 2, only coarse *wet* intervals count as unknown time. An hourly gauge (Leigh 2 EWS, which logs
     hourly totals after 2019 and daily 9 am totals before) therefore reaches about 90% known time in drier years
     and fails in wetter ones. That would be a rainfall-dependent filter.
   - **New rule:** a gauge-year qualifies for duration d only if the median interval of its wet records (its native
     resolution) is no longer than d's limit: 15 minutes (6 h), 5 minutes (1 h) or 60 minutes (24 h). The plan's
     resolution limits are unchanged; this is how they are applied.
   - The median is used, not a share. The first light tip after a dry silence carries a long interval, which a share
     would count against fine-resolution gauges.
2. **In-sample years start in 1995/96.**
   - The plan sets no start for the in-sample control ("water years up to 2014/15") and requires 10 complete
     in-sample years.
   - The first fetch began in 2005/06, which allows at most 10. Water years 1995/96–2004/05 are now fetched for the
     207 candidate gauges whose records start earlier (`code/fetch.py PER_SERVER early`). That gives the control a
     fair sample.
   - The out-of-sample test is unaffected.
3. **Coordinates.** Hawke's Bay's Hilltop server gives NZ Map Grid (EPSG:27200) coordinates; the other six give
   NZTM2000 (EPSG:2193). This was verified by matching gauge names to HIRDS's own site list (median distance 0.2 km
   and 0.0–0.1 km). Gauges with missing coordinates, or coordinates outside New Zealand, get no HIRDS depth and are
   counted (G2).

## D4 — 2026-10-28 14:40 NZDT — Auckland Council gauges added; before any exceedance

Plan section 1 names Auckland Council's Environment Auckland portal as a source. Its click-through terms include an
indemnity clause, so the lab asked the owner, who agreed on 2026-10-28 ("Add Auckland").
- **What is used.** Rainfall datasets whose record span covers the out-of-sample window (70 candidates of 254
  listed), from `code/fetch_auckland.py`: points as recorded (tips and logged zeros), NZST, with grade codes.
- **Grade codes are NEMS.** A long-record gauge (Hoteo at Oldfields) is graded 500 from 2005 to 2026, so D2's
  quality rule applies unchanged.
- **NaN values.** The portal's export writes "NaN" for some records. These count as missing records: unknown time
  and no rain, like a 1xx code (`maxima.py`). No Hilltop series has any.
- **Terms.** Auckland Council is acknowledged as the data source in the report. Raw series stay under `data/`
  (not in git); only derived results are published.
- **G1.** HIRDS v4 fitted Auckland Council data to early 2017, so matched HIRDS sites listed past 2016 move that
  gauge's out-of-sample start (analysis rule from D1).
- **No result had been seen.** The council maxima had been computed, but no annual maximum had been compared with
  any HIRDS depth, and no exceedance or O/E computed.

## D5 — 2026-10-28 15:16 NZDT — a data-reader bug found by the G3 checks after the first full run; all series refetched

**What happened.**
- The first full analysis ran at about 15:15. Its results were seen before the bug was found:
  - H1: O/E 1.29 (0.65–2.07), Inconclusive;
  - in-sample control: 0.81 (0.61–1.03);
  - Wellington: 0.13.
- Wellington's implausible value prompted a check of its series. Annual totals were steady while 6-hour maxima fell
  by about a third after 2015, the years when several gauges moved to 0.2 mm buckets.
- **Cause.** `fetch.py` (and `fetch_auckland.py`) truncated time stamps to the minute, then dropped records sharing a
  minute. That step was meant only for the one boundary record that consecutive yearly windows share. It also
  discarded genuine tips in the same minute, i.e. rain in the most intense bursts.
- **Measured** on Akatarawa River at Cemetery, 2022/23:
  - 51,396 raw records against 49,612 stored;
  - 2,227 mm against 1,873 mm (16% of the year's rain lost);
  - the 6-hour maximum 38.6 against 36.6 mm.
- The loss grows with tip frequency and bucket resolution, so it biased exceedance counts downward and unevenly
  across councils and years.

**Fix (mechanical; no analytic rule changed).**
- Times are kept to the second (stored as fractional minutes).
- Only the shared boundary record of consecutive windows is dropped, matched by its exact time.
- Nothing else is de-duplicated, and the early-years splice drops only the 2005-07-01 boundary record.
- All Hilltop and Auckland series are refetched, and the maxima and analysis re-run with the same code otherwise.
- The invalid tables are kept in `results/tables/v0_invalid_minute_dedupe/` for the record, and the report states
  what the first run showed. `series_structure.csv` (the D2 description) came from the truncated series. D2's
  thresholds were set from its clearly bimodal shape and are kept.

**Why G4 missed it, and the added check.** G4's 30 recomputed maxima read the same stored series, so they could not
catch a reader bug. G4 now also refetches 10 random gauge-years raw from the servers and compares record counts and
totals with what is stored.

## D6 — 2026-10-28 16:48 NZDT — a physical-plausibility screen, added after the corrected results (found while building the next lead)

**What was found.** Building the FENZ lead on these series turned up impossible values. Checking this lead's own
included gauge-years found a few in its primary set too:
- 998 mm in one 10-minute record (Motueka at Western Boundary, 2019/20; code 0);
- 730 and 431 mm in 10-minute records (Wakapuaka at Hira Forest, 2019/20);
- 327.6 mm in one 15-minute record (Lake Waikopiro buoy, 2018/19);
- a stuck sensor reporting exactly 5.2 mm every 5 minutes for days (Lake Tutira buoy, 2020/21).

At 6 hours, three included gauge-years exceeded twice their HIRDS 250-year depth. These are false exceedances, and
plan section 1's quality rules (NEMS codes) do not catch values coded 0.

**The screen** (`maxima.py` physical_bad; rule fixed before re-running). A record counts as missing (unknown time,
no rain) if either:
- it exceeds 50 mm in an interval of 15 minutes or less, or 150 mm in one of an hour or less (beyond New Zealand's
  short-duration records); or
- it belongs to a run of 24 or more consecutive identical values of at least 2 mm (a stuck sensor).

**Handling.**
- The tables before the screen are kept in `results/tables/v1_before_screen/`, and the report gives both.
- This is a correction found after results. The rule is generic and does not depend on any exceedance. It removes
  records, so it can only lower O/E or make gauge-years incomplete.
