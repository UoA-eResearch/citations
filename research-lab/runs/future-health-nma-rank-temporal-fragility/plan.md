# Preregistration: are network meta-analysis treatment rankings a forecast or a snapshot?

Lead: `future-health-nma-rank-temporal-fragility`. Written 2026-10-18, after downloading the nmadb catalogue and
datasets and surveying their column formats, before any network was fitted.

## 1. Question

Treatment rankings from network meta-analyses (NMA), and the "probability of being best", are read by guideline and
funding bodies as if they were forecasts. When the next tranche of evidence arrives, how often does the top-ranked
treatment change? Is the stated probability of being best calibrated against that? And can simple features of the
network predict which rankings flip?

## 2. Hypotheses (from the lead, with decision rules)

- **H1 (fragility).** Withholding the newest tranche of studies (about 10%, by publication year; §4), and then adding
  it back, changes the top-ranked treatment in at least 30% of networks.
  - Supported: the point estimate is ≥ 0.30 and the 95% Wilson lower bound is ≥ 0.25.
  - Refuted: the upper bound is < 0.30.
  - Otherwise: Inconclusive.
- **H2 (miscalibration).** Before the update, the probability of being best of the top-ranked treatment overstates
  the empirical rate at which that treatment keeps top rank, by at least 20 percentage points. The measure is mean
  P(best) minus the retention rate, across networks, with a 2,000-resample network bootstrap.
  - Supported: the point estimate is ≥ 0.20 and the lower bound is ≥ 0.15.
  - Refuted: the upper bound is < 0.20.
  - Otherwise: Inconclusive.
- **H3 (predictability).** The pre-update gap between the top two P-scores and the log number of studies in the
  pre-update network together explain less than half of the variation in which networks flip. The model is logistic
  regression of the H1 flip indicator on these two predictors, measured by Nagelkerke R² with a 2,000-resample
  network bootstrap.
  - Supported: the upper bound is < 0.50.
  - Refuted: the lower bound is ≥ 0.50.
  - Otherwise: Inconclusive.

## 3. Data

- **Network Meta-Analysis Database (nmadb; Petropoulou et al. 2016).** Downloaded through its public REDCap API at
  ISPM Bern. The public token is read at run time from the archived CRAN package nmadb 1.2.0 and is not stored in this
  repository.
  - The catalogue has 453 records, of which 278 are "Verified" with a downloadable arm-level or contrast-level
    dataset.
  - The catalogue supplies the effect measure, the outcome type and whether the outcome is harmful or beneficial.
  - Snapshot checksums are in `data/raw/SHA256SUMS` and are released in `results/tables/`.
- **Europe PMC** is used only for validation V3 (§6).

## 4. Definitions

**Standardisation (`code/standardise.py`).**
- **Formats.** Long format: one row per arm. Continuous outcomes give y, sd, n; binary give r, n; rates give r and
  time. The inverse-variance format gives effect, se, t1, t2.
- **Columns.** Column-name variants ("study year" or "year"; "study", "study name" or "id") are mapped to one schema.
- **Years.** A study's year is carried from its first row to its other rows, within the study id.
- **The single wide-format network** is converted to long format.
- **Inverse-variance effects** are used as given, on the scale the catalogue's measure implies. Ratio measures are on
  the log scale; the parser checks this (negative values present, or the catalogue says log).

**Inclusion.**
1. **Parsing.** The dataset parses, and its effect measure is not "other".
2. **Size.** At least 3 treatments and at least 10 studies, so the newest tranche contains at least one study.
3. **Years.** A year is available for at least 90% of studies. A study without a year is never withheld; it stays in
   both the pre-update and the full network.
4. **Full fit.** The full network is connected and its random-effects fit (§5) succeeds.
5. **Tranche size.** The withheld tranche is at most 50% of studies.

**Primary holdout (newest tranche).**
- **Tranche.** Studies are ordered by year. The tranche is the smallest set of whole latest years containing at
  least ⌈0.10 × k⌉ of the k dated studies. Studies from the same year are never split.
- **Pre-update network.** All other studies. If removing the tranche disconnects the network, the pre-update network
  is its connected component with the most studies.
- **Treatments.** Those not in the pre-update network are "new entrants".

**Secondary holdouts.**
- **S1:** the newest ≥ 25% (same whole-year rule).
- **S2:** the single latest year.
- **S3:** a longer horizon, where the pre-update network is the oldest ≥ 50% of studies (whole years).

**Ranking.**
- **Metric.** Treatments are ranked by P-score, the frequentist analogue of SUCRA (Rücker & Schwarzer 2015). For
  treatment i in a treatment set A:
  - P_i = (1 / (|A| − 1)) Σ_{j ∈ A, j ≠ i} Φ(s · (θ_j − θ_i) / se_ij), with the random-effects estimates and their
    standard errors;
  - s = +1 when small values are good (harmful outcomes) and −1 when large values are good (beneficial outcomes).
- **Top-ranked treatment.** The treatment with the highest P-score.

**The flip (H1).** The pre-update top-ranked treatment differs from the full-data top-ranked treatment. Both are
computed over the set of treatments in the pre-update network: full-data P-scores are recomputed on that set from
the full fit. A new entrant that becomes top-ranked over all treatments is counted separately, as "new-entrant top".

**P(best) (H2).**
- **Source.** The pre-update fit's probability that its top-ranked treatment is best, from netmeta's `rankogram`.
  `rankogram` resamples from the random-effects estimates' multivariate normal distribution, with nsim = 10,000 and
  a seed fixed per network.
- **Retention.** The same treatment is top-ranked in the full data, over the pre-update treatment set.

## 5. Model

- **Fit.** netmeta 3.6.1 (R 4.4.3), random effects, DerSimonian–Laird τ, the effect measure the catalogue records.
- **Inputs.** `pairwise()` builds the contrasts for arm-level data with `allstudies = TRUE`, netmeta's default
  continuity correction for zero cells, and `tol.multiarm = 0.2` for continuous outcomes, as in the nmadb package's
  own `runnetmeta`.
- **Sensitivity.** A common-effect model.

## 6. Validation, before any holdout result is computed

- **V1 (parsing).** For 20 random included networks, the standardised file is compared with the raw spreadsheet:
  studies, arms, treatments, years and outcome values (`code/validate_parse.py`, with the comparison saved).
  - Abort rule: if more than 2 of the 20 have an error, the parser is fixed and a fresh 20 is drawn.
- **V2 (counts).** For every network, the number of studies and treatments is compared with the catalogue's
  "Number of Studies" and "Number of Treatments". This is reported, not used as a gate, because the catalogue counts
  can refer to the whole review.
- **V3 (published ranking, descriptive).** For 30 random included networks, the abstract is retrieved from Europe PMC
  by title. The treatment the authors name as best for the analysed outcome is recorded, where they name one, and
  compared with the full-network top-ranked treatment. Agreement is reported. It is not a gate: published analyses
  often used Bayesian models or a different outcome.

## 7. Further analyses (not verdict-bearing)

- **Negative control.** For each network, 200 random holdouts with the same number of studies as the primary tranche
  (not time-ordered, same rules) give a random-holdout flip probability. The temporal and random flip rates are
  compared across networks (paired difference, network bootstrap). This separates "new evidence" from "less
  evidence".
- **The full predictor model.** Logistic regression of the flip on:
  - the top-two P-score gap;
  - log studies;
  - number of treatments;
  - I² (netmeta);
  - the proportion of direct evidence in the pre-update top-versus-second comparison;
  - the withheld tranche's share of participants (or of studies, for contrast-level data);
  - outcome type.

  AUC and Nagelkerke R² are reported.
- **The calibration curve.** P(best) in five bins against retention, with network-bootstrap intervals.
- **Rank agreement.** Kendall's τ between pre-update and full P-scores over common treatments; change in the top-two
  set.
- **Secondary holdouts.** S1–S3, the common-effect model, and the resampling SUCRA (`netrank(method = "SUCRA")`) in
  place of the P-score.

## 8. Reporting

- **Report.** Every verdict follows the rules above. Deviations are logged in `deviations.md` with Auckland
  timestamps. Code is committed before the outputs it produces. The report includes a plain-language section.
- **Scope.** This is a retrospective holdout on networks published 2000–2015; the "next tranche" is the last tranche
  those authors included, not evidence published later.
