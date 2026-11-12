# Plan (preregistration): how robust are OpenNeuro task-fMRI group maps to defensible first-level analysis choices, dataset by dataset?

Lead: `extra-open-neuroimaging-reanalysis-openneuro-multiverse-robustness-atlas`. Written 2026-11-10, before any
fMRI data, events file or derivative image was downloaded.

**Seen before this plan:**
- **The lead's text.**
- **A novelty search** (OpenAlex, 2026-11-10): analytic-variability work covers one or a few datasets in depth (NARPS;
  Bowring et al. 2019 and 2021; the HCP Multi-Pipeline dataset, Germani et al. 2025) or curates pipelines (Atay et al.
  2026). No per-dataset robustness score across many OpenNeuro datasets was found.
- **Bucket and repository listings, no images:** the `openneuro-derivatives` S3 bucket lists fMRIPrep derivatives for
  308 datasets and FitLins outputs for 54; one subject's file list for ds000001 (names and sizes only); the list of 57
  dataset folders in `demidenm/openneuro_glmfitlins/statsmodel_specs` and the text of one spec (ds000001).
- No statistical map, time series, events file or result has been read.

## 0. Design

**Datasets.** Every dataset with a BIDS Stats Model spec in `openneuro_glmfitlins/statsmodel_specs` (57 at the time of
writing) that also has fMRIPrep derivatives in `s3://openneuro-derivatives/fmriprep/<ds>-fmriprep/` with
`space-MNI152NLin2009cAsym_res-2_desc-preproc_bold` images, `desc-confounds_timeseries.tsv` files, and events files in
the raw dataset (`s3://openneuro.org/<ds>/`). One task per dataset: the first task, alphabetically, that has a spec.
Subjects: those in the spec's `Input.subject` list with at least one usable run. Datasets with more than 100 such
subjects are analysed on a seeded random subset of 100 (seed 20261110); N below is the analysed N. A dataset is
dropped, with the reason counted, if fewer than 10 subjects remain or the spec cannot be applied.

**Contrast.** The first contrast listed in the spec's run-level node: chosen by the spec's authors, not by us, and
before any result. A secondary contrast is every condition in that contrast's condition list against the implicit
baseline (equal positive weights), a "task-positive" map that is expected to be robust.

**Design matrices.** pybids applies the spec's run-level transformations to the raw events, as FitLins does. The
multiverse then changes four things and keeps everything else in the spec:
- **smoothing:** 4, 6 or 8 mm FWHM Gaussian, applied to the preprocessed BOLD within the fMRIPrep brain mask;
- **HRF:** the spec's convolution model (SPM canonical), or SPM canonical plus its temporal derivative;
- **confounds:** in place of the spec's motion terms, one of 6P (6 motion parameters), 24P (6P, their derivatives
  and squares), 24P plus the first 5 aCompCor components, or 6P plus one spike regressor per volume with framewise
  displacement above 0.5 mm; fMRIPrep's cosine drift regressors are kept in every configuration;
- **noise model:** AR(1) or OLS (nilearn `run_glm`).

That is 3 × 2 × 4 × 2 = **48 configurations** per dataset. The lead's software axis (FSL FEAT) is not run: FSL is not
installed on the guest machine, and installing system packages there is not allowed. This is a planned reduction.

**Subject and group level.** Per configuration: the run-level contrast's effect and variance per run, fixed effects
across a subject's runs, then a one-sample t-test across subjects (nilearn `SecondLevelModel`, intercept only), giving
a group z map in MNI152NLin2009cAsym 2 mm space within the intersection of subjects' brain masks.

**Thresholding** (identical for every configuration): voxelwise FDR q < 0.05, two-sided (primary); z > 3.1 with
clusters of at least 20 voxels (secondary).

**Robustness index per dataset (R).** The mean pairwise **signed Dice** of the 48 thresholded maps over the 1,128
pairs: a voxel counts as overlapping only if it is suprathreshold with the same sign in both maps. Pairs where both
maps are empty are excluded and counted; a pair with one empty map scores 0. Also reported: the mean pairwise Pearson
correlation of the unthresholded z maps, and the share of configurations in which the voxel of the median
configuration's peak keeps its sign and stays suprathreshold.

**Predictors.**
- **N:** analysed subjects (used as log10 N).
- **tSNR:** for each run, the voxelwise temporal mean over temporal standard deviation of the unsmoothed preprocessed
  BOLD after removing fMRIPrep's cosine regressors, the median over brain-mask voxels; the dataset value is the median
  over runs.
- Secondary (descriptive): number of runs and volumes per subject, events in the contrast's conditions per subject,
  median framewise displacement.

## 1. Hypotheses

- **H1 (the lead's main claim):** across datasets, R is strongly predicted by log10 N and tSNR together: R² > 0.4 in
  an OLS regression of R on both. The 95% interval comes from 2,000 bootstrap resamples of datasets (seed 20261110).
  **Supported** if the interval's lower bound exceeds 0.4; **Refuted** if its upper bound is below 0.4; otherwise
  **Inconclusive**.
- **H2:** datasets with N < 25 are majority-fragile: their median R is below 0.5. 95% interval from 2,000 bootstrap
  resamples of those datasets. **Supported** if the upper bound is below 0.5; **Refuted** if the lower bound is at
  least 0.5; otherwise **Inconclusive**. Not testable (and reported so) if fewer than 5 datasets have N < 25.

Both use the primary contrast and the primary threshold.

## 2. Secondary analyses (reported, not confirmatory)

1. H1 and H2 with the secondary threshold, the secondary (task-positive) contrast, and the unthresholded correlation
   index in place of R.
2. **Which choice matters:** for each axis, the mean Dice between configurations that differ only on that axis,
   per dataset and pooled.
3. **External check:** the configuration closest to the spec (6 mm, SPM canonical, 6P, AR(1)) against the published
   FitLins group map for the same contrast (`s3://openneuro-derivatives/fitlins/<ds>-fitlins/`): spatial correlation
   of the z maps and Dice of the thresholded maps.
4. A per-dataset, per-contrast table (the "atlas"): N, tSNR, R, the correlation index, the most influential axis, and
   the share of configurations with any suprathreshold voxel.
5. R against the remaining descriptive predictors.

## 3. Leakage audit (G1)

There are no labels. The things that could bias the result are choices made after seeing data:
- **The contrast and the datasets** are fixed by rule (section 0) from a third party's specs before any data is read.
- **The multiverse** is fixed here; no configuration is added or dropped after results (failures are counted, not
  removed).
- **Thresholds** are fixed here and identical across configurations and datasets.
- **The FitLins reference maps** are read only for secondary 3, after R is computed for every dataset.

## 4. Other gates

- **G2 (coverage):** datasets, subjects, runs and configurations attempted, completed, dropped (with reasons) and
  failed, in `results/tables/coverage.json`. No silent defaults: a run with a missing confound column is dropped from
  that configuration and counted.
- **G3 (plausibility):** one random subject's first-level design matrix and contrast map checked by hand for one
  random configuration; expected ranges (tSNR 20–200 for 3T task BOLD; R in [0, 1]; the task-positive contrast more
  robust than the primary for most datasets) checked and reported; three random datasets' maps inspected.
- **G4 (validation of the automated pipeline):** secondary 3, the external check against the published FitLins maps;
  an expected correlation of at least 0.7 for the spec-closest configuration. Datasets falling short are inspected
  and the cause reported (artefact, genuine difference, or bug).
- **G5 and G6:** the overclaim check and the attribution ledger before review.
- **G7:** not applicable (no labelling).

## 5. Compute and data

(Changed before any data by D1: the lab's own VM, at most 14 workers, data under `/mnt/data/omv/`.) Originally: the
guest A100 machine's CPUs (28 cores), under `/mnt/claude-lab/omv/`: one dataset at a time is streamed from the
public buckets, processed, and its BOLD images deleted; group maps, run-level effect and variance maps for two
configurations (for audits) and all summary tables are kept. No GPU is needed. Everything must finish, and the guest
workspace be cleaned up, before the end of November 2026.

## 6. Limits stated in advance

- **Preprocessing is held fixed** (fMRIPrep 20.2 as published); the work of the Milham group and others suggests
  preprocessing may dominate variability, so R measures first-level robustness only.
- **One software package** (nilearn), and parametric thresholds only.
- **One contrast per dataset**, chosen by the spec's authors, may not be each dataset's headline contrast.
- **Datasets are those with published specs and derivatives,** not a random sample of OpenNeuro.
