You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger/ (read-only except your output in
review/).

**The question.** How much New Zealand wind and solar output is curtailed, measured as bias-corrected dispatch-time
potential (the plant's own ForecastOfGenerationPotentialMegawatts in EMI offers) minus metered output (Generation_MD),
2020 to 2026, and why?

- **Reported:** the preregistered measurability gate fails (median plant floor 27% of mean potential vs 25%). H1
  Refuted by rule (2020 share 2.27%), H2 Supported by rule (72.7% non-price).
- **Post hoc (D2):** the rule flags about 5% of unconstrained half-hours by construction; that noise mass is about
  2.2% of available energy. Price-driven curtailment (node price at or below the plant's offer) rose from 0.01% to
  2.22% of available energy; of non-noise curtailment in 2025/26, 73% is price-driven, which the report says reverses
  H2's reading.

**What to read:** plan.md, deviations.md (D1, D2), report.md and report.html; code/ (fetch.py, build.py,
analysis.py, diagnostics.py, figures.py, weather.py); results/tables/; data/ (a symlink to /mnt/data/nz-curtailment,
with filtered offers, generation, prices and panel.parquet).

**Git.** Read-only git is fine. Check that plan.md (3bc4894) preceded every series, code preceded outputs, and what
D1 and D2 changed after which results.

**Environment.** Python: /mnt/citations/research-lab/runs/energy-outage-major-event-day-ratchet/venv/bin/python
(pandas, numpy, pyarrow), with -I. Do NOT pip install. Scripts and outputs under review/reviewer_checks/. You may
re-fetch a few public EMI files from https://emidatasets.blob.core.windows.net/publicdata/Datasets/Wholesale/
politely.

Check at least:

1. **Potential.** Is taking the potential from the highest-numbered latest submission right, given that older
   tranches keep stale potentials? Is the latest potential truly dispatch-time (submitted before the trading
   period)? Spot-check a few plant-days in the raw offers.
2. **Matching.** POC-level summation of offers and Generation_MD: are the matched plants right (output/potential
   ratios in build_log.json), are the two fuel codings read correctly, and is excluding Mahinerangi and Rotohiko
   right? Are any offered plants' outputs metered elsewhere?
3. **The measure.** Is the "noise mass" argument right: does the rule flag about 5% of unconstrained half-hours by
   construction, and is the 2020 baseline then an artefact? Is the gate computed as the plan says? Is it fair to
   report H1/H2 by rule while leading with the gate?
4. **The post hoc decomposition.** Is "price-driven" (price at or below the plant's max offer price) a sound
   definition when wind offers at $0.01? Does that class also absorb network-constrained curtailment, since a
   constrained node's price falls to the marginal offer? If so, is "reverses H2's reading" overstated?
5. **Bootstrap and windows.** Is the 7-day block bootstrap with re-calibration correct? Are the 12-month windows
   computed consistently (the first spans 18 months)?
6. **Projection.** Is the frozen 2026/27 projection computed by the stated rule, and is it scoreable?
7. **The report.** Every number against the tables; plain terms; whether the headline (a growing price-driven core
   reaching 2.2%) is supported, and whether claims about hydrology or spells go beyond the data.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered
findings (severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
