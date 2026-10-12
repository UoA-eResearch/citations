# Pre-plan notes (12 October 2026): novelty check, data and tooling only; no SAE trained, nothing matched

## Novelty check (12 October 2026)

**Passed, but the lead's gap statement needs updating.** No study I found decomposes SAE-feature reproducibility into
the part due to the SAE's own training seed and the part due to the language model's pretraining seed. None uses
PolyPythia's decoupled seeds, which separate initialisation from data order.

**Found and cited in the lead:**

- **Paulo & Belrose** (arXiv 2501.16615, ICLR 2026): SAE seeds on one model. About 42% of latents are shared on
  Pythia-160M by an encoder-and-decoder cosine criterion; TopK SAEs are more seed-dependent than ReLU ones.
- **"Unstable Features, Reproducible Subspaces"** (arXiv 2606.12138): SAE seeds only.
- **Lan et al.** (arXiv 2410.06981) and **SharedSAE** (arXiv 2609.04344): different model sizes and families.

**New since the lead was written; the plan must cite them:**

- **McCann, "Polymorphism Is Rotation"** (arXiv 2605.24577, 23 May 2026). It trains SAEs on nine pretraining seeds of
  Pythia-70m (`pythia-70m-seed1..9`).
  - **What it reports.** By decoder-column cosine (Hungarian-matched, threshold 0.5), at least 98% of features match
    across seeds at late residual sites. Yet an SAE trained on one seed reconstructs another seed's residual stream at
    negative explained variance. An orthogonal Procrustes rotation, statistically indistinguishable from a Haar-random
    rotation, restores reconstruction.
  - **What it does not do.** It has no within-model SAE-seed baseline, no activation-correlation matching, and no
    decoupled seeds. It also does not resolve how decoder columns can match at raw cosine across bases that differ by a
    random rotation. The present design can check that claim at 160M (secondary analysis: raw and Procrustes-aligned
    decoder cosine).
- **Váradi & Kmetty** (arXiv 2607.08499, 9 July 2026). This is a method for cross-seed universal features: a
  Procrustes-conditioned joint TopK SAE on five pairs of independently trained BERT models, matching at Pearson
  r ≥ 0.70 across seeds. It is a method paper, with no SAE-seed versus pretraining-seed comparison.
- **Searches run:**
  - "sparse autoencoder features different pretraining seeds PolyPythia universality";
  - "SAE feature reproducibility across model training seeds same architecture";
  - "crosscoder compare models trained from different random seeds";
  - "pretraining seeds versus SAE seeds variance decomposition".
- **The PolyPythias paper** (arXiv 2503.09543) studies downstream performance, probing and training dynamics. It does
  not study SAEs.

## Data and models on disk (verified 12 October 2026)

- **PolyPythia Pythia-160M**, final checkpoint `step143000`: the original (seed 0), `pythia-160m-seed1..9`,
  `pythia-160m-weight-seed1..3` and `pythia-160m-data-seed1..3`.
  - **Decoupled variants.** The PolyPythias paper's table labels the weight-seed variants "(only parameters)" and the
    data-seed variants "(only data)".
  - **Checkpoint format.** The seed repositories hold `pytorch_model.bin` (fp16, 375 MB) and no safetensors. The
    original also has an fp32 `model.safetensors`; for consistency, every model is loaded from its fp16
    `pytorch_model.bin`.
  - **Step-0 checkpoints** of the original and the six decoupled variants are downloaded, to check which initialisations
    are shared.
- **Text.** `monology/pile-uncopyrighted` (commit 3be9033): `val.jsonl.zst` and `test.jsonl.zst`, 0.338 GB each.
- **Reference SAEs.** `EleutherAI/sae-pythia-160m-32k` (commit 2046768): TopK, k = 32, 32,768 latents, `d_in` 768,
  trained on 8.2 billion Pile tokens. The `layers.4` and `layers.8` residual SAEs are downloaded as a recipe check.
- **Tooling.**
  - `eai-sparsify` 1.3.3, EleutherAI's TopK trainer (the one Paulo & Belrose used). It trains several SAE seeds and
    layers in one pass (`--init_seeds`, `--layers`) and does not shuffle a memmap dataset.
  - torch 2.14.1+cu130 and transformers 5.18.0, layered from the `llm-ml-science-mcf-emergence` venv.
- **GPU.** One A100 80GB, idle. The lab owner stopped their `vllm` container at 13:59 NZDT during an SSH login, and it
  is left as they set it.

## Power simulation (`code/power.py`, `results/power.txt`; no data)

The simulation applies the decision rule of plan section 6 to simulated pair scores:

- 10 full-seed models;
- a random model effect, SD 0.02 or 0.05;
- a model-pair effect, SD 0.02 or 0.04;
- within-pair noise, SD 0.01 or 0.02;
- a dyadic bootstrap with 400 draws over 300 simulations.

| True R | P(Supported) | P(Refuted) | P(Inconclusive) |
|---:|---:|---:|---:|
| 0.60-0.75 | 1.00 | 0.00 | 0.00 |
| 0.80 | 0.00-0.01 | 0.00-0.01 | 0.99 |
| 0.85-1.00 | 0.00 | 0.99-1.00 | 0.00-0.01 |

Under either noise setting, the rule distinguishes R ≤ 0.75 from R ≥ 0.85 almost surely. Only ratios within a few
hundredths of 0.8 give Inconclusive.
