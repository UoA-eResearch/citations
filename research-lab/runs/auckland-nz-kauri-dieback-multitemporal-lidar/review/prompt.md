You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/auckland-nz-kauri-dieback-multitemporal-lidar/ (read-only except your output
in review/).

**The question.** Do kauri graded symptomatic in Auckland Council's 2014–15 Waitākere track survey (ObsKauri) lose more
LiDAR canopy between 2016–18 and 2024 than trees graded healthy? The features are the change in P95, P50 and >15 m
cover of the CHM (DSM − DEM, 1 m) within 15 m, with a slip mask. The models are logistic, under spatially blocked CV.

**Reported:**
- H1 Refuted: change AUC 0.51 (0.44–0.56).
- H2 Inconclusive: gain +0.048 (−0.021 to +0.092).
- Secondary, 2021 labels: AUC 0.55 (0.51–0.59), gain +0.021 (0.002–0.041).
- Canopy rose about 1.25 m at random forest points.

**What to read:** plan.md, deviations.md, report.md, code/ (fetch_obskauri.py, features.py, model.py, figures.py),
results/tables/ (trees.csv, primary.json), results/figures/, and data/ (mosaic_*.tif, trees_xy.parquet,
raw/obskauri.parquet, raw/osm_tracks.json).

**Git.** Read-only git is fine. Verify that plan.md preceded the mosaics, and that features.py and model.py were
committed before trees.csv and primary.json existed.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. It is CPU-only, and the GPU is busy with
another study. Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **Mosaics.**
   - Are DSM and DEM aligned per epoch, and in the same vertical datum across epochs?
   - Is the +1.25 m stable-area rise a datum or processing artefact that biases the change features?
   - Does a different stable-area definition change it?
2. **Feature extraction (circle_stats).**
   - Row/column indexing and transforms; clipping CHM at 0.
   - The ≥50% valid rule, and the slip mask (|ΔDEM| > 1 m).
   - Are trees near mosaic edges or water handled?
3. **Labels.** The 2 m duplicate merge (12,512 → 9,069): too aggressive, or not enough? Are there status conflicts at
   the same location?
4. **CV and bootstrap.**
   - Blocks and folds by block; repeats averaged.
   - Is AUC on averaged out-of-fold predictions valid? Is the paired gain bootstrap right?
   - Could a coding error explain chance-level AUC? Try a positive control: a feature known to differ, or a synthetic
     label.
5. **Interpretation.**
   - Is "Refuted" fair, given position error and the 1–4 year lag that the plan stated in advance?
   - Is the 2021 "faint signal" overstated, given 2021 trees deep in the forest and a static AUC of 0.59?
   - Check the report's numbers, the plain-terms section and the care note (no coordinates published).

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
