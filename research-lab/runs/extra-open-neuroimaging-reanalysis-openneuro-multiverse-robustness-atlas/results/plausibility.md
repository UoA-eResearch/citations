# Plausibility gate (G3)

Filled in after D10, on the final tables (25 November 2026). Traces: `code/g3_trace.py` → `results/tables/g3_trace.json`
(seed 20261110), external check `code/external_check.py` → `results/tables/external_fitlins.{csv,json}`.

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | if not: what was found |
|---|---|---|---|---|
| tSNR per dataset (median over runs) | 31.5 to 142.9 (median 76.0) | 20–200 for 3T task BOLD (plan, section 4) | yes | |
| R (mean pairwise signed Dice) | 0.003 to 0.886 over 22 datasets; undefined for 2 (no suprathreshold voxel in any configuration) | [0, 1] by construction | yes | |
| Correlation index (mean pairwise r of unthresholded maps) | 0.53 to 0.98 | high (> 0.5): the 48 configurations share data and design | yes | |
| Spec-closest configuration (6 mm, canonical, 24P, AR(1); D2) vs published FitLins group map | r ≥ 0.7 in 23 of 23 datasets (median 0.98); thresholded signed Dice median 0.82. The matching FSL configuration (≤ 20 subjects): r ≥ 0.7 in 21 of 23 (median 0.91) | r ≥ 0.7 (plan, G4) | yes (nilearn); FSL: 2 short | Where the nilearn configuration has no suprathreshold voxel (ds000008, ds000052, ds000120, ds000144, ds000212), FitLins has at most 2, so these are genuine nulls, not pipeline failures; in ds000114 (R 0.19) ours has 11,342 voxels and FitLins (5 mm) none. The two FSL shortfalls are null datasets with FSL on 20 of 38–39 subjects (ds000144 0.68, ds000212 0.56): noise-dominated maps from half the sample, not a bug. A first run of the check compared the 6P configuration by mistake (median r 0.91). ds003397 has no FitLins output. |
| Task-positive contrast more robust than the primary | in 7 of 14 datasets with a task-positive contrast | "for most datasets" (plan, section 4) | **no** | The four sharpest drops have little or poorly separable implicit baseline: in ds000213 (fixation modelled) and ds000171 the modelled events cover 97% and 99% of the run, in ds002422 the blocks cover 88%, and in ds000117 the stimuli come every 3.2 s, so the summed regressor is nearly flat after convolution. "All conditions against baseline" is then poorly estimated, and its thresholded maps disagree across configurations (ds000117: 2 of 48 configurations have any suprathreshold voxel). The contrast code gives each listed condition weight 1/k, as planned (`firstlevel.py` lines 168–172); no bug. The plan's expectation did not allow for designs without rest. |
| Software (FSL vs nilearn, matched configuration) | mean signed Dice 0.69, mean r 0.96 (20 datasets) | similar to within-software variation | yes | The nilearn confound-only pairs on the same subjects give 0.65. |

## 2. Units traced end to end

Seeded random picks (`numpy.random.default_rng(20261110)`).

| unit | raw input | intermediate values | output used in the analysis | matches the pipeline? |
|---|---|---|---|---|
| ds000144 (dataset) | 38 subject map files | 38 complete subjects = 38 `ok` in the log = N 38 in the atlas; group z of configuration 16 recomputed from the subject maps | z within 0.0019 of `group.npz` (float16 storage); 0 FDR voxels recomputed vs 0 stored; peak z −4.69 at MNI (−14.5, −28.5, 41.5) | yes |
| ds000212 (dataset; traced before D10 changed 2 of its subjects, whose dropped runs stayed dropped) | 39 subject maps | 39 = 39 = 39 | z within 0.0018; 0 FDR voxels vs 0; peak −4.09 | yes |
| ds000157 (dataset) | 30 subject maps | 30 = 30 = 30 | z within 0.0020; 18,228 FDR voxels recomputed vs 18,228 stored; peak z 7.21 at MNI (−18.5, −96.5, −2.5), occipital pole, plausible for food vs non-food pictures | yes |
| ds000170 sub-1717, configuration 3 (4 mm, canonical, 24P, OLS) | events: Perf_1 block onset 24 s, 24 s long; Perf_2 at 84 s; Start/Stop markers; 45 volumes, TR 3 s | design: intercept, Perf_1, Perf_2, 1 cosine; contrast Perf_1 = +1; 24 confound columns (6P, derivatives, squares); the Perf_1 regressor is above 10% of its peak from 27 to 54 s (peak 36 s), Perf_2 from 87 to 111 s | rerun of the whole subject (all 48 nilearn configurations) matches the stored maps within 0.011 (float16); the map's largest value (−23.1) is an inferior edge voxel (MNI z −46.5), about 20 times its 95th percentile: edge noise in a 45-volume block run, not task signal | yes |

## 3. Invariants asserted in code

| invariant | where asserted (file:line) | holds? |
|---|---|---|
| counts reconcile between stages (n in → n out + dropped) | `coverage_final.py` (subjects 736 ok + 3 dropped = 739; runs 2,038 + 59 = 2,097; FSL arm 409 + 13 = 422); atlas N sums to 736 = subjects `ok` | yes, after D10 (the reconciliation found 19 subjects with runs dropped under D6's superseded rule and one subject's maps from the timing run; both fixed) |
| the setting / version / subset used is the one plan.md names | `eligible.py` (specs at commit e624fec), `firstlevel.py` (48 configurations, `cfg_label`), `driver.py` (seed 20261110, cap 100, FSL arm first 20, ds003397 skipped per D9) | yes, with deviations D1–D10 |
| no NaN reaches a primary statistic | `grouplevel.py`: complete subjects only (D6) and voxels finite in every subject; `analyse.py`: datasets with undefined R (2) dropped from H1/H2 and counted | yes |
| joins neither duplicate nor drop units | atlas: 24 rows, 24 unique datasets; first-level log: subject labels mapped to the spec's spelling before taking the last entry (the 14 November rows wrote "9" for "09") | yes, after the label fix |
