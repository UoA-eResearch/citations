# Do published FAERS safety signals survive an independent, calibrated recomputation?

*406 drug–event signals from 142 papers published in 2023–2025 were recomputed from the FDA's public adverse-event
files under one fixed protocol. They were then calibrated against an empirical null built from 190 negative-control
drug–event pairs.*

**Verdict: Refuted, as preregistered, but the result depends heavily on where the null is centred.**

- **H1 (fewer than 60% survive): Refuted.**
  - 71% of the published signals survive, i.e. they stay significant after recomputation and calibration (289 of 406;
    paper-cluster bootstrap 95% CI 65–77%).
  - Under the sample-SD null, reported beside the primary one, 63% survive (56–69%). That would have been
    Inconclusive.
- **H2 (published RORs at least 25% larger than recomputed ones): Refuted.** The median ratio of published to
  recomputed ROR is 1.08 (1.04–1.16).

**What qualifies the H1 verdict:**

- **The null's centre.** The negative controls put the null's centre far below "no association": a median control
  ROR of about 0.43. That centre makes calibration lenient.
  - With the same null width centred at zero, only 45% survive (36–55%). This check is exploratory, added after the
    results were seen, and cannot change the verdict.
  - So the answer to "do most published signals survive?" turns on a modelling choice that the negative-control
    method makes automatically and that FAERS may not support.
- **Agreement at the median hides wide disagreement.** The median ratio is near 1, but 119 of 392 recomputed RORs
  differ from the published value by more than a factor of 2. Only 151 (39%) are within 0.8–1.25 of it.
- **Weak signals rarely survive.**
  - 29% survive among published RORs up to 2, and 48% between 2 and 5.
  - 82% survive between 5 and 20, and 92% above 20.

**Two implementation errors were found after the first analysis (deviation D3).** The per-paper cap was applied
before one eligibility rule, and the spelling map broke two UK spellings. Both were corrected. The first-pass result
was 72% (66–78%) for H1 and 1.08 (1.02–1.16) for H2, with the same verdicts.

## In plain terms

Thousands of papers mine the FDA's public database of adverse-event reports. They flag a drug as "reported
disproportionately often" with some side effect, using a statistic called the reporting odds ratio. These flags are
meant to prompt closer study, but how often do they hold up?

We took 406 such flags from 142 recent papers. We recomputed each one from the same public database, using one fixed
and fully published recipe. We then asked whether each flag still stood out once we allowed for the background noise
this kind of data produces. To estimate that noise we used 190 drug and side-effect pairs that are known to be
unrelated.

About 7 in 10 flags held up. Flags that were very strong in the paper almost always held up. Weak ones (a ratio under
about 5) often did not.

But the "7 in 10" depends on a judgement call. The unrelated pairs looked *less* likely than average to be reported
together. Measuring against them makes it easier for a flag to pass. Measured against a neutral baseline with the same
noise, fewer than half the flags pass.

Our recomputed numbers matched the papers' numbers on average. For nearly a third of flags, though, they differed by
more than a factor of two.

None of this says whether any drug causes any side effect. These are reporting patterns, not rates of harm.

## What was asked

Disproportionality analyses of the FDA Adverse Event Reporting System (FAERS) are among the most common pharmacovigilance
publications. Each paper makes its own choices: which reports, which drug roles, which comparison group, how to remove
duplicates, which years. It then reports reporting odds ratios (RORs) whose lower confidence bound exceeds 1.

The study asks two preregistered questions (`plan.md`):

- **H1:** Under one fixed protocol and an empirical null from negative controls, do fewer than 60% of published
  significant signals remain significant (Benjamini–Hochberg q < 0.05)?
- **H2:** Is the median published ROR at least 1.25 times the recomputed one?

## What was already known

- **Calibration with negative controls** is established for observational database studies (Schuemie et al. 2014,
  the OHDSI programme).
- **In FAERS**, one 2026 study (İnkaya & Güngör, *Pharmaceuticals*) calibrated a single drug class against 72
  negative-control pairs.
- **No population-level re-analysis** of published FAERS signals was found (search 2026-10-18).

## How it was done

**The published signals:**
- **Search.** A saved Europe PMC search for FAERS disproportionality papers published 2023–2025 returned 2,265
  records; 1,830 research abstracts were processed.
- **Extraction.** A locally served open-weight model (Nemotron 3 Nano, temperature 0, JSON-schema-constrained output)
  extracted every reported drug–event estimate with its CI, case count and stated FAERS window.
- **The extraction check.**
  - **Round 1 failed.** On fully eligible signals, precision was 51/71 = 0.72 against a bar of 0.90. Most errors were
    windows ("June 2023" read as 2023Q4) and estimates from other databases.
  - **Round 2 passed.** As the plan allows, the prompt and schema were revised once (deviation D2). On a fresh sample
    of 272 papers, precision was 68/71 = 0.96, with no eligible signal missed.
- **Eligibility.** All of the following:
  - a ROR with a point estimate and 95% CI, and a lower bound above 1;
  - one active ingredient, mapped through RxNorm;
  - an event that is a MedDRA Preferred Term (PT) after a fixed US-to-UK spelling map;
  - a stated window;
  - the FAERS database, and a comparison other than an interaction.
- **Result.** 495 signals were eligible. At most 5 per paper were kept at random, giving 406 signals from 142 papers.

**The recomputation** (`code/recompute.py`):
- **Data.** All FDA quarterly ASCII files, 2004Q1–2026Q2: 24.8 million report versions, in DuckDB.
- **Deduplication.** The latest version of each case.
- **Drug.** The drug as primary suspect, matched on the active-ingredient field or on its RxNorm brand names.
- **Event.** The event PT.
- **Statistic.** A report-level 2×2 table over the paper's own window.
- **Variants:**
  - all suspect roles;
  - no deduplication;
  - the full window up to the paper's publication.
- **The pipeline check.** For the 10 eligible signals with the largest published case counts, the recomputed count is
  a median 1.00 times the published one (`results/tables/pipeline_check.csv`).
  - 8 of the 10 are within about 15%.
  - The two exceptions are hydroxychloroquine–pemphigus and lanreotide–cholelithiasis. The first is a known cluster
    of duplicated co-suspect reports: 84 primary-suspect cases recomputed against 1,545 published, and 5,990 with all
    suspect roles.

**The empirical null** (`code/negative_controls.py`, `code/analysis.py`):
- **Controls.** The OHDSI MethodEvaluation negative controls: 332 drug–PT pairs from 119 drugs and 64 PTs, mapped by a
  table fixed before any control was computed.
- **Computation.** Each pair over 2004Q1–2025Q4. The 190 pairs with at least one report enter the fit.
- **Fits.**
  - **Primary:** maximum likelihood with each pair's standard error (Schuemie). μ = −0.85, σ = 0.96.
  - **Beside it:** the sample mean and SD. μ = −0.92, σ = 1.12.
- **Calibration.** Each recomputed signal gets a calibrated p-value, then BH-FDR across all 406.
- **Survival.** A signal survives if its recomputed ROR exceeds 1 and its calibrated q is below 0.05.
  - The 14 signals with a zero cell have no recomputed ROR. They count as not surviving.
- **Inference.** Intervals come from a paper-cluster bootstrap, 2,000 resamples.

## Results

### H1: survival (`results/tables/primary.json`, `results/figures/F3_survival.png`)

| | survive | 95% CI |
|---|---|---|
| **Primary: MLE null** | **71% (289/406)** | **65–77%** |
| Sample-SD null | 63% | 56–69% |
| Uncalibrated (recomputed lower bound > 1, a ≥ 3) | 87% | 82–91% |
| All suspect roles, MLE null | 74% | |
| No deduplication, MLE null | 70% | |
| Full window, MLE null | 69% | |
| All-drugs comparisons only (354), MLE null | 72% | 66–78% |
| *Exploratory: MLE width, centred at 0* | *45%* | *36–55%* |

The bootstrap lower bound under the primary null, 65%, is above the 60% bar, so **H1 is Refuted**.

Where the 117 non-survivors come from:
- **48 are not significant even before calibration.** Of these:
  - 14 have a zero cell;
  - 16 have a recomputed ROR at or below 1;
  - 5 have an ROR above 1 but fewer than 3 reports;
  - 13 have an interval that includes 1.
- **69 are significant before calibration but not after.**

Five signals with only 1 or 2 recomputed reports survive calibration. The preregistered survival rule has no case
minimum.

![The share of published signals that survive](results/figures/F3_survival.png)

### The null and why it matters (`results/figures/F2_null.png`, `results/tables/null_sensitivity.json`)

The negative controls sit mostly below zero on the log scale. A drug in the control set is, on average, reported with
these unrelated events less often than the rest of FAERS is. Only 14 of the 190 controls (7%) are significant before
calibration.

A plausible cause is the reporting background. Large patient-support programmes generate many reports listing
everyday conditions such as sinusitis, allergies and dermatitis. Those reports inflate the comparison group's rate
for the control outcomes. This study did not test that explanation.

Calibrating against a null centred at an ROR of 0.43 lowers the bar for a positive signal. The exploratory grid
(`null_sensitivity.json`) shows survival depending on both the null's centre and its width:

| centre μ \ width σ | 0.50 | 0.75 | 0.96 (fitted) | 1.12 (sample SD) |
|---|---|---|---|---|
| −0.85 (fitted) | 90% | 84% | **71%** | 62% |
| −0.50 | 85% | 72% | 62% | 52% |
| −0.25 | 78% | 66% | 54% | 42% |
| 0 | 72% | 59% | 45% | 35% |

Survival clears the 60% bar in the fitted corner of the grid, and falls below it once the centre moves towards zero
at the fitted width.

The plan's two null fits were meant to bracket notoriety bias. Both are centred well below zero, so neither brackets
the centre. Whether the published signals' events share the control outcomes' reporting background is untested. This
is the main limitation of the H1 verdict.

![The empirical null against the published signals](results/figures/F2_null.png)

### H2: inflation (`results/figures/F1_published_vs_recomputed.png`)

- **The median.** The published ROR is a median 1.08 times the recomputed one (392 signals with a finite recomputed
  ROR; 95% CI 1.04–1.16). The upper bound is below 1.25, so **H2 is Refuted**. The all-drugs-only subset gives the
  same median, 1.08.
- **The spread.**
  - 69 published RORs are more than twice the recomputed value, and 50 are less than half of it.
  - So the protocol reproduces published values on average, but not signal by signal.
  - Papers' own choices (comparators, roles, deduplication, MedDRA level, date handling) plausibly account for the
    spread. This study cannot attribute it.

![Published against recomputed RORs](results/figures/F1_published_vs_recomputed.png)

### Who survives (secondary, preregistered)

- **Logistic regression of non-survival** on the log published ROR, window length, top-5 journal and publication year
  (406 signals, paper-clustered SEs):
  - A larger published ROR strongly predicts survival (coefficient −0.96 per log unit, p < 0.001).
  - Later publication years survive slightly more often (coefficient −0.47 per year, p = 0.025). By year: 2023 67%,
    2024 67%, 2025 76%.
  - Window length and journal show nothing detectable.
- **Adding the published case count** is possible only for the 72 signals that report one. A larger count also
  predicts survival (coefficient −0.60 per log unit, p = 0.018).
- **By paper.** 18 of the 142 papers have no surviving signal, and 76 have all of theirs survive.

## What this does and does not show

- **It shows:**
  - most published FAERS signals with large RORs reappear under one transparent protocol;
  - published and recomputed RORs agree on average;
  - weak published signals (ROR below about 5) often do not survive calibration.
- **It does not show that most published signals are robust.** The headline share swings from 71% to 45% with the
  null's centre, and the negative-control null for FAERS is centred far from zero for reasons this study did not
  establish.
- **One protocol by design.** A paper's comparator, subgroup or role choices can explain non-replication. This
  measures robustness to one fixed recipe plus calibration, not error or misconduct.
- **Selection.**
  - Only abstract-level signals with a single ingredient, a PT-named event and a stated window are included.
    Class-level, SMQ-level and grouped-event signals are excluded, and they may behave differently.
  - US spellings missing from the fixed map (for example "hyperprolactinemia", "gynecomastia") still fail the PT rule.
- **Extraction.** Precision 0.96 on the validation sample, so a small share of the 406 may be mis-extracted.
- **Pharmacovigilance limits.** FAERS reports are not incidences. No causal claim about any drug is made.

## Process and deviations

- **Preregistration.** The plan (`plan.md`, 2f4c30d) was committed before any signal was extracted.
  - The negative-control mapping and all pipeline code were committed before the outputs they produced.
- **D1:** a larger token budget for 64 extraction failures.
- **D2:** the round-1 extraction check failed. The prompt and schema were revised once, and the revision passed on a
  fresh sample. This happened before any signal was recomputed.
- **D3:** after the first analysis, two implementation errors were found and corrected.
  - The plan's per-paper cap applies to fully eligible signals, but the code capped before the PT rule.
  - The spelling map doubled a leading "o" ("ooesophagitis").
  - Both the as-run results (`results/asrun/`) and the corrected ones are reported. The verdicts are the same.
- **The null-centre sensitivity** (`code/null_sensitivity.py`) and the last row of F3 are exploratory. They were added
  after the results were seen.

## Reproducing it

`code/fetch_epmc.py`, `code/extract_signals.py v2`, `code/fetch_faers.py`, `code/faers_db.py`,
`code/negative_controls.py`, `code/eligible.py`, `code/recompute.py`, `code/validate_pipeline.py`, `code/analysis.py`,
`code/null_sensitivity.py`, `code/figures.py`.

- **The extraction validation** is in `code/validation_adjudication.py` (rounds 1 and 2) and
  `results/tables/extraction_validation*.{csv,json}`.
- **Results** are in `results/tables/`: `primary.json`, `signals_results.csv`, `pipeline_check.csv` and
  `null_sensitivity.json`.
