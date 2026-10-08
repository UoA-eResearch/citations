# Deviations and implementation details

The plan (plan.md) was committed in 86f1489 at 2026-10-05 08:14 NZDT. Entries are timestamped with `date`.

## D1. Environment fix, validation and timing pilot (2026-10-05 08:50 NZDT)

**REPL output flushing.** The REPL fork's own `Main.lean` does not flush stdout, so on a pipe it returns nothing until
it exits. STP's setup script replaces it with `assets/setup/Main.lean`, which flushes after every response. We
made the same replacement (`lean/repl/REPL/Main.lean` = kfdong/STP `assets/setup/Main.lean`), so the toolchain now
matches STP's verifier. No Lean semantics change.

**Controls** (results/tables/validation_controls.csv; criteria from plan section 6):

- 20 of 20 vacuous controls certified (criterion: at least 18);
- 0 of 20 satisfiable controls certified;
- split check passed on 40 of 40;
- re-verification passed on 40 of 40.

On the first run, two controls failed re-verification because of an error in our hand-written proofs. They reverted the
bounded hypothesis in the wrong order for `decide`. The proofs were corrected and the whole set rerun.

One limitation surfaced. The automation step's `decide` on `∀ B, False` uses the binders in their written order,
so it fails when a bounded hypothesis such as `n < 5` comes after the hypothesis it bounds. Vacuous control 2 was
certified only by the goal swap. This is within the plan's acknowledged lower-bound nature and is not changed.

**Timing pilot.** 300 rows were drawn from outside the main sample and run with triviality on every row; only timing and
health were printed.

| Measure | Value |
|---|---|
| Throughput | 2,072 rows/h on 12 workers (mean 17.9 s per row, wall-clock) |
| Re-verification rate | 0.960 (2 timeouts) |
| Split check | 0.993 of re-verified rows |
| Parse errors | 0 |
| Worker errors | 0 |

The projected time for the whole STP sample is 101,600 rows × 17.9 s / 12 ≈ 42 h, which is at most 72 h. By the
plan's rule, every iteration therefore gets 2,000 rows. The pilot's vacuity outcomes are in
`data/sealed_pilot/pilot.jsonl`, unread and excluded.

**Run order.** The run order does not affect the analysis:

1. primary windows (iterations 1-9 and 38-47, with triviality);
2. the other conjecture iterations;
3. statement rows.

Workers are pinned to cores 16-27 while the quantum lead's GPU jobs use the rest of the machine.

## D2. Split-check failures: cause and a sensitivity repair pass (2026-10-05 09:03 NZDT)

**What was looked at.** The first 2,788 main-run rows, using split-check health fields only. No vacuity field was
examined.

**What was found.** 81 of 2,699 re-verified rows fail the split check:

- 54 report "unexpected end of input";
- 16 report "don't know how to synthesize implicit argument";
- 11 report other elaboration errors.

**Cause of the main class.** In the 54 rows the conclusion begins with `let x := by …`. STP's own prompt/target split
cut the prompt at that inner `:= by`, so the prompt holds a truncated conclusion and the target carries the rest of
the statement and the proof. Our binder/conclusion split is still correct for the hypotheses before the colon. Only the
conclusion C is truncated, so `∀ B, C` cannot elaborate.

**Primary analysis.** It stays as preregistered: split-check failures are excluded and their rate is reported by
iteration.

**Sensitivity analysis, defined before any outcome of these rows is seen.** After the main run, every re-verified row
that failed the split check gets a repair pass:

- **Repair check.** `example : ∀ B, _ := orig`, which checks that B is the hypothesis telescope of the original theorem
  and lets Lean infer the conclusion.
- **Automation only.** If the repair check passes, the automation portfolio (b) is run on `theorem v B : False`. It
  uses only B, so it is valid when C is unknown. The goal swap (a) is not attempted, because the released proof text
  cannot be separated from the statement.

The primary contrast is then reported again with the repaired rows included, as "sensitivity: split repair".

**Secondary-corpus samples and imports.** `code/sample_other.py` drew and converted the samples. 753 of 10,000
Goedel SFT v2 rows had no final Lean block or a term-mode proof, and 55 of 10,000 NuminaMath rows could not be split.
The import check now accepts any `Mathlib.*` module, because environment 0 imports all of Mathlib. Some Numina rows
import `Mathlib.Tactic` or a single Mathlib module. Every STP row imports exactly `Mathlib` and `Aesop`, so STP rows
are unaffected.

**CPU pinning.** The quantum lead's three GPU processes were pinned to cores 0-15 at 08:57. Without the pinning they had
drifted onto the REPL cores, and GPU utilisation fell to 20%.

## D3. Main run complete; the repair pass runs early (2026-10-06 13:55 NZDT)

**Main run.** It finished at 13:54 with all 92,000 conjecture rows and 9,600 statement rows. The secondary-corpus run
(`run_other.sh`) started on cores 16-27.

**Repair pass.** The quantum lead's GPU jobs have released cores 0-15, so the split-repair pass (D2) now runs
immediately on cores 0-11 with 10 workers (`code/run_repair_now.sh`). It no longer waits behind the secondary
corpora. The queued `run_repair.sh` was cancelled by its PID before it started. The rows, code and rules are
unchanged; only the timing and the worker count differ.

**Primary analysis.** It is run now with the analysis code committed in c9f1baa, before any outcome existed. The
primary test uses only the STP conjecture rows, which are complete.

**Row files.** `results/rows/` is untracked in git while the runs are in progress. It will be committed in compressed
form when they finish.

## D4. Analysis code guard (2026-10-06 13:55 NZDT)

`analysis.py` read the repair file while the repair pass was still writing it, and crashed because a column was
missing. It now reports the D2 split-repair sensitivity only after `logs/repair.log` records completion, and treats a
missing `vacuous_repair` column as no certificate. The primary analysis is unchanged.

## D5. Bug in the split-repair check; the repair pass is rerun (2026-10-06 13:57 NZDT)

**The bug.** The repair pass (D2) failed every row:

- 1,034 failed the telescope check;
- 216 had no binders, so cannot be repaired by design.

The cause was in our check, not the rows. Lean rejects any `example` whose stated type contains holes, so
`example : ∀ B, _ := orig` cannot elaborate.

**The fix and rerun.** The check is now `#check (orig : ∀ B, _)`, which elaborates the binder telescope against the
original theorem and leaves the conclusion to Lean. Checked by hand on three rows: it passes where the old form failed.
The repair pass was rerun with the fix. The buggy outputs are kept as `*_repair_v1_buggy.jsonl`. No vacuity outcome
of the repaired rows had been produced before the fix, because no row had passed the check.

## D6. NuminaMath runs in parallel (2026-10-06 14:21 NZDT)

The NuminaMath-LEAN secondary corpus is run now on cores 0-11 (`code/run_numina_now.sh`, 10 workers, Lean 4.15). The
other secondary corpora continue in sequence on cores 16-27. `run_rows.py` is resumable, so when `run_other.sh`
reaches Numina it finds every row done. Only the scheduling changes.

## D7. Certificate soundness fix, STP's environment and a coverage measure, after the independent review (2026-10-06 23:29 NZDT)

The independent review (review/review.md, recommendation "fix first") found four measurement defects. This entry
fixes them before any new outcome is computed. The decision rule, windows, weights and sample are unchanged.

**1. Certificate soundness (review A1).** v1 elaborated the certificate as `theorem v B : False`. A variable whose type
only the conclusion fixed then defaulted to ℕ: an auto-bound implicit, or a binder written without a type. So
hypotheses that are satisfiable over ℝ or ℤ could be refuted over ℕ. The reviewer found 18 such rows among the 1,207
primary-window certificates.

- **v2 certificate.** It is elaborated in the original statement's context:
  `theorem v B : C := False.elim (by <released proof>)` for the goal swap, and
  `theorem v B : C := by exfalso; <tactic>` for automation. It is a kernel-checked proof of False from exactly the
  original hypotheses. The axiom check is unchanged.
- **`decide`.** It runs after reverting the original hypotheses in order, so it matches v1's `∀ B, False` form.
- **Probes.** v2 records whether the statement uses auto-bound variables, using `autoImplicit false`.

v1 is kept in `code/vacuity.py` as `check_row_v1`, and its outputs in `results/rows/`.

**Validation of v2, before the rerun** (results/tables/validation_controls_v2_{minif2f,mathlib}.csv):

- The original controls give 20 of 20 vacuous certified and 0 of 20 satisfiable certified, in both environments.
- New controls:
  - 0 of 4 satisfiable statements with undeclared variables are certified (the reviewer's minimal case among them);
  - 1 of 1 undeclared-variable statement that is genuinely vacuous over ℕ is certified.
- **Regression on 318 real rows** (miniF2F environment):
  - v2 certifies 2 of the reviewer's 18 false positives. Both are genuinely vacuous in their original elaboration
    (ℤ, forced by a `-1` or a negation in the conclusion). Row 1064402: 2x²+3y²=1 has no integer solutions. Row
    1802958: a²+b²=1 over ℤ forces ab=0, contradicting (ac)(bd)=1. v1 had certified them over the wrong (ℕ) types.
  - On 299 other rows, v1 and v2 agree on 297. v1 had one certificate that was not sound (row 704535, auto-bound,
    outside the primary windows). v2 finds one that v1 missed: row 1851228, whose proof uses a variable that only the
    conclusion declares.

**2. Environment (review A2).** STP's verifier compiles under `import miniF2F`, its curated subset of Mathlib, not
`import Mathlib`. Under all of Mathlib, `π` is ambiguous, which excluded 2.6% of rows.

- `lean/stp_env/miniF2F.lean` is fetched from kfdong/STP (commit 2b5fe8b, sha256 b59fe463…) and compiled into the
  workspace.
- v2 runs the STP rows with `import miniF2F`. Rows that do not re-verify there are rerun under all of Mathlib (the v1
  environment). A row is eligible if it re-verifies in either, and its certificate comes from that environment.
- Exclusions will be reported by cause and window: truncated prompts, dropped per-row headers, timeouts, and split
  failures.
- The other four corpora keep their v1 environments, with the v2 certificate.

**3. Coverage (review A3), secondary.** Statements with no binders, whose hypotheses all sit in the conclusion, cannot
be certified by the preregistered certificate. v2 records the binder-less share and the number of hypotheses `intros`
adds from the conclusion.

It also adds a **secondary** certificate: `theorem v B : C := by intros; exfalso; <tactic>`, which refutes the
hypotheses together with the premises inside the conclusion. It runs only where `intros` adds hypotheses and the
final target is not `False`; otherwise refuting the premises would prove the claim itself.

- Controls: a binder-less vacuous statement is certified only by this route, and a binder-less satisfiable one is
  not.
- A satisfiable statement whose conclusion ends in `→ False` is correctly skipped.

**4. Split repair (D2 sensitivity).** The repaired rows' conclusion text is unreliable, so their v1-style certificate
counts only if `example : type_of% @orig := by intros; exfalso; apply v <;> assumption` compiles. That is, it must
refute the original theorem's hypotheses as elaborated there. Tested on the reviewer's minimal case (rejected) and two
genuine cases (accepted).

**5. Analysis and reporting (review A4, B1-B8).**

- The primary contrast is recomputed on v2 rows with the preregistered rule.
- Added: the statement-control contrast, swap-only and automation-only rates by iteration, coverage by iteration, the
  rate among checkable rows and under the secondary certificate, the exclusion taxonomy, and the `π` and split-repair
  sensitivities.
- Disclosed: the `C(iteration)` fixed effects in the training-weight regression.

**Run.** `code/run_v2.sh`: 22 workers on cores 4-27, about one day.

**Timing.** All of this follows sight of the v1 outcomes and of the review. No change to the decision rule is
possible, so the verdict can only change through the measurement.

## D8. Results of the v2 rerun, and re-coded causes (2026-10-08 12:25 NZDT)

**The rerun.** `code/run_v2.sh` finished at 23:13 NZDT on 7 October. `analysis.py` (v2, committed in 3e4ebf6 before
the rerun finished) gives the primary ratio 0.609 (0.543-0.684): **Refuted**, as with v1 (0.599).

On the rows of the primary windows eligible under both v1 and v2:

- v2 removes 18 of v1's certificates and adds 12;
- 905 rows became eligible under STP's miniF2F environment, mostly the `π` rows, and 5 of them are vacuous;
- 33 of the 1,152 fallback rows re-verified under all of Mathlib.

**Re-coded causes (review C2).** The 100-row cause sample was redrawn from the v2 certified rows (seed 7). A separate
coder agent (Claude Fable 5.1) coded it with the prompt saved in `review/coder_prompt.md`. The categories are those of
v1, plus K6, "undeclared variable defaulted to ℕ". The first coding prompt had not been saved.

| Cause | Rows |
|---|---|
| K2 | 52 |
| K5 | 33 |
| K3 | 9 |
| K1 | 2 |
| K4 | 2 |
| K6 | 2 |

Locality: 88 local. Real claim: 76 yes. The v1 coding is kept in `results/tables_v1/`.

**Figure.** The x = 0 label now reads "self-play start".

## D9. Confirmation pass: publish with edits (2026-10-08 13:02 NZDT)

The same reviewer verified the following:

- the v2 code is byte-identical to the pre-rerun commits;
- the compressed row files decompress to the tables' inputs;
- every number in the report;
- in Lean, 30 of 30 certified rows reproduce by the same route, with `vac_thm` having the same type as `orig_thm`, and
  15 of 15 non-certified rows stay non-certified.

The verdict stands. Edits made:

- **N1.** The coverage claim is corrected: the goal swap cannot apply to binder-less rows.
- **N2.** The pooled rates in the primary table are correct (4.19%, 2.53%).
- **N3.** 44 fallback rows re-verified, 33 became eligible and none was vacuous.
- **N4.** The Mathlib version is upstream d1d1e4b72.
- **N5.** The header and the deviation summary include D8, and the HTML date is corrected.
- **N6.** A caveat on the instability of the coder's "real claim" judgement (97 against 76 of 100).
- **N7.** The 18 removed and 12 added certificates are explained.

**Reproduction.** `analysis.py` reads `results/rows_v2/*.jsonl`. Run `gunzip -k results/rows*/*.jsonl.gz` first.
