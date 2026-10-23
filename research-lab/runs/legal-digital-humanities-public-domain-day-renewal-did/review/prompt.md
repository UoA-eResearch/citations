You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/legal-digital-humanities-public-domain-day-renewal-did/ (read-only except your
output in review/).

**The question.** When renewed 1923–1929 US books entered the public domain (2019–2025), did new Open Library editions
rise relative to same-vintage never-renewed books? The design is a PPML Sun–Abraham event study, with H1 RR ≥ 1.5.

**Reported:** Inconclusive.
- **The preregistered estimator** gave RR 0.33, which is degenerate: perfectly separated cells, mostly in 2024–2025.
- **D1, a post-result separation fix,** gives RR 1.86 (1.01–3.43), which the rule calls Supported. It is not
  robust:
  - no print-on-demand: RR 794, with a failing pre-trend;
  - lag filter: RR 1.15, with a failing pre-trend;
  - placebo: 1.17;
  - Sun–Abraham OLS: +0.004.
- **Gutenberg secondary:** 1.83% of renewed works were released within 0–2 years of expiry, against 0.25%.
- **Linkage:** precision 0.81, recall 0.38 (renewed 0.29, never renewed 0.50).

**What to read:** plan.md, deviations.md (D1, logged after the first result, and the Gutenberg data fix), report.md,
code/ (registrations.py, link.py, validate_links.py, did.py, secondary.py, figures.py), results/tables/ and
results/figures/. Data are in data/ (registrations.parquet, links.parquet, editions.parquet, candidates.parquet,
validation/{sample.jsonl,labels.json,key.json}, raw/).

**Git.** Read-only git is fine. Verify that plan.md preceded the linkage and editions, and look at exactly when D1 and
the did.py separation change were committed relative to the first results.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. It is CPU-only. Put scripts and outputs under
review/reviewer_checks/.

Check at least:

1. **Renewal matching (registrations.py).** Number match, date window and title rule. Are renewed shares per year
   plausible against the plan's pre-counts? False positives or negatives?
2. **Linkage (link.py).**
   - Blocking, title ≥ 90 and surname, the date check, and the uniqueness drop (30,965 dropped as ambiguous).
   - Does the drop select against popular renewed books?
   - Does linking only one of several duplicate Open Library works split the editions?
   - Check the validation scoring (validate_links.py score) and the labels' sanity on a few items.
3. **Editions (link.py editions).** The regex pre-filter cannot drop true matches, can it? The publish-year parse, and
   the 2008–2025 window. Are 2023–2025 so under-ingested that post-periods for late cohorts are meaningless?
4. **The DiD (did.py).**
   - Cohort definition and controls (renewed 1930 works as not-yet-treated).
   - Dummies and the binning at −8 and +6.
   - Is the D1 separation rule implemented correctly, and is it the right fix, or does it bias towards H1 by
     dropping only zero cells?
   - The aggregation weights, the delta-method CI and the pre-trend Wald test.
   - Why does no print-on-demand explode? Is there remaining separation or a bug?
   - Is the verdict "Inconclusive" (rather than "Supported by rule") the honest summary?
5. **Secondaries (secondary.py).**
   - The Gutenberg match (exact normalised title plus surname) and the same-window comparison.
   - The HathiTrust match.
   - RR by cohort.
   - The OLS variants: the plan says Sun–Abraham OLS; did.py's 'ols' is TWFE.
6. **Report.** Check every number against the tables, and that the plain-terms section and title are fair.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
