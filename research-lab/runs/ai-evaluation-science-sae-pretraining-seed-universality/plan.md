# Preregistration: are SAE features properties of the model or of the training run? SAE seeds against pretraining seeds in PolyPythia-160M

Lead: `ai-evaluation-science-sae-pretraining-seed-universality` (research-lab/leads.json). Written 12 October 2026.
Committed before any SAE is trained and before any latent is matched.

## What has been seen before writing (disclosure)

The novelty check, the data and model checks, the tooling and the power simulation are in
[`NOTES_pre_plan.md`](NOTES_pre_plan.md). In short:

- **Novelty.** It passed. Two works appeared after the lead was written and are cited here: McCann (arXiv 2605.24577),
  on SAE decoder cosine across Pythia-70m pretraining seeds, and Váradi & Kmetty (arXiv 2607.08499), a joint SAE
  across BERT seeds.
- **Inputs.** The text and the reference SAEs are downloaded. The model checkpoints were still downloading, and the text was being tokenized, when this plan was committed.
- **Not done.** No SAE has been trained, no model has been run on the held-out set, and no latent has been matched.

## 1. Question and hypothesis

Sparse autoencoders (SAEs) are trained on a language model's activations to find "features". Two independent sources
of randomness decide which features an SAE reports:

1. **The SAE's own training seed.** Paulo & Belrose found that only about 42% of latents are shared between two SAE
   seeds on Pythia-160M.
2. **The language model's pretraining seed**, which sets its initialisation and data order.

If features are properties of what a model of this architecture and data learns, SAEs on two independently pretrained
models should match about as often as two SAE seeds on one model. If features are largely properties of the particular
training run, they should match much less often.

**H (from the lead).** For TopK SAEs (32,768 latents, k = 32) trained on the residual stream of Pythia-160M:

- *cross-seed matching* is the fraction of latents that have an activation-correlation match (Pearson r ≥ 0.7 on a
  fixed held-out token set) in an SAE trained on a *different pretraining seed*;
- *within-model matching* is the same fraction for an SAE trained on the *same model with a different SAE seed*.

H says that cross-seed matching is less than 0.8 times within-model matching.

## 2. Models and data

- **Models.** 16 Pythia-160M variants at their final checkpoint (`step143000`), all loaded from their fp16
  `pytorch_model.bin` and run in bf16:
  - **Full seeds (10):** the original `pythia-160m` (seed 0) and `pythia-160m-seed1` to `seed9`. Both the
    initialisation and the data order differ.
  - **Weight-seed variants (3):** `pythia-160m-weight-seed1..3`, labelled "(only parameters)" by PolyPythias. Only the
    initialisation differs from seed 0.
  - **Data-seed variants (3):** `pythia-160m-data-seed1..3`, labelled "(only data)". Only the data order differs from
    seed 0.
  - **Check before analysis (validation step 9.3).** The step-0 checkpoints of the data-seed variants should equal the
    original's, and those of the weight-seed variants should not. If this fails, the decoupled comparisons (section 7)
    are relabelled by what the checkpoints show.
- **Layers.** The residual stream output of blocks 4 and 8 of 12, i.e. sparsify hookpoints `layers.4` and `layers.8`.
  These are the reference SAEs' names.
- **Training stream.** The Pile (uncopyrighted) validation split, tokenized with the Pythia tokenizer:
  - documents are separated by the end-of-text token and cut into 2,048-token sequences;
  - the sequence order is shuffled once (seed 20261012);
  - every SAE sees the same sequences in the same order.
- **Held-out set H.** 1,025 sequences of 2,048 tokens from the Pile (uncopyrighted) test split, with position 0 of each
  sequence dropped (its residual stream is an outlier attention sink). That gives 2,098,175 tokens.

## 3. SAE training

- **Trainer.** `eai-sparsify` 1.3.3 with its defaults, except as listed:
  - TopK activation, k = 32, 32,768 latents;
  - decoder rows normalised to unit norm;
  - FVU loss;
  - the library's default optimizer (signum) and automatic learning rate;
  - batch 32 sequences;
  - no AuxK loss (the library's default, `auxk_alpha` 0).
- **One pass per model.** A single training run per model trains six SAEs together: layers 4 and 8 × SAE seeds 0, 1
  and 2 (`--init_seeds 0 1 2`). The SAE seed sets only the initialisation. The data and its order are identical across
  seeds and models.
- **Token budget.** 200 million tokens per SAE (97,657 sequences), unless the pilot (section 9) shows that the 16 runs
  would take more than 72 GPU-hours. In that case the budget is the largest of 150 or 100 million tokens that fits.
  The choice is logged in `deviations.md` before the main runs start, and is the same for every model.
- **Precision.** Models in bf16, as sparsify loads them; SAEs in fp32.

## 4. Matching

For a pair of SAEs (A, B), possibly on different models, both are applied to H. Each SAE reads its own model's residual
stream at its own layer, on the same tokens.

- **Correlations.** Pearson correlation between every latent of A and every latent of B, over the tokens of H, with a
  latent's activation taken as 0 where it is not in the top k.
- **Assessable latents.** A latent is assessable if it fires at least 20 times on H. Only assessable latents enter
  numerators, denominators and candidate sets.
- **Directional score f(A→B).** The fraction of A's assessable latents whose best correlation with an assessable
  latent of B is at least 0.7.
- **Pair score.** f(A, B) = (f(A→B) + f(B→A)) / 2.

**Pairs** (`code/pairs.py`; 246 per layer):

| Kind | Models | SAE seeds | Pairs per layer |
|---|---|---|---:|
| within | the same model | (0,1), (0,2), (1,2) | 16 × 3 = 48 |
| full | two different full seeds | (A₀,B₁), (A₁,B₂), (A₂,B₀) | 45 × 3 = 135 |
| init | weight-seed k vs seed 0; weight-seed j vs k | as for full | 6 × 3 = 18 |
| data | data-seed k vs seed 0; data-seed j vs k | as for full | 6 × 3 = 18 |
| both_dc | a weight-seed vs a data-seed variant | as for full | 9 × 3 = 27 |

**Different SAE seeds across models.** Two SAEs in a model pair never share an SAE seed. A shared SAE
initialisation in two models whose residual bases happen to be aligned would inflate matching for reasons unrelated to
the features.

## 5. Primary statistic

The primary statistic uses the 10 full-seed models only. For each layer L ∈ {4, 8}:

- **W_L:** the mean over the 10 models of the mean of each model's three within pair scores;
- **X_L:** the mean over the 45 model pairs of the mean of each pair's three SAE-seed combinations.

The primary statistic pools the two layers:

**R = (X₄ + X₈) / (W₄ + W₈).**

**The interval** comes from a dyadic bootstrap over the 10 models: 2,000 draws, seed 20261012. Each draw resamples the
10 models with replacement and uses the same draw for both layers.

- W* averages the drawn models' within scores, counting multiplicity.
- X* averages the scores of all pairs of draws that are different models; pairs of the same model are skipped.
- The 95% interval is the 2.5th and 97.5th percentiles.

## 6. Decision rule

- **Supported:** the upper bound of R is below 0.8.
- **Refuted:** the lower bound of R is at least 0.8.
- **Inconclusive:** otherwise.

The report also says, descriptively, whether the upper bound is below 1, i.e. whether there is any loss of
reproducibility across pretraining seeds.

**Power** (`code/power.py`, `results/power.txt`). The simulation varies the model effect (SD 0.02-0.05), the
model-pair effect (SD 0.02-0.04) and within-pair noise (SD 0.01-0.02). Across that range the rule returns:

- Supported, with probability at least 0.99, for a true R ≤ 0.75;
- Refuted, with probability at least 0.99, for a true R ≥ 0.85;
- Inconclusive only for R within a few hundredths of 0.8.

The minimum detectable departure from the threshold is therefore about ±0.05 in R. If the model-to-model spread in
matching is much larger than simulated, the interval widens; the report gives its width.

## 7. Secondary and exploratory analyses (all reported; none changes the verdict)

1. **Per layer.** R₄ and R₈, each with the same bootstrap.
2. **Initialisation against data order.**
   - Compare the mean scores of the init, data and both_dc pairs, and of the full pairs, each relative to the mean
     within score of the seven models in the seed-0 lineage (the original, the weight-seed and the data-seed variants).
   - Intervals come from a bootstrap over model pairs within each kind. With only 6-9 model pairs per kind these are
     descriptive.
   - This is the decomposition the lead names: does losing reproducibility come from the initialisation, the data
     order, or both?
3. **Other thresholds:** R at r ≥ 0.5 and at r ≥ 0.9.
4. **By firing frequency.** Directional match rates by the tercile of the source latent's firing frequency on H, within
   versus full.
5. **Decoder geometry** (McCann's claim). The fraction of latents whose best decoder cosine with the other SAE is at
   least 0.5 (and 0.7), for within and full pairs.
   - It is computed both raw and after an orthogonal Procrustes rotation of A's residual basis onto B's.
   - The rotation is fitted on the first 262,144 tokens of H.
   - If independently pretrained residual bases differ by a near-random rotation, raw cross-seed decoder cosine should
     be low and the rotated one high.
6. **SAE quality.** FVU on H and the dead fraction (no activation on H), per SAE.
   - The report says whether pair scores track SAE quality.
   - **Flagging.** An SAE is flagged if its FVU is more than twice its layer's median, or more than half its latents
     are dead.
   - **Sensitivity.** Flagged SAEs are reported. The primary analysis keeps them, and a sensitivity analysis drops
     their models.
7. **Recipe reference.** The FVU on H of EleutherAI's `sae-pythia-160m-32k` at layers 4 and 8 on the original model.
   Also its match score (section 4) with each of the original model's three SAEs. Both are context for how far this
   study's training budget is from the reference recipe's 8.2 billion tokens.

## 8. Implementation (code committed before any outcome)

- `code/fetch.py`: downloads.
- `code/tokenize_pile.py`: training stream and H.
- `code/pairs.py`: the pair design.
- `code/match.py`:
  - encodes H with every SAE, using the same hookpoint as sparsify (the block's output);
  - computes the cross-moments sparsely and exactly (k × k products per token, accumulated in fp32);
  - computes the correlations, best matches and decoder cosines.
- `code/analysis.py` (written before the main matching runs): the statistics of sections 5-7.

## 9. Order of work

1. Commit this plan.
2. **Pilot.** One sparsify run on the original model, with all six SAEs, for a few million tokens. It measures
   throughput (for the budget rule in section 3) and checks the saved format. The pilot SAEs are used only to test
   `match.py`:
   - an SAE against itself must give f = 1;
   - an SAE against itself with its latents permuted must give f = 1;
   - an SAE against a randomly initialised SAE must give f near 0;
   - a pilot SAE against the reference SAE.

   No full-budget SAE exists at that point.
3. **Validation.** The step-0 equality checks (section 2) and the token counts.
4. **Main training.** 16 sparsify runs on the GPU. The lab owner stopped the `vllm` container themselves on
   12 October. It is not touched, so the GPU stage stops no service.
5. **Matching.** The 246 pairs at each of the two layers.
6. **Analysis.** Then the report, with an independent adversarial review.

Every departure from this plan goes into `deviations.md`, timestamped and written before the outcome it could affect is
seen, wherever that is possible.

## 10. Reporting

- **The verdict.** By the rule in section 6, with W, X and R per layer and pooled, and the bootstrap interval.
- **Every secondary analysis**, the per-SAE quality table, and the pair-level table.
- **Released:** the SAE weights (96 × about 200 MB, published if hosting allows, else their training configuration and
  per-pair results), the pair tables and the per-latent best-match arrays.
