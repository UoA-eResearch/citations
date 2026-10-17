# Confirmation pass: ancestral-tk-notice-machine-readability

Reviewer confirmation of the D5 fixes (commits 368e59e, ff5aaa3, 36306ce, 264d7bd, ffd5ac1; origin/main ffd5ac1),
2026-10-18. Checked against report.md, report.html, deviations.md, code/, results/tables/ and the data files; no new
live calls were needed. Recomputation on the D5 data files is in `review/reviewer_checks/recompute_v2.py` →
`recomputed_v2.json`.

## Recommendation: publish

Every number I recomputed from the D5 data files matches `results/tables/primary.json` exactly: H1 1 / 48,362
(exact CI 0.00005–0.0115%), without Neotoma 1 / 30 (0.084–17.2%, Inconclusive); H2 7,746 / 17,762 = 43.61%
(bootstrap 43.48–43.73%), Neotoma 43.8%, other publishers 65 / 226 = 28.76% (24.0–33.6%); leave-one-view-out
36.46–36.54% for the three citation formats, 37.37% without OpenAIRE, 49.1% without any other view; doi.org
formats only 49.83%; unavailable as drop 44.30%; JSON-LD as drop 54.8%; 7 distinct record patterns. The census
delta between `census_v1.jsonl` and `census.jsonl` is exactly the DMPTool record. None of the 100 hand-checked views
changed result under the re-score, so "all 100 scorer calls are right" still holds; the 7 changed views are the ones
listed in D5. The code for each rerun was committed before its outputs (ff5aaa3 and 36306ce before 264d7bd).

The four reasons for "fix first" are addressed: the view-list dependence is now the second sentence of the verdict
and has its own table; the citation-format mechanism is the first-rights-entry rule; "only one record anywhere" is
gone and the two Biocode DOIs are reported with an alternative count; the community name, the geography, the record
type and the HTML metadata are fixed. Five minor points remain (issues 2, 8, 16 and two new ones below); none needs
to hold publication, and all are one-line edits.

## Per-issue status

| # | issue | status | evidence |
|---|---|---|---|
| 1 | DataCite free text cannot see URIs; FN 10.48321/d190108951 | resolved | `census.py datacite_fields`, 13 field/scheme/domain/Notice-name queries; raw/datacite_fields 52 rows, 0 errors, 5 new DOIs, 1 element-bearing (the DMPTool plan); n = 48,362 / 30; D5.1; report "How it was done" and platform note |
| 2 | TERMS omit two Notice names and all Label names | partly (disclosed) | the two Notice names are queried; specific Label names are not, stated in D5.1 and under "Not shown". Acceptable: my probes of three names found nothing element-bearing |
| 3 | Zenodo count is an API-visibility artefact | resolved (disclosed) | platform table note; "Not shown: the Zenodo records whose rights entries its public JSON hides" |
| 4 | Harvard Dataverse structural zero | resolved | platform table note "no Local Contexts metadata block installed"; ADA named as the Dataverse source |
| 5 | GBIF machine tags not queried as planned | resolved (disclosed) | platform table note and "Not shown"; not in deviations.md, but visible in the report |
| 6 | RAiD: no TK-label key exposed; plural URI paths | resolved | platform note "no public RAiD exposes a TK label field"; `URI_RE` now `(labels?\|notices?\|projects?)` with category pages excluded (36306ce, before the rerun, D5.2) |
| 7 | re3data searches names/descriptions, not policies | resolved | platform table note |
| 8 | per-platform table with zeros/status; Wilson intervals, concentration by type/year, trend; stale census.log | partly | `platforms.csv` and the nine-row report table added. Per-platform Wilson intervals, concentration by resource type and year and the trend by year (plan section 4) are still absent and not logged as a deviation; `logs/census.log` still reads "zenodo 0 / raid 25" from the first run. Minor |
| 9 | error recording honest | n/a | unchanged, correct |
| 10 | Biocode 1.0 Label records; H1 alternative; detector to read rightsIdentifier | resolved | `H1_alternative_biocode` (3 / 48,362 Supported; 3 / 30 Refuted) in primary.json and the report; "anywhere" removed. The alternative is a hard-coded pair of DOIs in analysis.py rather than a detector rule; acceptable, as the report explains why the preregistered rule excludes them |
| 11 | H1 without Neotoma is Inconclusive by the rule | resolved | verdict block, H1 table, primary.json `verdict` |
| 12 | TK CB naming mismatch accurate; scheme as census key | resolved | wording kept; `rightsList.rightsIdentifierScheme:"Local Contexts"` is now one of the field queries |
| 13 | hyphenated Notice names | resolved | `NOTICE_RES` tolerant of `[ \-_]+`; notices 25 / 30 without Neotoma; 4 citation-format views drop → degrade (the iSamples "BC-Notice" records), H2 7,750 → 7,746 |
| 14 | precision re-adjudication; template-field sentence | resolved | "two universities have built Local Contexts fields into their templates"; platform note "2 of 65 filled" |
| 15 | three scorer misclassifications | resolved | `views.json_rights` parses Crosscite `rights_list` and OpenAIRE `bestAccessRight` / `instances[].license` / `accessRight`; `rescore.py` keeps `result_v1`; matrix now OpenAIRE 0 / 6 / 1,772 / 220, Crosscite 1,992 / 6 / 0 / 0 |
| 16 | citation formats: first-rights-entry mechanism | resolved, one clause to add | verdict block, scoring definition and results text rewritten. "All 17 sampled records that list the Local Contexts entry first carry it" is true of the text, but 6 of the 17 carry wording the detector cannot recognise (5 Attribution Incomplete, 1 Label template) and are scored drop, which is why the matrix shows 12 / 11 degrades, not 17. Add "11 recognisably; 6 as wording the detector does not recognise, scored as drops" |
| 17 | JSON-LD prose | resolved | "Only the URI's domain distinguishes…; the field asserts that both are licences"; "as drops, H2 would be 54.8%" (recomputed 54.84%) |
| 18 | oai_dc flattens typing | resolved | results bullet |
| 19 | unavailable handling | resolved | unchanged logic; "unavailable as drop 44.3%" in the sensitivity table |
| 20 | reviewer hand re-score | resolved | cited in "Hand check" |
| 21 | view-set sensitivity and candour | resolved | verdict block ("The crossing comes from the view list"), sensitivity table, 7 patterns, "What this does and does not show" |
| 22 | Neotoma dominance carried through | resolved | header, "The pooled verdict is Neotoma's", other publishers Refuted |
| 23 | Hub cross-check | resolved | `hub_check.py` (creator type only, no names), `hub_projects.csv` matches my probe (17 live, 3 404, 2 with Labels, 15 Notices only); "At the Hub" paragraph |
| 24 | D4 ordering and the e39b994 breach | resolved | D5.5; "with one exception noted in D5" |
| 25 | numbers match results files | resolved | every number in report.md and report.html matches primary.json, platforms.csv, view_matrix*.csv and hub_projects.csv; md/html number sets identical; F1 reads 28 |
| 26 | report.html meta description | resolved | template and page fixed (368e59e); the status line still says "pre-review draft" because it keys on `review/confirmation.md`, so rebuild report.html after this file lands |
| 27 | F1 caption | resolved | "the two figshare DOIs are registered but absent from DataCite's public index" |
| 28 | community name in the repository list | resolved | "three datasets from a community-led project"; no community named anywhere in report.md or report.html; "The Label is the community's own statement and is not evaluated here" |
| 29 | Tetiaroa, thesis, publisher variants | resolved | "Tetiaroa Society on Tetiaroa"; "thesis record"; "publisher name appears in two forms" |
| 30 | plain-language summary | resolved | strict-rule wording, 1,998, first-entry explanation, Hub sentence, "depends on which formats are counted" |
| 31 | absence by design given its due | resolved | now backed by the Hub cross-check |
| 32 | H2b wording | resolved | "None of these formats has a field for such a warning, and none was found" |

## Two small new points (do not block)

- **Platform table, "DataCite 52,012 records returned".** `analysis.py` sums the lines of `raw/datacite` and
  `raw/datacite_fields`; 47 of the 52 field-query records were already in the first file. Unique DOIs returned are
  51,965 (51,960 + 5). Write "51,965 (51,960, plus 5 new from the field queries)".
- **"Their 6 'degrade' calls are records whose repository put the notice in the description."** Four did (Landcare /
  GBIF and the three ADA datasets); two (10.5281/zenodo.13127018 / 13127019) put the Hub URI in
  `alternateIdentifiers`. Write "in the description or an alternate identifier".

## Reviewer files added in this pass

- `review/reviewer_checks/recompute_v2.py`, `recomputed_v2.json`: the first-pass recomputation rerun on the D5 data
  files (census.jsonl, views.jsonl after rescore.py); first-pass outputs are unchanged in `recomputed.json`.
