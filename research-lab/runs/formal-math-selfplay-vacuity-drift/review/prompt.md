You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/formal-math-selfplay-vacuity-drift/ (read-only except your output). Read plan.md
(preregistration, commit 86f1489), deviations.md (D1-D6), report.md (draft), code/ (lean_repl.py, vacuity.py, sample.py,
sample_other.py, run_rows.py, repair_split.py, analysis.py, controls.py, figures.py), results/tables/, results/figures/,
and the row-level outputs results/rows/*.jsonl (large; sample them). The Lean environments are in lean/ (mathlib4 for
Lean 4.9; mathlib4_v415 for Lean 4.15; the REPLs in repl/ and repl_v415/). You may run the study's venv python and the
Lean REPL through code/lean_repl.py to re-check certificates. You may run read-only git commands in /mnt/citations.

Check at least:
1. Is the vacuity certificate sound? Re-check a random sample of certified-vacuous rows and of non-vacuous rows yourself
   (compile the certificate; inspect axioms). Could the goal-swap or automation produce a "certificate" that does not
   actually show the hypotheses are contradictory (parser errors, binder loss, autoImplicit, universe or instance issues)?
2. Was the preregistered decision rule applied correctly? Are weights, variance and the RR CI computed as the plan states?
3. Are exclusions (re-verification failures, split failures, repair) handled as preregistered, and could they bias the
   primary contrast (check exclusion rates by iteration)?
4. Are the deviations justified and disclosed, and did any change follow sight of outcomes?
5. Does every number in report.md match the results files? Recompute the key ones.
6. Are the interpretive claims (pass-rate filter mechanism, training weight explanation, NuminaMath win-rate inference)
   supported or appropriately hedged?
7. What would a formal-methods / ML-for-theorem-proving expert object to? Use web search if useful (e.g. related work on
   vacuous statements in autoformalization benchmarks).

Write your review to /mnt/citations/research-lab/runs/formal-math-selfplay-vacuity-drift/review/review.md with a
recommendation (publish / publish with edits / fix first), numbered issues with locations and concrete fixes, and a
table of recomputed numbers. Reply with the recommendation and the number of issues.
