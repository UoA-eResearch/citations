You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/blue-pacific-tuna-redistribution-detectability/ (read-only except your output in
review/).

The claim under review: Bell et al. (2021) project that climate change moves ~13% of tuna biomass out of ten Pacific SIDS'
EEZs by 2050. Is that redistribution detectable in 42 years of open WCPFC purse-seine data, and does SEAPODYM's historical
simulation reproduce what was observed?

**What to read:**

- plan.md (preregistration, commit 3cc5aff — committed before any observed series was computed);
- deviations.md (D1–D7). D1–D3 predate the plan; D4 was logged before primary.py ran; D5–D7 are post hoc;
- report.md and report.html (pre-review draft, commit 9f05cfc);
- code/: model_targets.py, indices.py, observed.py, analysis.py, test_analysis.py, primary.py, exploratory.py,
  footprint.py, figures.py;
- results/tables/ and results/figures/.

**Git.** Read-only git in /mnt/citations is fine. Check that each stage's code was committed before the outcomes it
produced — the commit sequence is 3cc5aff (plan) → db9d946 (D4) → b51f02b (primary results + exploratory code unrun) →
ddf284f (D6) → footprint code → 9f05cfc (draft).

**Environment:** venv/bin/python in the run directory (xarray, statsmodels, geopandas, numpy, pandas, scipy). Data under
data/raw/ (symlinked to /mnt/data). Do NOT pip install into that venv; if you need a package, make your own venv under
review/reviewer_checks/. No GPU needed. Do not start or stop any Docker container.

Check at least:

1. **Timing and disclosure.** Was every threshold fixed before the outcome it governs? τ was derived from model output
   before the plan, deliberately — is that legitimate, and is what the model showed (§4) fully disclosed? Are D5–D7
   honestly labelled, and does the report lean on post-hoc results harder than it should?
2. **The Bell reproduction.** Recompute the three-species biomass change from the SEAPODYM files. The report gets −14.2%
   against a published −13% and attributes the gap to the files, not its own method. Is the EEZ mask right (12 areas,
   Torres Strait excluded, antimeridian handling, fractional overlap)? Is the 2009–2018 baseline handled sensibly given
   the projections start in 2011?
3. **The SEAPODYM file anomalies (D2).** Verify independently: do the bigeye projection "Btot" files really hold total
   biomass under a mislabelled variable, and is the historical bigeye "Btot" really a different quantity? This will be
   reported to SPC; it must be right.
4. **The observed series.** Spot-check observed.py against the raw file: skipjack summed over the five school types, the
   coordinate conventions, the domain, the EEZ fraction on the 1° grid, the density share's MIN_DAYS rule. Recompute O1
   for at least three years by hand.
5. **The statistic and the verdict.** Recompute H1's trend and both intervals independently. Is the moving-block
   residual bootstrap appropriate for a 42-year series with lag-1 autocorrelation 0.56? The synthetic coverage was 0.89;
   is that disclosed adequately, and does it matter here given both intervals clear τ? Is a linear trend a fair summary
   of a series the report itself describes as U-shaped with a 2010 jump?
6. **H3.** Both predictors have negative out-of-sample R². Is "not supported" the right reading, or is the comparison
   meaningless with n_test = 11? Is the calibration of SEAPODYM (a linear map trained on 1980–1999) reasonable?
7. **Power — the report's central practical claim.** "Catch-share monitoring could not confirm a 2050 projection until
   decades after 2050." Check the injection-recovery procedure, the size calibration (critical value from injected-zero
   simulations), and the detection-year simulation (hinge from 2011, AR(1) noise from ENSO-adjusted residuals). Is
   excluding ENSO-explained variance from future noise right? Is the 2098 figure sensitive to the AR(1) assumption, the
   residual SD, or the hinge start? Would a fishery-independent index or a different estimator change the conclusion?
8. **The 2010 step and the "management, not fish" reading.** The report claims the share is moved by management and
   fleet expansion rather than fish. The per-EEZ prediction failed (D6). After that failure, is the report still
   claiming more than the evidence supports anywhere? Are there other explanations for the 2010 step (VDS maturation,
   ENSO phase — 2010–2011 was a strong La Niña, the 2015 El Niño, FAD-closure rules, reporting changes)?
9. **The fixed-footprint check (D6, D7) — attack it hardest.** The headline "the eastward move is the fishery, not the
   fish" rests on a centroid trend of +0.002 deg/yr on 86 cells spanning 141.5–159.5E over 31 covered years. A footprint
   only 18 degrees wide, 96.8% inside EEZs, in the western core, may be structurally unable to show an eastward shift
   even if one occurred — the fish could leave the core without the within-core centroid moving. Is "the fish have not
   moved east" supported, or only "density within the western core has not shifted"? The covered-years restriction (D7)
   was post hoc and prompted by a coverage figure — is it a legitimate refinement or a convenient one? Re-run with other
   footprint thresholds and coverage rules.
10. **Interpretation and scope.** Is "Supported" stated with the right caveats? Is "the projection is untested by the
    catch record" a fair summary? Does the report anywhere imply the projection is wrong? Does it correctly avoid
    treating the domain share as the 13% figure?
11. **Novelty and facts.** Web-search: detection or power tests of tuna redistribution projections; SEAPODYM validation
    of redistribution trends; the 2010 high-seas-pocket closure (CMM 2008-01 and the PNA Third Implementing Arrangement —
    check the date and which vessels it applied to); Dutta (2025). Are the cited claims accurate?
12. **Numbers.** Does every number in report.md, tiles.json and the figures match the results files?
13. **Plain-language summary.** Is "## In plain terms" accurate and not overstated? In particular: "the fish had not
    moved east at all" and "one time in six".

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of the numbers you recomputed.

Put any scripts in review/reviewer_checks/. Reply with the recommendation and the number of issues.
