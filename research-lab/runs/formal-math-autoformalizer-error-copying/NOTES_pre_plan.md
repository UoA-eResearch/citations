# Pre-plan notes (12 October 2026): novelty check and format probes only; no model has been sampled

**Novelty check.** Passed on 12 October 2026.

- **arXiv 2606.14867** (Gui, Yang, Shi; proof autoformalization robustness). It perturbs numbers, symbols and steps in
  natural-language *proofs* and labels outputs faithful, reverted or unclear. The closest probe, but it does not test
  copying of *statement* defects or frame the result as memorization.
- **arXiv 2511.03108** (miniF2F-Lean Revisited / v2). It notes that Herald and Kimina decline from v1 to v2 while
  o4-mini improves, and that this "suggests that current autoformalizers may suffer from data contamination". It does
  not test that.
- **Paraphrase robustness:** 2511.12784 and 2604.23135.
- **Defect catalogue:** 2606.29493 (atp-checkers).

**Data on disk.** The repos were cloned into `data/raw/`:

| Source | Commit | What it holds |
|---|---|---|
| `roozbeh-mohit/miniF2F_v2` | 905eca8, 2025-11-17 | v2s / v2c jsonl: name, split, informal statement, formal_statement, header |
| `ibrahimmian36/minif2f-v2-audit` | 9e38e22, 2026-09-28 | 23 v2s findings; 8 introduced by the v2 edit, original v1 faithful |
| `Shashi456/atp-checkers` | 3e7e99d, 2026-04-28 | defect checkers |
| ProofNet# (`PAug/ProofNetSharp` @ a8da405fbd) | | test 186, valid 185 |

**Already on disk from the contamination run** (`../formal-math-certified-contamination-did/data/statements/`):
`bench_minif2f.parquet` (v1 Lean 4, 488), `bench_minif2f_v2c.parquet`, and `bench_proofnet.parquet`. The last is the
371 ProofNet# items, not the original port.

**Design implications.**

- **The memorizable defects are the originals.** They are the miniF2F v1 Lean 4 statements that v2 corrected, and the
  original ProofNet Lean 4 port (rahul3613/ProofNet-lean4) that ProofNet# corrected. All candidate autoformalizers
  were trained before miniF2F-v2 appeared (November 2025).
- **The audit's v2-introduced defects cannot have been memorized** by those models, so they serve as a natural
  negative control.
- **Still needed:** the v1 informal statements (the input the formalizers would have seen in Lean Workbook) and the
  original ProofNet Lean 4 port.

## Format probes, 12 October 2026 (counts only; no model sampled, no Lean check run)

**Two more sources, cloned into `data/raw/`.**

| Repository | Commit | What it holds |
|---|---|---|
| `deepseek-ai/DeepSeek-Prover-V1.5`, `datasets/` only | 2c4ba91 (2024-08-16) | `minif2f.jsonl`: the 488 v1 Lean 4 statements with v1 informal statements as `informal_prefix`. `proofnet.jsonl`: 371 items of the original ProofNet Lean 4 port, with NL. |
| `rahul3613/ProofNet-lean4` | 6deae98 (2025-06-09, Lean v4.20.0) | The current port, 374 items |

**How much changed (normalised strings: header, name and `:= by` stripped, whitespace collapsed).**

| Comparison | Formal changed | NL changed | Formal changed, NL unchanged |
|---|---:|---:|---:|
| miniF2F v1 → v2s (488 items) | 253 | 133 | 181 |
| miniF2F v1 → v2c (488 items) | 303 | 106 | not counted |
| ProofNet (DSP-V1.5 copy) → ProofNet# (349 unique names) | 156 | 14 | not counted |

**ProofNet names are not unique.** 22 names repeat across textbooks, so items must be matched by order or by textbook
prefix, not by bare name.

**Not every change fixes a defect.** For example, v2s rewrites `mathd_algebra_478` with a units variable `u`, which is
a change of style. Defect tagging (error vs style) must therefore be preregistered and done before any sampling.

## Design notes, 12 October 2026 (from reading 8 random v1→v2s diffs; no model sampled, no Lean check run)

**Most v2 changes are not v1 defects.**

- **Rewrites and equivalences:** `∑ k in` → `∑ k ∈`; `0 < x` → `1 ≤ x` on ℕ.
- **Changes of style:** `mathd_algebra_329` rewritten over `EuclideanSpace`.
- **Arguable cases:** `mathd_algebra_43` (v1 proves that 3 is an intercept, v2s that it is the unique one);
  `mathd_algebra_392` (v1 shifts the three consecutive numbers).
- **Genuine v1 defects:** `induction_1pxpownlt1pnx` adds a hypothesis `0 < n` that the NL does not state.
- **Changes the audit counts as v2 miscorrections:** `numbertheory_aneqprodakp4_anmsqrtanp1eq2` moves ℝ → ℕ.

**Consequences for the plan.**

1. **Defect status needs an explicit rubric, applied before any sampling.** Ideally a blind second rater (an
   independent subagent) tags v1 as unfaithful to the NL or not, with the category of error. Disagreements are
   resolved by a rule set in advance.
2. **Pairs certified equivalent are dropped first** (the bidirectional portfolio from the contamination run).
3. **atp-checkers is a linter, not a list of defects.** Running its high-confidence checkers (counterexample, vacuous
   hypotheses, unguarded natural-number subtraction or division) on the v1 statements gives an objective defect
   source. The natural-pitfall categories are exactly what the twin control is for.
4. **Truth of the twins.** Twin NL statements whose answers are not recomputed are false statements. The plan must
   choose between:
   - recomputing answers where computable (sympy, or Lean `norm_num`/`decide` on the corrected twin) and dropping
     the rest;
   - allowing false twins and reporting a true-twin subset as a sensitivity analysis.
