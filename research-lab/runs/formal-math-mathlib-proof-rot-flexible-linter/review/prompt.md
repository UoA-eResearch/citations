You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/formal-math-mathlib-proof-rot-flexible-linter/ (read-only except your output
in review/).

**The question.** Do mathlib proofs that the FlexibleLinter flags (in a 2025-03-31 snapshot) fail more often when
replayed verbatim into the 2026-03-31 library (odds ratio at least 1.5)?

**Reported:** H1 Inconclusive. OR 1.48 (0.92–2.39); 43.6% against 25.1% failing. Secondaries: 6 months 1.67
(1.01–2.77); without unknown-identifier-only failures 1.62 (1.01–2.59); second pair 0.99; pooled 1.29.

**What to read:** plan.md, deviations.md (D1 before replay; D2 error classes after the first results), report.md,
code/ (rot.py, analyse.py, figures.py, run_all.sh, fetch_snap.sh) and results/tables/ (primary.json,
primary_v1.json). Snapshots are in data/snaps/<name>/ (with .lake caches), and work files in data/work/ (pop_*,
label_*, replay_* parquet; rewritten replay files in replay_<O>_<N>/; linter copies in label_<O>/).

**Git.** Read-only git is fine. Verify that the plan, D1 and analyse.py preceded replay results.

**Environment.** Use venv/bin/python with -I. Do NOT pip install. Lean is available via ~/.elan/bin (`lake env lean`
inside a snapshot directory). Keep at most 6 concurrent compiles; each mathlib file takes seconds to minutes.

Check at least:

1. **The parser** (`rot.parse`, `rot.features`).
   - Declaration spans, qualified names (namespaces and sections, including `public section`), statements, and
     proof-body extraction.
   - The non-terminal-simp detector.
   - Spot-check about 20 population declarations against the source, and look for missed declarations (`where`
     clauses, `termination_by`, nested `by`).
2. **Labelling.**
   - Is injecting the FlexibleLinter import into O faithful? Could it change elaboration?
   - Are warnings mapped to the right declaration? Check a few flagged cases by hand.
   - Is the 4% flagged share plausible?
3. **Replay.**
   - Substitution correctness. Diff a few rewritten files against N.
   - Error attribution by span after rewriting.
   - Do failures in one declaration cascade into others in the same file, so that later proofs fail spuriously? This
     matters a lot for the OR.
   - The timeout handling.
4. **Model.** GEE specification, exchangeable correlation, clustering, and the low flagged count. Is "Inconclusive"
   the right reading? Is the secondary pair's null properly weighed?
5. **D2.** Was the error-class fix legitimately secondary-only? Is the H1 statistic identical between v1 and v2?
6. **Report.** Check every number against the tables, and that the title and plain-terms section are fair.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7; this study predates the gates, so G5 and G6 were run as a pre-review gate).**
Verify:
- **G5:** `review/overclaim_check.md` passes and is honest.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check . --show`.
- **G1:** could the flag be correlated with the outcome through the population filter (statement-unchanged
  declarations)?
- **G2:** replay timeouts and files that failed to compile wholesale — counted, or silently treated as failures?
- **G3:** spot-check a few replayed proofs by hand (a G3 trace).

Report any gate that is missing or hollow as a finding.
