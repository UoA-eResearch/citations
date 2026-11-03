# A model ranks where antibiotic-resistance genes will be confirmed in new species about five times better than sampling effort, but cannot pick out first appearances at the top of its list; the preregistered fit was the one seed in ten that failed

*NCBI Pathogen Detection, 106 organism groups: 1.62 million isolates with uniform AMRFinderPlus calls, 264 species,
4,417 gene symbols. Candidate (gene, species) pairs not yet established by the end of 2022 were ranked for
appearance in 2023–2025. Two rankings were compared: a gradient-boosted model trained on the same task one period
earlier, and a sampling-effort null that knows only each gene's frequency and how many isolates of each species were
sequenced in the forecast window. Isolates are dated by collection, so this is a retrospective test, not a real-time
forecast. The plan was committed before any data were downloaded. This version follows an independent review that
returned "fix first" (deviation D3).*

**Verdict: H1 Refuted by the preregistered rule, but not robustly; H2 Inconclusive.**

- **H1 (the model's precision@100 is at least twice the null's): Refuted as preregistered, on a single fit that is an
  outlier.**
  - At the preregistered seed the model's precision@100 is **0.00** against the null's **0.033**. The ratio's 95%
    interval over gene resamples is 0 to 0.97, which meets the plan's refutation rule.
  - Refitted with nine other seeds and the same hyperparameters, the model scores **0.10 to 0.19**, three to six
    times the null. Ranked over the whole list, it beats the null at every seed: average precision **0.075 to 0.090**
    against **0.016**.
  - The review showed that the null's originally reported 0.08 came from rounding: its probability saturates at 1.0
    for thousands of candidates, and row order then decided its top 100. Computed exactly, and with ties scored by
    their expectation, it is 0.033 (D3).
- **H2 (ESM-2 protein embeddings add signal beyond co-occurrence and taxonomy): Inconclusive.** The paired
  difference in average precision at the preregistered seed is −0.005 (−0.013 to +0.001). By the plan's rule that is
  neither below zero nor within ±0.005; the first draft mislabelled it Refuted. Across ten seeds the embedding adds a
  little average precision at seven, +0.004 on average.
- **For genuine first appearances the model fails at the top of the list.** Under the preregistered variant, in
  which one isolate is enough to count as a first appearance, the model's precision@100 is about zero at nine of ten
  seeds, against the null's 0.044. Its average precision is still two to three times the null's (0.031–0.051 against
  0.018).
- **What the primary rule rewards.** It needs two isolates from different BioProjects, to exclude single outbreaks.
  Of its 847 emergences, 705 (83%) already had a carrier isolate collected before 2023, but only 316 (37%) had one
  deposited, and so public, by then. The contrast between the two rules suggests that much of the model's skill is in
  ranking confirmations of pairs that already existed, often unpublished at the cutoff.

## In plain terms

Genes that make bacteria resistant to antibiotics spread between species. We asked whether it is possible to
forecast which gene will turn up in which species next, using 1.6 million sequenced isolates that one pipeline has
annotated the same way. Any forecast has to beat a simple baseline that knows only how common each gene is and how
many samples of each species are being sequenced, since more sequencing finds more genes.

A machine-learning model beat that baseline clearly when the question was "which gene–species pairs will be
confirmed by two separate studies". Over the whole ranked list it did about five times better. But the single model
run we had committed to in advance happened to be the one of ten that did no better at the very top of its list.
Our first draft took that run at face value, and got the comparison wrong in the other direction too: a rounding
problem made the baseline look stronger than it is.

When the question is the first appearance of a gene in a species, with one isolate enough, the model does better
than the baseline across the whole list but almost never puts a true first appearance in its top 100. That contrast
suggests much of the model's skill is in spotting pairs that already existed but were not yet confirmed.

## What was asked

The lead (`bioinformatics-amr-gene-species-emergence-forecast`) asked whether first appearances of AMR genes in new
species can be forecast prospectively against an explicit sampling-effort null.
- **The uniform calls** come from AMRFinderPlus and its Reference Gene Catalog (Feldgarden et al., 2021).
- **The feasibility claim** comes from Ellabaan et al. (2021), who found dissemination partly predictable
  retrospectively.
- **The gap** is a calendar-time test against an effort null.

## How it was done

- **Corpus.** All 106 bacterial organism groups' metadata tables. Kept: isolates with a collection year in 1990–2025,
  a resolved species binomial and an AMR call field; acquired genes only.
- **Pairs and candidates.**
  - A pair is *established* in a year when two isolates from different BioProjects carry it.
  - *Candidates* at the 2022 cutoff are pairs not established by then, where the gene is established somewhere and
    the species has at least 20 isolates: 472,779 candidates, of which 847 emerged in 2023–2025.
- **The model.** Histogram gradient boosting over 14 features in four families: sampling effort, co-occurrence,
  taxonomy, and ESM-2 embedding similarity. It is trained on the 2019 → 2020–2022 task, with hyperparameters chosen by
  gene-grouped cross-validation (D2). After the review it was refitted with ten seeds at those hyperparameters (D3).
- **The null.** The probability that a gene at its pre-2023 frequency appears at least twice among the species'
  2023–2025 isolates. It is computed in log space so that it does not saturate (D3).
- **Scoring.** Precision@k is the exact expectation under random order within tied scores (D3). Intervals come from
  resampling candidates by gene, 2,000 times. The catalog-growth restriction (D1) and its sensitivity are reported.

## Results

| ranking (primary rule) | precision@100 | average precision | recall in the top 1,000 |
|---|---|---|---|
| sampling-effort null (exact) | 0.033 | 0.016 | 0.044 |
| model, preregistered seed | **0.00** | 0.076 | 0.16 |
| model, nine other seeds | 0.10–0.19 | 0.075–0.090 | 0.15–0.17 |
| model without the embedding, ten seeds | 0.06–0.23 | — | — |

| outcome rule (preregistered variants) | candidates / emergences | null precision@100 | model precision@100 | null / model average precision |
|---|---|---|---|---|
| two BioProjects (primary) | 472,779 / 847 | 0.033 | 0.00 (seed 1); 0.10–0.19 (others) | 0.016 / 0.075–0.090 |
| first isolate | 665,655 / 1,307 | 0.044 | ≈0 at 9 of 10 seeds; 0.13 at one | 0.018 / 0.031–0.051 |
| at least three isolates | 442,342 / 848 | 0.024 | 0.12 | 0.013 / 0.079 |
| all genes (D1 sensitivity) | 489,561 / 871 | 0.033 | 0.19 | 0.016 / 0.085 |

- **The preregistered fit's top 100 is unusual.** It is saturated (118 scores above 0.999), and 93 of its pairs are in
  two rarely sequenced species, with a median of 24 isolates in the window against 414 for pairs that emerged. No
  other seed does this, so it describes that fit, not the model.
- **The null is flat at the top.** Its precision is 0.033 at both 100 and 500. It cannot order the thousands of
  candidates in large, well-sequenced species, and its probabilities are badly calibrated: its top decile predicts
  0.47 against an observed 0.011.
- **Literature check (the model's 20 highest-ranked true emergences):** 15 of 20 are co-mentioned with their species in at least one Europe PMC
  record before 2023, but most in only one or two records, and a co-mention does not show the gene was found in that
  species (`epmc.csv`). By the plan's definition these were foreseeable from the literature; the evidence is thin.

## What this does and does not show

- **The model beats sampling effort at ranking confirmations.** On average precision and recall it does so at every
  seed and under every rule except first appearance, by three to six times. That is the robust finding.
- **The preregistered H1 is refuted only by a fragile statistic.** Precision@100 on 847 positives among 472,779
  candidates moves from 0.00 to 0.19 between seeds. A single fit should not have been the primary test; the review
  caught this, and the verdict is reported with that caveat rather than changed.
- **Genuine first appearances are not forecast at the top of the list.** No model put a first appearance in its top
  100 at nine of ten seeds.
- **The embedding's role is unclear.** It neither clearly helps nor clearly hurts. The first draft's claim that it
  "breaks the model" described one seed and is withdrawn.
- **Limits.**
  - **Retrospective, not real-time.** 45% of isolates collected by 2022 were deposited after 2022, so the features
    and labels use data that were not public at the cutoff (D3).
  - **Observation is not emergence.** The effort null addresses sampling only in part.
  - **The model is not the lead's.** It is gradient-boosted trees over engineered features, not a temporal graph
    network.
  - **Coverage.** Pathogen Detection covers chosen, mainly clinical and foodborne, pathogens. Dates are by year;
    599,000 isolates had no usable year and 722,000 no AMR call field.
  - **Not run.** The gene × country variant was not run (D3).
- **Not shown:** that richer features (plasmid context, geography, host) would forecast first appearances; anything
  about clinical risk.

## Process and deviations

- **Preregistration:** `plan.md`, committed before any data were downloaded.
- **Deviations** (`deviations.md`):
  - D1: catalog-growth restriction (decided with 2023–2025 counts in view; its sensitivity is reported);
  - D2: hyperparameter rule;
  - D3: fixes after review, covering the exact null, seeds, the plan's verdict rules, the missing secondaries,
    deposit dates and gates.
- **Gates:**
  - G1: in the plan; see D3 for the deposit-date limit.
  - G2: `results/tables/coverage.json`.
  - G3: `results/plausibility.md`.
  - G4: `results/tables/g4_check.csv` (30 of 30 pairs recomputed independently from the raw metadata).
  - G5: `review/overclaim_check.md`.
  - G6: `results/attribution_ledger.csv`.
  - G7: does not apply.
- **Independent review:** fix first (12 findings); fixes in D3; confirmation pass pending.

## Reproducing it

1. `code/list_groups.py`, then download the metadata tables listed in `data/groups.csv`.
2. `code/build.py`, `taxonomy.py`, `proteins.py` and `embed.py`.
3. `code/candidates.py` for the train and test tasks, with `RULE=any`, `RULE=3` or `KEEP_ALL_GENES=1` for the
   variants (`d3_prep.py` first, for `RULE=3`).
4. `code/analyse.py`, `posthoc.py`, `variant_any.py`, then `d3_fixes.py`, `hindsight.py`, `g4_check.py`, `epmc.py`
   and `coverage_report.py`.
