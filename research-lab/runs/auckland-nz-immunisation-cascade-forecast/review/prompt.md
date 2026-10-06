You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/auckland-nz-immunisation-cascade-forecast/ (read-only except your output).
Read plan.md (preregistration, commit 691a47e), deviations.md (D1), report.md (draft), code/ (fetch.py, parse.py,
backtest.py, score.py, figures.py), results/ (tables, figures, forecasts_frozen.csv) and data/ (raw files with
data/raw/manifest.csv; data/coverage.parquet). Use the study's venv (./venv/bin/python) on cores 0-3 only (taskset -c
0-3); other cores run a separate job. You may run read-only git commands in /mnt/citations.

Check at least:
1. Parsing: are all quarterly files parsed correctly across the changing layouts (2009-2020 archive sheets, 2020-23
   long layouts with swapped/forward-filled columns, 2023-26 current files)? Spot-check cells against the raw files,
   the ethnicity harmonisation (NZE + Other -> European or Other), the Otago/Southland -> Southern merge, quarter-end
   assignment, and that suppressed cells are never back-calculated.
2. Was the preregistered model, baselines, metrics, DM test, block bootstrap and decision rule implemented exactly as
   plan.md specifies? Any look-ahead (data not published at the origin used in a forecast or in the interval
   calibration)? Recompute the H1 numbers.
3. Timing: plan and backtest code committed before the first run; was anything changed after seeing results other than
   D1? Is D1 justified and is H2 still scored on the preregistered interval? Are the frozen forecasts committed and
   hashed before any target release, and does score.py do what the plan says?
4. Interpretation: is the explanation of the post-2020 failure (schedule change, AIR migration, catch-up) supported or
   appropriately hedged? Are the frozen forecasts and the H2 cautions described accurately? Is the Te Mana Raraunga
   framing respected?
5. Does every number in report.md match the results files?
6. What would an epidemiologist or a forecasting expert object to (e.g. the measure's definition changes, cohort
   misalignment, the 8-month milestone, small-cell noise, interval construction)? Use web search if useful.

Write your review to review/review.md with a recommendation (publish / publish with edits / fix first), numbered issues
with locations and concrete fixes, and a table of recomputed numbers. Reply with the recommendation and the number of
issues.
