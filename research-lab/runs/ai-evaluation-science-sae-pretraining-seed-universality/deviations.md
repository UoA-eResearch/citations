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
