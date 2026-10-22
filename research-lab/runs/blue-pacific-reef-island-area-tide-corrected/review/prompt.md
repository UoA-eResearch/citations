You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/blue-pacific-reef-island-area-tide-corrected/ (read-only except your output
in review/).

**The question.** At the eight Pacific atolls with an on-atoll UHSLC tide gauge, has reef-islet loss accelerated
since 2016 once every image is corrected for the tide (H1)? And how much does a missing tide correction bias
decadal rates (H2)? Islet areas come from MNDWI with an Otsu threshold, in Sentinel-2 L2A (2016–2026) and Landsat
Collection 1 Level-1 (1999–2015). Each islet is regressed on gauge water level at image time, and rates are Theil–Sen
slopes as % of OSM area per year.

**Reported:**
- **H2: Supported.** Mean |uncorrected − corrected| = 2.08%/yr (1.57–2.65) over 150 islets. Post hoc: the
  permuted-level noise floor is 0.29, and r = 0.97 with tide slope × overpass water-level drift.
- **H1: not testable.** The sensor-step guard fails: Landsat minus Sentinel-2 at 30 m is +1.24%/yr (0.46–2.07) on 13
  islets. Without the guard, D = +0.15 (−0.52 to +0.86), Inconclusive.
- **Deviations D1–D6.** D5 (the land screen, revised once) was made before any rate. D6 (the guard's minimum span)
  was made AFTER the first rates run.

**What to read:**
- plan.md, deviations.md, report.md;
- code/:
  - measure.py (areas, cloud rule, offsets);
  - rates.py (land screen, gross filter, tide regression, rates, guard, H1/H2);
  - h2_diag.py, dep_audit.py, dep_compare.py, figures.py, scenes.py, gcp_scenes.py, tides.py, inventory.py;
- results/tables/: h1_h2.json, h1_h2_run1_before_D6.json, islet_rates.csv, land_screen.csv, h2_diagnostics*.json/csv,
  dep_compare.json;
- results/figures/;
- data/areas/*.parquet (per islet and image), data/tides/*.parquet, data/inventory.csv.

**Git.** Read-only git is fine. Check that:
- plan.md preceded any area;
- D1–D5 preceded the first rates output;
- D6 is honestly described: the first-run output is kept, and the verdict cannot have been chosen by it.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. There is no matplotlib in that venv; use
../auckland-nz-2023-storms-estuary-mud-natural-experiment/venv/bin/python if you need it. Everything is CPU-only.
Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **The tide correction.** Is the linear area-on-level regression per islet and epoch sound? It uses levels from
   gauge hourly data within 2 h, relative to the 1999–2026 mean. Do non-linear responses, reef-flat exposure, or
   islets with near-zero tide slope (Tarawa) distort it?
2. **H2.**
   - Is the mean ABSOLUTE difference a fair statistic, given that noise inflates it?
   - Is the permutation floor the right null? It permutes levels within islet, keeping the fitted slope's noise.
   - Is the "drift in sampled water level" mechanism real? Check the per-atoll level trends at image times against
     the gauge's own trend over 2016–2026.
3. **The guard and D6.**
   - Is 4.5 years a reasonable, non-opportunistic span?
   - Is the guard itself well built (Landsat 8 C1 against Sentinel-2 at 30 m by 3×3 block means, Otsu at 30 m)?
   - Could the +1.24%/yr be an artefact of different scene sets or cloud rules rather than the sensors?
4. **The land screen (D5).**
   - Is "MNDWI < 0 over ≥10% of the OSM area in ≥50% of clear S2 scenes" outcome-neutral? Spot-check several removed
     and kept features at Penrhyn and elsewhere, using imagery or the per-scene table.
   - Is the possible-loss rule adequate?
5. **Measurement:**
   - the cloud rule (D2);
   - the Sentinel-2 offset rule (D4);
   - Landsat TOA conversion and the BQA bits;
   - the connected-component area;
   - the gross-failure rule (5 MAD on log area).
   Check whether any of these drives the rates.
6. **Coverage.** Kapingamarangi and Kanton have no Sentinel-2 imagery before 2022 in Earth Search. Is that true, or
   a search bug in scenes.py? Kiritimati has only 2 islets. Report what this does to generality.
7. **The report.** Check every number against the tables, the plain-terms section, the DEP comparison, and the care
   note. Results must be by atoll and pooled, with no islet-level habitability framing.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
