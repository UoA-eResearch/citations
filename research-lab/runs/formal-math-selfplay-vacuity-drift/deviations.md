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
