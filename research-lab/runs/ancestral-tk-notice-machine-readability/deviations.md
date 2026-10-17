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

## D4 — 2026-10-18 05:56 NZDT — H2 excludes DOIs judged not genuine; hand check done, before H2 was computed

- **The hand check.** 100 record-views were checked by hand (plan §3; `code/handcheck.py`,
  `results/tables/handcheck.csv`). The sample was stratified by view, with each view's rare calls oversampled. All
  100 scorer calls are right under the preregistered URI-or-name definitions.
  - **Notes.** In two views of one DOI, the Attribution Incomplete Notice's wording survives without its name or URI.
    That is a drop by definition, and invisible to a machine. Several "degrade" calls are inherited from the source
    record, which puts the notice in the description rather than in the rights list.
- **The exclusion.** The views sample was drawn before the free-text hits were adjudicated, and two of its DOIs were
  later judged not genuine: a conference abstract and its version (10.5281/zenodo.17496296 and 17496297). H1 already
  drops adjudicated false positives. H2 now does the same, so its denominator is element-bearing records only. Of the
  other 1,998 DOIs, none were judged not genuine.

## D5 — 2026-10-18 06:47 NZDT — corrections from the independent review (review/review.md)

1. **Census recall (review issues 1–2).** DataCite's free-text query indexes URIs as domain tokens, so
   `query=localcontexts` cannot see a Hub, Notice or Label URI outside rightsList.
   - **The fix.** A supplementary pass, `census.py datacite_fields` with 13 queries, adds field-wildcard queries over
     descriptions, relatedIdentifiers, identifiers, alternateIdentifiers, subjects and rights text. It also queries
     the "Local Contexts" rights scheme, the two domains, and the two Notice names the first run omitted.
   - **Result.** It finds one more element-bearing record, a DMPTool plan with a Hub project in relatedIdentifiers,
     so the denominator is 48,362, and 30 without Neotoma.
   - **Name-only recall** still covers only generic names. Specific Label names were not searched; the review's probes
     of three found nothing element-bearing.
2. **Detector (review issues 6, 13).**
   - Notice names are matched with hyphens or underscores ("BC-Notice").
   - Plural URI paths (/labels/, /notices/) are matched, except category pages such as
     /labels/traditional-knowledge-labels/, which name no element. The plural pattern first caught one such reference-
     list citation; the exclusion was added before the analysis was rerun.
3. **Scorer (review issue 15).** Crosscite JSON and OpenAIRE rights fields are now parsed as JSON rather than read
   through regex windows. All 18,000 saved bodies were re-scored offline (`rescore.py`; first-run scores kept as
   `result_v1` and in `views_v1.jsonl`).
   - **Changes.** 3 corrected calls (OpenAIRE preserve → degrade ×2; Crosscite degrade → preserve ×1), and 4 citation-
     format views (drop → degrade) where "BC-Notice" is now recognised.
4. **Further analyses (review issues 8, 10, 11, 21, 23).**
   - a nine-platform table with status (`platforms.csv`);
   - H1 without Neotoma, with its verdict by the same rule;
   - an alternative H1 count including the two Moorea Biocode 1.0 DOIs, whose rights entries carry a BC Label's
     template text and a live Hub project where that Label is applied;
   - an H2 view-set sensitivity: leave one view out, the doi.org formats only, and the views with a rights field;
   - a Hub cross-check of every linked project (`hub_check.py`; creator type only, no names).
5. **The D4 ordering, restated (review issue 24).** D4 came before `analysis.py` was run, but the per-view result
   distribution was necessarily seen when the hand-check sample was stratified. The by-stratum table was added to
   `analysis.py` in the same commit as its outputs, a small breach of code-before-outputs. That table implements
   plan §4, and changes no verdict.
