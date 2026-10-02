# Preregistration: are benchmark activity cliffs real, or partly measurement noise?

Lead: `cheminformatics-drug-discovery-cliff-noise-ceiling` (research-lab/leads.json). Written 2026-10-03 and committed to
git before any ChEMBL activity data were downloaded and before any model was trained.

## Probes made before writing

- **Novelty.**
  - OpenAlex searches: activity cliff with noise, uncertainty, regression to the mean, replicates, label noise and
    MoleculeACE noise, from 2023 on.
  - An arXiv search.
  - The abstracts of the two closest 2026 items: Nature Machine Intelligence "Molecular deep learning at the edge of
    chemical space", and a Zenodo deposit with a noise-ceiling analysis of HIV integrase and thrombin QSAR.
  - None propagates replicate noise into the cliff definition across the MoleculeACE benchmark.
- **MoleculeACE repository.**
  - The file list.
  - One benchmark file's columns: `smiles`, `exp_mean [nM]`, `y`, `cliff_mol`, `split`, `y [pEC50/pKi]`.
  - Its row count.
  - The code that defines cliffs (`benchmark/cliffs.py`) and merges replicates (`data_fetching/exp_property_curation.py`).
- **ChEMBL 37.** The FTP listing: `chembl_37_sqlite.tar.gz`, 5.76 GB, 2026-05-29. Nothing has been downloaded.
- **Not computed.** No cliff count, potency difference, model error or replicate statistic.

**Prior knowledge (disclosed).**

- Landrum & Riniker (JCIM 2024) report that combining IC50 or Ki values from different sources adds roughly 0.5–0.6
  log units of noise.
- MoleculeACE (van Tilborg et al., JCIM 2022) reports larger errors on cliff molecules for most methods.

Every later departure goes to `deviations.md` with a timestamp taken from `date`.

## 1. Background and gap

- **The benchmark.** MoleculeACE defines activity cliffs as pairs of molecules that are very similar but differ more
  than 10-fold in potency. It reports that models err more on molecules involved in cliffs. A 2025–2026 architecture
  literature takes that gap as a learning problem.
- **The counter-argument.** Cliffs are selected for extreme observed potency differences. With 0.5–0.6 log units of
  noise, some observed cliffs are noise, and regression to the mean guarantees larger apparent errors on molecules
  selected for extreme values.
- **The gap.** No study was found that propagates measured replicate uncertainty into the cliff definition. None asks
  how much of the cliff error gap a noise-only world reproduces.

## 2. Data

- **MoleculeACE.** The 30 benchmark datasets (GitHub `molML/MoleculeACE`, main branch): published SMILES, `exp_mean [nM]`,
  potency `y [pEC50/pKi]` (= 9 − log10 nM), `cliff_mol` and the train/test `split`.
- **Cliff pairs.** Recomputed with MoleculeACE's own definition and code (`cliffs.py`): consensus similarity ≥ 0.9
  (ECFP4 Tanimoto, generic-scaffold Tanimoto, or normalised SMILES Levenshtein) and fold change > 10 on `exp_mean`.
  - The recomputed `cliff_mol` must match the published column; any mismatch is reported.
- **ChEMBL 37 (SQLite).** For each benchmark target and activity type (Ki or EC50):
  - all activities with `standard_relation = '='`, a non-null `pchembl_value` and `data_validity_comment` null;
  - each with molregno, standard InChIKey, assay id, assay type, document id and document year.
- **Matching.** Benchmark molecules are matched to ChEMBL compounds by RDKit InChIKey (full key; if that fails, the
  14-character connectivity block), and the match rate is reported.
- **Replicate pairs.** Two values for the same compound, target and activity type from *different documents*
  (inter-document) or from the same document (intra-document).

## 3. Noise model

**Primary.** For each activity type (Ki, EC50), from inter-document replicate pairs in the 30 targets:

- σ = robust SD of pairwise differences / √2, with the robust SD = 1.4826 × MAD;
- noise is Gaussian.

**Sensitivity arms:**

- a Student-t noise model (ν = 4, with the same scale);
- σ estimated over all ChEMBL targets;
- σ by potency tertile;
- intra-document σ.

**Validation.** On a random 20% of replicate pairs held out from the σ fit, the nominal 90% interval for a pairwise
difference (±1.645·√2·σ) must contain 85–95% of held-out differences. Outside that range, the t-model becomes
primary; this is logged.

**Uncertainty of each benchmark value.** The value is a mean of n_i entries, where n_i is the number of ChEMBL 37 entries
for that compound, target and type in documents up to 2021. MoleculeACE fetched its data in 2021–22. If n_i = 0,
n_i = 1 is used.

- Standard error s_i = σ/√n_i.
- Sensitivity: n_i = 1 for all molecules (the noisiest case), and n_i = all ChEMBL 37 entries.

## 4. Cliff confidence (empirical Bayes)

For every similar pair (consensus similarity ≥ 0.9) in a dataset:

- observed difference d = y_i − y_j, with noise variance s² = s_i² + s_j²;
- true difference Δ, with d = Δ + e and e ~ N(0, s²).

**Prior on Δ.** A nonparametric distribution on a grid (−5 to 5 log units in steps of 0.05), fitted by maximum
likelihood (EM; Kiefer–Wolfowitz NPMLE, symmetrised).

- It is fitted pooled over all similar pairs of all 30 datasets, cliffs and non-cliffs alike. Per-target fits are a
  sensitivity arm.

**Cliff confidence** of a pair: P(|Δ| > 1 | d), the posterior probability that it is a true 10-fold cliff.

**A molecule is a "high-confidence cliff molecule"** if at least one of its cliff pairs has confidence ≥ 0.9.

## 5. Models and the cliff gap

- **Models** on the published train/test splits, with ECFP4 (2,048 bits, radius 2):
  - random forest (500 trees);
  - support vector regression with a Tanimoto kernel;
  - LightGBM;
  - k-nearest neighbours (k = 5, Tanimoto).
- **Seeds.** Ten for the stochastic models.
- **Hyperparameters.** Fixed defaults, identical across datasets. No tuning on test data.
- **Gap.** gap = RMSE on test cliff molecules (published `cliff_mol` = 1) − RMSE on test non-cliff molecules. It is
  computed per target and model, then averaged over seeds and models.
- **Restricted gap.** The same with the cliff set restricted to high-confidence cliff molecules.

## 6. Hypotheses (from the lead) and decision rules

**H1.** At least 25% of MoleculeACE cliff pairs, pooled over the 30 targets, have cliff confidence ≤ 0.8, so a
posterior probability ≥ 0.2 of not being a true 10-fold cliff.

- The 95% interval is a bootstrap over targets (2,000 resamples).
- Supported if the lower bound ≥ 25%. Contradicted if the upper bound < 25%. Otherwise inconclusive.

**H2.** Restricting to high-confidence cliff molecules shrinks the cliff gap by at least 40%:

- shrinkage = 1 − mean(restricted gap) / mean(full gap) over targets;
- the interval is a bootstrap over targets;
- supported if shrinkage ≥ 0.40 and its lower bound > 0. Contradicted if the upper bound < 0.40. Otherwise
  inconclusive;
- targets with no high-confidence cliff test molecule, or fewer than 10 cliff test molecules, are excluded and
  counted.

**H3.** A noise-only world reproduces at least 50% of the observed gap.

- **Building the world.** For each target, a smooth potency surface f is built from out-of-fold kNN predictions (k = 5,
  Tanimoto weights, 5-fold). The labels are y* = f + noise drawn from the noise model with each molecule's s_i.
- **Running it.** Cliffs are re-detected on y*. Models are retrained on y* with the same splits, and the gap is
  measured. There are 20 noise draws per target.
- **Statistic.** Reproduced fraction = mean null gap / mean observed gap over targets, with a bootstrap over targets.
- **Decision.** Supported if the fraction ≥ 0.50 and its lower bound > 0. Contradicted if the upper bound < 0.50.
  Otherwise inconclusive.
- **Control.** A label-shuffle run within each target checks that the null machinery gives no gap when cliff labels
  are random.

**Secondary analyses:**

- **Do cliffs survive new measurements?** For cliff pairs where both molecules have entries in ChEMBL 37 from documents
  after 2021, the fraction still more than 10-fold apart on the post-2021 means alone.
- Per-model and per-target gaps.
- The gap using MoleculeACE's own definition: RMSE on cliff molecules against RMSE on all test molecules.

## 7. Validation before the main analysis

- **Cliff detection.** The recomputed cliff molecules must reproduce the published `cliff_mol` column (target: ≥ 99%
  agreement in each dataset).
- **Empirical Bayes.** On synthetic pairs with a known prior and noise, the NPMLE posterior must be calibrated: among
  pairs with confidence in [0.7, 0.9], 70–90% must be true cliffs.

## 8. Review and reporting

- An independent reviewer agent checks code, deviations and the draft before any verdict is stated.
- The report opens with an "In plain terms" section.
- Derived tables are committed; raw ChEMBL is not.
