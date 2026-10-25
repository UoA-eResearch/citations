# Deviations from the preregistration

## Technical

- **CSV dialect.** `idmap.py` first read the CourtListener dumps with Python's default CSV dialect. They use
  backslash escapes, so opinions split mid-field (406 million "rows"). It was fixed before any count; the
  phantom-citations study had recorded the same lesson.
- **Bootstrap deadlock.** The bootstrap's forked worker pool deadlocked: pyfixest thread pools in the parent. It now
  uses spawn workers. No logic changed.

## D1 — 2026-10-23 21:03 NZDT — a CourtListener coverage break (POST-RESULT: found after the primary result was read)

**The break.** Lower-court citations to Supreme Court clusters in CourtListener jump in 2019–2020
(`results/tables/scotus_cites_by_year.csv`):
- federal citations go from 126,788 (2018) to 234,605 (2019) and 384,806 (2020);
- state citations stay at about 40,000–50,000 a year.

This is a change in coverage (scraped federal opinions), not in citing behaviour. Calendar-year × stack fixed
effects absorb a common jump. They cannot absorb its interaction with a case's mix of federal and state citers. The
symptom is the out-of-sample Chevron path (secondary 6), which jumps to D = 0.55 at event −5 (2019) and stays near
0.8, with very narrow intervals.

**The added check (post hoc).** `event.py pre2019` repeats the primary analysis on stacks whose overruling year is no
later than 2013, with calendar years cut at 2018. Every window therefore lies before the break, and event +5 is
observed for every stack. It is reported beside the preregistered result and does not replace it.

## Pre-review gate (G5, G6) — 2026-10-25 22:43 NZDT, after all results (wording and attribution only)

The lab's METHODS.md gates were run before this draft's review. No number changed.
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 10 claims, passes):
  - **Feldman's essay was misattributed.** The lead and the report said it claims that *lower courts* stop relying on
    precedents before overruling, without statistics. The essay (SCOTUSblog, 16 June 2026) argues that the
    *Supreme Court* erodes precedents first, while lower courts often keep applying them. It does report citation
    and negative-treatment counts.
  - The report now frames the hypothesis as the lead's lower-court version and notes that the result is consistent
    with Feldman's account.
  - The unverifiable "5-year pre-window" detail of Broughman & Widiss (2017) is removed. Their finding (citations
    fall far more after overrulings than after overrides) is kept, with its DOI.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - the title now labels the clean-window result as post hoc;
  - "salience rises" becomes "citations rise";
  - the plain-terms answer now says it rests on a check added after the first result.

## D2 — 2026-10-26 10:02 NZDT — after independent review ("fix first"); POST-RESULT

The first version's tables are kept in `results/tables/v1_pre_review/`.

**Corrections that change inputs** (the whole pipeline after counting was re-run):
- **Controls follow the plan.** plan.md requires controls in the same SCDB issue area. The first version admitted
  clusters with no SCDB id (cert-denial orders, Harvard CAP duplicates: 81 of 672 controls). `event.py` now requires
  an SCDB id and the treated case's issue area.
- **Old-reporter cites.** `overruled.py`'s U.S.-cite pattern missed parentheticals such as "80 U.S. (13 Wall.) 29".
  It now accepts them.
  - The list grows from 132 to 141 pairs. Low v. Austin, Kentucky v. Dennison, Pace v. Alabama and Minturn v. Maynard
    enter the 1960–2024 range. The Schooner Catherine (58 U.S. 476) has no CourtListener cluster.
  - The treated count is 73 (was 71).
  - Every table row is now counted (G2, `results/tables/coverage.json`): 142 of 146 parsed, 4 dropped with
    reasons.
- **Coverage of the list.** SCDB leaves usCite blank for the 2016–2021 terms, so 13 recent alterations had been
  counted as missing. Matched by first-party name and year, 101 of SCDB's 174 alterations in 1960–2024 are on the
  list (58%), not "about half".
- **Unrecorded process facts:**
  - the Constitution Annotated table was attempted first, and `data/raw/conan_overruled.html` is a Cloudflare
    challenge page;
  - Wikipedia's page is self-tagged as an incomplete list, and favours famous overrulings;
  - the committed `event.py` (18acfb2) could not run (`d.stack` attribute access) and was patched in the results
    commit;
  - 4 treated cases are partial overrulings (Pollock, Yates, Ahrens, Teague);
  - the lead's own lit_against named the CourtListener coverage shift, so the break was foreseeable.
- **Balance** is reported as a distribution, not one mean.

**Re-run results.** The preregistered verdict is unchanged.
- **Primary:** D(+5) +0.29 (−0.05 to +0.51), so H1 is not testable. D(−1) is +0.21. The pre-share is 0.73.
- **Balance:** mean SMD 0.25, median 0.12; 30 of 73 stacks above 0.5, 9 above 1.
- **Excluding co-citing opinions:** D(+5) 0.66 (0.41 to 0.83), now clear of zero. The pre-share is 0.35 (−1.22 to
  0.81): Inconclusive by H1's rule.
- **Post hoc, pre-2019 (D1; 59 stacks):** D(−1) −0.52 (−0.96 to −0.18). The largest gap is −0.71, the year after
  overruling. D(+5) is +0.03.

**New post hoc analyses** (`code/posthoc_d2.py`, `results/tables/posthoc_d2.json`, labelled throughout):
- **The pre-2019 analysis is a sample restriction, not a window restriction.** Cutting calendar years at 2018
  changes nothing: D(−1) is −0.522 with all years and −0.521 with the cut (`posthoc_d2_yearcut.json`; the
  `yearcut()` step of posthoc_d2.py, run on its own). The difference from the primary comes from dropping the
  overrulings after 2013.
  - The break is in district-court citations only: 59,504 pairs in 2018 against 319,779 in 2020, with courts of
    appeals and state courts flat (F2). D1 had said "federal".
  - The direct fix keeps every stack and drops district-court citers: D(−1) −0.27 (−0.74 to −0.01), D(+5) +0.09
    (−0.26 to +0.37), 68 stacks.
- **Era.** The rise before overruling belongs to the 1960–89 overrulings: D(−1) −1.01 (−1.57 to −0.47), 42 stacks.
  - For 1990–2013 (17 stacks), D(−1) is −0.05 (−0.32 to +0.14) and D(+5) is +0.41 (+0.21 to +0.65). H1's
    precondition holds there, and the pre-share −0.13 (−1.22 to +0.31) is Refuted by H1's rule.
  - Without district-court citers: 1960–89 gives −1.05; 1990–2013 gives −0.17 (−0.51 to +0.03), with D(+5) +0.33;
    2014–2024 (13 stacks) gives +0.10, with D(+5) +0.51 (+0.11 to +0.68).
- **Weighting.** Stacked PPML weights stacks by citation volume. In the pre-2019 sample, the five most-cited stacks
  carry 49% of the treated pre-period citations.
  - Fitted alone, 68% of the 59 stacks have D(−1) below zero (median −0.26).
  - The pooled D(−1) without the 1, 3, 5 or 10 most-cited stacks is −0.43, −0.47, −0.39 and −0.42.
  - Fay v. Noia (372 U.S. 391), the fourth-heaviest, shows erosion (+0.35).
- **Chevron by court** (its matching is poor: SMD 1.28; 1.64 without district courts; 2.15 appellate only).
  - **Without district-court citers,** its relative decline grows gradually: 13% (2019), 22%, 24%, 29%, 36% (2023).
  - **Courts of appeals alone:** it is flat until a 45% drop in 2023.
  - The 2019 step is the coverage break, but a decline before Loper Bright remains.

**G1 leakage audit (added in D2; the study predates the gates).** Fields that could correlate with treatment, and
how the design handles them:
- **Matching** uses citations in event years −20 to −11 only, before the outcome window (−10 to +10).
- **The ≥ 50-citation filter** uses citations up to T0 − 1, inside the outcome window, for treated and controls
  alike. It binds on 6 treated cases.
- **Unlisted overrulings among controls.** Controls could include SCDB-flagged alterations that are not on the list
  (73 of 174). Such contamination would bias the comparison towards zero, and it is small.
- **Co-citation** of the overruling decision is mechanically linked to overruling. It is handled by the
  preregistered exclusion variant, whose post-overruling decline is partly mechanical and is reported as an upper
  bound.
- No LLM or agent judges any unit.
