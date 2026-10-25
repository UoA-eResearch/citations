You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/metascience-retraction-citer-contagion/ (read-only except your output in
review/).

**The question.** Do unrelated works that cited a later-retracted paper (depth 1), and citers of those works (depth
2), lose citations after the retraction, more so for misconduct?

**Reported:**
- **Preregistered DiD:** +0.068 (exposed gain), with a clear pre-trend. H1 Inconclusive by rule; H2's contrast
  "Supported" by the letter of the rule but declared not testable, because both penalties are negative; H3 Refuted.
- **Post hoc design B** (not-yet-treated controls citing papers retracted after T+4, matched to T−1): depth 1 +0.003
  (−0.015 to +0.021), depth 2 +0.010. The claim is that there is no collateral penalty.

**What to read:** plan.md, deviations.md (D1), report.md, code/ (build.py, run_build.sh, analyse.py, posthoc.py,
posthoc_b.py, figures.py) and results/tables/ (primary.json, posthoc.json, posthoc_b.json, event_profile*.csv). The
data are in data/interim/ (d1, d2, candidates*, cites*, pairs, retracted, rw, citers1/2 parquet). The OpenAlex
snapshot is /mnt/data/ubuntu/impact-snapshot/works (read-only).

**Git.** Read-only git is fine. Verify that plan.md and analyse.py preceded the results, and that D1's design B text
preceded posthoc_b outputs.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. Keep CPU to at most 8 processes; full
snapshot passes take about 10 min with 14 workers, so avoid them unless essential. Put scripts under
review/reviewer_checks/.

Check at least:

1. **Construction.**
   - Retraction Watch DOI matching and the reason classes against the plan's list.
   - The exposure window (T−6..T−2); the overlap exclusion (OpenAlex author and institution ids; are empty
     institution lists a loophole?); earliest exposure.
   - The depth-2 sampling, and the "not citing r" rule.
   - Citation counting (counting citing works by publication year; self-citations included?).
2. **Controls and matching.**
   - Candidate pools; the caliper; nearest matching with replacement.
   - Design B's pool: works whose earliest cited retraction is after T+4. Is this defined correctly (first_ret
     uses only Retraction Watch-matched works)? Could unknown or never-retracted citations leak in?
   - How many exposed works lose a match in each design, and does that selection matter? Design B keeps 3,203 of
     4,355 depth-1 retractions.
3. **Estimation.** The pair DiD, the retraction-level averaging, the bootstrap, and the event profiles. Is the "kink
   at the matching anchor" explanation right? Check whether exposed and controls differ in growth rate before T.
4. **Interpretation.**
   - Is "no collateral penalty" justified by design B, given its assumptions and smaller sample?
   - Is the H2 "not testable" call legitimate, or a post-result redefinition?
   - Is the honest-error +0.054 handled fairly?
   - Should H1's verdict be stated differently?
5. **Report.** Check every number against the tables, and that the title and plain-terms section are fair.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7; this study predates the gates, so G5 and G6 were run as a pre-review gate).**
Verify:
- **G5:** `review/overclaim_check.md` passes and is honest (the headline rests on post hoc design B).
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check . --show`; spot-check
  claims, including the replaced Cor and Sood citation.
- **G1:** do not-yet-treated controls share any label-correlated structure with the exposed works (for example the
  same retraction cluster or authors)?
- **G2:** silent drops in matching (unmatched exposed works counted?).

Report any gate that is missing or hollow as a finding.
