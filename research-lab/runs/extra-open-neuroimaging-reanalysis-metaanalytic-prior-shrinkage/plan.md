# Preregistration: how many subjects is a meta-analytic prior worth in a small fMRI study?

Lead: `extra-open-neuroimaging-reanalysis-metaanalytic-prior-shrinkage` (research-lab/leads.json). Written 2026-10-01 and
committed to git before any first-level model was fitted or any group map computed.

## Probes made before writing

- **Literature search** (§1).
- **OpenNeuro S3 listings for AOMIC PIOP1 (ds002785) and PIOP2 (ds002790).**
  - Read: participant counts, file names and sizes, one subject's event files (trial types and durations), and the
    column names of one confounds file.
  - One BOLD header (shape 65 × 77 × 60 volumes, 3 × 3 × 3.3 mm, TR 2 s), read from a partial download.
  - A download-speed test fetched partial BOLD files for subjects 0003–0067 (working-memory task). They were deleted
    unread.
- **NeuroQuery** (the `neuroquery` 1.1.0 model, 4 mm grid). Checked which query terms are in its vocabulary, and
  looked at the "working memory" map's shape and similar-word list.
- **Not examined.** No first-level or group statistics and no correlation between any prior map and any data.

Every later departure goes to `deviations.md` with a timestamp taken from `date`.

## 1. Background and gap

- **The problem.** Most task-fMRI studies have 15–30 participants. At that size, group maps replicate poorly
  (Turner et al. 2018).
- **Meta-analytic tools.** NeuroQuery (Dockès et al. 2020) predicts a brain map for any query text from about 13,000
  articles. Such maps encode where a task usually activates.
- **The idea.** Shrinking a noisy small-sample map toward a meta-analytic prediction could borrow that knowledge.
- **Closest work.**
  - Han & Park (2019) did image-based Bayesian meta-analysis.
  - Han & Park (2021, PeerJ) tuned one global prior scale of a Bayesian second-level test from meta-analysis.
- **The gap.** No study was found that does either of these:
  - shrinks small-sample maps voxel by voxel toward a predicted meta-analytic map and validates the result against a
    large-sample ground truth;
  - says how many extra subjects such a prior is worth.

  A recent survey of methods for small task-fMRI studies (Imaging Neuroscience, doi:10.1162/IMAG.a.1076) does not cover
  meta-analytic priors.

## 2. Data

**AOMIC** (Snoek et al. 2021, CC0): fMRIPrep-preprocessed BOLD in MNI152NLin2009cAsym space, events and confounds,
from OpenNeuro's public S3 bucket. The five primary domains come from PIOP1 (ds002785, 216 participants); the sixth and
the two replications come from PIOP2 (ds002790, 226 participants).

| Domain | Dataset, task | Contrast | NeuroQuery query (matched) | Mismatched query |
|---|---|---|---|---|
| Working memory | PIOP1 `workingmemory` | ½(active_change + active_nochange) − passive | "working memory" | "face perception" |
| Emotion processing | PIOP1 `emomatching` | emotion − control | "emotional faces" | "working memory" |
| Cognitive conflict | PIOP1 `gstroop` | incongruent − congruent | "stroop" | "face perception" |
| Face perception | PIOP1 `faces` | mean of all expressions − baseline | "face perception" | "working memory" |
| Anticipation | PIOP1 `anticipation` | cue_negative − cue_neutral | "anticipation" | "finger tapping" |
| Response inhibition | PIOP2 `stopsignal` | succesful_stop − go | "stop signal" | "emotional faces" |
| Replication (secondary) | PIOP2 `workingmemory`, `emomatching` | as above | as above | as above |

- **Mismatched queries.** These are chosen to name a different domain. A mismatched map can still overlap the truth
  (for example task-general networks); that is part of the realistic test.
- **Inclusion.** A subject is included for a contrast if all of these hold:
  - the task's MNI preprocessed BOLD, confounds and events exist;
  - mean framewise displacement is ≤ 0.5 mm;
  - the first-level fit succeeds;
  - their brain mask covers ≥ 90% of the analysis-grid mask.
- **Circularity.** AOMIC was published in 2021; NeuroQuery's corpus predates it, so these data are not in the prior.

## 3. First-level models

nilearn 0.14.1 `FirstLevelModel`, settings fixed before fitting:

- `t_r` from the image header (2.0 s); `slice_time_ref` 0.5 (fMRIPrep slice-timing reference).
- Glover HRF; cosine drift with high pass 1/128 Hz; AR(1) noise.
- Smoothing 6 mm FWHM; `signal_scaling=0`, so estimates are in percent signal change.
- **Analysis grid.** NeuroQuery's 4 mm MNI grid and brain mask, intersected with the subject's fMRIPrep brain mask.
- **Confounds.** Six motion parameters and their first derivatives, CSF, white matter, and any
  `non_steady_state_outlier` columns. NaNs in the first row are set to 0.
- **Regressors.** Every trial type in the events file is its own regressor, with the given durations.
- **Output.** One contrast-estimate (effect size) map per subject and contrast.

**Group mask.** The intersection of included subjects' masks with the NeuroQuery mask.

## 4. Methods compared (applied to a subsample of n subjects)

Let b_v be the mean contrast estimate at voxel v, and s²_v the sample variance divided by n.

- **S (standard):** the mean map b.
- **EB-Q (the method under test).** Empirical-Bayes shrinkage toward the matched NeuroQuery map m (z-scored within the
  mask).
  - Model: b_v ~ N(θ_v, s²_v), with θ_v ~ N(α + β·m_v, τ²).
  - α, β ≥ 0 and τ² ≥ 0 are fitted by maximising the marginal likelihood
    Σ_v log N(b_v; α + β·m_v, τ² + s²_v) over the subsample's voxels. The fit uses L-BFGS-B over α, β, log τ².
  - Estimate: θ̂_v = w_v·b_v + (1 − w_v)·(α + β·m_v), with w_v = τ²/(τ² + s²_v).
  - Everything is estimated from the subsample alone.
- **EB-W.** The same, with the mismatched map.
- **EB-0.** The same, with β fixed at 0 (a flat prior). This separates the meta-analytic content from generic shrinkage.

## 5. Subsampling experiment

For each contrast:

- **Ground-truth size.** N_GT = N_included − 80.
- **Draws.** For n in {10, 15, 20, 25, 30, 40, 50, 60, 80} and r = 1..500 (seeded):
  - draw a ground-truth set of N_GT subjects;
  - from the remaining subjects, draw a subsample of n;
  - the ground truth is the mean contrast map of the ground-truth set.
  - Because N_GT is fixed, ground-truth noise does not change with n.
- **Primary metric.** Pearson correlation across mask voxels between the method's map and the ground-truth map.
- **Secondary metrics:**
  - **Dice.** Dice overlap of the top 10% of voxels (positive direction).
  - **False-positive rate (FPR).** Ground-truth-null voxels are those with |z_GT| < 1.96 (one-sample t on the
    ground-truth set, converted to z). FPR is the share of them a method declares active at z > 3.09.
    - For S, z comes from the one-sample t with n − 1 degrees of freedom.
    - For EB methods, z_v = θ̂_v / √(w_v·s²_v).
    - FPR is not evaluable if fewer than 1% of mask voxels are ground-truth-null.
- **Effective sample size.**
  - r̄_S(n) is the mean over draws of S's correlation.
  - For a method at n = 15, n_eq solves r̄_S(n_eq) = r̄_method(15), by linear interpolation of r̄_S against log n over
    the grid. It is reported as ">80" or "<10" outside the grid.
  - Gain G = n_eq / 15.
- **Intervals.** 2,000 bootstrap resamples of the 500 draws per n, paired across methods, with percentile 95% intervals.
  They describe the expected performance within this dataset, not across populations.

## 6. Hypotheses and decision rules

**H1 (primary, from the lead).** At n = 15, EB-Q gives G ≥ 2 (worth at least doubling the sample) in at least 5 of the
6 domains.

| Domain outcome | Condition |
|---|---|
| Met | lower 95% bound of G ≥ 2 |
| Not met | upper bound < 2 |
| Unclear | otherwise |

| H1 verdict | Condition |
|---|---|
| Supported | ≥ 5 domains met |
| Contradicted | ≥ 2 domains not met |
| Inconclusive | otherwise |

**H2 (from the lead).** Mismatched priors do no harm. A domain shows harm at n = 15 if either of these holds:

- the upper bound of r̄(EB-W) − r̄(S) < −0.02;
- the lower bound of FPR(EB-W) / FPR(S) > 1.5.

H2 is supported if no domain shows harm, and contradicted if any domain does.

**H3 (attribution).** At n = 15, r̄(EB-Q) − r̄(EB-0) has a lower 95% bound > 0 in at least 5 of 6 domains. The gain then
comes from the meta-analytic content, not from shrinkage itself.

**Secondary analyses:**

- G at n = 10, 20 and 30 for each EB method;
- Dice and FPR for every method;
- the two PIOP2 replications;
- prior quality: the correlation between each NeuroQuery map and the full-sample group map.

## 7. Validation before the real analysis

**Synthetic check of the code.** Subjects are a smooth random truth plus noise, on the real mask.

- With a prior equal to truth plus noise, EB-Q must beat S and EB-0.
- With an independent prior, EB-W must perform close to EB-0.
- S against itself must give G = 1 exactly.

## 8. Robustness

- β unconstrained (allowed to be negative).
- The ground truth as the mean of all remaining subjects (variable size).
- Top-5% Dice.

## 9. Review and reporting

- An independent reviewer agent checks code, deviations and the draft before any verdict is stated.
- The report opens with an "In plain terms" section.
- Raw images are not committed. Per-subject contrast maps (4 mm, small) and all tables are.
