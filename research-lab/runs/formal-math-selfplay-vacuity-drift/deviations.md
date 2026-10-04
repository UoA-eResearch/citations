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
