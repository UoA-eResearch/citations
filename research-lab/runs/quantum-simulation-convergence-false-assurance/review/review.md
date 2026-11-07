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

## Confirmation pass

Reviewer: Fable 5.1, 2026-11-05. Independent of the earlier, uncommitted confirmation section (misdated 2026-11-06,
no check files; kept verbatim in `reviewer_checks/prior_confirmation_section.md`). Checks and the files that back them
(all under `review/reviewer_checks/`, run with `venv/bin/python -I` or `python3 -I`, paths passed as arguments; note
that `reviewer_checks/` is git-ignored by the repository's `.gitignore`):

- `confirm_steps.py` / `confirm_steps.txt`: `posthoc_steps.json` recomputed from the 2,400 stored runs (900 BP, 1,500
  PP, all ok) without importing the study's code. All 13 setting pairs, the 6 adjacent median error ratios, both
  finest-setting median errors and both "less than threefold" shares match the stored JSON exactly. Also: the
  "41% vs 13%" question, the zero-spread H2 counts, and the cross-check arithmetic (80 instances with n = 20).
- `confirm_text.py` / `confirm_text.txt`: each edit the brief lists is present in `report.md` and `deviations.md`
  (19 of 19 phrases found); the report's step-size table (6 rows) matches `posthoc_steps.json`; the main table matches
  `primary.json`; G5 has 41 rows, all with backing, all labelled Supported, row 1 carries the step-size qualifier.
- `confirm_crosscheck.py` / `confirm_crosscheck.txt`: the numpy statevector re-run on the same 16-instance subset
  that `instances.py crosscheck` selects (seed 1 over the 80 n = 20 instances) gives max |numpy − aer| = 3.2 × 10⁻¹⁴,
  as the report says (3 × 10⁻¹⁴ on 16). This closes the count question without a stored log of the original run.
- `confirm_g6.txt`: `python3 -I tools/attribution.py check . --show` → "G6 passed (6 claims)"; the arXiv id resolves
  to the Pauli-path guide the claim names.
- `git status`/`git log`: nothing outside `review/review.md` is uncommitted; D3 was committed 2026-11-05 22:07 +13:00.

### Final verdict: publish

- **Finding 1 (step size): fixed.** Title qualified ("with 3× steps in its threshold"); verdict sub-bullets give the
  finest PP median error 0.030 (= threshold; recomputed 0.0303), the per-step ratios 1.5× vs 2.5× (recomputed 1.534
  and 2.489), the 10× step 4.3% (2 of 46, recomputed), and the "not comparable objects" statement; a "Step size"
  results table with 6 pairs, each matching the JSON; the Limits bullet names the ladder rule that never adds a finer
  PP setting. The report shows 6 of the 13 pairs; the omitted pairs (coarse pairs up to 68%, pairs spanning ≥ 30×
  at 0%) are all in the JSON and, if anything, strengthen the stated dependence.
  - **"41% vs 13%":** reproduced. It is the share of instances whose error ratio second/finest is below 4/3 (PP 0.407,
    BP 0.133; `confirm_steps.txt`, same as the first review's `checks2.txt`). That is the necessary condition for
    false assurance when the finest error exceeds 0.03 (spread ≤ 0.01 and err > 0.03 imply err_second < 4/3 · err_finest),
    so the first review's wording "falls by less than a third" was loose (it means the error falls by less than about a
    quarter). The study's `share_error_falls_less_than_threefold` (0.83 / 0.57) is a different quantity. The median
    per-step ratios the report uses make the same point; no further edit is needed.
- **Finding 2 (D2 reconstruction): fixed.** `deviations.md` has the post-review note ("a reconstruction for the record,
  not the file that was read before the fix") and the report says "regenerated after the fix, for the record" in both
  the verdict and the process section.
- **Finding 3 (text): fixed.** Zero-spread H2 cases stated as 8 BP-PEPS and 12 PP, conservative (recomputed: 8 and 12,
  5 each in the test half, none with zero error, so each counts as uncovered); kicked Ising near-exact for PP (median
  error 0.006, recomputed 0.0060); the ladder rule named in Limits; BP's loop approximation now "untested here rather
  than shown to be safe". Cross-check count: the first review's 15 was wrong; the main set has 80 n = 20 instances,
  `max(2, int(80 × 0.05 × 4))` = 16, and the 16-instance re-run reproduces the report's figure. Withdrawn.
- **Gates:** G5 passes (41 rows, all Supported with backing; rows 9–13 and 31 cover the new sentences). G6 passes
  (6 claims).

Agreement with the prior section: my conclusions agree with it on every point (verdict, the three findings, the
41%/13% explanation and the count of 16); it was, however, misdated 2026-11-06 and left no check files, and it listed
no remaining issues where I list two minor ones below.

Remaining issues (minor, not blocking; outside `review/`, so not fixed here):
- `deviations.md` dates D3 and the post-review D2 note "2026-11-06"; the edits were committed 2026-11-05 22:07 NZDT
  and the system clock is NZDT, so both should read 2026-11-05.
- `report.md` "Process and deviations" still says "confirmation pending"; update it to record this pass (publish).
