# Do self-play provers drift toward vacuous conjectures?

*A preregistered, kernel-certified measurement of contradictory hypotheses across 46 iterations of the STP self-play
corpus and four other open prover-training corpora*

Run directory: `research-lab/runs/formal-math-selfplay-vacuity-drift` · Preregistration: [`plan.md`](plan.md)
(commit 86f1489) · Departures from it: [`deviations.md`](deviations.md) (D1–D6) · 6 October 2026, draft for
independent review

## In plain terms

Some AI systems learn to prove mathematical theorems by inventing their own practice problems, trying to prove them,
and training on whatever they prove. A practice problem whose assumptions contradict each other is a trap. It can be
"proved" without doing any real mathematics, a kind of cheating the training process could reward. We expected such
vacuous problems to pile up as self-play went on.

We checked 92,000 problems from STP, a published self-play prover, using the Lean proof checker to certify each
contradiction. The prediction was wrong. Vacuous problems were *less* common late in training (2.6%) than early
(4.3%). The more interesting pattern is the shape:

- each time self-play restarted from a re-trained model, vacuous problems jumped to 8–10%;
- they then declined steadily as the prover improved.

A likely reason is STP's own filter. It keeps only problems the prover usually fails, and contradictory problems
become easy and drop out.

Vacuous problems are far from rare elsewhere. In NuminaMath-LEAN, 6.2% of the problems the prover solved were
vacuous: 7.4% of machine-translated problems against 1.6% of human-written ones. Vacuous problems were also solved
more often during reinforcement learning, so the training signal favoured them. Almost all vacuous problems read like
genuine competition questions.

## What was done

**Corpus and sample.** The STP_Lean_0320 corpus has 3,262,558 rows. Its iteration numbers form two self-play phases:

- rounds 0–23, and rounds 24–47;
- rounds 0 and 24 contain no conjectures;
- STP restarts self-play from a re-trained model between the phases.

We drew 2,000 conjecture rows per iteration (92,000 in total) and 200 statement rows per iteration (9,600 LeanWorkbook
proofs, used as a control). Each row was checked in STP's own Lean environment: Lean 4.9.0-rc1, the DeepSeek mathlib
fork (upstream d1d1e4b72), and the STP REPL.

**Certificate.** A row counts as vacuous if a proof of `False` from its hypotheses compiles, contains no `sorry`, and
uses only the standard axioms. Two routes can produce one:

- **(a) Goal swap.** The released proof is re-run with the goal replaced by `False`.
- **(b) Automation.** A fixed portfolio is tried: omega, linarith, norm_num, simp_all, nlinarith, aesop and decide.

**Validation.**

- **Controls.** The pipeline certified 20 of 20 vacuous control statements and 0 of 20 satisfiable ones.
- **Re-verification.** The original proofs re-verified for 95.5% of rows, and the binder/conclusion split check
  passed for 94.2%. Rows failing either were excluded.
- **Split repair.** A sensitivity pass repaired split failures caused by STP's own prompt cut-off (D2, D5).

## Results

**Primary test (iterations 38–47 against 1–9; iteration 0 has no conjectures).** Rates are weighted by iteration
size.

| | Late (38–47) | Early (1–9) | Ratio (95% CI) |
|---|---|---|---|
| Certified vacuous | 2.56% (482 of 18,726) | 4.28% (725 of 16,706) | **0.60 (0.53–0.67)** |

**Verdict: Refuted.** The hypothesis predicted a ratio of at least 2, and the upper end of the 95% CI is 0.67. The same
verdict holds:

- at statement level (0.61, 0.54–0.68);
- unweighted (0.59, 0.53–0.66);
- with the 991 split-repaired rows added (0.60, 0.53–0.67).

![Certified-vacuous rate by STP iteration, with the LeanWorkbook statement control](results/figures/vacuity_by_iteration.png)

**Dynamics (secondary).** Vacuity is highest right after each self-play start and falls within each phase:

| Phase | Starting rate | Peak | Final five iterations | Spearman ρ |
|---|---|---|---|---|
| 1 | 2.8% at iteration 1 | 8.1% at iteration 3 | 0.7% | −0.89 |
| 2 | 8.1% at iteration 25 | 10.0% at iteration 26 | 2.1% | −0.94 |

| Contrast | Rate ratio |
|---|---|
| Phase 1, late (14–23) against early (1–9) | 0.20 |
| Phase 2, late (38–47) against early (25–33) | 0.37 |
| Phase 2 against phase 1, overall | 2.19 |

Across all 46 iterations the trend is flat (ρ = −0.004), because the decline within each phase cancels the restart
jump.

**Control.** The LeanWorkbook statement proofs, whose problems come from a fixed pool, have a vacuity rate of 1.9%
overall with no clear trend (ρ = −0.22, p = 0.12).

**How vacuity is certified.**

- Of the 1,207 certified rows in the primary windows, 994 were certified only by the goal swap, 123 only by
  automation, and 90 by both. In most cases, then, the released proof itself derives the contradiction.
- Conclusions provable with all hypotheses discarded fell from 3.8% to 0.1% between the early and late windows.

**Training weight.** Vacuous rows carry higher STP training weights: the odds ratio is 1.79 per 0.1 of weight
(1.73–1.85). STP weights a proof by `exp(-0.001 × proof length)`, and vacuous conjectures tend to have short proofs, so
the weighting gives them more emphasis in training.

**Causes (100 random certified rows, coded by a separate agent).**

| Cause | Rows |
|---|---|
| Contradictory numeric constraints | 59 |
| Unsatisfiable functional equations, domain or range confusions, and parsing slips (e.g. `x i+1` read as `(x i)+1`) | 21 |
| A hypothesis that is false on its own | 18 |
| Natural-number subtraction or division | 1 |
| Cast or division-by-zero conventions | 1 |

85 of the contradictions are local, visible from one or two hypotheses, and 97 of the 100 statements read like genuine
competition claims.

**Other corpora (secondary).** Each is a uniform sample, checked in its own Lean version.

| Corpus | Re-verified | Certified vacuous (95% CI) |
|---|---|---|
| NuminaMath-LEAN, model proofs (Lean 4.15) | 88.7% | **6.2%** (5.8–6.8) |
| Goedel Lean-workbook-proofs | 96.2% | 2.8% (2.4–3.3) |
| DeepSeek-Prover-V1 | 99.9% | 2.0% (1.7–2.4) |
| Goedel-Prover-V2 SFT | 83.2% | 1.0% (0.8–1.2); 1.2% excluding negation statements |

In NuminaMath-LEAN:

- autoformalized statements are vacuous 7.4% of the time (of 7,051), and human-formalized ones 1.6% (of 1,767);
- the RL win rate is higher for vacuous statements (0.73 against 0.67, Mann–Whitney p = 2×10⁻⁸). The RL loop
  solved them more easily, and so rewarded them more often.

## Caveats

- **A lower bound.** Certified vacuity requires either the released proof to prove `False` or one of seven automation
  tactics to find the contradiction. Hard contradictions are missed.
- **Final training data only.** STP_Lean_0320 is the final, filtered training set, not every conjecture generated. A
  vacuous conjecture that STP's filters removed is invisible here. The pass-rate explanation for the decline is a
  hypothesis that we did not test.
- **Two phases, not one run.** The preregistered contrast spans a restart. The within-phase contrasts, added as
  secondary analyses before any outcome was seen, show the dynamics more clearly than the primary contrast does.
- **Exclusions.**
  - About 4.5% of rows did not re-verify, and 1.3% failed the split check.
  - SFT v2 and NuminaMath re-verified less often (83% and 89%), possibly because of version differences.
  - Excluded rows could differ systematically.
- **Causes from one coder.** The cause categories come from a single coder agent (Claude Fable 5.1) reading the
  statements, without running Lean.

## Deviations (summary)

- **D1:** the REPL's output-flushing fix (STP's own `Main.lean`), validation and timing pilot; 2,000 rows per
  iteration under the pilot rule.
- **D2:** the split-repair sensitivity, defined before any outcome was seen.
- **D3:** the repair pass run early, on idle cores.
- **D4:** an analysis-code guard for the incomplete repair file.
- **D5:** a bug in the repair check (`example` rejects holes in its type), fixed and rerun; the result is unchanged.
- **D6:** NuminaMath run in parallel.

The decision rule never changed.
