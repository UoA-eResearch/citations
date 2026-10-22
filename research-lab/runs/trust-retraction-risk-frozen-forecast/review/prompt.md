You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast/ (read-only except your output in
review/).

**The question.** Can retraction be forecast from information available at publication, in a true cohort of
biomedical articles at the real base rate? The design fits on 2015–2019 articles with retractions known by
2020-12-31, tests on 2021–2022 articles against the October 2026 registry, and seals a forecast of 2025–2026 articles
to be scored on 2028-12-31.

**Reported:**
- **H1** (full model E@1% ≥ 5): **Inconclusive**, 3.7× (1.4–13.3). Without Hindawi it is 5.1× (1.5–19.8).
- **H2** (model without venue features, E@1% ≥ 3): **Supported**, 11.4× (6.0–14.1); 10.6× on complete-metadata
  articles.
- **H3:** sealed; only hashes are committed.
- **Bias audit:** China-based first authors are 12% of the cohort, 67% of retractions, and 51–54% of the top 1%.
- **Proposed tag:** Inconclusive on H1, with H2 Supported.

**What to read:**
- plan.md, deviations.md (D1–D2), report.md;
- code/: labels.py, pass1.py, reduce.py, pass2.py, features.py, model.py, forecast.py, posthoc_complete.py,
  figures.py;
- results/tables/ (labels_log, reduce_log, model_hashes, h1_h2, posthoc_complete_metadata, forecast_seal).

**Data** (large; read selectively):
- data/lookup/ (memory-mappable .npy arrays over 476M works, plus rates.parquet);
- data/features/*.parquet (16.1M cohort articles);
- data/models/*.pkl;
- the registry in /mnt/data/retraction-markers/raw/;
- the snapshot in /mnt/data/ubuntu/impact-snapshot/works.

Never publish or quote per-paper scores. data/forecast/ is sealed: you may verify its hash, but do not open the score
file.

**Git.** Read-only git is fine. Check that:
- plan.md preceded the cohort build;
- model_hashes.json (660d682) preceded any test scoring, and the frozen models still match it;
- D1 preceded fitting;
- D2 is honestly labelled post hoc.

**Environment.** Python: /mnt/citations/research-lab/runs/trust-retraction-risk-frozen-forecast/venv/bin/python
(pandas, numpy, pyarrow, scikit-learn), with -I. Do NOT pip install. Memory is about 90 GB shared with other jobs:
load features by year, not all at once. Put scripts and outputs under review/reviewer_checks/.

Check at least:

1. **Leakage.** This is the main risk. Is every feature computed only from information before the publication year?
   Check:
   - the as-of rate windows in reduce.py;
   - the author retraction counts (features.py: `ar_key`, retraction year ≤ Y−1);
   - the reference retraction share;
   - the newcomer share. Author first years come from the whole snapshot: can a later work lower an author's first
     year below Y?

   Could the 2026 snapshot's metadata encode retraction after the fact? Possibilities include references or
   authorships altered after retraction, or retracted works re-typed or dropped. Compare a sample of retracted against
   matched non-retracted test articles.
2. **Labels.** Check the DOI matching, the reinstatement removal, Crossref self-update dating, and the training
   cutoff applied as retraction year ≤ 2020. Are any retraction notices themselves in the cohort as "articles"?
3. **Evaluation.** Recompute E@1% for the full and no-venue models. Is the Poisson cluster bootstrap with a fixed
   top-k set reasonable (D1)? How would intervals change under a plain publisher resample? Is the leave-one-publisher-
   out refit done as the plan says?
4. **H2's meaning.** Does the no-venue model beat the full model because of the early stop at 10 iterations, or
   because of venue history misleading in a Hindawi-dominated period? Is "paper triage, not only publisher triage"
   justified, when author prior retractions and institution rates may themselves proxy for publishers or paper mills?
5. **The bias audit and the report's framing.** Is the country concentration fairly described, and are the ethics
   statements adequate? Is anything per-paper exposed anywhere in results/?
6. **The sealed forecast.** Verify the hashes against data/forecast/ without opening the score file. Is the H3 rule
   well specified for 2028, including which registry, which cohort and how articles not yet indexed are handled?
7. **The report.** Check every number against the tables, the plain-terms section, and the comparison with
   "Born Flawed?" (PDF at data/raw/born_flawed_rs-10177352v1.pdf).

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
