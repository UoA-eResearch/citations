# Preregistration: do published FAERS safety signals survive an independent, calibrated re-analysis?

Lead: `future-health-faers-published-signal-recalibration`. Written 2026-10-18, before any published signal was
extracted or recomputed.

**Examined beforehand (no outcome):**
- the Europe PMC hit count (2,228 papers, 2023–2025);
- three abstracts, for format only;
- the OHDSI negative-control file: 200 pairs, outcomes listed;
- the FAERS export page and download speed.

**Prior work.** İnkaya & Güngör (Pharmaceuticals 2026) calibrated one drug class against 72 negative-control pairs;
no population-level re-analysis was found (search 2026-10-18).

## 1. Hypotheses

- **H1 (survival).** Among published significant drug–event signals (§2), fewer than 60% remain significant when
  recomputed from public FAERS under one protocol (§3) and calibrated against an empirical null from negative-control
  pairs (§4), with Benjamini–Hochberg FDR control at q < 0.05.
  - Supported: the paper-cluster bootstrap 95% upper bound is < 0.60.
  - Refuted: the lower bound is ≥ 0.60.
  - Otherwise: Inconclusive.
  - The primary null is the maximum-likelihood fit; the sample-SD fit is reported beside it.
- **H2 (inflation).** The median ratio of published to recomputed ROR is at least 1.25.
  - Supported: the lower bound is ≥ 1.25.
  - Refuted: the upper bound is < 1.25.
  - Otherwise: Inconclusive.

## 2. The published signals

- **Papers.** Europe PMC search, run once and saved:

  `("FAERS" OR "FDA Adverse Event Reporting System") AND (disproportionality OR "reporting odds ratio" OR
  "proportional reporting ratio") AND PUB_YEAR:[2023 TO 2025]`

  Research articles in English are kept.
- **Extraction from abstracts.** An open-weight LLM extracts every reported drug–event signal from each abstract. It
  is Nemotron 3 Nano, served locally by the lab's vLLM, with temperature 0 and JSON-schema-constrained output. Each
  signal records:
  - drug, event, measure, point estimate, 95% CI and case count;
  - the paper's stated FAERS window (start and end quarter).
- **Eligible signal.** All of the following hold:
  1. the measure is a ROR with a point estimate and 95% CI;
  2. it is reported as significant (lower bound > 1);
  3. the drug is one active ingredient, or a product that maps to one;
  4. the event is a MedDRA Preferred Term: its name, after a fixed US-to-UK spelling map (hemorrhage → haemorrhage,
     anemia → anaemia, edema → oedema, diarrhea → diarrhoea, esophag- → oesophag-, tumor → tumour, leukemia →
     leukaemia, …), equals a PT in FAERS for the window;
  5. the paper states its window.
- **Cap.** At most 5 eligible signals per paper are kept, chosen at random (seed 20261018), so that a few
  long-list papers cannot dominate.
- **Target.** At least 300 eligible signals.

## 3. Recomputation protocol (one protocol for every signal)

- **Data.** FDA quarterly ASCII extracts, legacy AERS (2004Q1–2012Q3) and FAERS (2012Q4 onward), for the paper's own
  window.
- **Deduplication.** The latest version per case: FAERS caseid by caseversion and fda_dt; legacy AERS CASE by ISR.
  Overlap across the 2012 boundary is a stated limitation, with a FAERS-only sensitivity analysis.
- **Drug.** Reports where the drug is the primary suspect (role PS). It is matched on the active-ingredient field
  where present (prod_ai, 2014Q3 onward), otherwise on the drug name against the ingredient and its RxNorm brand
  names (RxNav, cached).
- **Event.** A MedDRA PT in the reaction table, exact after normalisation.
- **Statistic.** The report-level 2×2 table over the deduplicated window: a = drug and event, b = drug and other
  events, c = other drugs and event, d = the rest.
  - ROR = (a/b)/(c/d), with a 95% CI on the log scale.
  - Recomputed-significant: a ≥ 3 and the lower bound > 1.
- **Sensitivity variants:**
  - all suspect roles (PS, SS);
  - no deduplication;
  - the full window, 2004Q1 to the last quarter before publication.

## 4. Empirical null

- **Negative controls.** The OHDSI negative-control set (MethodEvaluation): every target and comparator drug with
  its outcome. Each outcome is mapped to one MedDRA PT by a fixed table in `code/negative_controls.py`, committed
  before any control is computed; outcomes with no PT equivalent are dropped.
- **Computation.** Each pair is computed with the §3 protocol over 2004Q1–2025Q4. Pairs with a ≥ 1 enter the fit.
- **Minimum.** At least 50 pairs, as the lead requires.
- **Null fits** of the systematic-error distribution N(μ, σ²) of log ROR:
  - (i) maximum likelihood, accounting for each pair's standard error (Schuemie et al. 2014);
  - (ii) sample mean and SD of the log ROR.
- **Calibration.** The calibrated p-value of a recomputed signal is 2·min(Φ(z), 1−Φ(z)), with
  z = (log ROR − μ) / √(σ² + se²). BH-FDR is applied across all eligible signals.
- **Survival.** A signal survives if its recomputed ROR > 1 and its calibrated q < 0.05.

## 5. Validation, before any recomputed signal is compared with its published value

- **The extraction check.** A random 15% of papers (at least 50) are hand-adjudicated against the abstract:
  - precision: each extracted eligible signal is correct in drug, event, estimate, CI and window;
  - recall: eligible signals missed.
- **Abort rule.** If precision is below 0.90, the prompt or schema is revised once and re-validated on a fresh
  sample. If it still fails, the study reports extraction as the finding.
- **The pipeline check.** For 10 signals with large case counts, the recomputed a is compared with the paper's
  reported case count. This is descriptive.

## 6. Secondary analyses

- **Predictors of non-replication.** Logistic regression with paper-clustered SEs on:
  - the log of the published ROR;
  - the published case count;
  - the window length;
  - journal (the five most frequent against the rest);
  - publication year.
- **Reported alongside:** uncalibrated replication, the sample-SD null, and the three protocol variants.

## 7. Threats and care

- **One protocol by design.** A paper's own comparator, subgroup or role choices can explain non-replication. The
  study measures robustness to one transparent protocol plus calibration, not misconduct, and says so.
- **The negative controls.** They come from healthcare-database research, and in FAERS some may carry notoriety bias.
  The two null fits bracket this.
- **Pharmacovigilance limits.** FAERS reports are not incidences, and no causal claim is made about any drug.
