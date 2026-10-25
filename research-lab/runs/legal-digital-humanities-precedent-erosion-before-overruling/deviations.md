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
