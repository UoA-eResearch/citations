# Confirmation pass — OpenNeuro multiverse robustness atlas

Reviewer: Fable 5.2, 2026-11-26. Revision reviewed: working tree at commit `4669ee7` (report.md of 26 Nov 05:17),
against the first review (`review/review.md`, draft `9c5cc3f`). New scripts and outputs are in
`review/reviewer_checks/` (`d11_maps.*`, `group_recompute_confirmation.out`, `ds000213_threshold_diff.out`,
`spec_derivative_logic_v2.*`, `stats_recheck_confirmation.out`, `g3_baseline_recheck.*`).

## Verdict: **publish with edits**

All nine findings are fixed or honestly re-scoped, the two first-level defects were fixed by a real rerun that I
could verify in the stored maps, and every number I checked in the report matches the tables. H1 and H2 stay
Inconclusive. Three small edits remain (new findings 1–3); none changes a verdict or a headline number.

## The nine earlier findings

| # | Finding | Status | Evidence |
|---|---|---|---|
| 1 | HRF axis void in 3 datasets | **Addressed** | `designs()` now sets `Derivative` at both levels and matches named X entries against wildcard Convolve inputs. Stored maps, all subjects: canonical and derivative maps are identical in 0 of 408 (ds000002), 0 of 624 (ds000213), 0 of 360 (ds003397) pairs. The rerun produced what the cause analysis predicts: in ds000213 the new canonical maps are bit-identical to the old ones (624 of 624) and the derivative maps are new; in ds003397 the new derivative maps are bit-identical to the old ones (360 of 360) and the canonical maps are new; in ds000002 the same, with correlation 1.000 but about 1.3% of voxels one float16 step apart (cause not found, immaterial). The old and new rule give different designs only for ds000213 among the 24 specs, so no dataset that was not rerun holds maps the current code would not produce. Report wording ("48 ways", HRF numbers) is now true. `axis_check.py` added to G3. |
| 2 | Software vs confounds on different datasets | **Addressed** | 0.773 vs 0.654 on 18 matched datasets, medians 0.806 vs 0.740, software higher in 16 of 18 (15 before D11; ds000148 moved): reproduced from `atlas.csv`. The two excluded datasets and the bundled differences are stated in the verdict, the limits, the figure caption and the tile. |
| 3 | ds000148 without drift regressors | **Addressed** (one residual note, new finding 3) | `add_tsv_cosines` appends the confounds file's cosine columns with zero contrast weight and raises on a row mismatch; it is applied to both HRF levels before the usability check, the tSNR and the GLM. All 49 subjects rerun with version 2 (`rerun_d11.jsonl`), all 2,352 nilearn maps changed (correlation with the old spec-closest map: median 0.88, minimum 0.61), run tSNR rose (first run 78.7 → 92.0), dataset tSNR 80.9 → 99.4. |
| 4 | Extent finding headlined, "independent" support | **Addressed** | Out of the title; "largely expected from how Dice and the empty-map rule work"; 0.73 for the 16 complete datasets reproduced; the correlation index is described as the same dependence. |
| 5 | What R measures; ds002422 coverage | **Addressed** | "What R measures" paragraph; "Brain covered" column (44% for ds002422, checked against `voxels`/235,840); stated again in the table note and in How it was done. |
| 6 | G5 rubber stamp; G4 conclusion too strong | **Addressed** | G5 redone: 68 rows including Results and limits, 9 Partially supported with fixes, and every fix is in the report text. The G4 conclusion now says what the check can and cannot see. ds000114 is in the report; its explanation checks out: the bucket lists `ses-test` and `ses-retest` maps, the check takes `ses-retest`, and our subject files hold two runs (one per session). |
| 7 | Undocumented departures | **Addressed** | D11 item 4 records the scipy group test, smoothing before masking, undefined R and the "no design" wording; the report gives R := 0 (H1 0.123, H2 0.399: reproduced), adjusted R² 0.050, and the 6P + spikes line. `coverage.json` now says "outside the spec's run list". |
| 8 | Runs keyed by run number only | **Not fixed, recorded** | D11 item 4, "Latent … Not fixed". Acceptable: harmless in these 24 datasets. |
| 9 | Ledger defects | **Addressed** | 11 rows, tool check passes. A7: the 24 versions are saved (17 × 21.0.2, range 21.0.1–23.0.2; I re-read ds000148's `dataset_description.json`: 22.0.0, as saved). A8 and A7 have roles. A10 corrected. A11 added and matches the OpenAlex record (Atay, Clénet, Bannier, Maumet 2026, a curated codebase of task-fMRI pipelines, preprint). A6 re-read at the pinned commit (default `5:run:iso`). A8: the listing has 54 FitLins datasets and none for ds003397. |

## Checks on the rerun and rebuild

- **FSL rows carried over unchanged:** configurations 48–95 of `eff` and `eff2` are identical to the superseded
  copies in 17/17, 26/26, 15/15 and 49/49 subjects. Run statuses are unchanged in all four datasets.
- **Group maps rebuilt from the new subject maps:** independent recomputation (scipy t-test, own BH and Dice) of all
  four datasets gives the stored mask and R (0.8395, 0.6755, 0.7192, 0.8117). Thresholded maps are identical except
  one voxel in one configuration of ds000213 (a tie at the FDR boundary). No `group.npz` is older than a subject
  map, and `atlas.csv` equals the 24 group JSON files on R and N.
- **Statistics:** H1 0.141 (0.021–0.483, adjusted 0.050), H2 0.434 (0.050–0.719), Spearman values, axis means and
  medians, most-influential counts (11/6/5/0), small-dataset values, software numbers, coverage shares and the
  task-positive counts (6 + 1 + 1 + 6 of 14) all reproduce (`stats_recheck_confirmation.out`). H1's upper bound is
  0.447–0.485 over five other seeds.
- **Before/after:** only the four rerun datasets changed in `atlas.csv`; the three HRF datasets' R moved by at most
  0.001.
- **Figures and HTML:** both figures and their captions match the tables; `report.html` carries the same numbers as
  `report.md` on the ten strings I compared.

## New findings

### 1. MINOR — the post hoc test of the task-positive explanation is weaker than it reads

**Evidence** (`g3_baseline_recheck.out`, from `g3_baseline.json`, 13 datasets). The reported association is with
the *gap* (task-positive R − primary R): Spearman 0.66 with the summed regressor's variation. But the explanation
("little rest makes all-conditions-against-baseline poorly estimated") predicts that the task-positive R itself is
low for flat designs, and it is not: Spearman −0.03 (p = 0.92). Flat designs instead tend to have a *higher primary*
R (−0.48), and the gap falls with the primary R (−0.52), as it must near 0 and near 1. Holding the primary R fixed,
the gap's association with flatness is 0.55 and the task-positive R's is 0.33. Two measures were tried and the
better one is quoted with an uncorrected p; both use every row of the events file (not the spec's modelled subset)
and the first 10 subjects, which the code says and the report does not. The dataset-level statements (three of the
four sharp drops are among the four flattest; ds000117 does not fit) are correct, and the analysis is labelled
post hoc.

**Fix.** Add one sentence: the task-positive R itself does not go with flatness (−0.03), part of the gap's
association comes from the primary R (floor and ceiling), and the measures are approximate (all event rows, 10
subjects). Say "consistent with" rather than letting 0.66 stand as the test of the explanation. G5 row 58:
Exploratory-labelled → **Partially supported**.

### 2. MINOR — the FSL arm used 407 subjects, not 409

**Evidence.** `coverage_final.py` now counts by maps, so the 2 ds003397 subjects that kept FSL maps from before D9
count as "ok" (409 + 13 skipped = 422). ds003397 has no software comparison (`group/ds003397.json` has no
`software` block; my map check finds FSL maps in exactly 2 of its 15 subjects), so 407 subjects enter a statistic.
The count appears in report.md (G2 line), report.html, plausibility.md and `coverage.json`.

**Fix.** Report 407 used, with ds003397's 15 excluded (2 of them have unused FSL maps). G5 row 4: Supported →
**Partially supported**.

### 3. MINOR — ds000148's "spec-closest" configuration is not close to its spec

**Evidence.** Its spec has no motion and no drift terms (`[1, "trial_type.*"]`), so the external-check
configuration (24P, and since D11 cosine regressors) differs from the published FitLins model in both. Its r (0.91)
and Dice (0.71) are among the lowest of the strong-effect datasets. The report says "the specs' motion terms are
24P" without this exception. This was the last point of the first review's finding 3.

**Fix.** One clause in the external-check paragraph or the table note.

## Gates

| Gate | Status |
|---|---|
| G1 | Unchanged plan (not edited since the draft); the gap the first review found (spec settings interacting with the axes) is now covered by D11 and the axis invariant. No result-dependent choice found in D11: the rerun was dictated by the review, and results before it are kept. |
| G2 | Present and reconciles (736/739 subjects; 2,038/2,097 runs with 45 + 10 + 4 dropped). No unplanned fallback in a statistic. FSL count: new finding 2. |
| G3 | Three datasets and one subject traced; the axis invariant holds (no void axis; before D11 it flags exactly the three datasets). The traces in `g3_trace.json` date from 24 November and were not rerun; none of the traced units was touched by D11, and plausibility.md says ds000212 was traced before D10. The unmet expectation is now tested across datasets (new finding 1 on its reading). |
| G4 | 23/23 with a judgeable denominator; conclusion correctly limited. New finding 3. |
| G5 | Honest now. My re-labels: row 58 and row 4 → Partially supported. |
| G6 | Passes (11 claims); A6, A7, A8, A10, A11 spot-checked against their sources. |
| G7 | Not applicable. |

## Not checked

- The design matrices themselves: pybids cannot rebuild a design without the BOLD files, which are deleted, and
  downloads were not allowed. That the HRF derivative and ds000148's cosine columns are in the designs is inferred
  from the code and from the stored maps and tSNR, not read off a design.
- First-level maps were not regenerated; FSL design files were not rerun.
- The 1.3% of ds000002 voxels that differ by one float16 step between the old and new derivative maps were not
  traced to a cause.
- A1–A5 and A9 were not re-fetched in this pass.
