# Deviations from plan.md

## D1 — 2026-11-11 — the FSL software axis is restored (before any data was downloaded)

The plan dropped the lead's software axis because FSL could not be installed on the guest machine. The lab's owner
then offered Docker, so FSL now runs in a container. No data, events file or derivative image had been downloaded when this was written.

**The image** (`code/docker/Dockerfile`): FSL 6.0.7 conda packages for the first-level tools only (`fsl-feat5`
2201.9, `fsl-film` 2111.2, `fsl-avwutils` 2209.8, `fsl-susan` 2111.0), on `mambaorg/micromamba:1.5.10`. FSL is free
for non-commercial academic use.

**The FSL arm** mirrors the nilearn arm's four axes with FSL's own implementation of each, as FEAT's pre-stats and
stats stages do on data that is already preprocessed and in MNI space:
- **smoothing:** SUSAN at 4, 6 or 8 mm FWHM with FEAT's brightness threshold (0.75 × the median within the brain mask,
  the mean image as the USAN), then FEAT's grand-mean scaling (to 10,000) and high-pass filter (`fslmaths -bptf`,
  128 s, the same cut-off as fMRIPrep's cosine regressors);
- **HRF:** FSL's double gamma, with or without its temporal derivative (`feat_model` from a generated `.fsf`);
- **confounds:** the same four sets as confound EVs (6P, 24P, 24P + 5 aCompCor, 6P + spikes at FD > 0.5 mm), without
  the cosine regressors, which the high-pass filter replaces;
- **noise model:** FILM prewhitening on (FEAT's default) or off (`film_gls --noest`).

The task EVs are the same pybids-transformed variables as in the nilearn arm, written as FSL three-column files
(onset, duration, amplitude), and the contrast weights are the same. Run-level COPEs and VARCOPEs then go through the
same subject and group stages as the nilearn arm, so only the first level differs.

**How it enters the analysis.** H1 and H2 stay as preregistered, on R over the 48 nilearn configurations. Added,
before any data:
- **R96**, the same index over all 96 configurations (48 nilearn + 48 FSL), with H1 and H2 re-read on it as a
  sensitivity;
- **software** as a fifth axis in secondary 2 ("which choice matters"): the mean Dice between configurations that
  differ only in software;
- the external check (secondary 3) for the FSL configuration closest to the spec as well.

**Where it runs (changes plan section 5).** On 2026-11-12, before any data, the guest machine became unavailable (its
owner's colleague needs it). Everything runs on the lab's own VM instead: 28 cores shared with other work, so at most
14 worker processes; data streamed to `/mnt/data/omv/` (132 GB free) one subject at a time and deleted after
processing; Docker's storage is already on `/mnt`. Nothing runs on the guest machine.

**Compute rule, fixed now.** After a timing run on one subject of the first dataset (timing only; no group map is
made), if the projected total for both arms exceeds 6 days on 14 workers, the FSL arm is reduced, in this order, until
it fits: first, FSL with prewhitening on only (24 configurations; R96 becomes R72); then FSL on at most 60 subjects
per dataset (the first 60 of the seeded order). Any reduction is recorded in a later deviation before results.

**Eligibility (run 2026-11-12, metadata only; `code/eligible.py`, `results/tables/eligible.csv`).** Of the 57
datasets with specs, 24 are eligible; 30 have fMRIPrep derivatives that are "fit-only" (reference images and
transforms, no resampled BOLD and no confounds), so they fail the plan's requirement of MNI res-2 BOLD and confounds;
3 have fewer than 10 spec subjects. Of the 24, 12 have N < 25, and one (ds001734) has more than 100 and is analysed on
100. In 10 of the 24 the first run-level contrast is a single regressor (a condition against baseline, or one
parametric modulator), so the secondary task-positive map equals the primary map there; the secondary contrast is
reported for the other 14.

