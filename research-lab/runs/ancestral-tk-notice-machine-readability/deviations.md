# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 19:03 NZDT — before any census query or machine-view fetch

1. **Testing without seeing outcomes.** API syntax was checked on a neutral term ("pollen"), not on the study's
   search terms. The crosswalk scorer was tested on the one DOI the lead itself documents (10.21233/7mmk-mr58). That
   test found the Crosscite JSON key is `rights_list`, and the pattern was fixed before any sample was drawn.
2. **OSF/SHARE search returned 503 on 2026-10-17.** `census.py` records the platform as unavailable if it still
   does, rather than dropping it silently.
3. **The lead's "aggregator copies"** become the OpenAIRE Graph record only. BASE needs registration, and Google
   Dataset Search has no API.
4. **H2 unit.** The lead's "≥ 40% of the standard machine views" is made precise as record × view pairs, with a
   record-cluster bootstrap.
5. **Engagement** with Local Contexts, the repositories and Māori and Pacific data-governance advisers is a care note,
   not a gate (lab policy, 2026-10-16). The report frames counts as describing systems, not communities, and says
   that DOI-layer absence may be by design.

## D2 — 2026-10-17 20:20 NZDT — Zenodo page-size bug, before the census was scanned

The first census run asked Zenodo for 100 records per page. Anonymous requests are limited to 25, and the API
returned HTTP 400, which `census.py` treated as "no more results", so Zenodo was logged with 0 records. That is a
failure recorded as absence. Fixed: the page size is now 25 (up to 400 pages, Zenodo's 10,000-result cap), and every
paged platform writes an explicit error marker if its first page fails. `scan` reports those errors in
`data/census_errors.json` instead of counting them as zero. Zenodo is re-run. Any other platform that returns 0 records in
the first run is re-run under the new code, so a failure would show as an error marker.

## D3 — 2026-10-17 23:03 NZDT — RAiD paging, before the census was scanned

The first run fetched only RAiD's default first page (25 of 622 records). The public endpoint pages with
`limit=100` and `cursor=<pageInfo.endCursor>`, and `raid()` now follows it, with an error marker if the first
page fails. re3data's 0 was checked: the API returns an empty list with status 200, a genuine zero. Zenodo is re-run
under the D2 fix.
