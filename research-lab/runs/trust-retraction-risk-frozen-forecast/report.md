# Forecasting retractions from what is known at publication: author and reference signals concentrate future retractions 7–11-fold, the preregistered full model failed to fit, and the flags fall mostly on one country

*Every biomedical research article in OpenAlex was used, at its real base rate:
- 16.1 million articles in total;
- 7.8 million from 2015–2019 for fitting, with retractions known by the end of 2020;
- 4.0 million from 2021–2022 for testing, against the retraction registry of October 2026;
- 4.4 million from 2025–2026 for a sealed forecast, to be scored at the end of 2028.

Only aggregate results are published; no per-paper score is. This version incorporates an independent review
(`review/review.md`; changes logged as D3).*

**Verdict: Inconclusive on the full model; Supported for the author-and-reference model.**

- **H1 (the full model concentrates 2021–2022 retractions at least 5-fold in its top 1%): Inconclusive.**
  - Enrichment in the top 1% is **3.7× (95% interval 1.4–13.3)**, with intervals from a bootstrap clustered by
    publisher.
  - **The frozen full model is a failed fit.** It stopped after 10 trees, with validation log-loss worse than
    predicting the base rate. 59% of its top 1% are articles hosted by PubMed Central, a repository whose prior
    retraction rate jumped 30-fold between the training and test windows.
  - **Without that host,** the same frozen model reaches 6.6× (4.1–11.5).
  - **The review's refits** (not frozen) give 2.9–6.9× with other seeds and 9.7× (4.6–12.3) with a fixed 100 trees.
  - So H1's verdict reflects the preregistered fitting recipe, not a lack of signal in venue features.
  - One publisher, Hindawi, holds 57% of the test-period retractions, largely from its 2023 mass retraction.
- **H2 (paper triage, not only publisher triage: the model without venue features reaches at least 3-fold): Supported.**
  - Using only author and reference-list features, enrichment in the top 1% is **11.4× (6.0–14.1)**, and 31× in the
    top 0.1%.
  - **Without Hindawi,** the frozen model reaches **7.4× (5.4–9.3)**. Refitted without it (the review's refit) it
    reaches 6.7× (5.1–8.4), and other seeds give 8.1–9.9×. "About 7–11×" is the honest range.
  - It holds at 10.6× (5.8–12.7) among articles with complete metadata (D2).
  - **Much of it is institution triage.** 90% of the top 1% have an institution with prior retractions (57% of the
    cohort), and 41% have an author with a prior retraction (10% of the cohort).
- **H3 (forward forecast): sealed, not yet scorable.** 4,375,482 articles from 2025–2026 are scored by the same
  pipeline refitted on information known by 2024. The score file's and model's SHA-256 are committed; the file stays
  local. The preregistered test is enrichment of at least 3× in the top 1% against the registry on 2028-12-31.
- **Who gets flagged.**
  - Articles whose first author is in China are 12% of the test cohort, 67% of the retractions detected by October
    2026, and about half (51–54%) of each model's top 1%.
  - Country is not a feature. The models learn where *detected* retractions fall, so a triage list built this way
    would concentrate scrutiny on one country's output, and on institutions with past retractions.
  - Part of the country concentration reflects the Hindawi era, and it will be re-measured in 2028.

## In plain terms

Journals retract papers that turn out to be fraudulent or badly flawed, but usually years after publication, by which
time the papers have been read and cited. Could warning signs visible on the day a paper is published (who wrote it,
what it cites, where it appears) pick out the papers most likely to be retracted later?

We trained a model only on what was known up to the end of 2020, then asked it to rank 4 million biomedical papers
published in 2021–2022, about 2 in every 1,000 of which have since been retracted.
- **Author and reference signals worked.** Using only those, the 1% of papers the model ranked riskiest held 7 to 11
  times more later retractions than average, depending on whether one publisher's mass retraction is counted.
  - These signals include institutions and authors with retracted papers in their past, and reference lists that
    cite already-retracted work.
- **The full model, journal signals included, failed for a technical reason.** Its fitting stopped after ten steps,
  before it had learned anything useful. It then flagged a large block of papers hosted by PubMed Central, a
  repository, because that repository's past retraction count had jumped. Fitted properly (a check, not part of the
  preregistered test), journal signals help rather than hurt.

Two cautions.
- **Not misconduct.** A retraction is not proof of misconduct, and these are only the retractions someone found.
- **One country, and past records.** Half of the papers the model flags have a first author in China, because
  two-thirds of the detected retractions do. Most flagged papers come from institutions with past retractions. A
  screening tool built like this would point its suspicion at one country's researchers and at institutions with a
  history, and would be self-reinforcing. We publish only these totals, never a list of flagged papers.

We have also sealed a forecast for papers published in 2025–2026, to be checked against reality at the end of 2028.

## What was asked

The lead (`trust-retraction-risk-frozen-forecast`) asked whether integrity triage can be *forecast* rather than
hindcast: in a true cohort at the real base rate, with a strict time split, leave-one-publisher-out checks against
mass-retraction clusters, and a sealed forward forecast.
- **The closest prior work** is "Born Flawed?" (Research Square, July 2026; read in full before preregistration). It
  reports publication-time reference features raising out-of-time AUC from 0.49 to 0.66. Its sample is a matched
  case-control set of 219 retracted and 184 control papers, which cannot show how a triage list performs at a 0.1–0.2%
  base rate.
- **The plan** (`plan.md`) was committed before any cohort or feature was built.

## How it was done

1. **Cohort** (`pass2.py`).
   - **Inclusion:** OpenAlex works of type "article" with a DOI and a Life Sciences or Health Sciences primary topic,
     from the local snapshot of 22 September 2026 (476 million works).
   - **Windows:**
     - training, 2015–2019: 7,758,062 articles;
     - test, 2021–2022: 3,958,510;
     - forward, 2025–2026: 4,375,482.

     2020 is a gap year: none of its articles is used for fitting or testing.
2. **Labels** (`labels.py`).
   - **Sources:** 78,857 retracted DOIs from Retraction Watch (nature "Retraction"; reinstated papers removed) and
     Crossref retraction notices, fetched 2026-10-21.
   - **Matching:** by DOI.
   - **Training positives:** retraction year 2020 or earlier, 2,813 (0.036%).
   - **Test positives:** retracted by October 2026, 7,660 (0.19%).
3. **Features**, computed from information before 1 January of the publication year (`pass1.py`, `reduce.py`,
   `features.py`):
   - **venue:** the source's and publisher's share of articles from the previous three years that were already
     retracted, source growth, source type, open access, field;
   - **authors:** authors with an earlier retracted paper, the largest such count, the share of newcomer authors,
     institutions' prior retraction rate, numbers of institutions and countries;
   - **references:** count, share already retracted, spread and recency of reference years, share citing the same
     source, share unresolvable.

   Full-text checks, self-citation and submission-to-acceptance lag were out of scope by design.
4. **Model** (`model.py`).
   - **Primary:** gradient-boosted trees fitted on all training positives and a 5% sample of negatives, reweighted.
     Default settings, with early stopping on a 10% validation split. It stopped at 10 iterations.
   - **The fit, read after the review** (`posthoc_review.json`):
     - The full model's validation log-loss went from −0.00323 (the constant base-rate predictor) to −0.00585 at
       iteration 10, worse than constant.
     - The cause: scikit-learn's defaults (no L2 regularisation, a leaf minimum counted in samples) at a 20:1 weight
       ratio let near-pure positive leaves saturate.
     - The author-and-reference model trained for 32 iterations and improved slightly on the constant (−0.00323 to
       −0.00317).
   - **Also fitted:** block ablations and a logistic regression.
   - **Frozen first:** all were frozen, and their SHA-256 committed (660d682), before any test label was read.
5. **Evaluation.**
   - **Metric:** E@k, the retracted share among the top k% of scores divided by the base rate.
   - **Intervals:** a bootstrap clustered by publisher (Poisson weights, B = 1,000; D1).
   - **Robustness:** leave-one-publisher-out refits for the three publishers with the most test-period retractions.
   - **Bias audit:** by first-author country and publisher, in aggregate only.

## Results

### Test cohort, 2021–2022 (`results/tables/h1_h2.json`; `results/figures/F1_enrichment.png`)

| model | E@0.1% | E@1% (95% CI) | E@5% | E@10% | PR-AUC |
|---|---|---|---|---|---|
| full (H1; failed fit) | 5.2 | **3.7 (1.4–13.3)** | 5.1 | 4.2 | 0.0067 |
| authors + references (H2) | 31.3 | **11.4 (6.0–14.1)** | 6.3 | 4.5 | 0.0128 |
| venue only | 9.3 | 8.0 (1.7–24.9) | 3.0 | 2.9 | 0.0064 |
| authors only | 6.9 | 5.8 (4.8–7.3) | 4.5 | 4.0 | 0.0069 |
| references only | 9.0 | 6.0 (4.0–7.1) | 5.0 | 4.1 | 0.0070 |
| logistic regression | 1.4 | 2.6 (1.0–9.6) | 3.1 | 2.6 | 0.0040 |

The base rate is 0.19% (7,660 of 3,958,510).
- **The top 1% of the H2 model** holds about 40,000 articles, of which about 2.2% have been retracted, against 0.19%
  overall.
- **Calibration:** in the full model's top decile, the observed rate is 0.81% against a mean score of 0.57%.

### Publishers

- **Concentration.** Hindawi accounts for 4,374 of the 7,660 test-period retractions (57%), Elsevier for 479 and
  Springer for 428.
- **Without each in turn:**
  - Hindawi: 5.1× (1.5–19.8);
  - Elsevier: 5.8× (3.6–15.0);
  - Springer: 3.9× (1.2–20.5).
- **Why the intervals are so wide.** Resampling publishers lets one cluster move the result.
- **Hosts in the top 1%** (`posthoc_review.json`, aggregate):

  | host | share of cohort | top 1%, full | top 1%, H2 |
  |---|---|---|---|
  | National Institutes of Health (PubMed Central, a repository) | 0.9% | **59.0%** | 0.1% |
  | Elsevier | 16.6% | 7.6% | 21.0% |
  | Frontiers | 3.5% | 5.7% | 8.7% |
  | MDPI | 5.9% | 1.5% | 7.8% |
  | Wiley | 6.0% | 1.9% | 5.9% |
  | Springer | 5.0% | 3.8% | 5.5% |
  | Hindawi | 0.75% | – | 4.7% |
  | no host | 16.7% | – | 6.9% |

  The PubMed Central host's prior retraction rate was 0.00003–0.00005 in every training year, then 0.0013–0.0015 for
  2021–2022: COVID-era retracted works whose primary location is PMC. The model learned "a host rate near 1e-3 is
  risky" from real publishers and fired on a repository. Its own retraction rate is 0.035%, a fifth of the base rate.
- **Without hosts** (frozen models, publisher-clustered intervals):

  | | full | H2 |
  |---|---|---|
  | all | 3.7 (1.4–13.3) | 11.4 (6.0–14.1) |
  | without PubMed Central | 6.6 (4.1–11.5) | 11.4 (6.1–14.2) |
  | without Hindawi | 4.7 (1.7–15.2) | 7.4 (5.4–9.3) |
  | without both | 7.4 (4.3–12.6) | 7.5 (5.4–9.5) |

- **The bootstrap choice decides H1's label.** An iid-article bootstrap would give 3.3–4.2 for the full model
  (Refuted) and 10.7–12.1 for H2. Clustered by publisher, as preregistered, the full model's interval spans the bar.
- **Leave-one-publisher-out** drops the publisher's articles but keeps its history in the feature tables (plan §5
  allows this), and its refits share the 10-iteration fit.

### Metadata completeness (D2)

- **The difference.** Retracted test articles are far more often fully deposited than the rest of the cohort: 2.3%
  have no references, against 21%. A model could score well just by favouring complete records from mainstream
  publishers.
- **The check.** Restricted to the 2,820,712 test articles with at least one reference, one author and a known
  country, which hold 7,061 of the 7,660 retractions, the H2 model still reaches 10.6× (5.8–12.7) and the full model
  4.9× (2.3–11.2).

### Bias audit (`results/figures/F2_country_audit.png`)

| first-author country | share of cohort | share of test retractions | share of top 1%, full | share of top 1%, H2 |
|---|---|---|---|---|
| China | 11.9% | 67.1% | 54.1% | 51.3% |
| USA | 13.7% | 2.4% | 4.9% | 5.4% |
| India | 4.8% | 5.0% | 2.4% | 5.8% |
| unknown | 18.3% | 6.3% | 10.8% | 4.9% |

The scores track the *detected* retraction record, which is itself concentrated: mass retractions of paper-mill output
by large publishers. A tool built on this record would reproduce that concentration. Whether it also reflects where
misconduct actually occurs cannot be told from retraction data, because retraction depends on who investigates.

### The sealed forecast (H3; `results/tables/forecast_seal.json`)

- **The refit.** The pipeline was refitted on 2018–2019 and 2021–2022 articles, with labels known by 2024 (D1: 2020
  was not extracted). It had 9,959 positives and stopped at 10 iterations, so it very likely shares the primary
  model's failed fit. The model file was not reopened.
- **The scoring.** It scored 4,375,482 articles from 2025–2026; the top 1% is 43,755 articles.
- **The seal.** The score file (SHA-256 `973d5968…`) and the model (SHA-256 `2950dd43…`) are kept on local disk.
  822 of the articles were already retracted when sealed.
- **The preregistered test:** E@1% of at least 3 against the registry on 2028-12-31.
- **The H3 addendum** (D3 §6, committed 2026-10-23, long before any 2028 label exists):
  - **Decision rule:** Supported if the lower bound of the publisher-clustered interval is at least 3; Refuted if
    the upper bound is below 3.
  - **Registry:** Retraction Watch and Crossref retraction assertions, fetched on or after 2028-12-31. Crossref-only
    self-update dates are not used for anything.
  - **Cohort:** the sealed works only, keyed by `data/forecast/forward_wid_doi.csv` (SHA-256 `486a8f592c82d286b521993b21609af62d3926e64cb034cd8de8bd4870fde61a`;
    4,375,482 works).
  - **Excluded:** the 822 works already retracted at sealing (`forward_retracted_at_seal_wids.csv`, SHA-256
    `9e9a5e62b899829638e63e9fc449925fe7aaaf392bd9ece0daf2ef4d2b685c76`).

## What this does and does not show

- **Publication-time signals carry real information about later retraction, at the real base rate.**
  - A 7–11-fold concentration in the top 1% comes from institutions' and authors' earlier retractions and the
    reference list.
  - It holds without Hindawi (7.4×) and on well-deposited records.
  - Much of it is institution triage, an entity-level proxy with the same equity risks as country.
- **The preregistered full model failed to fit.** That, not venue information, is why it misses the bar. One feature
  also misfires: venue rate features treat a repository host like a publisher. A future forecast should exclude
  repository locations or flag them, and should regularise the fit.
- **Label dating is a leak channel.** For Crossref-only self-updates, the retraction "date" is usually the paper's own
  deposit year. 256 of 2,813 training positives (9%) carry such dates, and author and reference features inherit
  them. The review's bound, a one-year as-of buffer, moves H2 only from 11.36× to 11.21×.
- **Retraction notices in the cohort.** 2,252 notices sit in the cohort as "articles" (956 in the test window), and
  the plan's OpenAlex is_retracted check had not been run. The review ran it: 7,617 of 8,789 OpenAlex-flagged test
  articles overlap the labels, and most of the rest are notices. The effect on E@k is negligible (0.02% of the test
  set).
- **This is a forecast of *detected* retraction.** It inherits who investigates: publishers that run mass
  integrity sweeps, and the sleuths who target paper mills. The country concentration of its flags is the clearest
  sign. Retraction is not proof of misconduct, and a high score is not evidence against any paper.
- **The settings were fixed in advance to keep the test honest,** and they failed for the full model. Better-fitted
  models do more (the review's refits). Any next forecast should be preregistered with a regularised recipe.
- **Smaller notes:**
  - `newcomer_share` counts a first year equal to Y as a newcomer;
  - "top 20 fields" is 10 codes;
  - publisher ids are OpenAlex host organisations (Hindawi P4310319869; PubMed Central's host I1299303238).
- **Not included:** full-text signals (tortured phrases, statistical inconsistencies), which other work finds
  informative.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - D1: the forward refit's years, year granularity, labels, and the Poisson cluster bootstrap;
  - D2: the post-hoc completeness check, the country audit for both models, and the publisher names;
  - D3: after the review:
    - the failed fit;
    - the PubMed Central host;
    - the self-update dates;
    - H2's Hindawi robustness and institution component;
    - notices;
    - the H3 addendum.
- **Models frozen** in 660d682 before scoring, and never refitted in place.
- **Independent review:** Fable, 2026-10-23, "fix first" (`review/review.md`). Both preregistered verdicts stand;
  the explanation changed. A confirmation pass follows.

## Reproducing it

1. **Labels and lookups:** `code/labels.py`, `code/pass1.py`, `code/reduce.py`.
2. **Cohort and features:** `code/pass2.py`, `code/features.py`.
3. **Models:** `code/model.py fit`, then `code/model.py score`.
4. **Forecast:** `code/forecast.py`.
5. **Checks and figures:** `code/posthoc_complete.py`, `code/posthoc_review.py` (D3), `code/figures.py`. The review's
   refits and the buffer test are in `review/reviewer_checks/`.
6. **Data:** the OpenAlex works snapshot (22 September 2026, a local sparse column copy) and the registry layers
   fetched for `trust-corrected-record-machine-readable`.
