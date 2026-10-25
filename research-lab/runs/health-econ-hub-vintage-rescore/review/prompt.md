You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/health-econ-hub-vintage-rescore/ (read-only except your output in review/).

**The question.** Does scoring FluSight forecasts (2022–23 to 2024–25) against first-reported instead of finalised
hospital admissions reverse at least 20% of pairwise model orderings (H1), and change the best non-ensemble model
(H2)?

**Reported:**
- **H1 Refuted:** 6.2% of pairs reverse (4.9–7.4); by season 0.7%, 3.0% and 10.6%.
- **H2 Supported:** the leader changes in 2024–25 at h1 and h2, in 61% and 53% of bootstrap resamples.

**What to read:** plan.md, deviations.md (D1), report.md, code/ (build.py, score.py, figures.py) and results/tables/
(primary.json, relative_wis.csv). The data are in data/interim/ (truth.parquet, forecasts.parquet) and data/raw/
(the two hub clones with full git history).

**Git.** Read-only git is fine, including in the hub clones. Verify that the plan preceded scoring.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. Keep CPU moderate. Put scripts under
review/reviewer_checks/.

Check at least:

1. **Truth vintages.**
   - Is "first report" right? Earliest commit containing the location-week: are early partial values, or rows later
     deleted, mishandled?
   - Location code normalisation (the US and zero-padding).
   - The old hub's daily commits against the new hub's weekly ones: is first report comparable across seasons?
   - The 2022–23 "finalised" value (the last version in an archived repo): is it truly final?
2. **Forecast loading.**
   - Season assignment, horizons (old 1–4 against new 0–3), quantile filtering, and dropped files.
   - Are all models and reference dates included? Compare with the hubs' own counts.
   - Duplicate submissions.
3. **Scoring.**
   - WIS (the interval form), and quantile sorting.
   - Merging forecasts to truth by target_end_date.
   - Pairwise common sets, the MIN_PAIR threshold, ties, and the relative WIS (geometric mean over the selected
     set).
   - Exclusion by name: FluSight-lop_norm and other hub ensembles are not excluded. Does that matter for H2?
4. **Bootstrap and H2.** Date resampling by weights, and the 0.5 bootstrap rule. Is "Supported" fair when one change
   is between two variants of the same team's model, and the other is at 53%?
5. **Report.** Check every number against the tables, and that the plain-terms section and title are fair.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7; this study predates the gates, so G5 and G6 were run as a pre-review gate).**
Verify:
- **G5:** `review/overclaim_check.md` passes and is honest.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check . --show`.
- **G1:** could the first-report reconstruction leak final values (truth-file commits made after the forecast
  deadline but before the first report)?
- **G2:** forecasts dropped for missing first reports or unparseable quantiles — counted?

Report any gate that is missing or hollow as a finding.
