# Preregistration: certified training-test leakage in open Lean prover corpora, and whether it explains the reformulation drop on miniF2F

Lead: `formal-math-certified-contamination-did` (research-lab/leads.json). Written 7 October 2026 and committed before
any candidate retrieval, Lean certification or prover sampling.

## What has been seen before writing (disclosure)

- **Novelty check (7 October 2026).** No study was found that certifies training-test leakage in the Lean kernel and
  links it to prover performance. The nearest pieces of work:
  - **MiniF2F-ALF / Pythagoras-Prover (arXiv 2606.12594):** mutations used for training augmentation, not certified
    equivalent.
  - **"What are the Right Symmetries for Formal Theorem Proving?" (arXiv 2605.22257):** brittleness to equivalent
    statements, with no link to training data.
  - **Text-level decontamination:** Kimina's 13-gram matching; LeanPolish's goal-hash Jaccard.
  - **miniF2F-Lean Revisited (arXiv 2511.03108):** benchmark defects (miniF2F-v2).
- **Data downloaded, with revisions in `results/tables/revisions.json`.**
  - The benchmarks: AI-MO/minif2f_test (Kimina-revised, 244 items), DeepSeek-Prover-V1.5's `minif2f.jsonl` (244 valid
    + 244 test), miniF2F-v2, ProofNet# and PutnamBench.
  - Corpora: Goedel-Pset-v1 and internlm/Lean-Workbook.
  - Corpora already on disk from the vacuity study: DeepSeek-Prover-V1, Goedel's Lean-workbook-proofs,
    NuminaMath-LEAN, Goedel-Prover-V2's SFT_dataset_v2 and STP_Lean_0320.
- **Inspected so far:** each file's columns and first row. Also, 225 of the 244 Kimina test statements are textually
  identical to DeepSeek-V1.5's test statements; 19 are revised.
- **Not done:** no corpus has been searched for benchmark items, no Lean check has been run, and no prover has been
  sampled. (The vacuity study certified vacuity in samples of these corpora. That says nothing about overlap with
  miniF2F.)

## 1. Question and hypotheses

Open provers might do well on miniF2F partly because equivalent statements sit in their own training data. If so,
a reformulation that keeps the meaning but changes the text should hurt them more on leaked items than on clean ones.
A difference-in-differences separates that memorisation effect from general brittleness to rewording.

**H1 (primary).** On the 488 miniF2F items, the drop in pass@32 from the original statement to a reformulation
certified equivalent by the Lean kernel is at least 10 percentage points larger for items "leaked" relative to the
prover's own documented training corpora than for clean items. The test pools three open provers (section 4).

**H0 (descriptive, always reported).** The leak rate: the share of benchmark items with an L0, L1 or L2 match (section
3), by corpus and benchmark.

## 2. Benchmarks and corpora

**Primary benchmark:** 488 miniF2F items, being Kimina's revised test set (AI-MO/minif2f_test, 244) plus DeepSeek-V1.5's
validation set (244).

**Secondary benchmarks (leak rates only):** PutnamBench, ProofNet# and miniF2F-v2c.

**Corpora.** Formal statements are extracted from each:

| Corpus | Source of the statement |
|---|---|
| Goedel-Pset-v1 | `formal_statement` |
| Lean-Workbook | `formal_statement`, both splits |
| DeepSeek-Prover-V1 | `formal_statement` |
| NuminaMath-LEAN | `formal_statement` |
| Goedel's Lean-workbook-proofs | the theorem in `full_proof` |
| STP_Lean_0320 | the theorem in the prompt, unique statements |
| SFT_dataset_v2 | the theorem in the user prompt, unique statements |

**Each prover's own corpora**, from its paper, model card and dataset cards:

| Prover | Corpora |
|---|---|
| Goedel-Prover-V2-8B | Goedel-Pset-v1, SFT_dataset_v2, Lean-workbook-proofs |
| Kimina-Prover-Distill-8B | NuminaMath-LEAN |
| DeepSeek-Prover-V2-7B | DeepSeek-Prover-V1 (its documented public lineage; the V2 training set is not public) |

A secondary analysis defines a leak against all corpora for every prover.

## 3. Leak tiers (certified)

**Normalisation.** Remove the header, comments and the theorem name; collapse whitespace; drop `:= by` and anything
after it.

**Candidate retrieval** (no Lean; deterministic). For each benchmark item and corpus, take the union of:

- the top 10 statements by MinHash-estimated Jaccard similarity on character 5-grams of the normalised text (128
  permutations), with an estimate of at least 0.3;
- every statement with the identical multiset of numerals, provided it shares at least half of the item's
  identifiers.

**Tiers.**

| Tier | Meaning |
|---|---|
| L0 | The normalised texts are identical. |
| L1 | The Lean kernel proves train ⇒ test and test ⇒ train. |
| L2 | The Lean kernel proves train ⇒ test only, so the training statement is at least as strong. |

**Certification.** Each direction is a theorem of the form
`theorem chk : (∀ B_a, C_a) → (∀ B_b, C_b) := by intro h; intros; <portfolio>`. The portfolio is:

1. `exact h ..` style application followed by `assumption`, `norm_num`, `linarith`, `simp_all`;
2. `aesop`;
3. `simp_all`, then `linarith`/`nlinarith`.

Each direction gets 20 s. The axioms are restricted to propext, Classical.choice and Quot.sound, and `sorry` is
rejected. Binders and conclusions are split by the parser from the vacuity study.

**Lean environment.** Pairs from Lean 4.9 corpora are checked in the Lean 4.9 environment; NuminaMath-LEAN pairs in
Lean 4.15. A pair whose statements do not both elaborate is "unchecked".

**Leak status.** An item is leaked for a prover if it has an L0, L1 or L2 match in any of that prover's corpora.

## 4. Reformulations and prover runs

**Reformulations.** Two per benchmark item, by deterministic transforms:

- **R1:** rename every bound variable and hypothesis (a fixed renaming map) and reverse the order of independent
  hypotheses.
- **R2:** R1, plus flipping every equality (`a = b` to `b = a`) in the hypotheses and the goal.

Each must be certified equivalent to the original in both directions with the portfolio above. If it cannot be, the
item has no reformulation of that kind.

**Provers:** DeepSeek-Prover-V2-7B, Goedel-Prover-V2-8B and Kimina-Prover-Distill-8B, at exact revisions recorded at
download.

**Sampling.**

- vLLM; each model's documented prompt; temperature 1.0 and top-p 0.95 (DeepSeek and Goedel) or each model card's
  recommended values.
- At most 4,096 new tokens, the same cap for originals and reformulations. A truncated output counts as a failure.
- 32 samples per item version (original, R1, R2).
- Thinking modes are used as each model's default prompt specifies, under the cap.

**Verification.** Each proof is checked in that prover's environment:

- DeepSeek-Prover-V2 and Goedel-Prover-V2 in Lean 4.9 (DeepSeek-Prover-V1.5's environment);
- Kimina in Lean 4.15.

`sorry`, `native_decide`, new axioms and `admit` are rejected, and the axioms are checked as above.

**pass@32 per item version:** 1 if any of the 32 samples verifies, else 0.

## 5. Primary test and decision rule

**Unit:** an (item, prover) pair whose original and at least one certified reformulation have been sampled.

**Drop:** d = pass@32(original) − mean pass@32 over its certified reformulations.

**Estimand.** DiD = mean d over leaked pairs − mean d over clean pairs, pooled over the three provers. The interval is
an item-cluster bootstrap (resampling items with all their provers; 10,000 draws; one-sided 95%).

**Power and minimum detectable effect, computed before any sampling from the leak counts** (recorded in
`deviations.md`):

  MDE = 2.49 × 0.30 × sqrt(1/n_leaked + 1/n_clean),

where 2.49 = z(0.95) + z(0.80) and 0.30 is an assumed standard deviation of d. The standard deviation is
recomputed from the data as a secondary.

**Decision rule.**

| Verdict | Condition |
|---|---|
| **Supported** | DiD ≥ 10 pp, and the one-sided 95% lower bound is above 0. |
| **Refuted** | The one-sided 95% upper bound is below 10 pp, and the MDE is at most 10 pp. |
| **Inconclusive** | Anything else, including fewer than 20 leaked (item, prover) pairs. In that case the leak rates are the main finding. |

**Secondary analyses (labelled secondary).**

- The mixed logistic model at sample level, `success ~ reformulated × leaked + (1|item) + (1|prover)`.
- Each prover separately.
- L0/L1 leaks only.
- Leak status against all corpora.
- Excluding the 19 items Kimina revised.
- Leak rates for PutnamBench, ProofNet# and miniF2F-v2c, as a low-leak contrast.
- Per-sample pass rates instead of pass@32.

## 6. Compute and order

1. **Extraction, normalisation, L0 and candidate retrieval:** CPU, Python.
2. **Certification of candidates and reformulations:** Lean, after the vacuity study's rerun frees the CPUs.
3. **The MDE,** recorded before sampling.
4. **Prover sampling:** GPU. The lab owner's vLLM container is stopped for this stage and restarted afterwards, as
   authorised.
5. **Verification:** Lean.
6. **Analysis.**

## 7. Reporting

- "In plain terms" first.
- The pre-review draft is committed.
- The reviewer's prompt and full review are saved in `review/`.
- Departures from this plan are logged with timestamps.
- The leak-tier list (item, corpus, training id, tier) is published so that corpus maintainers can act on it.
