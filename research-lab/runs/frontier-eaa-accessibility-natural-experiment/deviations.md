# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 16:04 NZDT — before any archived page was fetched

1. **Periods.** The lead compares Jan–Jun 2024 with Jan–Jun 2026. The plan uses four 2024 quarter-months as pre and
   2025-10, 2026-01 and 2026-04 as post, and excludes 2025-01 to 2025-07 as anticipation and transition, so remediation
   ahead of the deadline does not dilute the pre-period. The lead's literal windows are S5.
2. **Sample size.** The lead suggests about 12,000 sites with monthly snapshots. The plan draws up to 300 sites in each
   of 18 jurisdictions (about 5,400) at ten quarterly targets, to keep Wayback load polite. The event study keeps the
   time structure.
3. **H3 restated.** The lead's H3 asks what share of the measured improvement comes from sites that installed an
   overlay "rather than changes in the underlying markup". The outcome is measured without running scripts, so an
   overlay cannot change it, and every measured change is markup by construction. H3 therefore asks whether new overlay
   adopters improved their markup less (substitution), and S4 measures whether the Act drove overlay adoption.
4. **Sector labels by rules plus a blind agent check**, not by a local LLM. The adjudicator is the agent running the
   study (plan section 5).

## D2 — 2026-10-17 16:06 NZDT — after 7 CDX rows, before any archived page was fetched

1. **CDX collapse.** The first rows returned up to 24,693 captures per domain and the index began answering 503. Queries
   now ask for one capture per day (`collapse=timestamp:8`, the day's first). The rule picks the capture on the day
   closest to the 15th, and the first capture of that day when there are several, so the selected snapshots are
   unchanged; `n_captures` now counts days with a capture. The 7 rows already written were discarded and re-queried.
2. **Public bodies.** Those 7 rows included bundestag.de, bayern.de and uni-hamburg.de: public bodies the frame's
   label filter missed (it matches whole labels such as "gov" or "bund"). The plan excludes public bodies, which the
   Web Accessibility Directive has covered since 2018–2020, so `sector.py` now marks a site "public" and excludes it
   when its domain labels (gov, bund*, landtag, uni, univ, tu, stadt, gemeente, kommune, gmina, police terms) or its
   page title (ministry, parliament, government, municipality, university, police terms in 14 languages) mark it as
   one. The rule is applied before the sector rules, to the same earliest pre-period snapshot. The frame itself is
   unchanged; public counts are reported.

## D3 — 2026-10-17 16:13 NZDT — operational, before any archived page was fetched

The archive began refusing plain-HTTP connections to web.archive.org (port 80) after the first rows, while HTTPS
still answered (8–25 s per CDX query). `cdx.py` now queries over HTTPS; nothing else changes. The 7 rows already
written are valid and kept, since the job resumes by domain.

## D4 — 2026-10-17 16:46 NZDT — source changed from the Wayback Machine to Common Crawl, before any page was fetched

1. **Why.** About 30 minutes into the CDX job (116 of 5,400 domains), web.archive.org stopped accepting connections
   from this host altogether. Plain HTTP had already been refused (D3). The job was also recording failed queries as
   "no captures" (24 of the 116 rows), which would have silently dropped sites. It was stopped, and the 116 rows are
   discarded (`data/cdx/ia_partial_discarded.jsonl`). Even unblocked, the measured rate (about 3.6 domains a minute
   for the index, before any page fetch) meant days of load on the Internet Archive.
2. **Common Crawl instead.** Each target quarter-month maps to one crawl:

   | target | crawl |
   | --- | --- |
   | 2024-01 | CC-MAIN-2024-10 (Feb/Mar 2024, the first 2024 crawl) |
   | 2024-04 | 2024-18 |
   | 2024-07 | 2024-30 |
   | 2024-10 | 2024-42 |
   | 2025-01 | 2025-05 |
   | 2025-04 | 2025-18 |
   | 2025-07 | 2025-30 |
   | 2025-10 | 2025-43 |
   | 2026-01 | 2026-04 |
   | 2026-04 | 2026-17 |

   - **Lookup.** One index request per domain per crawl, a domain match filtered to the homepage URL, status 200,
     HTML.
   - **Pages.** Fetched by range request from data.commoncrawl.org (`code/cc_index.py`, `code/fetch_cc.py`).
   - **Unchanged:** the frame, the eligibility rule (≥ 2 of 4 pre, ≥ 2 of 3 post), the period labels, every
     outcome and analysis rule.
   - **Failures.** A failed request is recorded as an error and retried, never as absence.
   - **Staging.** Queries are staged (post crawls first, then pre, then anticipation and transition for eligible
     sites only). This saves requests without changing who is eligible.
3. **New selection to disclose.** Common Crawl obeys robots.txt, and many sites, notably publishers, block CCBot.
   Those sites are absent from every crawl and drop out as ineligible. Exclusion counts are reported by group and
   sector. Capture dates within a crawl vary by site; the capture timestamp is kept.

## D5 — 2026-10-17 18:55 NZDT — back to the Wayback Machine at one request at a time on a seeded half-sample, before any page was fetched

1. **Common Crawl was not usable.** Its index server answered only intermittently: about a third of requests failed
   with transient 400/502/504 errors, and it then refused connections from this host for about an hour. 11 domains
   were indexed (`data/cdx/cc_snapshots.jsonl`). They are discarded.
2. **The Wayback Machine is reachable again** (17 Oct, evening NZDT). To avoid another block:
   - `code/cdx_v2.py` and `code/fetch.py` now make one request at a time, 2 s apart, with hard backoff on
     429/5xx;
   - a failed request is recorded as an error and retried, never written as absence;
   - each job stops itself after 20 consecutive connection failures.
3. **Half-sample.** At that rate the full frame would take several days of archive load. The sample is a seeded
   (20261018) random 150 of the 300 sites per jurisdiction: 2,700 sites, of which 2,100 EU, 450 placebo and 150 UK
   (`data/frame/sample_d5.csv`, also in `results/tables/`, sha256 a8479b8bf0b33a6a…).
4. **Unchanged:** targets, eligibility (≥ 2 of 4 pre, ≥ 2 of 3 post), sector rules, outcome, analysis, decision rules.
   Lower power is the cost, and the report will give the achieved minimum detectable effect.
