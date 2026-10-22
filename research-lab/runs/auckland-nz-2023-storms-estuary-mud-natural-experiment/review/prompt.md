You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/auckland-nz-2023-storms-estuary-mud-natural-experiment/ (read-only except
your output in review/).

**The question.** Did Auckland estuary monitoring sites whose nearby land was most stripped by the January–February
2023 storms get muddier in the October–November 2023 survey? The design is a site and year fixed-effects DiD on LAWA
mud content, 2010–2024, over 56 Auckland Council sites. Exposure is the newly bare share of land draining to the coast
within 5 km of each site. Newly bare means Sentinel-2 NDVI at least 0.5 in November–December 2022 and at most 0.3 in
February–April 2023, routed on the LINZ LiDAR DEM.

**Reported:**
- **H1 (top minus bottom tercile, 2023, ≥4 pp): Inconclusive.** +1.93 pp (wild cluster bootstrap −2.33 to +5.67).
- **H2 (dose-response per IQR): Inconclusive.** −0.21 pp (−3.06 to +3.20). The CR2 interval is −0.57 to +0.15.
- **Exposure validity:** 63% of newly bare area is in patches over 5 ha (harvest). The slip-sized exposure (D3) gives
  the same answer.
- **Post hoc (added after H1/H2 were read):** a region-wide 2023 pulse of +4.26 pp in mud against site baselines
  (site bootstrap 2.26–6.30; earlier yearly means −1.27 to +1.68). Exploratory regional comparison in
  regional_2023.json.
- **Deviations:** D1 (DEM source and sea mask, with an addendum), D2 (priority-flood routing), D3 (slip exposure,
  after the exposure froze) and D4 (metals not estimable, after the run).

**What to read:**
- plan.md, deviations.md, report.md;
- code/: sites.py, dem.py, s2.py, seamask.py, route.py, bare.py, exposure.py, exposure_slips.py, analysis.py,
  analysis_slips.py, figures.py;
- results/tables/: sites.csv, exposure.csv, exposure_summary.json, exposure_slips*.json/csv, contrib_summary.csv,
  bare_log.json, seamask_log.json, primary.json, slips.json, event_study.csv;
- results/figures/;
- data/: dem20.tif, sea20.tif, bare20.tif, contrib.npz, raw/lawa_estuary_2025v2.xlsx.

**Git.** Read-only git is fine. Verify that:
- plan.md and sites.csv preceded any outcome read;
- exposure.csv (commit d2411cf) and D3 preceded primary.json;
- D1, its addendum and D2 preceded exposure.csv.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. It is CPU-only. The ASR study's GPU jobs
are running; do not touch them. Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **Inference.**
   - Is the wild cluster restricted bootstrap correct: Webb weights, null imposed, CR1 t statistic, CI by test
     inversion in `wild_ci`?
   - With 11–13 harbour clusters and two high-leverage sites, is the tenfold gap between the wild and CR2 intervals
     for H2 a bug or real?
   - Does the verdict depend on which interval is used?
2. **Fixed effects and sample.**
   - Is the panel right: one value per site and year, years 2010–2024, the year-only rows?
   - Does `design()` give a full-rank model?
   - Is H1 rightly restricted to top and bottom terciles, and are the terciles built without outcome information?
3. **Exposure.**
   - Spot-check the sea mask (harbours as sea; rivers?) and the priority-flood routing (does each site's contributing
     land make sense?).
   - Check the NDVI composite and its offset rule (s2.py: the 0.5th percentile of red DN below 900 means the offset
     is already removed).
   - Is "newly bare" dominated by harvest, as claimed? Does that make the study uninformative, or only weaker?
4. **The event study and placebos.** Is 2022's +1.45 a real pre-trend? Do the placebos use the same estimator?
5. **The post-hoc pulse.** Is it a storm signal or a sampling or laboratory change? Check site composition in 2023
   (56 sites against about 45 a year before) and whether the report attributes it too strongly.
6. **The report.** Check every number against the tables, the plain-terms section, the claim about what is "not ruled
   out", the macrofauna scale wording, and the care note.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
