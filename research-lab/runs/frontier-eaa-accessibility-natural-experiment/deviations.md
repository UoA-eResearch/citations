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
