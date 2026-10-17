You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag/ (read-only except your output in review/).

The question: how long do new active substances (first FDA/EMA approval 2010-2024) take to reach New Zealand funding,
and which stage takes the time? There are four dates per substance:
- T0, first FDA/EMA approval;
- T1, Medsafe application;
- T2, Medsafe consent;
- T3, PHARMAC first funded listing.

Plus Australian comparators: PBS listing (Medicine Status Website, 2019+) and TGA registration. Also PHARMAC
application dates from the user-suggested UoA-eResearch/pharmac repository.

**What to read:**

- plan.md (preregistration, commit 8d0bc67);
- deviations.md (D1-D7). Note especially:
  - D3: new sources added after the preregistration;
  - D4: the XML archive gap;
  - D5-D6: cohort cleaning, duplicate merging, T0 overrides and alias / first-word matching, all made after the
    first validation;
  - D7: re-validation;
- report.md and report.html (pre-review draft, commit c0386fc);
- code/: cohort.py, names.py, medsafe.py, medsafe_parse.py, fetch_xml.py, pharmac.py, su_text.py, su_listings.py,
  msw.py, link.py, crosscheck_medsafe.py, validate.py, analysis.py, forecast.py, score_forecast.py, supplementary.py,
  figures.py;
- results/tables/:
  - primary.json, stage_table.csv, supplementary.json, linked.csv;
  - link_validation*.csv, medsafe_crosscheck.json, forecast_training.json;
- results/forecast_2026.csv and its sha256;
- data/ (large; on HDD via symlink):
  - cohort.csv, linked.csv, all_first_approvals.csv;
  - medsafe_products.csv, medsafe_applications.csv, pharmac_listings.csv, su_listings.csv, msw.csv;
  - raw/ (fda, ema, medsafe html, pharmac xml and su pdfs, pbs msw, uoa_pharmac);
  - validation/ (the evidence files the agent adjudicated, and the keys).

**Git.** Read-only git in /mnt/citations is fine. Check from commits and timestamps:
- that the validations were adjudicated before analysis.py ran;
- that the forecast file was committed (and pushed, 4577be4) before anything later.

**Environment:** venv/bin/python in the run directory (pandas, numpy, scipy, lifelines, sklearn, pymupdf, rapidfuzz,
playwright). Do NOT pip install into it, and do not run medsafe.py (the crawl is done). Make your own venv under
review/reviewer_checks/ if needed; caches go under review/reviewer_checks/cache.

Check at least:

1. **Cohort validity.**
   - Re-check a random sample of cohort substances against FDA/EMA: is each a new active substance first approved
     2010-2024? Is T0 right?
   - Probe the known weak spots: EMA-first substances with no NAS flag, FDA biologic proper names, re-approved
     products, salt/ester variants, combination strings.
   - Estimate the residual error rate, and whether it biases the lags.
2. **Post-validation changes (D5-D6).** The plan allowed one revision if precision < 0.90; precision passed, yet D6
   changed the cohort and the matching. Judge whether this is a justified correction or analyst degrees of freedom.
   Does the fresh 100-sample re-validation (D7) adequately cover the changes? Are the D6 merges right?
3. **Linking.**
   - Independently re-adjudicate at least 40 substances from the two validation samples, plus 30 new ones (seed of
     your choice), for T1, T2 and T3. Focus on present dates and on near misses.
   - Is "correctly absent" verified adequately?
   - Check the provisional-consent issue (T2 may be the later full-consent date): how many, and how much does it move
     H1a?
4. **PHARMAC T3.**
   - Is first appearance in the monthly XML (community Section B or HML) a valid "first funded listing"? Consider HML
     entries that appear because the HML archive starts in Oct 2013, name changes, and new formulations.
   - Is the Schedule Update gap fill (su_listings.py) right? Check several gap-window listings by hand.
5. **H1a/H1b.** Recompute them. Is the aggregate share the right statistic? How sensitive is it to:
   - excluding funded-before-consent substances;
   - the 13 substances outside the T0 <= T2 <= T3 ordering;
   - provisional consent?

   Is "regulatory stage = T0->T2 including the sponsor delay" faithful to the lead, and is the report's framing (40%
   mostly sponsor delay) supported by the stage table (n = 49)?
6. **H3.**
   - Recompute the denominators. Is the plan's verdict rule applied correctly?
   - Is the report's claim that "7.7 years fits a censoring-aware measure" sound? The Shawview figure's actual
     definition matters (Medsafe approval to a PHARMAC *decision*, possibly an average over decided applications). Try
     to find the original definition.
   - Check the application-based versions (D3) and the claims about 1,050 days and 7-10 years.
7. **H2 and TGA.** Is "not testable" correctly applied? Is the TGA comparison valid, given that the ARTG lists current
   entries and is matched on product-name text? Spot-check 10 T_TGA dates.
8. **Forecast (H4).** Is the model frozen and reproducible? Any leakage (features using post-origin information)? Is
   the scoring script correct?
9. **Numbers.** Does every number in report.md and the figure captions match the results files?
10. **Plain-language summary and framing.** Accurate and not overstated? Especially:
    - "the regulator's own review: about 14%";
    - "7.7 years is a reasonable summary";
    - "Its regulator approved the same medicines a median of about 14 months earlier";
    - the care note.

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of recomputed numbers;
- your re-adjudication table, kept under review/reviewer_checks/.
