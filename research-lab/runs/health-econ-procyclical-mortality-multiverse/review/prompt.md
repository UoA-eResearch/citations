You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/health-econ-procyclical-mortality-multiverse/ (read-only except your output
in review/).

**The question.** Is US state mortality procyclical (Ruhm 2000) across a preregistered specification multiverse,
1976–2023? Are post-2010 drug-poisoning deaths countercyclical?

**Reported:**
- **H1 Inconclusive:** 47.4% of 2,304 total-mortality specifications are negative and significant (WCR), against
  the bands <0.40 / >0.60. The joint test puts the null median at 1.8%. The window and the measure drive the answer.
- **H2 Refuted:** 1.6% of 576 post-2010 drug specifications are positive and significant.

**What to read:** plan.md, deviations.md (D1 data construction before estimation; D2 the plan's arithmetic in the
specification count), report.md, code/ (build.py, multiverse.py, figures.py) and results/tables/ (primary.json,
specs_*.csv, splice_validation.json, synthetic_test.json). The data are in data/interim/panel.parquet and data/raw/.

**Git.** Read-only git is fine. Verify that plan.md preceded the panel, and D1 the estimation.

**Environment.** Python is venv/bin/python, with -I; it has pyfixest 0.60.0. Do NOT pip install. Set
OMP_NUM_THREADS=4 and keep CPU moderate. Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **Data construction (build.py).**
   - NBER state codes (NCHS alphabetical vs postal after 2003), resident-status exclusion, and the age recode.
   - The SEER parse (20 age groups) and the age-adjustment formula.
   - The weekly apportionment and calibration.
   - D1: 2023 from the quarterly rate × SEER population, and the VSRR calibration.
   - Is the splice a hidden driver? For example, a level shift in 2018 or 2023 correlated with unemployment. Compare
     windows ending 2017 vs 2019 vs 2023.
2. **The estimator (multiverse.py).**
   - Design matrices for each estimator, trend and lag combination: FD trend mapping, the lag reparametrisation,
     division × year effects, and weights in FD.
   - The closed-form WCR derivation and the CR1 small-sample factor.
   - Spot-check several specifications against pyfixest, or a brute-force bootstrap with fewer draws.
3. **Multiverse definition.**
   - Is any option indefensible, or does it mechanically drive the shares? Examples: quadratic trends in a 12-year
     window; level crude rates with population weights; employment/population over population aged 15+.
   - Is the equal-weight share a fair summary for the verdict?
4. **The joint test.** Shared draws, null construction from restricted residuals, and the CR1 critical value. Is
   p < 0.002 correctly reported, given 500 draws?
5. **H2.**
   - Is "Refuted" fair, given drug deaths' enormous common trend absorbed by year effects?
   - Does calibrating VSRR, or zero-count handling, matter?
   - Is the 1999–2010 contrast labelled correctly?
6. **Report.** Check every number against the tables. Is "the window and the measure decide it" supported by the
   decomposition, and are the plain-terms section, title and mechanism sentences fair?

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
