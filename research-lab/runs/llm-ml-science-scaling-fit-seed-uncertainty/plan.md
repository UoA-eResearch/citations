# Preregistration: how much does training-seed noise move a scaling-law extrapolation, and do three seeds per size fix it?

Lead: `llm-ml-science-scaling-fit-seed-uncertainty`. This plan is committed before any model is evaluated.

**Seen before this plan:** Hugging Face metadata only.
- PolyPythias is `EleutherAI/pythia-{14m,31m,70m,160m,410m}-seed{1..9}`, plus the original `pythia-{size}` as seed 0.
  Each has 155 checkpoint branches, step0 to step143000.
- The checkpoint file sizes, and the Pile-uncopyrighted file list.

**Novelty** (2026-10-24: web, OpenAlex, arXiv abstracts):
- **No study** fits scaling laws to many-seed ladders.
- **Choshen et al. 2025** (Hitchhiker's Guide) has no controlled seed replicates.
- **arXiv 2605.08541** varies fitting seeds, not training seeds.
- **The PolyPythias paper** reports seed variation in training dynamics, but not in scaling-law extrapolation.

## 1. Data

- **The eval corpus.** The validation split of `monology/pile-uncopyrighted` (`val.jsonl.zst`), held out from all Pythia
  training.
  - Documents are taken in file order and tokenized with the Pythia (GPT-NeoX) tokenizer until 5,000,000 tokens.
  - Documents are cut into 2,048-token sequences, with each sequence's first token not scored.
  - The token list's SHA-256 is recorded.
- **The ladders.** Sizes 14M, 31M, 70M, 160M and 410M; seeds 0 (the original Pythia) to 9.
  - 8 checkpoints per run, at steps 2,000, 4,000, 8,000, 16,000, 32,000, 64,000, 100,000 and 143,000. At 2,097,152
    tokens per step, D runs from 4.2B to 300B tokens.
  - N is the non-embedding parameter count from each config.
- **Targets.** The final checkpoints of Pythia-1B, 1.4B and 2.8B (original seed), on the same corpus.
- **The loss.** Mean token cross-entropy in nats, on the GPU in bf16 with logits in fp32.
  - Evaluation noise is a bootstrap over documents (200 resamples), on the 410M final checkpoint of seed 0.

## 2. Fits

- **The form.** Chinchilla, L(N, D) = E + A / N^α + B / D^β, fitted as in Hoffmann et al. and Besiroglu et al.: a
  Huber loss (δ = 10⁻³) on log L against the log-sum-exp of the three terms, by L-BFGS from a fixed grid of 64
  starting points. The best start is kept.
- **A single-seed ladder** picks one seed per size, using all 8 checkpoints of that run, for 40 points.
  - 2,000 ladders are sampled uniformly at random from the 10⁵ possible (seed 20261024).
  - Each is fitted and extrapolated to Pythia-2.8B: N of its config and D = 300B.
- **An n-seed ladder** (n = 2, 3, 5) averages, per size and checkpoint, the losses of n distinct seeds drawn at
  random (2,000 draws), then fits.
- **Seed-induced width.** W_n is the 5th to 95th percentile range of the extrapolated 2.8B loss across n-seed
  ladders.

## 3. Hypotheses and decision rules

Intervals come from a bootstrap over seeds: resample the 10 seeds within each size with replacement, then recompute
W_1 and W_3 (B = 200, with 500 ladders per replicate).

- **H1 (single-seed ladders are too noisy): W_1 > 0.05 nats.**
  - **Supported** if W_1's lower bound is above 0.05.
  - **Refuted** if its upper bound is below 0.05.
  - **Otherwise Inconclusive.**
- **H2 (three seeds halve it): the shrinkage 1 − W_3 / W_1 is at least 0.5.**
  - **Supported** if the shrinkage's lower bound is at least 0.5.
  - **Refuted** if its upper bound is below 0.5.
  - **Otherwise Inconclusive.**

  Under independent seed noise the expected shrinkage is about 1 − 1/√3 = 0.42.

## 4. Secondary (reported, not confirmatory)

1. **Accuracy:** the distribution of single-seed and 3-seed extrapolation errors against the actual Pythia-2.8B, 1.4B
   and 1B losses.
2. **The fitted exponents:** the distribution of α and β across single-seed ladders.
3. **Procedure against seed variance.** Huber δ ∈ {10⁻⁴, 10⁻³, 10⁻²}, a 16-point instead of a 64-point grid, and
   fitting in linear space are crossed with seed choice, in a two-way decomposition of the variance of the
   extrapolated loss.
4. **Final checkpoints only** (5 points per ladder, N-only law L = E + A/N^α): seed width at 2.8B.
5. **Evaluation noise against seed noise:** the document-bootstrap SD of one checkpoint's loss, against the across-seed
   SD at each size.

## 5. Limits stated in advance

- **The range is narrow.** 14M–410M is about 1.5 orders of magnitude in N, so extrapolation to 2.8B is 7× beyond the
  largest rung.
- **The targets are single seeds.** Only seed 0 exists for 1B–2.8B, so "accuracy" compares against one draw.
- **Checkpoints within a run are correlated.** The D dimension comes from one training run per seed, not independent
  runs.
- **The eval corpus is fixed,** so the uncertainty here is about seeds, not about data.

## 6. Outputs

- `results/tables/`: `losses.csv` (run, size, seed, step, N, D, loss), `primary.json`, `ladders_single.csv`.
- `results/figures/`.
- `deviations.md` records any change before the results it affects.
