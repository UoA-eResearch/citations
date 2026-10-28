# Deviations from plan.md

## D1 — 2026-10-25 02:29 NZDT — after primary.json: a pre-trend, an uninterpretable H2 contrast, and post hoc designs

1. **The preregistered DiD fails its parallel-trends premise.**
   - Matched on citations up to T−2, exposed works outgrow their controls between T−2 and T−1: the event-year
     profile is −0.083 at T−2 relative to T−1 at depth 1, and −0.108 at depth 2.
   - The preregistered estimator (post mean minus pre mean) is therefore positive (+0.068, 95% interval 0.054 to
     0.082).
   - Its verdicts are reported as computed: H1 Inconclusive (by rule), H3 Refuted (the interval excludes 0).
2. **H2's contrast is uninterpretable here.** C = P_misconduct − 2 P_honest is meaningful only when both penalties
   are positive. Both are negative (gains of 0.060 and 0.088), so C > 0 (0.116; 0.026 to 0.205) comes from the
   honest-error group's larger gain. The rule's output, "Supported", is reported but **not** claimed as support.
   H2 is treated as not testable.
3. **Post hoc design A** (`code/posthoc.py`, labelled post hoc). Matching on the trajectory up to T−1 (cumulative
   citations by T−1, and citations in T−1 and T−2), with the effect measured as the mean over T+1..T+4 minus the
   difference at T−1. Pre-trends are then flat.
4. **Post hoc design B** (planned now, before it is run). Not-yet-treated controls: works in the same source and
   year that cite only papers retracted after T+4. They share the "cites retracted work" trait without being
   treated in the window. This separates a retraction effect from membership of the citing network.

## Pre-review gate (G5, G6) — 2026-10-25 22:54 NZDT, after all results (wording and attribution only)

The lab's METHODS.md gates were run before this draft's review. No number changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - the title and plain terms now say the no-penalty result comes from a post hoc comparison;
  - "standing" became "citations";
  - "no one had checked" became "no study we found had estimated".
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 8 claims, passes):
  - "Cor and Sood 2022" (continued citation of retracted papers) could not be found in OpenAlex. It is replaced by
    Hsiao & Schneider (2021, QSS), the lead's verified source for the same point;
  - Lu et al. 2013, Jin et al., Azoulay et al. (RESTAT 2015, DOI 10.1162/rest_a_00469) and RealSpill (Zenodo
    23607726) resolve.

## D2 — 2026-10-28 13:42 NZDT — after the independent review (publish with edits): interpretation, sample reporting and undocumented details; no estimate changed

1. **D1.1's reading is replaced.** D1.1 says exposed works "outgrow their controls between T−2 and T−1". They do
   not outgrow them. The raw exposed-minus-control gap is flat up to the matching year (+0.005, +0.013, +0.001 at
   T−4, T−3, T−2), then steps to +0.083 at T−1 and slowly closes.
   - That is regression to the mean: citers of later-retracted papers sit at a higher citation level than clean
     controls with the same early counts, and the gap opens in the first year the match leaves free.
   - In design A the step lands on T. It is +0.116 for works published at T−2 and +0.035 for works published at
     T−4 or earlier, fading to +0.005 by T+4.
   - On the same 6,056 exposed works, clean controls give +0.085 and not-yet-treated controls +0.008.
   - Unmatched, exposed works sit 0.49 log points above their clean candidate pool in citations to T+4, but 0.06
     below their not-yet-treated pool.
   - Source: `code/posthoc_review.py` (post hoc, after the review) → `results/tables/posthoc_review.json` and
     `gap_profiles.csv`.
2. **Implementation details that plan.md did not state** (found by the review; no estimate changes):
   - exposed works that OpenAlex flags as retracted were not excluded (137 at depth 1, 57 at depth 2);
   - depth 2's "not citing r" is implemented as citing no Retraction Watch-retracted work at all, which is stricter;
   - self-citations are included in citations per year;
   - citations with a null publication year count towards the cumulative pre-period metric (7,996 of 139.9 million);
   - `R.T` became `R["T"]` in `analyse.py` after the data existed. This is a crash fix with no analytic content.
3. **Reason-class gaps.**
   - The plan's label "Plagiarism of Article" does not occur; the file's label is "Plagiarism of/in Article".
   - Several misconduct labels are absent from the plan's list, including "Falsification/Fabrication of Results",
     "Manipulation of Data/Results", "Euphemisms for Misconduct" and "Taken via Peer Review".
   - Within 2000–2021, 1,011 usable retractions classed "other" would be misconduct, 184 of them at depth 1. No
     honest-error retraction is affected, so H2 and the design-B honest estimate do not move.
   - The classes are left as preregistered and the gap is reported as a limit.
4. **Post-review additions.**
   - `code/coverage_report.py` → `results/tables/coverage.json` (G2) and `selection.json`: analysed works per
     design and depth, why the rest drop, and the analysed works' citation levels.
   - `results/plausibility.md` (G3).
   - The G5 and G6 ledgers are updated for the rewritten report. The review's suggested prior work, Madlock-Brown and
     Eichmann (2014), studies citation of the retracted articles themselves, so it does not contradict the absence
     claim.
