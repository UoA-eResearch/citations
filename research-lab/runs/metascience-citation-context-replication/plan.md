# Preregistration: does early citing language predict replication failure?

Lead: `metascience-citation-context-replication` (research-lab/leads.json). Written 2026-10-01 and committed to git before
any citation context was collected or scored, and before any predictor was joined to a replication outcome.

Probes made before writing:

- **Literature search** (§1).
- **FLoRA / FReD** (FORRT; `output/flora_filtered.csv` and `output/FReD.xlsx` from github.com/forrtproject/FReD-data,
  FReD last updated 2026-02-01). Inspected:
  - column names and outcome codes;
  - numbers of pairs and originals;
  - the gap from original to replication year.
- **CC30k** (github.com/lamps-lab/CC30k): column names, label counts, three example negative contexts.
- **Semantic Scholar citations endpoint.** For 20 random originals: how many citing papers carry contexts (39%). No
  context text was read.
- **The local vLLM server** serves `nemotron_3_nano_omni`; the GPU has about 10 GB free.

Every later departure goes to `deviations.md` with a timestamp taken from `date`.

## 1. Background and gap

- **Predicting replication from the paper itself.** Yang, Wu & Uzzi (2020, PNAS) predicted replicability from paper
  text and metadata. Prediction markets and surveys do well too (Dreber et al.; Camerer et al.).
- **Replication outcomes change later citations.** Failed replications reduce later citations modestly (von Hippel 2023,
  PNAS; Schafmeister 2021). Non-replicable papers are cited more (Serra-Garcia & Gneezy 2021). Criticism rarely
  appears in citing text: across the Reproducibility Project: Psychology, the average paper drew 0.83 disputing
  citations in 2010-19 (scite). Hardwicke et al. (2021) documented citation patterns after contradictory replications.
- **Citation context as a reproducibility signal.** Obadage et al. (2024) linked citation contexts to ML
  Reproducibility Challenge outcomes in a small case study. CC30k (Obadage, Rajtmajer & Wu 2025) built 30,734 labelled
  contexts for reproducibility-oriented sentiment.
- **The gap.** Nobody has tested whether the community's citing language *before* a replication anticipates its
  outcome, across a large database of replications with known results.
- **Why it matters.** If it did, citation contexts would be a cheap early-warning signal for unreliable findings. If it
  does not, "the literature knew" narratives are post hoc.

## 2. Sample and outcome

- **Pairs.** FLoRA replication pairs (`type == replication`) with a DOI for the original.
- **Unit.** The original paper (DOI).
- **First replication.** The earliest `year_r` among the original's replications.
- **Outcome.** The coded outcome of the replications published in that first year.
  - "failed" = 1; "successful" = 0.
  - If first-year replications disagree, the majority decides; ties are "mixed".
  - "mixed" and other codes are excluded from the primary analysis. Sensitivity: "mixed" counted as failed.
- **Pre-replication window.** Citing papers with publication year < first replication year. The original must be
  published before that year.
- **Eligibility.** At least 5 citing papers with contexts in the pre-replication window. Sensitivity thresholds: 1 and 10.

## 3. Citation contexts and classifiers

**Contexts.** For every original, all citing papers are fetched from the Semantic Scholar Graph API
(`/paper/DOI:{doi}/citations`, fields `contexts, intents, year, isInfluential`, all pages). A citing paper counts if it
has a year and at least one context.

**Classifiers.** Each is scored on each context; a citing paper is negative if any of its contexts is negative.

- **C1.** SciBERT (`allenai/scibert_scivocab_uncased`), fine-tuned on CC30k's majority-vote labels (Positive / Negative
  / Neutral).
  - Split: 90/10 stratified.
  - Training: 3 epochs, learning rate 2e-5, max length 256.
  - The held-out 10% gives CC30k test metrics.
- **C2.** The local LLM (`nemotron_3_nano_omni`, via its OpenAI-compatible API), zero-shot.
  - Prompt: "Does this citation context express doubt about the reliability, replicability or validity of the cited
    work's findings (for example failed replications, contradictory results, methodological criticism)? Answer
    NEGATIVE, POSITIVE (explicit confirmation or successful replication), or NEUTRAL."
  - Temperature 0.
  - Moderate concurrency; the server is shared.

**Validation on psychology text.** Before any outcome is joined:

- **Sample.** 300 contexts drawn at random from the harvested contexts of the eligible originals, stratified to include
  150 that either classifier calls negative.
- **Labels.** Assigned by the analyst (the AI agent running this study), blind to the original's identity and
  replication outcome, with the prompt's definition. The labels are saved before the classifiers' outputs are shown
  side by side.
- **Primary classifier.** The one with the higher F1 for NEGATIVE (vs the rest) on this sample, provided that F1 is at
  least 0.5. If neither reaches 0.5, both are reported, and the study is labelled as limited by measurement.

## 4. Predictors

- **Primary predictor.** neg_share = negative citing papers / citing papers with contexts, in the pre-replication
  window.
- **Secondary predictors:**
  - neg_share in the first 3 years after the original (and before the first replication);
  - pos_share;
  - the negative count per 100 citing papers.
- **Baseline covariates:**
  - log(1 + number of citing papers in the window);
  - original publication year;
  - discipline group (psychology / economics and business / other, from the FLoRA journal and OpenAlex topics);
  - venue impact (OpenAlex source two-year mean citedness, log);
  - years from original to first replication.

  In the FReD subset, the original's log sample size and p-value category (< .001, < .01, < .05, ≥ .05 or not
  reported) are added (H3).

## 5. Hypotheses and tests

- **H1 (primary).** neg_share predicts failure with AUC ≥ 0.65.
- **H2.** Adding neg_share to the baseline logistic regression raises cross-validated AUC by at least 0.05. The
  cross-validation is 10-fold, stratified, repeated 20 times.
- **H3.** The same in the FReD subset, with the original sample size and p-value in the baseline.
- **Intervals.** 95% intervals come from 2,000 bootstrap resamples of originals. Cross-validation is repeated within
  each resample for H2 and H3; for speed, 200 resamples with 5-fold cross-validation.
- **Direction.** It is preregistered: a higher negative share predicts failure.

**Decision rules.**

| Hypothesis | Supported | Contradicted | Otherwise |
|---|---|---|---|
| H1 | AUC ≥ 0.65 and lower bound > 0.5 | upper bound < 0.65 | inconclusive |
| H2, H3 | gain ≥ 0.05 and lower bound > 0 | upper bound < 0.05 | inconclusive |

"Any signal" (H1 lower bound > 0.5; H2 lower bound > 0) is reported separately.

**Positive control, V1.** neg_share from citing papers published at least 1 year *after* the first replication should
predict the outcome, because citing papers then report the replication. If the post-replication AUC is not above 0.5
(lower bound), the pipeline cannot see replication-related language, and a null H1 is uninformative.

**Leakage sensitivity.** A window ending 2 years before the first replication, which removes preprint-era awareness.

## 6. Robustness

- Eligibility thresholds of 1 and 10 citing papers.
- "Mixed" outcomes counted as failed.
- Psychology-only originals.
- Originals published from 2000 onward.
- The other classifier.
- The share computed over contexts rather than citing papers.

## 7. Review and reporting

- An independent reviewer agent checks code, deviations and the draft before any verdict is stated.
- The report opens with an "In plain terms" section and reports every preregistered number.
- **Data and publishing.**
  - FLoRA/FReD, CC30k, Semantic Scholar and OpenAlex are open.
  - Citation contexts are not redistributed: only derived counts are committed.
  - The analyst's validation labels are committed, as context IDs and labels only.
