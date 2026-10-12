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
