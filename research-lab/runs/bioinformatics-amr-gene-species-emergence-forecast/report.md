# For first appearances of antibiotic-resistance genes in new species, sampling effort beats a trained model at the top of the list; for confirmations, the model ranks about four times better overall

*NCBI Pathogen Detection, 106 organism groups: 1.62 million isolates with uniform AMRFinderPlus calls, 264 species,
4,417 gene symbols. Candidate (gene, species) pairs not yet established by the end of 2022 were ranked for
appearance in 2023–2025. Two rankings were compared: a gradient-boosted model trained on the same task one period
earlier, and a sampling-effort null that knows only each gene's frequency and how many isolates of each species were
sequenced in the forecast window. Isolates are dated by collection, so this is a retrospective test, not a real-time
forecast. The plan was committed before any data were downloaded. This version follows an independent review and a
confirmation pass that both returned "fix first" (deviations D3 and D3b), and a second confirmation pass (publish with
edits; D3c).*

**Verdict: H1 Refuted by the preregistered rule; H2 Inconclusive.**

- **For genuine first appearances the effort null wins at the top of the list.** Under the preregistered variant, in
  which one isolate is enough to count as a first appearance:
  - the null puts about **15 true first appearances in its top 100** (precision 0.150);
  - the model puts none at nine of ten seeds;
  - over the whole list, the model's average precision is 1.4–2.4 times the null's.
- **H1 (the model's precision@100 is at least twice the null's): Refuted.**
  - At the preregistered seed the model scores **0.00** against the null's **0.070** (ratio 0, 95% interval 0 to
    0.50).
  - That fit is the worst of ten. At the other nine seeds the ratio is 1.4–2.7, and five clear the 2× bar.
- **For confirmations the model is better overall.** Under the primary two-BioProject rule, its average precision is
  **3.7–4.4 times** the null's at every seed (0.075–0.090 against 0.021).
- **H2 (ESM-2 protein embeddings add signal): Inconclusive.**
  - The paired difference in average precision is −0.005 (−0.013 to +0.001). The first draft mislabelled this
    Refuted.
  - Across seeds the embedding adds a little at seven of ten.
- **What the primary rule rewards.** It needs two isolates from different BioProjects. Of its 847 emergences, 705
  (83%) already had a carrier collected before 2023, but only 316 (37%) had one deposited, and so public, by then. The
  contrast between the two rules suggests that much of the model's skill is in ranking confirmations of pairs that
  already existed, often unpublished at the cutoff.
- **The scoring of the null was fixed twice.**
  - Its probability saturates at 1.0 for thousands of candidates, and row order then decided the first draft's 0.08.
  - The first fix (log P of two or more) saturated at 0.0 in the same place and gave 0.033.
  - The second fix (log P of at most one, via `logcdf`) still underflowed for about 200 of the most heavily
    sequenced candidates, which tied them.
  - Computed in closed form, log P(≤1) = (n−1)·log1p(−f) + log1p((n−1)·f), the score stays finite. The null then
    has 988 distinct scores in its top 1,000 and precision@100 0.070 (D3c).

## In plain terms

Genes that make bacteria resistant to antibiotics spread between species. We asked whether it is possible to
forecast which gene will turn up in which species next, using 1.6 million sequenced isolates that one pipeline has
annotated the same way. Any forecast has to beat a simple baseline that knows only how common each gene is and how
many samples of each species are being sequenced.

For a gene's very first appearance in a species, it does not: the baseline puts about 15 real first appearances in
its top 100 guesses, and the trained model almost never puts any. Where the model does better, about four
times better over its whole list, is in predicting which gene–species pairs will be confirmed by a second, separate
study. Many confirmed pairs had already been sampled before the cutoff, often not yet published.

Our first draft got several things wrong. It relied on the one model run, of ten, that did worst. It also scored the
baseline in a way that let the order of rows in a file decide its result. An independent review caught both.

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
  2023–2025 isolates. It is computed in closed form as −log P(≤1) = −[(n−1)·log1p(−f) + log1p((n−1)·f)], which stays
  finite for every candidate (D3c).
- **Scoring.** Precision@k is the exact expectation under random order within tied scores (D3). Intervals come from
  resampling candidates by gene, 2,000 times. The catalog-growth restriction (D1) and its sensitivity are reported.

## Results

| ranking (primary rule) | precision@100 | average precision | recall in the top 1,000 |
|---|---|---|---|
| sampling-effort null | 0.070 | 0.021 | 0.059 |
| model, preregistered seed | **0.00** | 0.076 | 0.16 |
| model, nine other seeds | 0.10–0.19 | 0.075–0.090 | 0.146–0.182 |
| model without the embedding, ten seeds | 0.06–0.23 | — | — |

| outcome rule (preregistered variants) | candidates / emergences | null precision@100 | model precision@100 | model / null average precision |
|---|---|---|---|---|
| two BioProjects (primary) | 472,779 / 847 | 0.070 | 0.00 (preregistered seed); 0.10–0.19 (others) | 3.7–4.4× |
| first isolate | 665,655 / 1,307 | **0.150** | ≈0 at 9 of 10 seeds; 0.13 at one | 1.4–2.4× |
| at least three isolates | 442,342 / 848 | 0.040 | 0.12 (3.0× the null) | 5.5× |
| all genes (D1 sensitivity) | 489,561 / 871 | 0.070 | 0.19 | 4.2× |

- **The preregistered fit's top 100 is unusual.** It is saturated (118 scores above 0.999), and 93 of its pairs are in
  two rarely sequenced species. No other seed does this.
- **The null ranks well but is badly calibrated.** It has 988 distinct scores in its top 1,000: precision 0.070 at k = 100 and 0.060 at
  k = 500, and recall 0.059 at k = 1,000. But its top decile predicts 0.47 against an observed 0.011.
- **Literature check (the model's 20 highest-ranked true emergences):** 15 of 20 are co-mentioned with their species
  in at least one Europe PMC record before 2023. Most appear in only one or two records, and a co-mention does not
  show the gene was found in that species (`epmc.csv`).

## What this does and does not show

- **The model beats sampling effort at ranking confirmations.** On average precision it does so at every seed and
  under every rule, by about four to five and a half times except for first appearances (1.4–2.4×). That is the robust finding.
- **The preregistered H1 is refuted only by a fragile statistic.** Precision@100 on 847 positives among 472,779
  candidates moves from 0.00 to 0.19 between seeds. A single fit should not have been the primary test; the review
  caught this, and the verdict is reported with that caveat rather than changed.
- **For genuine first appearances, sampling effort is the better forecaster at the top.** The null's top 100 holds
  about 15; no model put one there at nine of ten seeds.
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
  - D3b: fixes after the first confirmation pass (the null re-ranked by log P(≤1));
  - D3c: edits after the second confirmation pass (the closed-form null, which `logcdf` underflowed for about 200
    candidates, and the derived numbers).
- **Gates:**
  - G1: in the plan; see D3 for the deposit-date limit.
  - G2: `results/tables/coverage.json`.
  - G3: `results/plausibility.md`.
  - G4: `results/tables/g4_check.csv` (30 of 30 pairs recomputed independently from the raw metadata).
  - G5: `review/overclaim_check.md`.
  - G6: `results/attribution_ledger.csv`.
  - G7: does not apply.
- **Coverage (G2):** Coverage — isolates: 1,621,194/2,943,808 ok; 1322614 dropped (duplicate biosample 1682, no collection year, or outside 1990-2025 598704, no species binomial (with a valid year) 423, no AMR call field 721790, screened with a reference catalog older than the oldest audited one (D1) 15) · gene_symbols_with_a_reference_protein: 4,381/4,417 ok; 36 dropped (no protein in the catalog or FASTA 36) · embedding_feature_rows_test: 472,623/472,779 ok; 156 fallback (UNPLANNED (not in the plan): gene without an embedding (dfrA51) given a zero vector, cosine 0; 2 positives 156) · candidates_train_2019: 1,271/1,698 ok; 427 dropped (emerged but outside the candidate set (species under 20 isolates, or gene not yet established) 427) · candidates_test_2022: 847/1,116 ok; 269 dropped (emerged but outside the candidate set (species under 20 isolates, or gene not yet established) 269)
- **Independent review:** fix first (12 findings), fixes in D3; first confirmation pass fix first, fixes in D3b; second
  confirmation pass publish with edits, made in D3c.

## Reproducing it

1. `code/list_groups.py`, then download the metadata tables listed in `data/groups.csv`.
2. `code/build.py`, `taxonomy.py`, `proteins.py` and `embed.py`.
3. `code/candidates.py` for the train and test tasks, with `RULE=any`, `RULE=3` or `KEEP_ALL_GENES=1` for the
   variants (`d3_prep.py` first, for `RULE=3`).
4. `code/analyse.py`, `posthoc.py`, `variant_any.py`, then `d3_fixes.py`, `hindsight.py`, `g4_check.py`, `epmc.py`
   and `coverage_report.py`.
