You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/seismology-geophysics-quakescope-analyst-validation/ (read-only except your
output in review/). Read plan.md (preregistration, commit 5bb0f02), deviations.md (D1-D4), report.md (draft, commit
d497663), code/ (fetch.py, parse.py, covariates.py, match.py, analysis.py, checks.py, figures.py and the run_*.sh
scripts), tests/, results/tables/ (including results/tables/checks/) and results/figures/, and logs/. Use the study's
venv (./venv/bin/python). Set OMP_NUM_THREADS=2 when you run sklearn or statsmodels (the machine oversubscribes
threads otherwise). You may run read-only git commands in /mnt/citations, for example to confirm that the plan and the
code were committed before matching.

Data on disk: data/raw/western/picks/ holds the QuakeScope catalogue partitions (CC0); data/raw/phases/ holds the
SCEDC and NCEDC phase files; data/raw/catalogues/ the NCEDC catalogues; data/raw/availability/ and stations.parquet
QuakeScope's availability and station tables. The derived files are data/reference_picks.parquet,
data/matched.parquet and data/covariates.parquet. Everything is public.

Check at least:

1. **Timing and disclosure.** Were the hypotheses, thresholds, matching and analysis code fixed before any pick was
   matched (git history, logs)? D3 says the first analysis run crashed before any outcome was printed or saved. Check
   logs/analysis_run1_crashed.log. Do D1-D4 disclose everything done after the outcome? Is any post-hoc result
   presented as if confirmatory?
2. **Reference picks.** Spot-check parse.py against raw phase files:
   - SCEDC: reference time = origin + travel time; local events only.
   - NCEDC: Hypoinverse Y2000 archive format, implied decimals, absolute arrival times, status-F join.
   - Time zones, magnitudes, distances, weights, and de-duplication across channels.

   Pick about 10 matched and 10 unmatched reference picks and verify them by hand against the catalogue partitions.
   Are any misses artefacts, for example of station-code or location-code conventions, renamed stations or time
   offsets?
3. **Matching and denominator.** Is the greedy one-to-one matcher correct? Is the `loaded` availability join right? It
   is per station-day across location codes. Does excluding unread station-days bias recall or its spread?
4. **H1.** Recompute SD_p from the VB fit; the main fit takes about 15 minutes. Check the bootstrap: duplicate station
   labels, seeds, and percentiles from h1_bootstrap_draws.csv. Is the VB non-convergence explanation in the report
   right? Check the AGHQ maximum-likelihood implementation in checks.py (the mode finding, quadrature, normalisation)
   and its synthetic test. Is applying the H1 rule as "Supported" correct? Is the "narrowly" framing fair given that
   the 95% CI includes 0.10? How sensitive is SD_p to the reference event and to the logit-normal assumption, given the
   long low tail?
5. **H2.**
   - Recompute the CV R² and its bootstrap.
   - Check the covariates: band from denominator days, sampling rate, and the noise computation in covariates.py
     (response removal, the 09:00-10:00 UTC window, the 1-10 Hz RMS).
   - Check the categorical encoding in analysis.design. Is HistGradientBoosting given the right categorical mask?
   - Does the shrinkage of posterior-mean station effects affect R²? Is the reliability correction right?
   - Is "Refuted" the right reading?
6. **The exploratory false-pick proxy.** Both the preregistered version and the post-hoc 5-nearest-neighbour variant.
   - Check the code: searchsorted keys, units, the neighbour selection and month edges.
   - Check the validation (0.9% of referenced vs 62% of unreferenced picks flagged).
   - Is "59% of confident P picks are isolated and unreferenced" stated with enough caveats? Neighbours that lacked
     data on that day, events below M 1.5 or outside 100 km, and other networks' stations should all be considered.
     Would a seismologist accept the interpretation?
7. **Numbers.** Does every number in report.md, results/tables/tiles.json and the figures match the results files?
8. **Interpretation.**
   - Is "Verdict: Refuted" a fair one-word tag when the plan had no headline rule, H1 is narrowly Supported and H2 is
     Refuted?
   - Are the descriptive claims supported: EH stations, regional shares, "location predicts nothing out of cell", the
     sensitivity/false-pick trade-off?
   - What would a seismologist object to? For example: analyst picks seeded by automatic pickers, PhaseNet having been
     trained on NCEDC picks (the `original` weights), or station-specific travel-time corrections.
   - Use web search to check novelty (prior validations of QuakeScope or of PhaseNet production catalogues against
     analyst picks) and the facts stated about QuakeScope.

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of the numbers you recomputed.

Reply with the recommendation and the number of issues.
