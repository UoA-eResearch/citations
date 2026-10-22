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
