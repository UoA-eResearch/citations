# Forecasting retractions from what is known at publication: author and reference signals concentrate future retractions about 11-fold, venue signals do not hold up, and the flags fall mostly on one country

*Every biomedical research article in OpenAlex was used, at its real base rate:
- 16.1 million articles in total;
- 7.8 million from 2015–2019 for fitting, with retractions known by the end of 2020;
- 4.0 million from 2021–2022 for testing, against the retraction registry of October 2026;
- 4.4 million from 2025–2026 for a sealed forecast, to be scored at the end of 2028.

Only aggregate results are published; no per-paper score is.*

**Verdict: Inconclusive on the full model; Supported for the author-and-reference model.**

- **H1 (the full model concentrates 2021–2022 retractions at least 5-fold in its top 1%): Inconclusive.**
  - Enrichment in the top 1% is **3.7× (95% interval 1.4–13.3)**, with intervals from a bootstrap clustered by
    publisher.
  - One publisher, Hindawi, holds 57% of the test-period retractions, largely from its 2023 mass retraction. Without
    it, the refitted model reaches 5.1×, but with an equally wide interval (1.5–19.8).
- **H2 (paper triage, not only publisher triage: the model without venue features reaches at least 3-fold): Supported.**
  - Using only author and reference-list features, enrichment in the top 1% is **11.4× (6.0–14.1)**, and 31× in the
    top 0.1%.
  - It holds at 10.6× (5.8–12.7) among articles with complete metadata (D2), so it is not only a sign of
    well-deposited records.
  - The venue features, which the full model includes, make it *worse* on this period.
- **H3 (forward forecast): sealed, not yet scorable.** 4,375,482 articles from 2025–2026 are scored by the same
  pipeline refitted on information known by 2024. The score file's and model's SHA-256 are committed; the file stays
  local. The preregistered test is enrichment of at least 3× in the top 1% against the registry on 2028-12-31.
- **Who gets flagged.**
  - Articles whose first author is in China are 12% of the test cohort, 67% of the retractions detected by October
    2026, and about half (51–54%) of each model's top 1%.
  - Country is not a feature. The models learn where *detected* retractions fall, so a triage list built this way
    would concentrate scrutiny on one country's output.

## In plain terms

Journals retract papers that turn out to be fraudulent or badly flawed, but usually years after publication, by which
time the papers have been read and cited. Could warning signs visible on the day a paper is published (who wrote it,
what it cites, where it appears) pick out the papers most likely to be retracted later?

We trained a model only on what was known up to the end of 2020, then asked it to rank 4 million biomedical papers
published in 2021–2022, about 2 in every 1,000 of which have since been retracted.
- **Author and reference signals worked.** Using only those, the 1% of papers the model ranked riskiest held 11 times
  more later retractions than average. These signals include authors who already had retracted papers and reference
  lists that cite already-retracted work.
- **Journal signals did not.** Adding signals about the journal made the ranking worse. One publisher's mass
  retraction dominates the period, and journals' past records did not foresee it.

Two cautions.
- **Not misconduct.** A retraction is not proof of misconduct, and these are only the retractions someone found.
- **One country.** Half of the papers the model flags have a first author in China, because two-thirds of the
  detected retractions do. A screening tool built like this would point most of its suspicion at one country's
  researchers. We publish only these totals, never a list of flagged papers.

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
| full (H1) | 5.2 | **3.7 (1.4–13.3)** | 5.1 | 4.2 | 0.0067 |
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
- **Why the venue block can mislead.** The full model's venue features reflect which venues had retracted papers
  before 2021. The 2023 mass retraction hit venues with little such history, so venue history misleads in this period.
  The author and reference signals transfer.

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
  was not extracted). It had 9,959 positives and stopped at 10 iterations.
- **The scoring.** It scored 4,375,482 articles from 2025–2026; the top 1% is 43,755 articles.
- **The seal.** The score file (SHA-256 `973d5968…`) and the model (SHA-256 `2950dd43…`) are kept on local disk.
  822 of the articles were already retracted when sealed.
- **The preregistered test:** E@1% of at least 3 against the registry on 2028-12-31.

## What this does and does not show

- **Publication-time signals carry real information about later retraction, at the real base rate.** About an
  11-fold concentration in the top 1% comes from authors' earlier retractions, institutions' records and the
  reference list. It survives removing the dominant publisher's influence on the venue block, and restricting to
  well-deposited records.
- **Venue history alone is not a reliable forecaster in a period shaped by one publisher's mass retraction.** The full
  model fails the preregistered bar for that reason.
- **This is a forecast of *detected* retraction.** It inherits who investigates: publishers that run mass
  integrity sweeps, and the sleuths who target paper mills. The country concentration of its flags is the clearest
  sign. Retraction is not proof of misconduct, and a high score is not evidence against any paper.
- **The models are deliberately simple.** The primary model stopped after 10 boosting rounds, so better-tuned models
  might do more. The plan fixed the settings in advance to keep the test honest.
- **Not included:** full-text signals (tortured phrases, statistical inconsistencies), which other work finds
  informative.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - D1: the forward refit's years, year granularity, labels, and the Poisson cluster bootstrap;
  - D2: the post-hoc completeness check, the country audit for both models, and the publisher names.
- **Models frozen** in 660d682 before scoring.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. **Labels and lookups:** `code/labels.py`, `code/pass1.py`, `code/reduce.py`.
2. **Cohort and features:** `code/pass2.py`, `code/features.py`.
3. **Models:** `code/model.py fit`, then `code/model.py score`.
4. **Forecast:** `code/forecast.py`.
5. **Checks and figures:** `code/posthoc_complete.py`, `code/figures.py`.
6. **Data:** the OpenAlex works snapshot (22 September 2026, a local sparse column copy) and the registry layers
   fetched for `trust-corrected-record-machine-readable`.
