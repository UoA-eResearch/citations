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
