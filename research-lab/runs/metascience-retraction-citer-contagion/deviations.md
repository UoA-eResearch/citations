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
