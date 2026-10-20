# Data collection started before preregistration (deliberately)

**Status: collecting only. No hypothesis has been tested and no analysis code has been written.**

Auckland Transport publishes its GTFS-Realtime feed live only. There is no public archive, so the pre-period of
the City Rail Link full-timetable step-up cannot be recovered later: it exists only if it is recorded now. The
lead (`movement-akl-crl-full-timetable-reliability` in `research-lab/leads.json`) says so, and its plan puts the
collector first and the preregistration second, once Auckland Transport announces the full-timetable date.

- **Started:** 2026-10-20 20:19 NZDT, by `code/collect.py` from cron, once a minute.
- **Opening:** the City Rail Link opened on 13 September 2026 on a reduced transitional timetable. Auckland
  Transport has committed to the full timetable within six months of opening, so about March 2027.
- **The plan will be preregistered before any outcome is computed**, and before the full-timetable date arrives.
  Nothing in this directory may be analysed until `plan.md` exists and is committed.

## What is recorded

| feed | cadence | why |
|---|---|---|
| `realtime/legacy/tripupdates` | every 60 s in service hours (05:00–00:59), every 30 s in weekday peaks (06:00–09:00, 15:30–18:30) | the legacy feed carries only the **next** stop per trip, so the polling rate sets how many stop events are seen; rail stops are 2–4 minutes apart, bus stops often less |
| `realtime/legacy/servicealerts` | every 15 minutes | cancellations and disruptions |
| `gtfs/v3/versions` | once a day | detects a timetable change |
| static GTFS zip (`gtfs.at.govt.nz/gtfs.zip`, no key needed) | whenever `feed_version` changes | the schedule each realtime message is relative to |

Every response is stored verbatim and gzipped under `data/gtfsrt/<date>/`, with one index line per call in
`data/gtfsrt/index_<ISO week>.jsonl` giving the fetch time, HTTP status, byte count and sha256. A failed call is
recorded as an error, never as absence. Static zips are checksummed in `data/static/SHA256SUMS`.

## The API key and its quota

The key is the owner's, read at run time from `~/.config/at/key` (mode 600). It is never written into this
repository, a log or an index line, and the pre-commit secret grep covers it.

The key allows 600 calls/minute and **35,000 calls/week**, and the owner's public map breaks if the weekly cap is
exhausted. This collector is held to about a third of it:

- trip updates ≈ 1,590 calls on a weekday and 1,200 at the weekend;
- alerts 80 a day, version check 1 a day;
- **≈ 10,900 calls a week (31% of the cap)**, leaving the rest free for the map.

`WEEKLY_CAP = 13000` in `code/collect.py` is a hard stop: before each call the collector counts the calls already
recorded in the current ISO week and skips if the cap is reached.

## Expected volume

About 94 KB gzipped per trip-update poll off peak (720 KB raw), so roughly 200 MB a day and about 40 GB by
March 2027. It is written to `/mnt/data` (HDD) and symlinked as `data/`.

## Known feed limitations (to carry into the plan)

- Only the next stop per trip is published, so stop coverage is a function of polling rate.
- Timestamps are sometimes implausible (Thomas Lumley's Auckland bots document entity timestamps hours in the past
  or the future), and drivers sometimes sign on to the wrong trip.
- Cancellations appear as service alerts with `NO_SERVICE` or `REDUCED_SERVICE`, some posted for future days.
- A VM restart kills nothing here (cron re-runs every minute), but gaps are visible in the index and must be
  modelled rather than ignored.
