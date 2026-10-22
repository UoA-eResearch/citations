# Plan: can retraction risk be forecast from what is known at publication, in a real cohort at its real base rate?

Lead: `trust-retraction-risk-frozen-forecast`. Written 2026-10-22, before any cohort was built or any feature computed.

**Examined beforehand (nothing computed):**
- The column list of the local OpenAlex works snapshot (22 September 2026; sparse copy at
  `/mnt/data/ubuntu/impact-snapshot/works`).
- The headers and row counts of the retraction registry layers fetched on 21 October 2026 for the
  `trust-corrected-record-machine-readable` study:
  - Retraction Watch, 173,444 rows;
  - Crossref retraction notices, 76,358;
  - OpenAlex `is_retracted`, 137,044.
- The full text of the closest prior work (the critic's precondition).

**Prior work, and what is new.**
- **"Born Flawed?"** (Zhang, Research Square rs-10177352, July 2026; PDF in `data/raw/`).
  - Design: publication-time reference-list features (self-citation rate, reference-year spread, recency) added to
    a gradient-boosted metadata model.
  - Result: out-of-time AUC rises from 0.49 to 0.66 (+0.176; 0.099 to 0.252).
  - Limit: it is a matched case-control sample of 219 retracted and 184 control papers. A balanced sample measures
    discrimination (AUC) but cannot show how many retractions a triage list would catch at the real base rate of
    about 0.1%.
- **Fletcher and Stevenson (2025)** classify retracted against matched non-retracted papers, joining Retraction Watch
  with OpenAlex.
- **Venturini et al. (arXiv 2604.02302, 2026)** report a cohort base rate near 0.12%.
- **New here:**
  - a true cohort, every biomedical article in a publication window, scored at its real base rate, with
    enrichment in the top 1% as the outcome;
  - a strict time split (fit on what was known by the end of 2020; test on 2021–2022 articles);
  - leave-one-publisher-out checks against mass-retraction clusters;
  - a block ablation;
  - a sealed forward forecast of 2025–2026 articles, to be scored on 31 December 2028.

**Ethics.**
- A per-paper risk score is an accusation in all but name. The lab publishes aggregate results only.
- The forward forecast is sealed as a hash: the per-paper file stays on local disk and is never published as a
  ranking.
- Retraction is not a synonym for misconduct. Retraction labels are *detected* retractions: papers are retracted
  partly because someone looked. Enrichment is enrichment in detected retraction.

## 1. Cohort

- **Source.** OpenAlex works with `type` = "article", not paratext, not `is_xpac`, with a DOI.
- **Biomedical.** `primary_topic.domain` Life Sciences (domains/1) or Health Sciences (domains/4).
- **Windows** (publication year):
  - **training:** 2015–2019;
  - **test:** 2021–2022;
  - **forward:** 2025–2026.

  2020 is a gap year: none of its articles is used for fitting or testing, so the split leaks nothing.
- **Exclusions are reported:** articles without a DOI, without a primary topic, or of other types.

## 2. Labels

- **Retracted article.** A cohort DOI that is the original paper of a Retraction Watch record whose
  `RetractionNature` is "Retraction", or the target of a Crossref retraction notice (update-type "retraction").
  - Self-updates (notice DOI equal to the target) count, but their dates are issue dates, so for dating them the
    Retraction Watch date is preferred where both exist.
  - Expressions of concern and corrections are not retractions.
- **Retraction date.** The Retraction Watch `RetractionDate`; otherwise the Crossref notice's date.
- **Training label.** Retracted with a date on or before 2020-12-31.
- **Test label.** Retracted as of the registry fetch (2026-10-21), so test articles have about 4–5 years of
  follow-up.
- **Agreement check.** OpenAlex `is_retracted` is reported as a check, not used as a label.

## 3. Features (information dated before 1 January of the article's publication year)

**Block A: venue.**
- The source's prior retraction rate: the share of its articles from the three previous years retracted with a date
  before 1 January of the publication year.
- The host organisation's (publisher's) prior retraction rate, defined the same way.
- The source's article-count growth (year y−1 over year y−3).
- Source type; whether the source is missing; open-access status.
- The primary topic's field (one-hot, top 20 fields).

**Block B: authors and institutions.**
- Number of authors.
- Number of authors with an earlier retracted paper (any field or year, retraction dated before 1 January of the
  publication year), and the largest such count for any one author.
- The share of authors whose first OpenAlex work is within the two previous years (newcomers).
- Numbers of distinct institutions and countries.
- The largest prior retraction rate among the paper's institutions, defined as for sources.

**Block C: the reference list.**
- Number of references.
- The share of references retracted before 1 January of the publication year.
- The spread (standard deviation) of reference publication years, and the recency gap (publication year minus the
  median reference year).
- The share of references to the same source (citation stacking).
- The share of references that cannot be resolved to a work in the snapshot.

**Not included, by design:**
- full-text content checks (statcheck, GRIM, tortured phrases), which would need full text for millions of articles;
- self-citation rate, which needs every cited work's author list;
- submission-to-acceptance lag, which OpenAlex does not carry.

These limit the claim to metadata, network and reference-list signals.

## 4. Model

- **Primary:** gradient-boosted trees (scikit-learn `HistGradientBoostingClassifier`, default settings, at most 300
  iterations, early stopping on a 10% validation split of the training years, seed 20261022).
  - Fitted on the training window with training labels.
  - All retracted training articles are kept, plus a 5% random sample of the others with weight 20.
- **Secondary:** an L2 logistic regression on the same features (standardised, missing values imputed with indicator
  flags).
- **Fixed before scoring.** The model is fitted once and frozen, and its file's hash is committed before any test
  label is read.

## 5. Hypotheses and decision rules

**Enrichment at k.** E@k = (retracted share among the top k% of scores) / (retracted share in the whole test
cohort). Intervals come from a publisher-clustered bootstrap: host organisations are resampled, with articles without
one as their own cluster; B = 1,000; seed 20261022.

- **H1 (forecastable).** E@1% ≥ 5 on the 2021–2022 test cohort.
  - **Supported** if both hold:
    - the lower 95% bound is at least 5;
    - the leave-one-publisher-out estimate also has a point estimate of at least 5. This removes the host
      organisation with the most test-period retractions from both training and test, and refits.
  - **Refuted** if the upper 95% bound is below 5.
  - Otherwise **Inconclusive.**
- **H2 (paper triage, not only publisher triage).** E@1% ≥ 3 for the model without block A (authors and
  references only). Supported if the lower bound is at least 3; Refuted if the upper bound is below 3; otherwise
  Inconclusive.
- **H3 (forward forecast, sealed; scored 2028-12-31).**
  - The same pipeline is refitted on information known by 2024-12-31: training window 2018–2022, labels dated on or
    before 2024-12-31, features as section 3.
  - It then scores every 2025–2026 cohort article.
  - The score file's SHA-256 and the model file's SHA-256 are committed. The file stays at
    `data/forecast/` and is never published.
  - **Preregistered:** E@1% ≥ 3 when scored against the registry on 2028-12-31, with the same bootstrap.
- **Secondaries:**
  - E@0.1%, E@5% and E@10%;
  - precision–recall AUC; calibration of the top decile;
  - single-block models (A, B, C alone);
  - leave-one-publisher-out for the three largest retracting publishers;
  - the logistic regression;
  - a bias audit: the share of each country (by first-author country) and each of the 20 largest publishers in the
    top 1%, against its share of the cohort, reported in aggregate only.

## 6. Order of work

1. `code/cohort.py`: cohort and the works lookup (year, source, host organisation, retraction date for every
   snapshot work).
2. `code/labels.py`.
3. `code/features.py`.
4. `code/model.py fit`, freeze the model and commit its hash.
5. `code/model.py score`.
6. `code/forecast.py` (H3 seal).
7. Report.

Deviations are logged in `deviations.md` with times from the clock, before the results they could affect.
