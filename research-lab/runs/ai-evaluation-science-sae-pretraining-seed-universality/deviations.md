# Deviations from the preregistration (plan.md, commit 3e34053)

## D1 - 2026-10-12 16:18 NZDT - pilot, budget, a bug the matching test caught, and the order of validation (before any full-budget SAE was trained)

1. **Pilot and token budget** (plan sections 3 and 9.2).
   - **Run.** One sparsify run on the original model (six SAEs, 2,048 sequences, 4.2 million tokens) ran at 1.16-1.24
     steps per second, at 65,536 tokens per step.
   - **Projection.** 200 million tokens therefore take about 45 minutes per model, and the 16 runs about 12.5
     GPU-hours.
   - **Decision.** That is below the plan's 72 GPU-hour limit, so the budget stays at 200 million tokens per SAE
     (97,657 sequences).
   - **Inputs.** The token stream is `data/train_tokens.bin`: 200,001,536 tokens from the 124,961 sequences of the
     Pile (uncopyrighted) validation split. H is 1,025 sequences drawn from 4,231 test-split sequences.
2. **A bug in `match.py`, caught by the test of plan 9.2 and fixed.**
   - **The test.** An SAE matched against itself gave f = 0.92 rather than 1.
   - **The cause.** `np.nanmean(best >= th)` counts the non-assessable latents (best = NaN) as unmatched, because
     comparing NaN with a threshold gives False, not NaN.
   - **The fix.** The fraction is now taken over finite entries only (`match.frac`).
   - **Re-run.** After the fix, `code/test_match.py` passes: self and permuted copy f = 1.0; random SAE 0.003 and
     0.002; decoder cosine of self 1.0; Procrustes rotation of a model onto itself the identity, to 1e-4.
   - **Context.** On 262,016 tokens of H, the pilot SAE (4.2 million tokens of training) has FVU 0.226, against 0.113
     for EleutherAI's 8.2-billion-token reference. Pilot and reference match at f = 0.15 and 0.15. These are pilot
     numbers only; no full-budget SAE existed.
3. **`encode_model` takes the SAEs to encode as an argument**, so that the test can pass pilot, permuted, random and
   reference SAEs. The main path is unchanged.
4. **Order of work.** The step-0 checks (plan 9.3) run while the main training runs, not before it. Training does not
   depend on them; they only label the decoupled comparisons (plan section 7, item 2).
5. **Disk.** sparsify's optimizer state (1.2 GB per model) is deleted after each run completes. It is needed only to
   resume a run.

## D2 - 2026-10-12 16:21 NZDT - validation checks (plan 9.3), run while the main training ran; no SAE matched

- **Step-0 checkpoints** (`code/check_step0.py`, `results/tables/step0_check.csv`).
  - **Data-seed variants.** The step-0 checkpoints of `pythia-160m-data-seed1..3` are identical to the original's,
    in all 184 tensors.
  - **Weight-seed variants.** Those of `pythia-160m-weight-seed1..3` differ: 134 of 184 tensors are identical, the
    maximum absolute difference in the rest is about 0.19. The identical tensors are presumably the biases and
    normalisation parameters, which start at constants.
  - **Effect.** The decoupled labels hold as the plan assumed: the data-seed variants share the original's
    initialisation, and the weight-seed variants do not. The plan's comparisons need no relabelling. That the
    weight-seed variants share the original's data order rests on the PolyPythias paper; it cannot be checked from
    the weights.
- **Tokenizers.** The `tokenizer.json` files are not byte-identical across the 16 repositories: 12 serialise the BPE
  `model` section differently. All 16 have the same vocabulary and give identical ids on the first 20,000 tokens of
  the training text. The training stream and H, tokenized once with the original's tokenizer, are therefore valid
  inputs for every model.

## D3 - 2026-10-12 16:22 NZDT - dry run of the matching pipeline (pilot SAEs only; outputs deleted)

`match.py` takes three environment overrides for dry runs: `SAE_ROOT`, `MATCH_TAG` (suffix for every output file)
and `N_SEQ` (fewer sequences of H). The main run sets none of them.

**The dry run.**

- **Pairs.** The three within pairs of the pilot SAEs on the original model, and one cross pair in which the pilot
  SAEs were applied to `pythia-160m-seed1`'s residual stream. The cross pair has no meaning; it only exercises the
  cross-model path and the Procrustes rotation.
- **Data.** 64 sequences of H.
- **Result.** It ran end to end, including the reference comparison. Its `*_dryrun` outputs were deleted.
- **What it did not touch.** No full-budget SAE was involved. The first main training run was still in progress.

## D4 - 2026-10-13 05:42 NZDT - main training finished; matching started; figure code; a docstring correction (no pair score seen)

- **Training.** All 16 runs finished between 16:18 on 12 October and 05:38 on 13 October NZDT (about 49-52 minutes
  each), with no failure and no error, NaN or traceback in any log. All 96 SAEs (16 models × 2 layers × 3 seeds) were
  saved, about 201 MB each.
- **Matching** (`code/run_match.sh`) started at 05:39 NZDT.
- **Figure code** (`code/figures.py`) was written and tested on the mock tables while the matching ran, and is committed
  before any pair score is seen.
- **Docstring correction.** `match.dec_cos_best` says it takes the maximum |cosine|. The code takes the maximum signed
  cosine. The signed version is the right quantity here: SAE activations are non-negative, so a decoder row and its
  negation are different features. The code is unchanged; only the description was wrong. The report describes the
  signed cosine.

## D5 - 2026-10-13 06:10 NZDT - matching finished; primary and secondary analyses run; two post-hoc exploratory checks

- **Matching** finished at 06:07 NZDT: 246 pairs at each layer, about 15 minutes per layer.
- **Analysis.** `code/analysis.py` ran unchanged at 06:09 NZDT, then `code/figures.py`.
- **Post hoc, exploratory** (`code/exploratory.py`, written after the primary and secondary results were seen; not
  in the plan; it changes no verdict). The decoder-geometry secondary analysis (plan 7.5) showed a pattern the plan
  did not anticipate:
  - **The pattern.** The raw decoder cosine is never ≥ 0.5 across full seeds, but it is for 3-8% of latents across
    the seed-0 lineage. That includes pairs of a weight-seed and a data-seed variant, which share neither the
    initialisation nor the data order.
  - **Init check.** Step-0 weights of `weight-seed1` correlate with the original's at about 0.000 in all 50 weight
    tensors (embedding, attention, MLP, unembedding). Their initialisation is independent, as labelled.
  - **(a) Outlier dimensions.** Do the models share privileged residual coordinates? The check takes, per model and
    layer, the top-10 residual dimensions by mean square.
  - **(b) McCann's central claim.** An SAE trained on one seed reconstructs another seed's residual stream badly, and
    an orthogonal rotation restores it. The check tests this directly: B's seed-0 SAE on A's residual stream, raw,
    Procrustes-rotated and least-squares mapped. The maps are fitted on sequences 0-127 of H and evaluated on
    sequences 128-255. It also records how well each map predicts B's residual stream from A's.

## D6 - 2026-10-13 06:41 NZDT - the weight-seed variants were not trained from their own initialisation (post hoc; corrects D2; its step-1 evidence, its "plan section 2" framing and its outlier-dimension sentence are corrected in D8)

**What D5's exploratory checks showed.**

- **Shared outlier dimensions.** All seven models of the seed-0 lineage share their top residual dimensions by mean
  square: dimensions 393, 684, 411, 625 and 634 head the list at layer 4 in all seven. Each of seeds 1-9 has its own
  distinct set (`results/tables/exploratory_outliers.csv`). Shared privileged coordinates point to a shared
  initialisation, which D2 had ruled out for the weight-seed variants.

**The check** (`code/lineage_check.py`, post hoc; `fetch.py early` downloaded step 1 and step 1000 of the original,
seed1, weight-seed1..3 and data-seed1).

- **Method.** Median correlation, over the 50 weight matrices, between each model's weights and each available step-0
  checkpoint.
- **Weight-seed variants against the original's step 0.** Step 1 correlates 1.000, step 1000 0.892-0.893, and the
  final checkpoint 0.068-0.069. These are the same values as for the original's own run (1.000, 0.892, 0.068).
- **Weight-seed variants against their own released step 0.** 0.000 at every step.
- **Control.** `pythia-160m-seed1` correlates 0.000 with every one of these step-0 checkpoints.
- **Pairwise at step 1000.** The weight-seed variants are closer to the original (0.977-0.980) than data-seed1 is
  (0.964).
- **Pairwise at the end.** All are about equally far apart (0.17-0.21; `results/tables/lineage_pairwise.csv`).

**This is a known defect, which the pre-plan checks missed.** EleutherAI/pythia issue #203, open since 21 July 2026,
reports it: <https://github.com/EleutherAI/pythia/issues/203>. Its 3 October 2026 comment adds three points:

- the weight-seed runs' step 1 is bitwise identical to the original's step 1;
- their published step-0 branches are copies of `pythia-160m-seed4..6`;
- their first training batch appears to be the original run's.

D2 compared only the step-0 checkpoints, so its conclusion that "the decoupled labels hold as the plan assumed" is
wrong for the weight-seed variants. Plan section 2's rule applies: "the decoupled comparisons are relabelled by what
the checkpoints show".

**Relabelling.** It is used for the decomposition (plan 7.2) and the decoder and exploratory analyses; the primary
statistic uses only the 10 full seeds and is unaffected.

| Kind in `pairs.py` | Preregistered label | What the checkpoints show |
|---|---|---|
| `init` | only the initialisation differs | Same initialisation and, per #203, the same first batch. The variants differ from the original in some way the artifacts do not identify: issue #203 suggests numerical nondeterminism or a later data-order change. Called "near-replicate" in the report. |
| `data` | only the data order differs | As labelled. Same initialisation; different batch composition. |
| `both_dc` | both differ (a weight-seed against a data-seed variant) | Same initialisation; different batch composition. This is effectively a second set of data-order pairs. |
| `full` | both differ | As labelled. Seeds 1-9 each start from their own initialisation (control above). |

- **Consequence.** No comparison in this study varies the initialisation alone. The only pairs that differ in
  initialisation are the full-seed pairs, which also differ in data order.
- **The 3-8% raw decoder alignment** in D5 is explained: all seven lineage models share the original's
  initialisation.
- **Analysis code** is unchanged. The report gives the decomposition under both the preregistered and the corrected
  labels.

## D7 - 2026-10-13 06:43 NZDT - one more post-hoc exploratory analysis (conditional replication)

- **Script.** `code/exploratory_conditional.py`, written after the results were seen and before it was run.
- **Question.** Are the latents that replicate across SAE seeds of one model the same ones that replicate across
  pretraining seeds?
- **Method.** For every SAE of the 10 full-seed models, and each of its assessable latents:
  - count the within pairs (0, 1 or 2) in which the latent has a match at r ≥ 0.7;
  - compute the share of its 9 full pairs in which it has one.
- **Data.** It uses only the stored per-latent arrays.
- **Status.** Exploratory; it changes no verdict.

## D8 - 2026-10-13 07:20 NZDT - independent review (publish with edits, 13 issues) and the changes made

- **Review.** `review/review.md` (Fable 5.1), on the pre-review draft 4928313: publish with edits, 13 issues. The
  reviewer re-derived the primary statistic and re-implemented the matching densely. Both reproduce, and no number
  or verdict changes.
- **Analyses requested by the review** (`code/review_fixes.py`, post hoc, exploratory; written before it was run):
  - (a) the firing-frequency table with the within row restricted to the 10 full-seed models (issue 13);
  - (b) D7 stratified by firing-frequency tercile (issue 11);
  - (c) outlier-dimension counts across the lineage (issue 9);
  - (d) ||R − I||_F and det(R) of the Procrustes maps for every cross-model pair (issue 8).
- **Changes made in response, by issue:**
  1. **McCann's claims restated.** For Pythia-70m he reports post-rotation explained variance of 0.85-0.99; the
     "within 0.025" gap is his toy model's. His intermediate-layer decoder match is ≥ 99%, falling to 62% at the final
     layer. His setting is now listed: ReLU + L1 SAEs on 256 × 256 tokens at seven residual sites. Verified against
     the paper's text.
  2. **D6's step-1 evidence withdrawn.** The step-1 checkpoints equal step 0, because the learning-rate warm-up starts
     at zero. D6's conclusion rests on step 1000 (0.892-0.893 against the original's step 0, 0.000 against their own)
     and on the final checkpoints. #203's first-batch claim is attributed to #203 and marked as not verified here.
  3. **The relabelling is called post hoc.** The plan's step-0 check had passed. A pattern in the results triggered
     the relabelling, and checkpoints outside the plan justified it.
  4. **The decomposition reading is narrowed.** The report no longer offers an "amplification" reading. "Near-replicate"
     is replaced by "same initialisation, perturbation unidentified". The value of a shared initialisation is now "at
     most about one point, not resolvable".
  5. **Wording on independence.** The subtitle and the plain summary no longer call all 16 runs independent.
  6. **Scope of the verdict.** It is stated in the summary and the plain terms: r ≥ 0.7, layers pooled; r ≥ 0.9 would
     be Supported; layer 8 alone is 0.817. "Noise" became "irreproducibility".
  7. **The reference-SAE inference is weakened** to what it shows.
  8. **The outlier-dimension caveat is replaced** by the review's test: standardising or dropping outlier dimensions
     does not help the orthogonal map. ‖R − I‖_F (39.12-39.28 against √1536 = 39.19 for full pairs; 22.9-26.6 for
     lineage pairs) and det(R) were computed for every pair. "Rotation" became "orthogonal map" where accuracy needs
     it: about half the maps are reflections.
  9. **Outlier-dimension counts.** Stated exactly from `review_outliers.csv`.
  10. **Disclosure gaps** (see below).
  11. **D7 framing.** It is now a precision filter, with pooled rates. The tercile-stratified table was added: the
      pattern holds inside every tercile.
  12. **Paulo & Belrose.** The comparison is marked as loose: different site and criterion.
  13. **Frequency table.** It now uses the 10 full-seed models in both rows. The figure stays the preregistered
      16-model version, with a caption note.
- **Disclosure gaps (issue 10):**
  - (a) `code/figures.py` was edited after the results, at 06:41 (commit b7c45a6), and again now. The changes are the
    decoupled kinds' labels per D6, captions and the key-result tiles; the plotted quantities are unchanged.
  - (b) `code/lineage_check.py` was committed together with its outputs (138e1a5); it is post hoc.
  - (c) D5 says the analysis ran at 06:09 NZDT. Its output files are stamped 06:07:54; the 06:09 was the approximate
    time I noted.
- **Other edits.**
  - The Limitations section now says that SAE-seed variation is averaged out. Each model pair's three SAE-seed
    combinations have a standard deviation with a median of 0.0013-0.0017, at most 0.004. The results are conditional
    on one SAE training stream and one held-out set.
  - No number in the primary or secondary analyses changed.

## D9 - 2026-10-13 07:26 NZDT - token-identity check (post hoc; written before it is run, during the confirmation pass)

- **Why.** The lead's risk note said that activation matching across models may be inflated by token-identity
  features, which every model has, and suggested stratifying them out. The plan did not include this, and neither the
  report nor the review addressed it.
- **The check** (`code/token_identity.py`).
  - **Purity.** Per latent of the 30 SAEs of the 10 full-seed models, at both layers: the share of its firings on H
    that fall on its most frequent input token.
  - **Token-identity latent:** purity ≥ 0.5.
  - **Outputs.** Within and cross match rates for token-identity and other latents. The primary statistic is
    recomputed with the directional scores restricted to non-token latents as sources. Candidates are unchanged,
    because the stored best-match arrays do not allow restricting them.
- **Status.** Exploratory; it does not change the verdict.
- **Result** (logged 07:39 NZDT, after it was seen).
  - **Token-identity latents** are 28.5% of assessable latents at layer 4 and 23.5% at layer 8. They match more often
    both within (0.645, 0.594) and across runs (0.606, 0.524) than other latents (within 0.391, 0.362; across 0.343,
    0.283).
  - **Without them as sources:** R = 0.833 (0.829-0.837), Refuted. Layer 4 is 0.878 (0.872-0.884). Layer 8 is 0.784
    (0.779-0.790), below 0.8.
  - **Timing.** The per-layer intervals were added to the script after the pooled result had been printed. It was
    rerun from the cached purities. The pooled numbers are unchanged.
  - **The preregistered verdict is unchanged.** The report now gives this result prominently as a qualification.
