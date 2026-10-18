You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/ancestral-pacific-rainfall-gauge-circularity/ (read-only except your output in
review/).

**The question.** Over Pacific Island countries, how much of CHIRPS v2.0's advantage over its satellite-only twin
CHIRP survives at GHCN-Daily gauges that CHIRPS did not ingest, compared with gauges it did?
- **Independent:** no input station within 100 km that month, from the CHIRPS monthly stations-used lists.
- **Supported:** an input station within 25 km.

**Hypotheses.**
- **H1:** gain ratio Ḡ_ind/Ḡ_sup < 0.5, with a station-block bootstrap.
- **H2:** ΔKGE at independent gauges < 0.
- **Secondary pair:** PERSIANN-CDR vs PERSIANN, with a GPCC numgauge label.

**What to read:**
- plan.md, and deviations.md (D1 and its addendum);
- report.md and report.html (the pre-review draft);
- code/: gauges.py, labels.py, extract_pentads.py, check_chirp_reader.py, fetch_persiann.py, extract_persiann.py,
  analysis.py, figures.py;
- results/tables/: primary.json, station_skill.csv, station_skill_secondary.csv, benchmark_stations.csv;
- results/figures/;
- data/: the daily gauge data, labels.csv, labels_gpcc.csv, extract/ (chirp*.csv, chirps*.csv, persiann_daily.csv),
  and raw/ (ghcn, gpcc, the chirps_used lists).

**Git.** Read-only git is fine. Check that code came before the outputs it produced, and that D1 came before any skill
was computed. Note the two post-hoc analysis.py fixes: the value dtype (before any output) and the masked-station
count (after).

**Environment.**
- venv/bin/python in the run directory. Do NOT pip install.
- Scripts and outputs go under review/reviewer_checks/, and caches under review/reviewer_checks/cache.
- Use at most 8 cores.
- Do NOT fetch from data.chc.ucsb.edu: it blocks parallel use. If you must re-read a CHIRP/CHIRPS pixel, use at most a
  handful of single requests, with pauses.
- Do not use localhost:8000.

Check at least:
1. **Gauges and timing.**
   - Gauge QC and pentad construction: the CHIRPS pentad calendar, complete pentads only, and the identical-run filter.
   - The day-shift rule (chosen against CHIRP only) and the 67/53/2 split.
2. **The labels.**
   - Parsing of the stations-used lists, the distance computation, the month assignment of pentads, and the 25/100 km
     strata.
   - The GPCC label for the secondary pair.
3. **The extraction.**
   - Pixel indexing for both products: cell centre vs edge, and the 0.05° grid origin.
   - Error handling, the masked station, and completeness (3,240 pentads each).
   - Spot-check a few values against the reader check.
4. **Skill and decisions.**
   - The skill metrics (RMSE, KGE components), the 30-pentad stratum rule, the 100-pentad inclusion and the station
     means.
   - The bootstrap and the H1/H2 decision rules.
   - Recompute the primary numbers independently.
5. **Sensitivity.** The sensitivity analyses and the secondary pair, as reported.
6. **Interpretation.** Is the 10× difference in gain an artefact? Consider:
   - station selection: the supported and independent strata are partly different stations, so compare within-station
     where a station has both strata;
   - rainfall regime;
   - the monthly label's resolution.
7. **The report.** Every number against the tables, overstated claims, and "In plain terms".

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in review/reviewer_checks/.
