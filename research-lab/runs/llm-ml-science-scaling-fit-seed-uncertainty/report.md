# Training-seed noise in scaling-law forecasts: one seed per size moves the 2.8B forecast by 0.12 nats, mostly because of two unstable runs, and averaging three seeds did not clearly help

*PolyPythias: ten training seeds at each of five sizes, 14M to 410M, eight checkpoints each, 400 checkpoints in all.
Each was evaluated in fp32 on 5.0M tokens of Pile validation. The Chinchilla law was fitted to 2,000 random
single-seed ladders and to 2-, 3- and 5-seed averaged ladders, each extrapolated to Pythia-2.8B. The plan was
committed before any model was evaluated. The evaluation precision changed (D1) before any fit.*

**Verdict: H1 Inconclusive; H2 Inconclusive.**

- **H1 (single-seed ladders are too noisy: the 5th–95th percentile range W₁ of the 2.8B forecast exceeds 0.05
  nats): Inconclusive.**
  - W₁ = **0.123 nats**. The seed bootstrap interval is 0.038–0.160, so its lower end is below the bar.
  - The distribution is bimodal. 1,578 of the 2,000 ladders avoid two 410M runs whose loss jumps late in training,
    and they have W₁ = 0.051 (post hoc).
  - Those jumps are properties of the released checkpoints, not of the evaluation. 410M seed 4 sits at 2.41–2.43
    nats at steps 141k–143k against 1.98 for seed 0, and a batch-size-1 re-evaluation reproduces it exactly (post
    hoc).
- **H2 (averaging three seeds per size at least halves the width): Inconclusive.**
  - The shrinkage is **0.16**, with an interval from −0.10 to 0.81: W₃ = 0.103 against W₁ = 0.123. Five seeds give
    0.088.
  - Averaging dilutes a bad run rather than removing it, so the heavy tail survives. Independent Gaussian noise would
    predict a shrinkage of 0.42.
- **Every route overshoots the real 2.8B loss.**
  - 98% of single-seed forecasts lie above the actual 1.704 nats; the median error is +0.068.
  - Averaging seeds does not fix this (+0.066 with three).
  - Fitting only checkpoints up to step 64k narrows the spread (W₁ 0.086) but overshoots by 0.13 (post hoc).
  - The bias is shared across seeds, so it reflects the fitting form and range rather than seed choice.
- **Fitting choices interact with seeds.** In a seed × procedure decomposition of the forecast, the seed accounts for
  69% of the variance, the procedure 2% and their interaction 29%. A 16-start grid instead of 64 widens the spread
  from 0.118 to 0.185.

## In plain terms

Before training a large AI language model, labs train a ladder of small ones and fit a "scaling law" to predict how
good the big one will be. Each small model starts from a random seed, and different seeds give slightly different
models. We asked how much that luck moves the prediction.

Using a public set of models trained ten times each with different seeds, we fitted thousands of ladders, each using
one seed per size. Which seeds you happen to get moves the prediction for a model 7 times larger by about 0.12 in
the loss units used. That is more than the real gap between the 1.4-billion and 2.8-billion-parameter models
(0.09). Most of that comes
from just two training runs that went wrong late in training. Averaging three seeds per size helped little here, though that estimate is very uncertain. Every approach also predicted the big model would be worse than it actually was.

The practical lesson is to look at the training curves of the small models and drop or rerun unstable ones, rather
than trusting averaging. Even then, the formula itself, fitted to this narrow range, was biased.

## What was asked

The lead (`llm-ml-science-scaling-fit-seed-uncertainty`) asked how much training-seed variation moves a
scaling-law extrapolation, and whether three seeds per size fix it. Prior work varies the fitting procedure or the
seeds of the fit itself, not training seeds across a ladder. The PolyPythias paper documents seed variation in
training dynamics but not in extrapolation.

## How it was done

- **Evaluation.**
  - 5,000,000 tokens of `pile-uncopyrighted` validation (SHA-256 `e276f22a…`), in 2,048-token sequences.
  - Mean token cross-entropy in fp32. bf16 corrupts late Pythia checkpoints, so D1 replaced it before any fit.
  - Pythia-2.8B was evaluated in fp16 beside the shared GPU server. Its fp16–fp32 difference at 1B and 1.4B is at
    most 6×10⁻⁵ nats.
- **Ladders.** Sizes 14M, 31M, 70M, 160M and 410M; seeds 0–9; steps 2k–143k, so D runs from 4.2B to 300B tokens.
- **Fits.** Chinchilla L = E + A/N^α + B/D^β, by a Huber loss (δ = 10⁻³) on log L from 64 starting points, as in
  Hoffmann et al. and Besiroglu et al.
- **Ladders sampled.** 2,000 single-seed ladders, and 2,000 n-seed averaged ladders for n = 2, 3, 5.
- **Intervals.** A bootstrap over seeds within size (200 × 500 ladders).

## Results

### The ladder (`results/figures/F1_ladder.png`)

![Ladder](results/figures/F1_ladder.png)

- **Small models rise late.** At 14M–70M, many seeds' losses rise late in training, consistent with the known
  saturation of small language models (Godey et al., 2024).
- **Two 410M runs jump:**
  - seed 3 at 100k steps (2.17 against 2.00), partly recovering by 143k (2.09);
  - seed 4 at 143k (2.41).
- **Seed SD of the final loss:** 0.133 (14M), 0.106 (31M), 0.029 (70M), 0.019 (160M), 0.132 (410M). Without the two
  jump runs, the 410M SD is 0.010.

### Forecasts of Pythia-2.8B (`results/figures/F2_extrapolation.png`)

![Extrapolation](results/figures/F2_extrapolation.png)

| seeds averaged per size | W (5th–95th, nats) | median error vs actual 2.8B |
|---|---|---|
| 1 | 0.123 (0.038–0.160) | +0.068 |
| 2 | 0.105 | +0.067 |
| 3 | 0.103 (0.020–0.110) | +0.066 |
| 5 | 0.088 | +0.071 |
| 1, excluding the two 410M jump runs (post hoc) | 0.051 | +0.062 |
| 1, checkpoints up to step 64k (post hoc) | 0.086 | +0.130 |
| 3, checkpoints up to step 64k (post hoc) | 0.073 | +0.135 |

### Secondary analyses

- **Accuracy at 1B and 1.4B (single seed):** median errors +0.044 and +0.061, with widths 0.084 and 0.096.
- **Fitted exponents (5th, 50th, 95th percentiles):** α 0.214, 0.249, 0.303; β 0.771, 0.884, 1.041. β is far above
  the Chinchilla paper's 0.28, as expected when the data dimension is a single run's checkpoints.
- **Procedure against seed** (300 ladders × 5 procedures): seed 69%, procedure 2%, interaction 29%. The widths are:
  - base 0.118;
  - Huber δ 10⁻⁴: 0.161;
  - Huber δ 10⁻²: 0.112;
  - 16-start grid: 0.185;
  - linear-space fit: 0.115.
- **Final checkpoints only** (N-only law): W₁ 0.755, median error −0.110. Five points cannot pin the law.
- **Evaluation noise.** The document-bootstrap SD of one checkpoint's loss is 0.047 nats. It is shared by all
  models on the same corpus, so it does not enter the seed width, but it bounds how precisely any forecast can be
  scored against one target.

## What this does and does not show

- **Seed noise in a small ladder is heavy-tailed.** Most seeds agree to about 0.01–0.03 nats at 70M–410M. The
  forecast spread comes mainly from rare runs that destabilise late, and averaging dilutes but does not remove them.
- **Inspecting curves and dropping unstable runs is the effective fix here,** an observation from this post hoc
  analysis, not a tested rule. Robust aggregation, such as the median across seeds, was not tested.
- **The systematic overshoot (+0.07 nats) exceeds the typical seed spread.** It is shared across seeds, so it is a
  property of the fitting form, the range or the targets, not of seed luck.
- **Not shown:**
  - **Other scales.** Ladders far beyond 410M, and seeds at the target scale (only seed 0 exists for 1B–2.8B).
  - **Data-order versus initialisation effects.** PolyPythias varies both together.
  - **Whether the 410M instabilities are typical** of other model families.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - D1, before any fit: bf16 to fp32 evaluation.
  - D2: batch-size changes to avoid out-of-memory, and the post hoc checks.
- **Post hoc** (labelled): `code/spike_check.py` (neighbouring checkpoints, and a batch-size-1 re-evaluation) and
  `code/posthoc.py` (excluding the jump runs; the 64k cut).
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. `code/evaluate.py corpus`, then `code/evaluate.py run` (about 6 h on one GPU), then
   `code/evaluate.py evalnoise`.
2. `code/fit.py` (about 7 h on 20 cores).
3. `code/spike_check.py`, `code/posthoc.py` and `code/figures.py`.
