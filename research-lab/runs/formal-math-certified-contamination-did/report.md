# Does training-set leakage explain how AI provers score on miniF2F?

*A preregistered study: Lean-certified leakage between seven open prover-training corpora and four benchmarks, and a
difference-in-differences test of whether leaked problems lose more of their solve rate when reworded into
certified-equivalent forms.*

Run directory: `research-lab/runs/formal-math-certified-contamination-did` · Preregistration: [`plan.md`](plan.md)
(commit 6bfdc63) · Departures from it: [`deviations.md`](deviations.md) (D1-D8) · 11 October 2026, draft for
independent review

## In plain terms

AI systems that write machine-checked proofs are usually compared on miniF2F, a set of 488 competition problems. If
the problems, or versions of them, sit in a system's training data, its score may reflect memory rather than skill.

We searched the seven public training sets behind today's open provers for every miniF2F problem, and used the Lean
proof checker to certify matches: identical, logically equivalent, or a stronger version of the same claim. **About
half of miniF2F (252 of 488 problems) has such a match in at least one open corpus.** For each prover's own training
data the rate is lower but substantial:

- about a fifth of problems for Goedel-Prover-V2;
- 11% for Kimina;
- 3% for DeepSeek-Prover-V2.

We then tested whether memory drives the scores. If a model has memorised a problem, rewording it (renaming
variables, reordering assumptions, flipping equations) should hurt more on leaked problems than on clean ones. It did
not. Rewording changed the solve rate by about 1 point more on leaked problems, far below the 10 points we set in
advance. **The prediction is refuted.**

Leaked problems were often solved far more frequently in absolute terms (100% against 43-73% for two provers). Whatever
the models learned from them survives simple rewording, and our design cannot tell memory from easier problems.

## What was done

**Benchmarks.**

- **Primary:** the 488 miniF2F items, being Kimina's revised test set (244) plus DeepSeek-Prover-V1.5's validation
  set (244).
- **Secondary (leak rates only):** miniF2F-v2c (488), ProofNet# (371) and PutnamBench (672).

**Corpora.** Seven public training sets, deduplicated by normalised statement:

| Corpus | Statements |
|---|---|
| Goedel-Pset-v1 | 1.65M |
| Goedel-Prover-V2 SFT | 910k |
| STP_Lean_0320 | 778k |
| Lean Workbook | 105k |
| NuminaMath-LEAN | 100k |
| DeepSeek-Prover-V1 | 27.5k |
| Goedel's Lean-workbook proofs | 21.5k |

**Leak certification.** Candidates were retrieved by:

- MinHash on character 5-grams;
- identical numeral multisets, capped at 20 per item and corpus (D2).

Each candidate pair was checked in the Lean kernel with a bounded tactic portfolio, in the training corpus's Lean
version (4.9 or 4.15):

| Tier | Meaning |
|---|---|
| L0 | Identical text after normalisation |
| L1 | Certified both ways |
| L2 | The training statement certifiably implies the test statement |

**Guards.** An implication counts only if it is *informative*:

- **The conclusion is not provable alone.** The conclusion must not be provable by a superset of the portfolio
  without the hypothesis (D3a).
- **The hypothesis is not refutable.** The training statement must not be refutable by the portfolio, because a false
  training statement implies anything (D3b).

Timeouts count as "not a leak". These guards came from spot-checks during the study, before any prover was run. The
first versions let through closed arithmetic facts and false training statements (D3-D3b).

**Reformulations.** Two per item:

- **R1:** fresh names for every variable and hypothesis, with hypotheses reordered.
- **R2:** R1 plus flipped equalities.

Each is kept only if Lean certifies it equivalent to the original in each prover's environment: 484 of 488 items in
Lean 4.9 and 483 in Lean 4.15.

**Provers and sampling.**

| Prover | Own corpora |
|---|---|
| DeepSeek-Prover-V2-7B | DeepSeek-Prover-V1 data |
| Goedel-Prover-V2-8B | Goedel-Pset, SFT v2, Lean-workbook proofs |
| Kimina-Prover-Distill-8B | NuminaMath-LEAN |
| STP (pre-specified secondary) | STP_Lean_0320 |

- 32 samples per version, each model card's prompt, at most 8,192 new tokens. STP: 2,048, as a completion model.
- **Items:** every leaked item plus 150 random clean items per prover. STP: all 488.

**Verification.** Every proof was checked in Lean in its prover's environment. Rejected:

- changed theorem statements;
- `sorry`, `admit` and `native_decide`;
- non-standard axioms.

**Test (H1).** For each (item, prover):

- d = pass@32 on the original − mean pass@32 on its certified reformulations;
- DiD = mean d over leaked pairs − mean d over clean pairs, pooled over the three provers;
- the interval is a one-sided 95% item-cluster bootstrap (10,000 draws).

**Decision rule.**

- **Supported:** DiD ≥ 10 pp and the lower bound > 0.
- **Refuted:** the upper bound is below 10 pp and the minimum detectable effect is at most 10 pp. It was set at 6.7 pp
  before sampling (D4).

## Results

**Leak map (H0).**

| Corpus | miniF2F | miniF2F-v2c | ProofNet# | PutnamBench |
|---|---|---|---|---|
| STP_Lean_0320 | 179 (36.7%) | 115 | 27 | 0 |
| Goedel-Pset-v1 | 67 (13.7%) | 48 | 6 | 9 |
| Goedel-Prover-V2 SFT | 61 (12.5%) | 42 | 5 | 2 |
| NuminaMath-LEAN | 55 (11.3%) | 53 | 5 | 22 |
| DeepSeek-Prover-V1 | 16 (3.3%) | 8 | 0 | 0 |
| Goedel's Lean-workbook proofs | 10 (2.0%) | 12 | 0 | 0 |
| Lean Workbook | 0 | 0 | 0 | 0 |
| **Any corpus** | **252 (51.6%)** | **171 (35.0%)** | **34 (9.2%)** | **26 (3.9%)** |

![Certified leak rates](results/figures/leak_rates.png)

- **STP_Lean_0320.** It contains 173 miniF2F *validation* statements verbatim, so STP trained on them. Only one test
  item matches verbatim.
- **NuminaMath-LEAN** (Kimina's corpus) contains 5 miniF2F *test* statements verbatim, plus 37 certified equivalents
  and 13 stronger statements. It also covers 22 PutnamBench problems.
- **Most leaks are not textual copies.** Across corpora, L1 and L2 leaks, which text-level decontamination can miss,
  outnumber verbatim ones apart from STP.
- **Automation alone.** 69 miniF2F items are provable by the certification portfolio alone, and so can only be leaked
  verbatim.

**H1: Refuted.** Pooled over the three provers (170 leaked and 450 clean pairs):

| | Drop from original to reformulation |
|---|---|
| Leaked items | +0.9 pp |
| Clean items | −0.4 pp |
| **Difference-in-differences** | **+1.3 pp (one-sided 95% bounds −0.7 to +3.5)** |

The upper bound is far below the preregistered 10 pp, and the minimum detectable effect was 6.7 pp. Using the
observed spread of d, it would have been 3.0 pp.

![Difference-in-differences by prover](results/figures/did.png)

**By prover.**

| Prover | Leaked pairs | DiD (one-sided 95% bounds) |
|---|---|---|
| DeepSeek-Prover-V2 | 16 | +1.0 pp (−1.3 to +3.3) |
| Goedel-Prover-V2 | 99 | +1.0 pp (−1.0 to +3.4) |
| Kimina | 55 | +1.2 pp (−3.6 to +6.1) |
| STP, secondary | 179 | **+3.5 pp (+1.0 to +6.2)** |

STP is the one prover whose leaked items lose measurably more on rewording. Those are items it demonstrably trained
on, and even there the effect is small.

**Robustness (pooled, secondary).**

| Variant | DiD (one-sided 95% bounds) |
|---|---|
| Per-sample solve rates instead of pass@32 | +1.5 pp (−0.0 to +3.1) |
| L0/L1 leaks only | +2.2 pp (−0.0 to +4.7) |
| Leak defined against all corpora | −0.1 pp (−2.1 to +1.8) |
| Excluding the 19 items Kimina revised | +1.0 pp (−1.1 to +3.1) |

**Solve rates by version (descriptive).** pass@32 on the original, R1 and R2:

| Prover | Leaked items | Clean items |
|---|---|---|
| DeepSeek-Prover-V2 | 100%, 100%, 100% | 73%, 73%, 77% |
| Goedel-Prover-V2 | 83%, 82%, 83% | 87%, 88%, 87% |
| Kimina | 78%, 78%, 85% | 72%, 73%, 73% |
| STP | 100%, 97%, 93% | 43%, 43%, 45% |

![Solve rates by statement version](results/figures/pass_by_version.png)

- **Levels.** For DeepSeek and STP, leaked items are solved far more often than clean ones. For Goedel they are not.
- **Rewording barely moves either group.** Rejections for a changed statement were at most 2.1% in any cell, so
  "correcting" a reworded statement back to its training form is rare.
- **Why levels prove nothing here.** Leaked problems may simply be easier: frequently reproduced problems tend to be
  standard exercises. That is why the preregistered test compares changes, not levels.

## Caveats

- **Surface rewording only.** R1 and R2 change names, order and equation direction. A model that has memorised a
  problem's solution, not its exact text, would pass both. The test rules out text-level memorisation as the driver
  of the scores, not memorisation of solutions. Deeper, certified-equivalent rewrites (e.g. changing the
  representation) are a natural next step.
- **Leaks are a lower bound.** Retrieval is MinHash plus capped numeral matching, and certification is a bounded
  portfolio. Equivalents that are textually different and hard to prove are missed.
- **DeepSeek-Prover-V2's own corpus is only its public lineage** (DeepSeek-Prover-V1). Its real training set is not
  public. That is why it has only 16 leaked pairs.
- **Each prover's design changed during the study** (D4), before sampling:
  - only 150 clean items per prover;
  - an 8,192-token cap instead of 4,096, because the pilot showed 24-44% of outputs truncated at 4,096.

  Truncation remains (Goedel 13-18%, Kimina 15-22% of outputs) and is treated alike across versions.
- **Two tokenizer failures were caught and fixed** (D5, D7). STP's and DeepSeek-Prover-V2's released tokenizer
  configurations garble Lean text under current libraries. Both were re-run in full, and the invalid outputs were
  discarded unscored. A preliminary pooled result with the invalid DeepSeek-Prover-V2 rows was seen and is disclosed
  (D7).
- **The memory watchdog** killed 22 runaway proof checks: 18 during STP verification and 4 during DeepSeek-Prover-V2's
  re-verification. Those outputs count as failures (D6, D8).

## Deviations (summary)

| Entry | Change |
|---|---|
| D1 | Certification guards (self-provability, autoImplicit off, `π` as `Real.pi`) |
| D2 | Cap on numeral candidates |
| D3-D3b | Informativeness and explosion guards replacing D1's, after spot-checks found spurious L2 leaks |
| D4 | Final tiers, sampling plan, 8,192-token cap, clean subsample, STP added, MDE recorded |
| D5 | STP tokenizer fix |
| D6 | Memory safety net |
| D7 | DeepSeek-Prover-V2 resampled after a tokenizer failure |
| D8 | Results and corrections |

The decision rule never changed.
