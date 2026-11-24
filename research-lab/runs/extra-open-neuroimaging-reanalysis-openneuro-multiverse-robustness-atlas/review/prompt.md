You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/extra-open-neuroimaging-reanalysis-openneuro-multiverse-robustness-atlas/
(read-only except your output in review/).

**The question.** How robust are OpenNeuro task-fMRI group maps to defensible first-level choices, dataset by dataset?
24 datasets with BIDS Stats Model specs (openneuro_glmfitlins) and fMRIPrep derivatives; 736 subjects; 48 nilearn
configurations (smoothing 4/6/8 mm × HRF ± derivative × confounds 6P/24P/24P+aCompCor/6P+spikes × AR(1)/OLS); the
spec's first contrast; robustness R = mean pairwise signed Dice of the 48 FDR-thresholded group maps. A reduced FSL arm
(4 configurations, ≤ 20 subjects per dataset) compares software.

**Reported:** H1 (R² of R on log10 N + tSNR > 0.4) Inconclusive: R² 0.14 (0.02–0.48), 22 datasets. H2 (median R < 0.5
for N < 25) Inconclusive: 0.43 (0.05–0.72), 11 datasets. Secondary-threshold and correlation-index versions of H1
Refuted. Post hoc: R tracks median suprathreshold extent (Spearman 0.89). Axis Dice: smoothing 0.57, confounds 0.58,
HRF 0.71, noise 0.78. Software (FSL vs nilearn) Dice 0.69 vs confounds 0.65. External check vs published FitLins maps
(spec-closest configuration 6 mm, canonical, 24P, AR(1)): 23/23 r ≥ 0.7, median 0.98.

**What to read:** plan.md; deviations.md (D1–D10; D10 was made after the first group results); report.md;
results/plausibility.md; results/attribution_ledger.csv; review/overclaim_check.md; results/tables/ (eligible.csv,
coverage.json, firstlevel_log.csv, group/<ds>.json, atlas.csv, primary.json, primary_before_D10.json, before_D10/,
external_fitlins.csv/.json, g3_trace.json); code/ (eligible.py, fetch.py, firstlevel.py, driver.py, grouplevel.py,
analyse.py, external_check.py, coverage_final.py, g3_trace.py, figures.py; vendor_glmfitlins/).

**Data on disk (do not download more, do not run driver.py, do not touch running processes):**
/mnt/data/omv/out/<ds>/sub-*.npz (per-subject maps: eff[96, 235840] float16 = 48 nilearn + 48 FSL configurations,
eff2 = secondary contrast, meta = per-run JSON), /mnt/data/omv/out/<ds>/group.npz, /mnt/data/omv/fitlins/ (published
FitLins z maps), /mnt/data/omv/out_superseded_D10/ (the 20 subjects' maps replaced under D10). Events and confounds
files are under /mnt/data/omv/<ds>/raw and deriv; the BOLD images were deleted after processing.

**Git.** Read-only git is fine. Verify that the plan preceded any data, that D1–D9 were committed before any group
result, and that D10 applies an already-agreed rule rather than a data-driven choice (compare before/after).

**Environment.** Use this run's venv: venv/bin/python -I (nilearn, numpy, pandas, scipy). Do not pip install. Loading
a dataset's subject maps takes up to ~9 GB of RAM: run at most one such recomputation at a time. Do not read ~/.config.

Check at least:
1. Eligibility and the contrast chosen by rule (eligible.py); the 30 datasets dropped as missing derivatives.
2. First level: configuration indexing (`cfg_index`, `cfg_label`), confound sets, the HRF derivative, AR(1) vs OLS,
   smoothing within the mask, fixed effects across runs, tSNR as defined in the plan, the D6/D8 run-usability rule.
3. Group level: one-sample t-test, the all-subjects voxel mask, FDR, signed Dice, empty-pair handling, and the two
   datasets with undefined R excluded from H1/H2 (the plan does not say what to do when every pair is empty).
4. Statistics: the H1 R² bootstrap and the H2 median bootstrap (2,000 resamples, seed 20261110).
5. Whether the post hoc extent finding is stated with the right caution (Dice is mechanically tied to map size).
6. Software comparison: the matched configurations (FSL no prewhitening vs nilearn OLS), the ≥ 10 FSL-subject rule,
   and D9 (ds003397 without FSL).
7. External check: configuration 18 vs FitLins (a first run used 6P by mistake), the FSL configuration 67, and the
   two FSL shortfalls.
8. G3's unmet expectation (task-positive contrast more robust in 7 of 14 datasets) and its explanation.
9. Report: every number against the tables; the title and "In plain terms".

> **Gate checks (METHODS.md G1–G7).** Verify:
> - **G1:** plan.md's leakage audit is real and complete; look for label-correlated fields it missed.
> - **G2:** `results/tables/coverage.json` exists, and no unplanned fallback entered a statistic.
> - **G3:** `results/plausibility.md` traces three units, and the asserted invariants hold.
> - **G4:** every validation metric has an error audit with a judgeable denominator.
> - **G5:** `review/overclaim_check.md` passes and is honest; re-label any sentence you disagree with.
> - **G6:** `results/attribution_ledger.csv` passes `tools/attribution.py check`; spot-check 5 claims against
>   their sources, including the role and conditions.
> - **G7:** validation labels come from two blind labellers, with agreement reported (not applicable here: no
>   labelling).
>
> Report any gate that is missing or hollow as a finding.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence, the fix). Put supporting scripts in review/reviewer_checks/.
