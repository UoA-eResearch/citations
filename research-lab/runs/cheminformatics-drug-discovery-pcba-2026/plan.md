# Plan (preregistration): does a leakage-audited benchmark from recent PubChem confirmatory screens change what virtual-screening methods look like?

Lead: `cheminformatics-drug-discovery-pcba-2026`. Written before any activity outcome was downloaded.

**Seen before this plan:**
- **PubChem BioAssay search counts** (E-utilities, 2026-10-27). Confirmatory assays with a single target, ≥ 50
  active and ≥ 5,050 tested substances: 21 deposited 2023–2026 and 51 deposited 2021–2026.
  - The 51 cover 34 gene symbols (PUG REST target lists).
  - Their depositors are NCATS (32), Tox21 (18) and ChEMBL (1).
- **The LIT-PCBA archive's size** (54 MB).
- **Abstracts:**
  - the LIT-PCBA leakage audit (arXiv 2507.21404): duplicated and analog ligands across its splits, so a
    parameter-free memorization baseline matches published state of the art; it released code but no corrected
    benchmark. Its four citing works (OpenAlex) release none either;
  - LIT-PCBA (Tran-Nguyen, Jacquemard & Rognan, JCIM 2020).
- No activity outcome, structure list or score has been read.

## 0. Hypotheses

**Benchmarks.**
- **NEW:** section 1.
- **LIT:** LIT-PCBA (15 targets) with its published training/validation split, as the literature uses it.

**Methods** (section 4):
- NN: 1-nearest-neighbour memorization; a compound's score is its maximum ECFP4 Tanimoto similarity to any training
  active;
- RF: ECFP4 + random forest;
- GBM: RDKit descriptors + LightGBM;
- CB: ChemBERTa-77M-MLM embedding + logistic regression;
- MF: MoLFormer-XL embedding + logistic regression.

**Metrics.** The primary metric is EF1%, the enrichment factor in the top 1% of the ranked evaluation set.
Secondaries are BEDROC (α = 20) and AUPRC.

- **H1 (memorization's advantage collapses on a leakage-controlled benchmark).**
  - A_B is the median over a benchmark's targets of (EF1% of NN − 1). Q = A_NEW / A_LIT.
  - The 95% interval comes from a bootstrap that resamples targets within each benchmark (2,000 resamples, seed
    20261027).
  - **Supported** if Q's upper bound ≤ 0.5; **Refuted** if its lower bound > 0.5; **Inconclusive** otherwise.
- **H2 (foundation-model embeddings do not beat ECFP4 + RF).**
  - For each NEW target and each embedding (CB, MF), a paired bootstrap over evaluation compounds (2,000 resamples)
    gives the 95% interval of ΔEF1% = EF1%(embedding) − EF1%(RF).
  - The embedding "beats RF" on that target if the lower bound > 0. S2 is the share of target × embedding pairs where
    it does not.
  - **Supported** if S2 ≥ 0.70; **Refuted** if S2 < 0.50; **Inconclusive** otherwise.
  - The share where RF significantly beats the embedding is reported alongside, because wide intervals alone favour
    "does not beat".
- **H3 (method rankings do not transfer).**
  - The LIT consensus ranking orders the five methods by median EF1% across LIT targets.
  - For each NEW target, τ is the Kendall τ between its method ranking (by EF1%) and the LIT consensus. T3 is the
    mean τ over NEW targets, with a target bootstrap.
  - **Supported** if T3's upper bound ≤ 0.4; **Refuted** if its lower bound > 0.4; **Inconclusive** otherwise.
  - **Noise ceiling** (secondary): the mean τ between rankings computed on two random halves of each NEW target's
    evaluation set.

## 1. The NEW benchmark

- **Assays.** PubChem confirmatory assays deposited from 2021-01-01 to the download date, with:
  - one protein target;
  - ≥ 50 active and ≥ 5,050 tested substances.
  - One assay per target gene: the one with most actives, ties broken by most tested, then lowest AID.
  - The 2023+ subset is reported separately.
- **Outcomes.** PubChem activity outcome: active = 1, inactive = 0. Inconclusive and unspecified outcomes are
  dropped and counted.
- **Structures.**
  - Substances map to CIDs and CIDs to canonical SMILES (PUG REST).
  - Compounds are deduplicated per assay by InChIKey first block (connectivity).
  - A connectivity group with conflicting outcomes is dropped and counted.
  - SMILES that RDKit cannot parse are dropped and counted.
- **Interference.**
  - PAINS alerts (RDKit FilterCatalog) are reported per assay, not used to exclude.
  - Frequent hitters are compounds active in ≥ 30% of the NEW assays in which they were tested, among compounds
    tested in ≥ 5. Their share among actives is reported, and a sensitivity drops them.
- **Feasibility rule.** The study needs ≥ 20 targets after this funnel. If fewer remain, the active threshold falls
  to ≥ 30, which is reported. If still fewer than 15, the study stops and reports the funnel.

## 2. Analog-disjoint evaluation (NEW, and LIT as a control)

- **Clusters.** Per target, all ligands are clustered by Butina on ECFP4 at Tanimoto distance 0.6.
- **Folds.** Clusters go to 5 folds, balancing compounds and actives (seed 20261027).
- **Leakage audit.** In each fold, any evaluation compound with Tanimoto > 0.4 to any compound in that fold's
  training set is removed from evaluation, and counted. The realised nearest-neighbour similarity distribution is
  reported.
- **Evaluation.** Every method is trained on four folds and scores the fifth. Metrics are computed on the pooled
  out-of-fold scores of each target.
- **Sensitivity.** A threshold of 0.6 instead of 0.4, and a random 5-fold split.
- **LIT control.** LIT-PCBA under the same analog-disjoint procedure separates the benchmark from the split. This
  is a secondary result.

## 3. LIT-PCBA as published

- The "full data" archive, with its published per-target training and validation sets.
- Methods are trained on training and scored on validation.
- Its duplicates are kept, because H1 asks about the benchmark as used.

## 4. Methods (fixed hyperparameters; seed 20261027)

- **NN:** the maximum Tanimoto similarity to training actives (ECFP4, radius 2, 2,048 bits).
- **RF:** 500 trees, class_weight balanced, max_features sqrt.
- **GBM:** LightGBM on RDKit 2D descriptors, 500 trees, learning rate 0.05, scale_pos_weight equal to the class
  ratio.
- **CB and MF.**
  - Embeddings come from `DeepChem/ChemBERTa-77M-MLM` and `ibm/MoLFormer-XL-both-10pct` (Hugging Face).
  - The embedding is the mean-pooled last hidden layer.
  - The head is logistic regression (C = 1, balanced classes, standardised features).
  - These are third-party models, so they run on CPU in Docker without credentials or network after download.
- **Random:** EF = 1 by definition, for reference.

## 5. Leakage audit (G1)

- Benchmark construction uses assay metadata and outcomes only, with fixed rules. No method's score informs which
  assays, compounds or folds are kept.
- Folds come from structure clusters only. The 0.4 audit removes evaluation compounds by similarity, never by label.
- Hyperparameters are fixed here. Nothing is tuned on evaluation folds.
- **Contamination.** NEW assay labels were deposited in 2021 or later. Many structures (NCATS and Tox21 libraries)
  predate the embedding models' pretraining corpora, which contain structures but not these assay labels. The 2023+
  subset is reported separately.
- No LLM or agent labels any unit.

## 6. Other gates

- **G2:** `results/tables/coverage.json`, covering:
  - assays through the funnel;
  - substances through the funnel (outcome, CID, SMILES, deduplication, conflicts);
  - fold leakage removals;
  - model fits, including failures.
- **G3:** `results/plausibility.md`, with three targets traced from raw outcomes to EF1%, and invariants: EF of a
  random scorer is about 1; NN on LIT reproduces the audit paper's direction.
- **G4:** the leakage audit itself (realised similarity distributions). LIT duplicates are counted and compared
  with the audit paper's figures.
- **G5 and G6:** at write-up.
- **G7:** does not apply (no human or agent labels).

## 7. Limits stated in advance

- The new assays come mostly from two depositors (NCATS, Tox21) and their compound libraries, so the benchmark is
  not a random sample of drug-discovery chemistry.
- Experimental inactives carry false negatives, which cap achievable enrichment.
- Analog-disjoint splits can over-debias and compress method differences. The 0.6 threshold and random-split
  sensitivities show this.
- With 5 methods, per-target τ is coarse; the noise ceiling is reported.
