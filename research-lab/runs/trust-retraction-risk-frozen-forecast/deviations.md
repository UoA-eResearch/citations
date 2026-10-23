# Deviations

## D1 — 2026-10-22 20:41 NZDT — the forward refit's training years, and implementation notes (before any model is fitted)

1. **H3's refit window.** The plan refits the forward model on articles from 2018–2022. The cohort extraction
   (`pass2.py`) took only the plan's study years (2015–2019, 2021–2022, 2025–2026), so 2020 articles were never
   extracted, and the as-of rate tables were computed only for those years. The forward model is therefore fitted on
   2018–2019 and 2021–2022 articles, with labels dated on or before 2024-12-31.
2. **Year granularity.** The snapshot columns give a publication *year*, not a date. "Before 1 January of the
   publication year" is implemented as retraction year ≤ publication year − 1, and training labels as retraction year
   ≤ 2020. A retraction dated during 2020 of a 2019 article counts as a training positive; one dated in 2021 does not.
3. **Labels.** The test and forward labels come from matching each article's DOI against the retraction registry in
   pass 1. The same DOI match gives every work in the snapshot its retraction year, so the reference-list and author
   features use the same labels.
4. **Bootstrap.** The publisher-clustered bootstrap uses Poisson(1) weights per cluster (B = 1,000), a standard
   approximation to resampling clusters. It is needed because each article without a host organisation is its own
   cluster, and the top-k set is fixed from the full-sample ranking.

## D2 — 2026-10-22 21:12 NZDT — post-hoc checks after the test results were read

1. **Metadata completeness** (`code/posthoc_complete.py`).
   - *Why:* retracted test articles are far less often missing references, authors or a country than other articles
     (2.3% have no references, against 21%), so the skill might only reflect well-deposited records.
   - *What:* every frozen model is re-evaluated on the 2,820,712 test articles (71%) with at least one reference, one
     author and a first-author country.
   - *Status:* exploratory; no verdict changes.
2. **Country audit for both models.** The plan's bias audit covered the primary model. The same country shares
   (cohort, top 1% and test retractions) are reported for the author-and-reference model (H2) as well.
3. **Publisher names** for the leave-one-publisher-out refits come from OpenAlex: Hindawi, Elsevier and Springer.

## D3 — 2026-10-23 14:17 NZDT — changes after the independent review (review/review.md, "fix first"); frozen models untouched

The preregistered verdicts are computed from the frozen models and stand: H1 Inconclusive and H2 Supported. What
changes is the explanation, plus a set of labelled post-hoc checks. Re-scoring of frozen models is in
`code/posthoc_review.py`, written to `results/tables/posthoc_review.json`. Refits and the buffer test are the
review's (`review/reviewer_checks/c2–c6`) and are cited as such.

1. **The primary model's fit** (finding 1). The frozen full model stopped after 10 trees, with validation and training
   log-loss worse than the constant base-rate predictor. The scikit-learn defaults (n_iter_no_change 10, no L2
   regularisation, min_samples_leaf counted in samples) at a 20:1 weight ratio let near-pure positive leaves saturate.
   H1's 3.7× therefore measures a failed fit.
   - **The review's refits, not frozen:** other seeds give 2.9–6.9×; fixed 100 iterations give 9.7× (4.6–12.3). The
     frozen venue-only model reaches 8.0×.
   - **The report** no longer says venue signals "do not hold up".
2. **The PubMed Central host** (finding 2). 59% of the full model's top 1% is PMC-hosted (host I1299303238, a
   repository, not a venue). Its host_rate shifted about 30-fold between the training and test windows. The host
   audit with names, and E@1% without that host, are reported.
3. **Crossref self-update dates** (finding 3). For Crossref-only self-updates, the retraction "date" is usually the
   paper's own deposit year. 256 of the 2,813 training positives carry such dates. The review's bound: a one-year
   as-of buffer moves H2 from 11.36× to 11.21×. Reported as a limit. Future forecasts treat these dates as unknown.
4. **H2's robustness** (finding 4). The claim that the result "survives removing the dominant publisher" had not been
   tested. Now:
   - H2 without Hindawi is re-scored here;
   - the review's leave-Hindawi-out refit gives 6.7× (5.1–8.4), and seeds 1–3 give 8.1–9.9×;
   - the institution component is reported.
5. **Notices in the cohort and the OpenAlex check** (finding 5). 2,252 retraction-notice DOIs (956 in the test window)
   sit in the cohort, and the plan's OpenAlex is_retracted agreement check was missing. Both are reported from the
   review's c4/c5. Notices are 0.02% of the test set.
6. **The H3 addendum** (finding 6), committed now, long before any 2028 label exists:
   - **Decision rule:** Supported if the lower bound of the publisher-clustered E@1% interval is at least 3, as for
     H2; Refuted if the upper bound is below 3.
   - **Registry:** Retraction Watch plus Crossref retraction assertions, fetched on or after 2028-12-31.
   - **Cohort:** the sealed works only, keyed by the committed SHA-256 of `data/forecast/forward_wid_doi.csv` (wid,
     doi).
   - **Excluded:** works already retracted at sealing, listed in `data/forecast/forward_retracted_at_seal_wids.csv`
     (SHA-256 committed).
   - The forward model shares the 10-iteration fit, and the addendum says so.
7. **Smaller items** (findings 7–10):
   - leave-one-publisher-out keeps the publisher's history in the feature tables;
   - the iid-article bootstrap is shown for contrast;
   - the metadata-completeness and newcomer-definition notes;
   - "top 20 fields" is 10 fields;
   - the publisher ids.
