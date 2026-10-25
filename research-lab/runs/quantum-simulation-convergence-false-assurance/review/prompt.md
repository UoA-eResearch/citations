You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/quantum-simulation-convergence-false-assurance/ (read-only except your output
in review/).

**The question.** Among approximate simulations whose two finest truncation settings agree within 0.01 ("apparently
converged"), how often is the true error above 0.03?

**Reported:**
- H1 Supported: Pauli propagation 40/129 = 31% (23–39%); BP-PEPS 2/103 = 1.9%.
- H2 Supported pooled: BP 93%, PP 87% coverage. But PP within Floquet is only 79%.
- PP false assurance concentrates in Floquet circuits (39/51) and hexagon-based patches. It is a shrinkage toward
  zero.

**What to read:** plan.md, deviations.md (D1 before approximate results, including the ladder freeze; D2 = a sort bug
in analyse.py found after the first results), report.md, code/ (instances.py, approx.jl, run_ladder.sh, analyse.py,
figures.py) and results/tables/ (primary.json, instances.csv, primary_v1_coarsest_pair_bug.json). Data is in data/ (a
symlink to /mnt/qsim): instances/*.json, results/exact_*.json, results/{pilot,main}/*.json.

**Git.** Read-only git is fine. Verify that the plan, D1 (including the ladder freeze) and analyse.py preceded main
results, and check what D2 changed.

**Environment.**
- Python: venv/bin/python with -I. Do NOT pip install.
- Julia: `JULIA_DEPOT_PATH=/mnt/qsim/depot ~/.juliaup/bin/julia --project=/mnt/qsim/env`.
- Keep compute modest: at most 8 cores, and 20 qubits or fewer for any statevector re-runs.

Check at least:

1. **Physics and convention consistency** across instances.py (numpy and aer), approx.jl (TNQS and
   PauliPropagation):
   - rotation-angle conventions (exp(-i t P/2)), Heisenberg ordering in the layer-chunked PP, qubit indexing, and the
     observable;
   - re-derive a few main-set values independently (for example a 20-qubit instance with your own small statevector).
2. **PauliPropagation semantics.**
   - Is min_abs_coeff truncation applied as described?
   - Does PauliRotation(:X, q) with angle t equal qiskit's rx(t)?
   - Could chunked propagation differ from a single propagate call beyond truncation-order effects, and does that
     matter?
   - Is the shrinkage-to-zero finding an artefact?
3. **BP-PEPS.**
   - apply_gates options, the cutoff, normalize_tensors = false, BP expectation without boundary MPS.
   - Is χ = 16 really "finest" after the freeze rule, and was the freeze rule applied as written (median over all
     pilot instances)?
4. **Patches.** The D1 hexagon-based change: legitimate and pre-result? The report discloses that random patches
   alone (the planned design) give PP 9.5% (3.1–17.4%), which is Inconclusive. Given that, is "H1 Supported" a fair
   headline, or should the verdict be qualified?
5. **Analysis.**
   - The bootstrap (resampling all instances; share among converged).
   - The H1 decision rule and the "fewer than 20" reading.
   - H2's fit/test split and the handling of spread = 0.
   - Is "H2 Supported" a fair headline given the within-family miscalibration?
6. **D2.** Confirm the bug and fix (the finest pair is now 8→16 and 3e-4→1e-4 for all instances), and that nothing
   else changed.
7. **Report.** Every number against the tables. Check the claims about the tracker, about scale and about BP's
   honesty. Are the title and plain-terms section fair?

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7; this study predates the gates, so G5 and G6 were run as a pre-review gate).**
Verify:
- **G5:** `review/overclaim_check.md` passes and is honest.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check . --show`, including the
  corrected tracker figures (Q2, Q3).
- **G3:** spot-check a few instances end to end (exact vs BP vs PP values in `data/results`).
- **G2:** were any runs timed out or skipped (status counts) and silently excluded?

Report any gate that is missing or hollow as a finding.
