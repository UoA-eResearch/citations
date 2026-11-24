# Independent review — OpenNeuro multiverse robustness atlas

Reviewer: Fable 5.2, 2026-11-25. Draft reviewed: commit `9c5cc3f` (report.md of 25 Nov 01:06).
Scripts and their outputs are in `review/reviewer_checks/`.

## Verdict: **fix first**

The H1 and H2 verdicts (both Inconclusive) reproduce and survive every sensitivity analysis I ran. But the
multiverse is not what the report says it is in 3 of the 24 datasets (the HRF axis was never varied there), one
headline sentence (software vs confounds) compares different sets of datasets and reverses in size when matched, and
one dataset has no drift model. These change per-dataset atlas entries, the "which choice matters" numbers and the
software conclusion, so they need fixing (rerun or explicit re-scoping) before publication, not just rewording.

## What I verified and found sound

- **Timeline (git + file dates).** Plan committed 10 Nov 17:05; specs fetched 12 Nov 17:15; first data on disk 12 Nov
  17:35, after D1 (17:18). D1–D9 committed by 24 Nov 11:00; the first `group.npz` is 24 Nov 17:05. D2's "24P, not
  6P" for the spec-closest configuration is in commit `93a192e` (13 Nov), so the external-check configuration was
  fixed before any result. D10 applies D8's rule; before/after: only ds000001 (0.562 → 0.628) and ds000108
  (0.428 → 0.469) moved, H1 0.145 → 0.141, H2 unchanged. Not a data-driven choice.
- **Eligibility.** Bucket listings (metadata only) for the first, middle and last spec subject of all 30 "missing
  derivatives" datasets: 0 preprocessed BOLD and 0 confounds files in every one, only boldrefs/transforms
  (`eligibility_listing.out`). The drop is real, not a failed listing.
- **Group level.** Independent recomputation (scipy t-test, own BH and signed Dice) for ds000002 and ds002422: mask,
  all 48 thresholded maps and R identical to the stored values (`group_recompute.out`).
- **Statistics.** H1 0.141 (0.021–0.478), H2 0.434 (0.050–0.719), all Spearman values, axis means/medians and counts
  reproduce from `atlas.csv` (`stats_recheck.out`). H1's upper bound is 0.445–0.483 over five other bootstrap seeds:
  Inconclusive is stable.
- **Undefined R (2 datasets).** Setting them to 0 (the natural limit: a dataset with 3/48 non-empty maps already
  scores 0.003) gives H1 0.12 (0.01–0.45) and H2 0.40 (0.03–0.67, 12 datasets): both still Inconclusive. Only the
  implausible R := 1 would turn H1 to Refuted (upper bound 0.394).
- **FSL shortfalls in the external check.** nilearn on the same 20 subjects gives 0.69 (ds000144) and 0.63
  (ds000212) against FitLins, about the same as FSL's 0.68 and 0.56 (`fsl_shortfall.out`). The report's explanation
  (half the sample, null contrast) holds.
- **Coverage.** 736 subject files; run statuses 2,038 / 45 / 4 / 10 match `coverage.json`; no file carries D6's old
  status string (`meta_scan.out`). G6 tool check passes; G2 file exists.

## Findings

### 1. MAJOR — the HRF axis is void in 3 datasets: 24 distinct configurations, not 48

**Evidence.** In ds000002, ds000213 and ds003397 the stored subject maps of every "canonical" configuration are
bit-identical to the matching "+ derivative" configuration (first 3 subjects each in `axis_identity.out`; all 17
subjects and all 24 pairs for ds000002 in `group_recompute.out`). `atlas.csv` shows it as `axis_hrf` = 1.0 exactly
for these three. Two different causes, both in `firstlevel.designs()`:
- **ds000213:** the spec convolves `trial_type.*` but lists the regressors by name in `Model.X`. The code adds
  `_derivative` columns only for X entries that appear literally in the Convolve inputs (`x in conv`), so none is
  added and the derivative design equals the canonical one.
- **ds000002 and ds003397:** the spec itself sets `"Derivative": true` (`"True"` in ds000002). The code never sets
  it to false for the canonical level, so both levels include the derivative. Here the *canonical* level is missing.
  (`spec_derivative_logic.out` replays the logic for all specs; no other eligible dataset is affected.)

**Consequences.**
- "Each of 24 … datasets … was reanalysed 48 ways" (standfirst, plain terms) is false for 3 datasets.
- Their R is over 3 axes, not 4, so it is not comparable with the other 21 and is biased upward (24 of the 1,128
  pairs are trivially 1.0, and no HRF variation enters the rest). ds000002 (R 0.84) is the report's showcase for
  "robust with only 17 subjects"; ds003397 and ds000213 are also in or near the H2 group.
- The pooled HRF-axis Dice is 0.67 without the three, not 0.71; the per-dataset median 0.78, not 0.89. "Most
  influential choice" counts (11/6/5/0) include three datasets where the HRF could not be chosen.
- ds000002's FSL comparison pairs FSL without a derivative against nilearn with one.
- H1/H2 without the three: R² 0.23 (0.04–0.61, 19 datasets), median 0.36 (0.005–0.63, 9): still Inconclusive.
- G3 and G4 did not catch this: the plausibility gate has no invariant that configurations differing on an axis give
  different maps, and the external check looks at one configuration.

**Fix.** Rerun the missing 24 configurations for the three datasets (force `Derivative` false for the canonical
level; expand wildcards before adding derivative columns), rebuild the group maps and all tables. ds000002 and
ds000213 are small; ds003397 needs the nilearn arm only. If ds003397 cannot be rerun, mark its HRF axis "not
varied", report its R as a 24-configuration value, exclude it from the HRF-axis statistics, and show H1/H2 with and
without it. Add the "axes differ" invariant to `g3_trace.py`. Record it as D11 (after results).

### 2. MAJOR — "software moves a map about as much as confounds" compares different datasets

**Evidence.** Software Dice 0.69 is the mean over 20 datasets; the confound Dice 0.65 "on the same subjects" is the
mean over 18. The two missing ones (ds000008, ds000120) have software Dice 0.00 (one package finds voxels, the other
none) and an undefined confound Dice (all nilearn maps empty). On the 18 datasets where both are defined, software
Dice is **0.77** against confounds 0.65, and software agreement is higher in 15 of 18 (`stats_recheck.out`).

**Consequence.** The like-for-like reading is that switching first-level software moved thresholded maps *less* than
switching confound sets, not "about as much". Overclaim rows 25, 26 and 43 are labelled Supported; they should be
Overstated.

**Fix.** Report both on the same 18 datasets (0.77 vs 0.65; medians 0.79 vs 0.74), say what happens in the two
excluded datasets, and reword. Also state that "software" here bundles SUSAN vs Gaussian smoothing, FSL's double
gamma vs SPM's HRF, `-bptf` vs cosine high-pass and grand-mean vs voxelwise scaling: "only the first-level software
differs" understates that.

### 3. MODERATE — ds000148 has no drift model and no spec confounds

**Evidence.** Its spec's `Model.X` is `[1, "trial_type.*"]`: no `cosine*`, no `trans_*`/`rot_*`. The nilearn arm
takes drift regressors only from the spec's X, so all 48 configurations for ds000148 run without any high-pass
filter, contrary to the plan ("cosine drift regressors are kept in every configuration"). Its tSNR (81) is computed
without drift removal, unlike the other 23. The FSL arm does high-pass filter at 128 s, so its software Dice (0.68)
also reflects filtering. And the "spec-closest" configuration (24P) is not close to a spec with no confounds, which
may be part of its r = 0.90.

**Fix.** Either add fMRIPrep's cosine columns for ds000148 and rerun (49 subjects, nilearn arm), or disclose it as
a deviation, footnote the atlas row and drop it from the software comparison. Recompute its tSNR as defined.

### 4. MODERATE — the post hoc extent finding is headlined and its "independent" support is not independent

**Evidence.** R is computed from the same thresholded maps whose size is the predictor, and the plan's rule (a pair
with one empty map scores 0) makes R nearly a function of the share of non-empty configurations whenever that share
is below 1. The report offers the correlation index as corroboration ("shows it too", 0.62), but the correlation
between z maps also rises mechanically with signal strength, so it is the same coupling, not a check on it. Among the
16 datasets with voxels in all 48 configurations the Spearman is 0.73 (n = 16), still by construction to an unknown
degree.

**Fix.** Take the extent claim out of the title. In the text say that the association is largely expected from how
Dice and the empty-map rule work, give the 0.73 for fully non-empty datasets, and drop "shows it too" or describe it
as the same dependence. Overclaim row 18 → Partially supported.

### 5. MODERATE — R mixes two things, and ds002422's R covers 44% of the brain

- For datasets with empty maps, R mostly measures how many configurations cross the FDR threshold at all
  (ds000120: 3/48 → 0.003). That is the preregistered index, but the report should say so where it reads R as
  "fragile maps".
- ds002422, the top-ranked dataset (0.89), has a group mask of 103,461 of 235,840 voxels; every subject has partial
  coverage (median 162,246; `group_recompute.out`). Its R is for under half the brain, with 57% of those voxels
  suprathreshold. Footnote it; add the `voxels` column to the report table.

### 6. MODERATE — G5 is a rubber stamp; G4's conclusion is too strong

- `overclaim_check.md`: 44 rows, 39 Supported, 5 Exploratory-labelled, no fix. It stops at "In plain terms" (nothing
  from Results or "What this does and does not show"). My re-labels: row 2 (48 ways) **Overstated** (finding 1);
  rows 22–24 **Partially supported** (HRF numbers); rows 25, 26, 43 **Overstated** (finding 2); row 18 **Partially
  supported** (finding 4); row 44 **Overstated**.
- Row 44, "which suggests the pipeline itself is sound": the check covers 1 of 48 configurations, and the reference
  shares the specs, the fMRIPrep derivatives and the GLM engine (FitLins uses nilearn). It shows the spec was applied
  as its authors applied it; it could not see findings 1 or 3. Reword to that.
- The report says "where that configuration finds nothing, the published map has at most 2 suprathreshold voxels"
  but omits the opposite case recorded in plausibility.md: ds000114, where ours has 11,342 voxels and FitLins none
  (r 0.86). Put it in the report.

### 7. MINOR — undocumented departures from the plan

- **Group test:** the plan names nilearn `SecondLevelModel`; `grouplevel.py` uses its own t-test (equivalent, but not
  in deviations.md). Ledger row A10 says nilearn's second-level tools were used: wrong.
- **Smoothing:** the plan says "within the fMRIPrep brain mask"; the code smooths the whole unmasked volume and then
  masks, so non-brain signal is blurred into edge voxels.
- **Undefined R:** excluding the two all-empty datasets from H1/H2 was decided after results and is not a numbered
  deviation. State it as one and give the R := 0 sensitivity (above).
- **"No design" (45 runs):** these are runs outside the spec's `Input.run` list (ds000051 runs 7–8, ds000144 run 2),
  not runs "without a design for the spec's contrast". Reword; they are not really drops.
- **In-sample R²:** with 22 datasets and 2 predictors the adjusted R² is 0.05; "explain only 14%" could say so.
- **6P + spikes** equals 6P for every subject with no volume above 0.5 mm (16–96% of runs have spikes, by dataset),
  so some confound pairs are identical by design. Worth one line.

### 8. MINOR — latent bug, harmless here

`designs()` keys runs by run number only. ds000114 has two sessions and no run entity, so both sessions share one
design entry. Their events files are identical (same md5), so nothing changes, but the code would silently
mis-assign designs in a dataset with session-specific events. Key by (session, run).

### 9. MINOR — attribution ledger

Tool check passes (10 claims). Spot-checks: A1 (NARPS), A2 (Bowring 2019, Dice 0.000–0.684), A3 (HCP
multi-pipeline, 24 pipelines, 1,080 participants) and A4 match the sources as I know them; I did not re-fetch them.
A7 (fMRIPrep 21.0.1–23.0.2) could not be confirmed from disk: the local `dataset_description.json` copies give no
version. A7 and A8 have an empty role. A10 is inaccurate (finding 7). The plan's "Atay et al. 2026" has no ledger
row.

## Gates

| Gate | Status |
|---|---|
| G1 | Real but incomplete: it did not consider that a spec's own settings (HRF derivative on, no drift terms) interact with the multiverse axes (findings 1, 3). No result-dependent choice found. |
| G2 | Present, reconciles; no unplanned fallback in a statistic. "No design" mislabelled (finding 7). |
| G3 | Three datasets and one subject traced, values reproduce. Hollow in one respect: no invariant that configurations differ, so finding 1 passed. The task-positive explanation (7 of 14) is plausible but shown for the four largest drops only, not tested across the 14. |
| G4 | 23/23 with a judgeable denominator; FSL shortfalls correctly explained (verified). Conclusion drawn from it is too strong (finding 6). |
| G5 | Passes formally; not honest enough (finding 6). |
| G6 | Passes; small defects (finding 9). |
| G7 | Not applicable. |

## Not checked

First-level maps were not regenerated (BOLD deleted; no downloads allowed), so the confound sets, AR(1) vs OLS,
fixed effects and tSNR were reviewed in code and by comparing stored maps only. FSL design files were read in code,
not rerun. Figures and report.html were not compared with the tables.
