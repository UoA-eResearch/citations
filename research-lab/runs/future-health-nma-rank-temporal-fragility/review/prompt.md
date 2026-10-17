You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/future-health-nma-rank-temporal-fragility/ (read-only except your output in
review/).

The question: are network meta-analysis (NMA) treatment rankings stable when the newest evidence arrives, and is the
stated probability of being best calibrated?
- **Design.** A temporal holdout across the verified networks of the open nmadb database (Petropoulou 2016).
- **Steps.** Withhold the newest ~10% of studies (whole publication years), fit a random-effects frequentist NMA
  (netmeta 3.6.1, DerSimonian–Laird), rank by P-score, add the studies back, refit, and compare the top-ranked
  treatment.
- **Hypotheses.**
  - H1: a flip in at least 30% of networks.
  - H2: P(best) overstates retention by at least 20 points.
  - H3: the top-two gap plus log studies explain Nagelkerke R² < 0.5.
- **Further analyses:** a random-holdout negative control, secondary holdouts, a common-effect model, resampling
  SUCRA, and a contrast-level (iv) sensitivity set.

**What to read:**
- plan.md (preregistration, commit 6152aa8);
- deviations.md (D1–D3). Note especially:
  - D1: years from study labels;
  - D2: the direction of benefit adjudicated per network, contrast-level networks moved out of the primary set, the
    natural-scale list;
  - D3: the multi-arm split fallback;
- report.md and report.html (pre-review draft, commit 9340e97);
- code/: fetch.py, standardise.py, direction.py, holdouts.py, nma.R, analysis.py, validate_parse.py,
  validate_counts.py, validate_published.py, figures.py;
- results/tables/:
  - primary.json, network_results.csv, direction.csv;
  - v1_parse_validation.csv, v2_counts.csv, v3_published.csv, nmadb_SHA256SUMS;
- data/:
  - raw/catalog.csv and raw/datasets/*.xlsx (the nmadb snapshot);
  - std/*.csv and *.trt.json (standardised), std_summary.csv;
  - jobs.json, holdouts.csv, fits.jsonl (42,435 fits), fits_full.jsonl;
  - validation/ (the V1 evidence, the V3 abstracts and sheet).

**Git.** Read-only git in /mnt/citations is fine. Check from commits and timestamps that the code was committed
before the outputs it produced, and that D1–D3 and the validations came before any holdout result (fits.jsonl).

**Environment.**
- Python: venv/bin/python in the run directory (pandas, numpy, scipy, statsmodels, openpyxl, matplotlib). Do NOT pip
  install into it.
- R: /mnt/research-lab-tools/r-nma/bin/Rscript has netmeta 3.6.1. Ignore the lme4/Matrix ABI warning.
- Your own files go under review/reviewer_checks/, with caches under review/reviewer_checks/cache. Use at most 8 cores
  for any R runs.

Check at least:

1. **Standardisation.**
   - Re-check a random sample of at least 20 included networks against their raw spreadsheets: studies, arms,
     treatments, years, values.
   - Probe the weak spots:
     - label years (D1), and whether combined labels (two studies in one label) take the right year;
     - year gaps;
     - inverse-variance scale handling (the NATURAL list) and seTE from CIs;
     - the wide-format network;
     - continuous outcomes with the y/sd/n layout.
2. **Direction of benefit (D2), the most consequential judgement in the study.**
   - Independently re-adjudicate at least 30 arm-level networks, including all where the catalogue and sheet labels
     disagree, and all 29 contrast-level calls.
   - A wrong direction turns the "top" treatment into the bottom one. How many calls do you dispute, and does
     correcting them move H1 or H2?
   - Is moving the contrast-level networks to a sensitivity set a justified response or an analyst degree of freedom?
3. **The holdout construction.**
   - Is the whole-year tranche correct (median 15% of studies)?
   - Are undated studies never withheld?
   - Is the pre-update network's largest-component rule applied correctly?
   - Are new entrants handled as preregistered?
   - Recompute the T10 tranche for 10 networks by hand.
4. **Fitting.** Re-fit 10 networks yourself (full and T10) with netmeta and compare the treatments, P-scores, top,
   P(best) and Kendall τ. Check:
   - that the P-score function matches netmeta;
   - the sign convention of TE in nma.R's pscore();
   - the use of TE.random[i, j] = θi − θj;
   - the rankogram's P(best) for the right treatment;
   - the restricted full-data P-scores (computed on the pre-update treatment set from the full fit's matrices).
5. **The verdicts.** Recompute H1 (Wilson CI), H2 (bootstrap) and H3 (Nagelkerke R² with bootstrap) from fits.jsonl,
   and check the decision rules against the plan. Is the H2 framing sound: "Refuted in the opposite direction", and the
   argument that understatement is partly by construction?
6. **The negative control.** Are the 200 random holdouts the same size as the primary tranche? Are they drawn only
   from dated studies, and analysed like the primary? Are the 887 failed random fits (2%) ignorable, or concentrated
   in some networks?
7. **The validations.** Is V1 (22 of 23 right) adequate? Is V3's coding (9 of 13 agree; control at the bottom in all 19
   checkable networks) right? Re-read at least 10 V3 abstracts.
8. **Numbers.** Does every number in report.md, report.html and the figure captions match the results files?
9. **The plain-language summary and framing.** Is anything overstated?
   - "a reasonable but fallible snapshot";
   - "the newest studies are not special";
   - "reading it as the chance this is still the top treatment next time is safe";
   - the comparison with Daly et al.

Write your review to review/review.md with:
- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of recomputed numbers;
- your re-adjudication tables, kept under review/reviewer_checks/.

Do not modify anything outside review/, and do not commit.
