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

## D2 — 2026-11-12 — implementation details (before any first-level result)

Settled while building and timing the pipeline on one subject of ds000001. No contrast map, group map or robustness
value had been computed.

1. **Applying the specs as their authors did.** The specs are written for openneuro_glmfitlins' own event files: its
   `modify_events.<ds>` functions fill `n/a` modulators with 0, rename trial types pybids cannot parse and add
   response-time regressors, and its pybids is pinned to a development commit. Without them, ds000001's spec fails in
   pybids. So the project's `modify_events.py` is vendored at the spec commit (`code/vendor_glmfitlins/`, MIT licence)
   and applied to each dataset whose basic details set `preproc_events` (12 of the 24), and pybids is pinned to the
   project's commit (26b3f7e). None of the 24 datasets trims dummy volumes.
2. **The spec's own confounds are 24P, not 6P.** Every spec lists `trans_*` and `rot_*`, which match fMRIPrep's
   derivative and squared columns too. The configuration closest to the spec (secondary 3) is therefore 6 mm, SPM
   canonical, 24P, AR(1) (FitLins used 5 mm, between our 4 and 6 mm levels), not 6P as the plan said.
3. **Raw and derivative files are matched by entities** (subject, session, task, acquisition, run as an integer,
   echo): raw files say `run-01` where fMRIPrep says `run-1`.
4. **Downloads.** The VM's link to AWS reaches about 85 KB/s per connection, so files are fetched as parallel byte
   ranges (32 connections per file). The eligible data total 1,068 GB (2,098 runs), 570 GB of it in ds001734.
5. **Storage.** Subject-level fixed-effects contrast maps are stored per configuration as float16 within the
   MNI152NLin2009cAsym res-2 template brain mask (235,840 voxels; the mask file from openneuro_glmfitlins), NaN outside
   the subject's own brain mask; the group analysis uses voxels inside every subject's mask.
6. **Scaling.** nilearn arm: percent signal change per voxel before the GLM (nilearn's `signal_scaling=0`); FSL arm:
   FEAT's grand-mean scaling to 10,000. Effects are compared only within a configuration, so the scale difference does
   not enter R; across software it enters only through thresholded overlap and correlation, which are scale-free.
7. **FSL EVs** are the same pybids variables taken just before the spec's Convolve step (onset, duration, amplitude),
   written as three-column files and convolved by FSL; task columns the spec does not convolve enter as one value per
   volume, unconvolved. FILM uses FEAT's settings (`--sa --ms=5`, threshold 1000).

## D3 — 2026-11-13 — the FSL arm is reduced after the timing run (before any group result)

The timing run (ds000001 sub-01, 3 runs of 300 volumes; first level only, no group map) took 24 minutes per run for
the 48 nilearn configurations and 8.9 hours per run for the 48 FSL ones, on this VM while another job held 8–20 of
its 28 cores. Per step, for one run: SUSAN 12 minutes per smoothing level, scaling and high-pass 3½ minutes,
`film_gls` without prewhitening 3 minutes, with FILM prewhitening about 17 minutes. Projected over the 2,098 runs on
14 workers: about 60 hours for the nilearn arm and about 55 days for the FSL arm.

D1's reduction rule does not make this fit. Its first step (prewhitening on only) assumed the two noise settings cost
about the same, when prewhitening is most of the cost; its second (60 subjects per dataset) still leaves weeks. The
FSL arm is therefore cut to a focused software comparison:
- **FSL configurations:** 6 mm, FSL's double-gamma HRF without derivative, each of the four confound sets, no
  prewhitening (OLS): 4 configurations (indices 1·48 + 1·16 + 0·8 + c·2 + 1);
- **FSL subjects:** at most 20 per dataset (the first 20 of the dataset's seeded order), about 1,244 runs, about 29
  minutes per run;
- **R96 and the R96 re-reading of H1 and H2 are dropped.** The software axis in secondary 2 becomes the Dice (and the
  correlation) between each FSL group map and the nilearn group map that differs only in software (6 mm, canonical,
  the same confounds, OLS), computed on the same subject subset, beside the Dice between nilearn maps that differ
  only in confounds on that subset;
- the external check (secondary 3) for FSL uses the 24P configuration;
- the nilearn arm runs on all subjects as preregistered, and H1 and H2 never wait for the FSL arm.

The timing subject's other 44 FSL maps exist but are not used.

## D4 — 2026-11-13 — the secondary contrast is added to the first level (before any group result)

The plan's secondary contrast (every condition in the primary contrast's condition list against the implicit
baseline) was missing from the first-level code. The first launch of the full run was stopped after about a minute,
before any subject finished, and the code now computes both contrasts in one fit: equal weights (1/k over the k
conditions) in the nilearn arm, and a second FSL contrast in the same design. Where the primary contrast names a
single regressor (10 of the 24 datasets) the secondary contrast is not computed, as D1 said. Subject files hold
`eff` (primary) and `eff2` (secondary). The same launch check also caught that pybids reports the Convolve step's
inputs with wildcards unexpanded (`trial_type.*`), which had sent those regressors to FSL already convolved; they are
now expanded, so every convolved task regressor reaches FSL as a three-column EV. The timing subject was rerun.

## D5 — 2026-11-14 — first-level fixes during the run (before any group result)

1. **An upstream bug in the vendored events preparation.** `modify_events.ds000002` returns an undefined name
   (`eventsdat_cpy`) on the branch that relabels trials without a response as "missed"; it now returns the frame it
   has just modified (`eventsdat`), which is the evident intent. Marked in the vendored file.
2. **Dataset-level sidecars.** Some datasets keep the repetition time only in the dataset-level
   `task-<task>_bold.json` (BIDS inheritance); the local mirror now copies those files, so pybids finds the TR
   (ds000009 failed without it).
3. **Subjects in a spec without derivatives** (for example ds000008 sub-09 and ds002422 sub-20 have no fMRIPrep output
   for the task) are dropped as "no usable run" and counted in coverage, as the plan says.
4. **Housekeeping:** each worker uses one BLAS thread, and a failed subject's images are deleted at once so failures
   cannot fill the disk. The driver was restarted three times for these changes; subjects already finished were kept,
   and interrupted ones were rerun from the start.

## D6 — 2026-11-14 — a run-usability rule (before any group result)

ds000115 sub-29's fMRIPrep output for the task holds 21 volumes, while its events run to 310 s: the derivative is
truncated. In such a run the larger confound sets (24P and 24P + aCompCor have 24 and 29 columns) exceed the number of
volumes, so half the configurations cannot be estimated. Rule, fixed now:
- a run is used only if the scan covers its events (the last onset plus duration is within the run's volumes plus one
  TR) and it has at least 10 more volumes than the largest design (task and drift columns with the derivative HRF,
  plus the largest confound set); other runs are dropped with the reason recorded;
- a subject with no usable run is dropped ("no usable run");
- the group stage uses only subjects whose 48 nilearn maps are all present, and lists any others.
Subjects processed before the rule that it would change are rerun in a second pass after the main run.

## D7 — 2026-11-20 — mechanical event fixes for three datasets and short aCompCor sets (before any group result)

After the first pass (642 subjects done, 31 dropped by rule, 55 failed), the failures had four causes, none involving
a result:
- **ds003397 (15 subjects):** the events say `flashing checkerboard`; the spec refers to `flashing_checkerboard`, so
  pybids dropped the contrast. Spaces and dashes in condition names are replaced by underscores when that is what the
  spec refers to, as openneuro_glmfitlins itself does for ds000008.
- **ds000170 (15):** the events' condition column is `name`, not `trial_type`. Where there is no `trial_type`
  column, the column whose values include the spec's conditions is used as `trial_type`.
- **ds000117 (16):** the spec assigns `response_time` as the duration of an RT regressor, and `response_time` is
  `n/a` on every stimulus row, which pybids cannot convolve. Where a spec assigns `response_time` as a duration,
  `n/a` response times are set to 0, as the project's own `add_reactiontime_regressor` does.
- **9 subjects in 5 datasets:** fMRIPrep kept fewer than 5 aCompCor components. The 24P + aCompCor set now uses the
  first five components, or all of them where fewer exist.

Each change is applied once per events file and written to a `.d7` note beside it (`code/firstlevel.py`
`normalise_events`). The 55 subjects, and any subject left incomplete under D6, are rerun.

## D8 — 2026-11-21 — D6's coverage test revised, and memory (before any group result)

1. **D6's coverage test was too strict.** It dropped a run whenever its events ended more than one TR after the last
   volume. That is common and harmless: in ds000213 every scan is 558 s and the last event ends at 580 s, and in
   ds000001 the last events end 2–12 s after 600-s scans. It dropped all 26 ds000213 subjects and 2 in ds000001, none
   of them truncated. The test now drops a run only if the scan covers less than 90% of the event span (last onset
   plus duration). ds000115 sub-29, the truncated case D6 was written for (22 volumes, 55 s, against events to 311 s;
   17%), is still dropped. The 28 subjects are rerun. The volume rule (at least 10 more volumes than the largest
   design) is unchanged.
2. **Memory.** At 00:05 on 21 November the kernel's out-of-memory killer stopped one worker at 23 GB, which broke the
   process pool. Smoothing held a full smoothed copy of the 4D image beside the original, and the scheduler's estimate
   (six times the compressed file size) badly undercounted large runs. The nilearn arm now smooths 64 volumes at a
   time (identical results, since the smoothing is spatial within each volume), and the scheduler estimates each
   subject's peak as 2.5 times its largest run's uncompressed size from the NIfTI header, plus 2 GB.


## D9 — 2026-11-24 — ds003397 without the FSL arm, and memory again (before any group result)

1. **ds003397 is too large for the FSL arm.** Its runs have 1,360 volumes (97 x 115 x 97 voxels, TR 4 s), 5.9 GB
   uncompressed each. Subject 05's FSL arm alone took 12.2 hours, and the FSL arm of subjects 08 and 10 was stopped by
   the kernel's out-of-memory killer (`fslstats` at 19 GB inside the container, 21 November at 16:55 and 18:17). The
   remaining 13 subjects would need about a week of FSL time on this machine. The FSL arm (D3) is the secondary
   software comparison; it is skipped for ds003397, which keeps the full 48-configuration nilearn arm for all its
   subjects. The software comparison already requires at least 10 FSL subjects per dataset, so ds003397 drops out of
   it (2 subjects have FSL maps). The other 23 datasets are unchanged.
2. **Memory.** At 20:26 on 21 November a ds003397 worker reached 27 GB (D8's estimate: 2.5 x 5.9 + 2 = 17 GB), the
   machine ran out of memory, and the killed worker broke the process pool; the driver stopped with 16 subjects left
   (13 in ds003397, 3 that have no usable run). The estimate is now 4.6 times the largest run's uncompressed size plus
   2 GB, the measured ratio, and the remaining subjects run on at most 2 workers. Memory used by the FSL container is
   not part of the estimate; skipping the FSL arm for ds003397 removes the largest case.

## D10 — 2026-11-24 — D8's coverage rule applied to every subject (found after the first group results)

The G2 coverage reconciliation, run after the first group results and H1/H2 (24 November, 17:40), showed 21 runs in
19 subjects still dropped as "events beyond the end of the scan", D6's original rule: 12 subjects in ds000001 (the
case D8 describes: events ending 2–12 s after 600-s scans), 3 in ds000108, 2 in ds000148 and 2 in ds000212. D8
replaced that rule with "the scan covers less than 90% of the event span" and reran the 28 subjects who had lost
every run, but not subjects who had lost only some runs; those kept maps from fewer runs than the agreed rule allows.
No new rule is introduced: D8's rule is applied to these 19 subjects too. Their maps are moved to
`/mnt/data/omv/out_superseded_D10/` and recomputed, the four datasets' group maps and every downstream table are
rebuilt, and the report shows the results before (`results/tables/primary_before_D10.json`) and after. ds000212's
two runs (22 and 67 volumes) are short and may be dropped again under D8.

**Addendum (same reconciliation, 25 November).** The atlas counted 736 subjects against 735 analysed in the log. The
extra one is ds000102 sub-10, whose maps came from the timing run (13 November, 23:05), before D5–D8. The driver
skipped it as done, so it was never logged. It is rerun with the final code like the 19 above (its old maps moved to
`out_superseded_D10/`), and ds000102 is rebuilt. Separately, the first log rows of 14 November wrote some subject
labels without their leading zero ("9" for "09"); the coverage count now maps labels to the spec's spelling, which
removes a double count (3 subjects without a usable run, not 4).
