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

## D6 - 2026-10-13 06:41 NZDT - the weight-seed variants were not trained from their own initialisation (post hoc; corrects D2)

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
