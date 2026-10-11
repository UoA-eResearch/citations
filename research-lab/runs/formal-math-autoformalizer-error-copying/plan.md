# Preregistration: do open autoformalizers copy the documented defects of miniF2F and ProofNet? An error-copying test with number-perturbed twins

Lead: `formal-math-autoformalizer-error-copying` (research-lab/leads.json). Written 12 October 2026. Committed before
any defect tagging, Lean check of the references, twin construction or model sampling.

## What has been seen before writing (disclosure)

- **Novelty check (12 October 2026; `NOTES_pre_plan.md`).** No study tests whether autoformalizers reproduce the
  known defects of benchmark formal statements. The nearest pieces of work:
  - arXiv 2606.14867, proof autoformalization under number and symbol perturbations;
  - arXiv 2511.03108 (miniF2F-Lean Revisited). It says the v1→v2 accuracy drop of Herald and Kimina "suggests"
    contamination, but does not test it;
  - paraphrase robustness (arXiv 2511.12784, 2604.23135);
  - the atp-checkers defect catalogue (arXiv 2606.29493).
- **Data on disk** (commits in `NOTES_pre_plan.md`):
  - DeepSeek-Prover-V1.5's `datasets/` (`minif2f.jsonl`: the 488 v1 Lean 4 statements with the v1 informal
    statements; `proofnet.jsonl`: 371 items of the original ProofNet Lean 4 port);
  - miniF2F-v2 (v2s, v2c), the minif2f-v2-audit findings, ProofNet# (valid 185, test 186), the current
    rahul3613/ProofNet-lean4 port, atp-checkers, and the Herald translator repository (for its prompt).
- **Models on disk:** Kimina-Autoformalizer-7B (ddd47cb), Goedel-Formalizer-V2-8B (fe2d362), Herald_translator
  (c819f87) and Qwen2.5-7B-Instruct (a09a354). DeepSeek-Prover-V2-7B (a8d9e14) is on disk from the
  contamination run (`../formal-math-certified-contamination-did/data/models/`). The model cards are in
  `data/model_cards/`. Every model was released before miniF2F-v2 (November 2025): the latest, Goedel-Formalizer-V2,
  was created on the Hub on 20 July 2025.
- **Inspected so far:**
  - counts of changed statements (miniF2F v1→v2s: 253 formal changes; ProofNet→ProofNet#: 156 of 349 unique names);
  - 8 random v1→v2s diffs, read to design the rubric;
  - which items have numerals in their informal statement (483 of 488 miniF2F, 201 of 371 ProofNet);
  - that DeepSeek's ProofNet order does not match ProofNet#'s.
- **Power simulation:** `code/power.py`, output in `results/power.txt` (section 7). It uses no data.
- **Not done:** no model has been sampled, no Lean check has been run on any statement, and no item has been tagged.

## 1. Question and hypothesis

Lean Workbook and similar training sets were synthesized from miniF2F and ProofNet, so autoformalizers may have seen
the benchmarks' own formal statements. If a model has memorized them, it should reproduce a benchmark statement's
*mistake* when given that benchmark problem, but not when given an isomorphic problem whose numbers differ. A model
that merely falls into the same natural Lean pitfall (truncating ℕ division, a missing positivity hypothesis) would
make the analogous mistake on both.

**H (primary, from the lead).** Take the items whose original formal statement has a documented semantic defect
(section 2). Given the original informal statement, open autoformalizers output a formalization certified equivalent
to the defective original at least 3 times as often as they output the analogous defect for number-perturbed
isomorphic twins of the same items. The pooled rate ratio's item-cluster bootstrap 95% CI must have a lower bound above
1.5.

## 2. The defect catalogue

### 2.1 Candidate items

| Source | Defective original D | Corrected reference C | Input NL |
|---|---|---|---|
| miniF2F (488) | v1 Lean 4 statement (DeepSeek-Prover-V1.5 `minif2f.jsonl`) | miniF2F-v2s statement of the same name | v1 informal statement (`informal_prefix`, comment markers stripped) |
| ProofNet (371) | original Lean 4 port (DeepSeek-Prover-V1.5 `proofnet.jsonl`) | ProofNet# statement | the original ProofNet informal statement from the same file |

- **v2s, not v2c.** v2s corrects the statement of the same problem; v2c also changes the problems.
- **Matching ProofNet items.** Items are matched on split and exercise name. When a name occurs more than once
  (22 names repeat across textbooks), the ProofNet# item with the most similar informal statement is used (difflib
  ratio). Pairs with a ratio below 0.8 are dropped.
- **Candidates.** An item is a candidate if D and C differ after normalisation. Normalisation strips the header, the
  theorem name and `:= by` / `:=`, collapses whitespace and rewrites `∑ x in` as `∑ x ∈`.

### 2.2 Mechanical filters (Lean; before tagging)

- **Environment.** Statements are checked with the conventions of `../formal-math-certified-contamination-did/code/
  certify.py` (autoImplicit off; bare `π` read as `Real.pi`), first in Lean 4.9 with DeepSeek-V1.5's Mathlib, then in
  Lean 4.15 with Mathlib v4.15.0. The item's environment is the first in which both D and C elaborate. If they elaborate
  together in neither, the item is dropped.
- **Equivalence.** Pairs certified equivalent in both directions by the bidirectional portfolio (`certify.check`, 20 s
  per direction) are dropped as rewrites.
- **Attrition** at each step is reported by source.

### 2.3 Blind defect tagging

Two independent raters tag every surviving candidate:

- **Rater A:** a Claude Opus 5.5 subagent.
- **Rater B:** a Claude Fable 5.1 subagent.

**What each rater sees.** The informal statement and two formal statements labelled A and B, in a random order set by
a seed (20261012). It does not see which statement is the original, the source, the theorem name (replaced by `X`) or
the other rater's tags. Items come in batches of about 40.

**What each rater returns,** for each of A and B:

- **Faithful or unfaithful to the informal statement.** "Faithful" means that the formal statement's objects,
  hypotheses and claim match the informal problem. Benign Lean conventions are faithful, for example stating "show
  that the answer is 65" as an equation.
- **If unfaithful, one category:**
  1. wrong constant or answer;
  2. missing hypothesis or condition;
  3. extra or stronger hypothesis;
  4. wrong domain or type (for example ℕ for ℝ, or truncating division or subtraction);
  5. wrong quantifier, scope or binding;
  6. wrong relation, operator or formula;
  7. weakened or trivial conclusion;
  8. vacuous or contradictory hypotheses;
  9. other.
- **A one-line reason.**

**Inclusion (primary).** Both raters tag D unfaithful and C faithful. Items that either rater tags otherwise go to the
**one-rater set**, a sensitivity analysis, if at least one rater tags D unfaithful and C faithful. The defect category
is Rater A's, and agreement on it is reported (Cohen's κ for faithfulness).

**Negative control.** These are the minif2f-v2-audit items with `v2_miscorrection = true` (8): the v2 edit introduced
the defect, and the v1 statement was faithful. Here D is the v2s statement and C the v1 statement. No model in the study
can have seen v2, so the rate at which models output these defects estimates the natural rate of those particular
mistakes. Items pass the same Lean filters, are not tagged, and are reported descriptively.

atp-checkers is not used. It needs Lean 4.30 and a separate Mathlib build in which the 2024-era statements would have
to be ported. The audit's other findings (defects that v2s did not fix) have no corrected reference and are not used.

## 3. Twins and paraphrases

### 3.1 Number-perturbed twins (condition T)

**Construction.** For each included item, a constructor subagent (Claude Opus 5.5) builds one twin, given N, D, C and
the protocol below:

- **The substitution.** Choose a substitution σ of the problem's numerical parameters, and apply it consistently to
  N, D and C. The new values must keep the problem well-posed and of similar difficulty.
- **The answer.** Recompute any stated answer, including the correct choice of a multiple-choice problem, so that the
  corrected twin C' is true. Record the computation as a short Python or sympy script.
- **The analogous defect.** Where D's defect involves a number with no counterpart in N (for example a wrong constant),
  carry the defect over by the same rule (the same offset, factor or relation) and state the rule.
- **Return:** N', D', C', σ, the answer script, and the span of any answer expression that changed form.

**Mechanical checks (scripted).** A twin is kept only if all of these hold:

1. D' and C' elaborate in the item's environment.
2. D' and C' are not certified equivalent in both directions: the defect survives.
3. The token-level diffs N→N', D→D' and C→C' change only numerals, apart from the declared answer span, and at least
   one numeral in N changes.
4. The answer script reruns and returns the value stated in N' and C'.
5. The portfolio cannot prove ¬C' (the negation of the closed statement) within 20 s.

Items without a valid twin are excluded from the primary test, and the attrition is reported by source and category.
A twin that fails may be rebuilt once, with the failure message, before it is dropped.

### 3.2 Meaning-preserving paraphrases (condition P; secondary)

- **Writing them.** A Claude Opus 5.5 subagent rewrites N with every number, object and claim kept and the wording
  changed. It gives one paraphrase per item, for every item that passes 2.3.
- **Checking them.** A Claude Fable 5.1 subagent, blind to which text is the original, judges whether the two texts
  state the same problem. Paraphrases judged different are dropped.
- **References.** P uses D and C as references.

The catalogue (items, tags, twins and paraphrases) is committed and frozen before any model is sampled.

## 4. Models, prompts and sampling

**Models.** Three dedicated autoformalizers make up the primary pool. Two more are secondary:

| Model | Role | Prompt |
|---|---|---|
| Kimina-Autoformalizer-7B (ddd47cb) | primary | The model card's prompt: system "You are an expert in mathematics and Lean 4."; user "Please autoformalize the following problem in Lean 4 with a header. Use the following theorem names: my_favorite_theorem.\n\n{N}" |
| Goedel-Formalizer-V2-8B (fe2d362) | primary | The model card's prompt, with theorem name `my_favorite_theorem`; it thinks before answering; the last ```lean4 block is used |
| Herald_translator (c819f87) | primary | The repository's template: "Please translate the natural language statement to Lean4 code with the header\n**Name**\n{name}\n**Informal statement**\n{N}\n", in the DeepSeek chat format, with name `my_favorite_theorem` |
| DeepSeek-Prover-V2-7B (a8d9e14) | secondary | Chat template; user "Translate the following problem into a Lean 4 (Mathlib) theorem statement named my_favorite_theorem, ending with `:= by sorry`. Do not prove it.\n\n{N}" |
| Qwen2.5-7B-Instruct (a09a354) | secondary (general-model control) | The same instruction with the three fixed examples below |

**The name is neutral in every condition.** The original theorem name (for example `mathd_algebra_478`) would itself
be a memorization cue, and twins cannot carry it.

**Qwen's few-shot examples.** They were written for this plan and are not from any benchmark:

- "Find the real number x such that 2x + 3 = 11. Show that x = 4." →
  `theorem my_favorite_theorem (x : ℝ) (h : 2 * x + 3 = 11) : x = 4 := by sorry`
- "Prove that n^2 + n is even for every natural number n." →
  `theorem my_favorite_theorem (n : ℕ) : Even (n ^ 2 + n) := by sorry`
- "Let G be a group in which every element is its own inverse. Prove that G is abelian." →
  `theorem my_favorite_theorem {G : Type*} [Group G] (h : ∀ g : G, g * g = 1) (a b : G) : a * b = b * a := by sorry`

**Sampling.** For every model × item × condition (O, T, P) there are 16 samples at temperature 0.8 (top_p 0.95) and
one greedy sample.

- **Lengths:** at most 2,048 new tokens; 16,384 for Goedel-Formalizer-V2, which thinks first.
- **Seeds:** fixed (20261012 plus the sample index).
- **Serving:** bf16, each model in turn from a temporary vLLM container. The lab owner's `vllm` container is stopped
  for the GPU stage and restarted by a trap on exit, as in `../formal-math-certified-contamination-did/code/
  run_gpu.sh`.

**Extraction.** The last ```lean or ```lean4 block is used, or the whole output if there is none. From it the first
`theorem` or `lemma` is taken, with any preceding `open` lines. The proof is dropped (`:= by …`, `:= sorry`). An output
with no declaration counts as "no statement".

## 5. Classifying outputs (Lean)

Each output O is compared with the item's references: D and C for conditions O and P, D' and C' for condition T. All
checks run in the item's environment.

- **Does not elaborate:** O fails to elaborate there (including "no statement").
- **Defect copy:** O ≡ D, meaning both O → D and D → O are certified by `certify.check` (20 s per direction).
- **Correct:** O ≡ C, by the same test.
- **Other:** O elaborates and is equivalent to neither.

Identical normalised outputs within an item × condition are checked once. An output certified equivalent to both
references would mean D ≡ C, which the filters rule out. If it happens it is logged and counted as "other".

**Verbatim copy (secondary).** O's normalised text equals normalised D, with the theorem name replaced by `X` and the
hypothesis names kept.

## 6. Primary test and decision rule

**The estimand.** It is computed on the included items with a valid twin, over the three primary models' temperature
samples:

- x_O = the number of defect copies in condition O;
- x_T = the number of analogous defects (O ≡ D') in condition T;
- n_O = n_T = items × 3 × 16;
- RR = ((x_O + 0.5) / n_O) / ((x_T + 0.5) / n_T).

The 0.5 keeps RR finite and pulls it towards 1.

**The interval.** A percentile interval from 2,000 item-cluster bootstrap resamples (seed 20261012). Each draw
resamples items with all their samples.

**The decision.**

- **Supported:** RR ≥ 3 and a lower bound above 1.5.
- **Refuted:** an upper bound below 3.
- **Inconclusive:** otherwise. The test is also Inconclusive if x_O + x_T < 20, since there is then too little
  defect output to compare.

The report also says, descriptively, whether the lower bound is above 1: any excess of copying over the natural rate.

## 7. Power

`code/power.py` applies the rule above to simulated item-clustered binomial data (3 models, 16 samples, 300 simulations per
cell, and 400 bootstrap draws per simulation instead of 2,000). The twin defect rate r is drawn per item and model from a Beta
distribution with mean r and concentration 2. A fraction f of items is memorized and copies the defect at rate 0.5 on
originals. The full output is in `results/power.txt`.

| Items | r | True RR | P(Supported) | P(Refuted) |
|---:|---:|---:|---:|---:|
| 100 | 0.03 | 2.6 | 0.26 | 0.11 |
| 100 | 0.03 | 4.1 | 0.96 | 0.00 |
| 100 | 0.05 | 2.8 | 0.38 | 0.07 |
| 100 | 0.05 | 3.7 | 0.90 | 0.00 |
| 100 | 0.05 | 1.9 | 0.00 | 0.71 |
| 100 | 0.05 | 1.0 | 0.00 | 1.00 |
| 60 | 0.05 | 3.7 | 0.82 | 0.00 |

**Minimum detectable effect.** With 60-150 items and twin defect rates of 3-5%, the rule returns Supported with at
least 80% power at a true RR of about 3.7-4.1. For a true RR ≤ 1.5 it returns Refuted with probability at least 0.85.
A true RR of 2.5-3 mostly gives Inconclusive; near 2 the rule often returns Refuted (probability 0.5-0.9).

**When there are too few items.** If fewer than 40 items have a valid twin, the plan's MDE no longer holds. The test is
still run and the report says so.

## 8. Secondary and exploratory analyses (all reported; none changes the verdict)

1. **By model:** RR for each of the five models.
2. **Originals against paraphrases (O vs P):** memorization keyed to the exact wording.
3. **Greedy outputs:** the defect-copy share in each condition.
4. **Verbatim copies of D:** how often they occur in O and in P.
5. **By source and category:** RR for miniF2F and ProofNet separately, and by defect category.
6. **Accuracy inflation:** the correct rate (≡ C) and the rate of equivalence to the benchmark's own reference (≡ D)
   in O against T. "Accuracy" against a v1 reference credits defect copies.
7. **Negative control:** the rate of v2-introduced defects (section 2.3), descriptive.
8. **Sensitivities:**
   - the one-rater item set;
   - twins whose C' the portfolio proves (truth certified);
   - rates among elaborating outputs only.
9. **Classification rate:** the share of elaborating outputs classed "other", by model and condition. A certifier that
   recognises verbatim copies more readily than reworded ones would favour condition O. This is reported, and the
   verbatim analysis (item 4) bounds it.

## 9. Order of work and compute

1. Commit this plan.
2. Build the candidates, run the Lean filters (section 2.2) and commit.
3. Run the blind tagging (section 2.3) and commit the tags and inclusions.
4. Build and check the twins and paraphrases (section 3), then commit the frozen catalogue.
5. Sample on the GPU (section 4).
   - About 120 items × 3 conditions × 5 models × 17 samples ≈ 30,000 generations, a few GPU-hours on the A100.
   - Stop the `vllm` container first and restart it immediately afterwards.
6. Run the Lean classification (section 5) on CPU, with identical outputs de-duplicated.
7. Analyse, write the report and get an independent adversarial review.

Every departure from this plan is logged in `deviations.md` with a timestamp, before the outcome it could affect is
seen, wherever that is possible.

## 10. Reporting

The report gives the verdict by the rule in section 6, with x_O, x_T, n and the bootstrap interval. It also gives the
attrition at every step, the per-model results and every secondary analysis.

**Released** (derived from open data): the catalogue (items, tags, twins, paraphrases), the classifier code and
per-output classifications. The raw model outputs are released as well (open weights; no licence restriction).
