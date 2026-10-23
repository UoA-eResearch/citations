# Species-interaction predictors beat "who gets studied" on GloBI's future records too: the taxonomic advantage grows, not shrinks, out of time

*GloBI's interpreted interaction snapshots: v0.6 (2023-08-25) as the past and v0.11 (2026-09-10) as the future.
Species-level trophic, pollination and host–parasite pairs. Three predictors: effort only (degree and citation
counts), a structural embedding (RDPG), and gradient boosting on taxonomic-neighbourhood features. Each is evaluated
on a random holdout within v0.6 and on 411,702 pairs first recorded in v0.11 between species already in v0.6. The plan
was committed before any graph was built.*

**Verdict: H1 Refuted.**

- **H1 (the structural advantage over effort at least halves on future records): Refuted.**
  - The best structural predictor, taxonomy + structure, beats effort by **+0.040 AUROC** on the random holdout
    (0.991 against 0.951; 95% cluster bootstrap +0.029 to +0.054).
  - On the temporal holdout it beats effort by **+0.068** (0.948 against 0.880; +0.053 to +0.075).
  - The ratio is **1.68** (1.10 to 2.30), against the hypothesis of at most 0.5.
- **What shrinks is effort.** Prior degree and citation counts lose 0.07 AUROC going from a random to a temporal
  holdout; the taxonomic model loses 0.04. Future records favour neither the most-studied species nor the bare
  network structure alone. The structural embedding by itself (RDPG) is worse than effort on both holdouts.
- **The edge holds where it matters most:**
  - for pairs introduced by datasets indexed after v0.6 (72% of the future pairs): 0.940 against 0.870;
  - for species with a single prior link: 0.882 against 0.718.
- **It grows with degree-matched negatives.** There effort falls to 0.568 on the temporal holdout and the taxonomic
  model stays at 0.850.
- **A caution on the records.** 26–42% of v0.6 species pairs, by class, are absent from v0.11 (name re-resolution and
  dataset changes), so some "new" pairs may be re-resolved old ones.

## In plain terms

Scientists use machine learning to guess which species interact, such as who eats whom, which insect pollinates which
plant, or which parasite lives on which host, so that field work can be pointed at likely pairs. A worry is that
these models mostly learn which species scientists already study a lot, and would be no better than simply betting
on well-studied species.

We used two archived snapshots of GloBI, a global database of species interactions, three years apart. We trained
models on the older snapshot and asked how well they picked out interactions that appeared in the newer one. A simple
"popularity" guess, based on how many interactions and studies a species already had, did well. A model that also
uses what related species do did clearly better, and its advantage was bigger on the genuinely new records than on a
random test drawn from the old snapshot. That held for interactions contributed by newly added studies and for
species that had been recorded only once before.

So in this database, taxonomy-aware prediction is not just repeating "who gets studied". The test has a caveat: the
database also renames species and changes its sources between versions, so some "new" records are old ones under
new names.

## What was asked

The lead (`ecology-biodiversity-globi-temporal-link-holdout`) asked whether species-interaction link predictors keep
their skill on genuinely later records, or mostly learn sampling effort. Prior work validates link prediction by
random edge holdout or single prospective cases, such as Becker et al. 2022 for bat betacoronavirus hosts. GloBI's
versioned snapshots allow a broad pseudo-prospective test, and none was found.

## How it was done

- **Data.** GloBI interpreted `interactions.tsv.gz` and `refuted-interactions.tsv.gz` for v0.6 and v0.11 (Zenodo),
  each MD5-verified. The v0.6 file needed a three-way chunk repair after corrupted downloads (deviations).
- **The graph.**
  - Records with species names at both ends are kept, with interaction types mapped to trophic, pollination and
    host–parasite, and direction normalised.
  - Refuted pairs are removed.
  - v0.6 has 427,844 trophic, 78,918 pollination and 356,050 host–parasite species pairs.
- **Positives.**
  - Temporal: pairs in v0.11 not in v0.6, with both species on the right sides of the v0.6 class graph.
  - Random: 10% of v0.6 pairs hidden.
  - Negatives are 10 per positive, uniform over non-edges in either snapshot.
- **Predictors.**
  - **Effort:** logistic regression on log degree and log citation counts of both species.
  - **RDPG:** a rank-32 SVD of the bipartite adjacency.
  - **Taxonomy + structure:** gradient boosting on the effort features, the RDPG score and five
    taxonomic-neighbourhood counts (links between the species and the other's genus or family, and genus–genus and
    family–family links).
  - The supervised models are trained on an inner split of the training graph.
- **The statistic.** ρ = A_temporal / A_random. A is the pooled AUROC, from within-class percentile ranks, of the best
  structural predictor (chosen on the random holdout) minus effort's. Intervals come from a cluster bootstrap over
  the positives' source datasets.

## Results

### AUROC by predictor and holdout (`results/figures/F1_auroc.png`)

![AUROC](results/figures/F1_auroc.png)

| | effort | RDPG | taxonomy + structure |
|---|---|---|---|
| random holdout, pooled (72,666 positives) | 0.951 | 0.942 | **0.991** |
| temporal holdout, pooled (411,702 positives) | 0.880 | 0.805 | **0.948** |
| temporal: trophic | 0.860 | 0.802 | 0.942 |
| temporal: pollination | 0.882 | 0.740 | 0.908 |
| temporal: host–parasite | 0.913 | 0.848 | 0.979 |

### Subsets of the future (`results/figures/F2_subsets.png`)

![Subsets](results/figures/F2_subsets.png)

| temporal positives | n | effort | RDPG | taxonomy + structure |
|---|---|---|---|---|
| from datasets new since v0.6 | 298,259 | 0.870 | 0.789 | 0.940 |
| from datasets already in v0.6 | 113,443 | 0.906 | 0.849 | 0.967 |
| cold start (an endpoint with one prior link) | 100,647 | 0.718 | 0.704 | 0.882 |
| all, degree-matched negatives | 411,702 | 0.568 | 0.748 | 0.850 |

- **Growth.** v0.11 has 827,885 new trophic, 199,350 new pollination and 386,201 new host–parasite pairs.
- **Eligible positives.** 26–36% of them join two species already in the v0.6 class graph and are the positives here.
- **Turnover.**
  - trophic: 112,825 of 427,844 v0.6 pairs are absent from v0.11;
  - pollination: 32,842 of 78,918;
  - host–parasite: 127,999 of 356,050.

## What this does and does not show

- **No collapse out of time.** On GloBI, a model that knows what related species do keeps, and widens, its lead over
  a sampling-effort baseline when predicting interactions recorded in the following three years. That holds for new
  data sources and for barely studied species.
- **Effort alone is strong** under uniform negatives (AUROC 0.88 on the future), because most random species pairs
  are implausible. Degree-matched negatives remove that and leave the taxonomic model well ahead.
- **Not shown:**
  - **True discovery.** New GloBI records include re-indexed literature and re-resolved names, not only newly
    observed interactions.
  - **Absences.** The negatives are unobserved pairs, not known absences.
  - **Embeddings.** node2vec-style embeddings were not tested; RDPG was the only pure-structure model.
  - **The v0.8 rolling origin**, not run (D1).

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - data acquisition (chunk-verified downloads);
  - D1: secondary 4 not run.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. Download and verify the four Zenodo files (MD5 in `deviations.md`).
2. `code/build.py 0.6`, then `code/build.py 0.11`.
3. `code/model.py`, with OMP_NUM_THREADS=8.
4. `code/figures.py`.
