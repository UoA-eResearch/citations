You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/formal-math-certified-contamination-did/ (read-only except your output). Read
plan.md (preregistration, commit 6bfdc63), deviations.md (D1-D8, including D3a/D3b), report.md (draft), code/
(extract.py, retrieve.py, certify.py, recheck.py, tiers.py, reform.py, sample.py, verify.py, analysis.py, figures.py and
the run_*.sh scripts), results/tables/ and results/figures/, logs/. Data are in data/ (statements/, candidates/,
certify/ incl. recheck_* files, reforms.parquet, samples/, verified/, invalid_D7/). Lean environments are in
../formal-math-selfplay-vacuity-drift/lean/ (Lean 4.9 Mathlib and Lean 4.15); the REPL client is
../formal-math-selfplay-vacuity-drift/code/lean_repl.py. Use the study's venv (./venv/bin/python). MEMORY: each Lean REPL
uses ~4 GB and can grow; use at most 4 REPL workers, cores 0-3 only (taskset -c 0-3). You may run read-only git commands
in /mnt/citations.

Check at least:
1. Leak certification soundness: re-check a random sample of L1 and L2 pairs (and some rejected ones) yourself in Lean.
   Are the guards (D3a hypothesis-free counterfactual, D3b explosion guard, fail-closed timeouts) correct and sufficient?
   Could any certified "leak" still be uninformative or spurious (e.g. elaboration differences, coercions, autoImplicit,
   pi substitution)? Are false negatives a big concern for the leak rates?
2. Reformulations: are R1/R2 genuinely equivalent and genuinely different surface forms? Is the certification sound?
3. Prover sampling and verification: are the prompts each model's documented format; is the statement-match check and
   the banned/axiom check correct; are tokenizer issues (D5, D7) fully resolved for the runs used (inspect decoded
   outputs); any other systematic verification failure (e.g. environment differences between provers)?
4. Was the preregistered decision rule applied correctly (DiD, bootstrap, MDE)? Recompute the primary result. Were the
   design changes in D2-D4 (cap, guards, clean subsample, token cap, STP) made before outcomes, and do they bias the
   result? Was anything decided after seeing the D7 preliminary result?
5. Does every number in report.md match the results files?
6. Interpretation: is "Refuted" stated with the right scope (surface rewording; DeepSeek's own corpus being only its
   public lineage; leak definition per prover)? Are the level differences (leaked items solved more often) hedged
   appropriately? What would an ML-evaluation / formal-methods expert object to? Use web search if useful (e.g. the
   Pythagoras-Prover ALF and "right symmetries" papers, decontamination practices of Goedel/Kimina/DeepSeek/STP).

Write your review to review/review.md with a recommendation (publish / publish with edits / fix first), numbered issues
with locations and concrete fixes, and a table of recomputed numbers. Reply with the recommendation and the number of
issues.
