# Review: quantum-simulation-convergence-false-assurance

Reviewer: independent adversarial review (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.py`, `checks2.py` with `.txt` outputs; `mk_test_instances.py`/`test_instances.json` were prepared for a
Julia re-run that could not be executed because the Julia binary lives under `/home/ubuntu`, unreadable to the
reviewer; the study's own `data/results/validate_*.json` were used instead). Python checks used `venv/bin/python -I`
with `code/` on `sys.path`.

## Verdict: publish with edits

Everything I could recompute reproduces: exact values (numpy vs aer, 1e-14 on two 20-qubit instances), both
engines' conventions (PP at ε = 0 and BP at χ = 64 match the numpy statevector to 1e-15 on a 6-qubit Floquet and a
6-qubit kicked-Ising validation instance, which fixes angle convention, qubit order and Heisenberg ordering), the
pilot ladder medians and the freeze rule, the bootstrap intervals, the H2 split and coverages, the 85% shrinkage
share, the strata, the runtime figures and all status counts (2,400 ok, none excluded). The D2 fix is correct and
the H1/H2 verdicts follow the preregistered rules. Two things need saying before publication: the 31% is specific
to the ladder's step size (with a 10× instead of 3× step in ε the share is 4%), and the "buggy first result" file was
written three seconds before the corrected one, so it is a reconstruction rather than the output that was read.

## Findings

### 1. (Moderate) The 31% depends on the ladder's step size, and the method comparison is confounded by it

Evidence: `checks2.txt`. On the main set the PP error falls only 1.5× (median) between ε = 3e-4 and 1e-4, while
the BP error falls 2.5× between χ = 8 and 16. False assurance needs the error to fall by less than a third between
the two finest settings; 41% of PP instances but 13% of BP instances satisfy that. Recomputing the preregistered
statistic with other pairs from the same runs: PP with a 10× step (1e-3 → 1e-4) gives 2 of 46 (4.3%), PP with
1e-3 → 3e-4 gives 13%, BP with 4 → 16 gives 2.0% and BP with 4 → 8 gives 7.5%. The ladders were frozen by the
plan's rule, so the H1 verdict stands, but the plan's provisional PP ladder (3× steps, finest setting with median
error 0.030 — the "wrong" threshold itself) and BP ladder (2× steps, finest median error 0.0035) are not comparable
objects, and the title's "31% … BP-PEPS's 2%" reads as a property of the methods. The report's own explanation
("refining ε reduces the error slowly and in the same direction") is the right one; the numbers that show it (error
ratio per step; the 10×-step sensitivity) are not in the report.

Fix: add the per-step error ratios and the 10×-step sensitivity to the Results and to "What this shows"; qualify
the title ("with 3× steps in ε") or the verdict bullet; state that the finest PP setting's median error equals the
0.03 threshold.

### 2. (Minor, process) The D2 record is a reconstruction

Evidence: file times. `primary_v1_coarsest_pair_bug.json` was written at 11:19:41 and `primary.json` at 11:19:44;
`exact_main.json` finished at 11:16:59 and the draft was committed at 11:21:58. D2 says the bug "showed up because
main-set errors were far above pilot errors" and that values were "checked by hand"; whatever was read before the
fix, the stored v1 file was produced by re-running the old sort after the fix. The fix itself is right (D2 diff:
explicit fineness key plus an assertion; `finest_pair` is 8→16 and 3e-4→1e-4 for all 300). State that v1 was
regenerated for the record.

### 3. (Minor) Small points for the text

- H2 with spread = 0: 8 BP and 12 PP instances have identical values at the two finest settings; in the test half
  (5 each) such an instance is covered only if its error is exactly zero. Say so (it is conservative).
- `crosscheck` draws 15 instances (`int(75 × 0.05 × 4)`), the report says 16; check the log and fix one of them.
- The pilot's BP χ = 32/64 drop is correctly applied (medians 0.0004 and 0.0003 < 1e-3); the plan's rule never adds
  a finer PP setting, which is the root of finding 1 and should be named in Limits.
- The kicked-Ising family is Clifford apart from RX, so PP is near-exact there (median error 0.006); its 1 of 78
  contributes little information and the pooled 31% is effectively a Floquet number (39 of 51), as the title now
  says.
- BP on loop patches: χ-agreement cannot detect BP's own loop approximation; the report says this for tracker
  scale, and the data (0 of 31 compact patches wrong) support "untested here" rather than "honest".

## Gate checks

- **G2:** `status_counts` bp:ok 900, pp:ok 1500; `excluded_fewer_than_two_settings` empty; no timeouts or term
  limits hit. Nothing silently dropped.
- **G3:** three instances traced end to end (`checks1.txt` §4): e.g. main_F000 exact 0.506088, BP 0.516/0.5061/0.5061,
  PP 0/0.004/0.280/0.411/0.454 — the PP shrinkage-to-zero pattern is visible in the raw ladder.
- **G5:** `review/overclaim_check.md` present and honest; row 1 (title) should carry the finding-1 qualifier.
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (6 claims)"; Q2/Q3 corrected tracker
  figures are in the ledger and the report.
- **Timeline:** plan 10:05 → D1 10:26 → pilot runs 10:26–10:31 → ladder freeze 10:31:54 → analysis code 10:32:56 →
  main approximations 10:37–10:41 → exact values to 11:17 → analysis 11:19 → draft 11:21. The freeze followed the
  pilot and preceded the main runs.
