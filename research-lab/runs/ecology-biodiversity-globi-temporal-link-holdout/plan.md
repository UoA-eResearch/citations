# Preregistration: do species-interaction link predictors beat "who gets studied" on GloBI's future records?

Lead: `ecology-biodiversity-globi-temporal-link-holdout`. This plan is committed before any graph is built.

**Seen before this plan:**
- the GloBI Interpreted Data Products schema (92 columns);
- interaction-type counts in the first 3 million rows of the v0.6 file, which was corrupt and is being downloaded
  again;
- the Zenodo record metadata (sizes and MD5s) for v0.6, v0.7, v0.8, v0.9 and v0.11.

**Novelty.** A semantic OpenAlex search (2026-10-24) and the lead's own search found no snapshot-based temporal
holdout for GloBI link prediction. Related but different:
- Becker et al. 2022, a prospective host–virus validation;
- Strydom et al. 2022, RDPG with taxonomic transfer;
- Al-Sayegh & Gholoum 2026, a plausibility audit of GloBI records.

## 1. Data and graphs

- **Snapshots.** GloBI v0.6 (2023-08-25; Zenodo 8284068) is the past, and v0.11 (2026-09-10; Zenodo 22691479) the
  future. v0.8 (2025-01-13) gives a second, rolling origin.
  - The files are `interactions.tsv.gz` and `refuted-interactions.tsv.gz`, verified by MD5.
  - If v0.11 cannot be obtained intact, the GloBI depot's latest snapshot is used instead, recorded with its SHA-256
    and date (a deviation).
- **Records.** Records whose source and target both have a species name (`*TaxonSpeciesName`) are kept, with
  interaction types mapped to three classes. All other types are dropped, including interactsWith, adjacentTo and
  coOccursWith. Direction is normalised to consumer → resource, pollinator → plant, and parasite/symbiont → host.
  - **trophic:** eats, preysOn; eatenBy and preyedUponBy, reversed.
  - **pollination:** pollinates, visitsFlowersOf; pollinatedBy and flowersVisitedBy, reversed.
  - **host–parasite:** parasiteOf, endoparasiteOf, ectoparasiteOf, hemiparasiteOf, parasitoidOf, hyperparasiteOf,
    pathogenOf, hasHost; hasParasite, hostOf, hasPathogen and hasParasitoid, reversed.
- **Refuted records** (the snapshot's `refuted-interactions.tsv.gz`) are removed by (class, source species, target
  species).
- **Nodes and taxonomy.** Nodes are species names. Genus and family come from the v0.6 record's genus and family
  fields, the most common value per species. The same v0.6 taxonomy is used for v0.11.
- **The graph.** For each class, a bipartite graph G6 of distinct species pairs in v0.6.

## 2. Evaluation sets

- **The temporal holdout.**
  - **Positives:** (class, s, t) pairs in v0.11 that are not in v0.6, where s has an edge on the source side and t on
    the target side of G6 for that class. Each positive is tagged with its introducing dataset (the `sourceNamespace`
    with the most v0.11 records for the pair) and with whether that dataset already existed in v0.6.
  - **Negatives:** 10 per positive per class, drawn uniformly from (s, t) pairs on the same sides that are edges in
    neither snapshot.
- **The random holdout.**
  - 10% of G6's edges per class (seed 20261024) are hidden. Training uses the remaining 90%.
  - **Positives:** the hidden edges whose endpoints both keep at least one training edge.
  - **Negatives:** as above, from non-edges of v0.6.
- **Degree-matched negatives** (secondary): negatives drawn to match the positives' distribution over deciles of
  log(deg_s × deg_t).

## 3. Predictors

All are trained on the training graph only: the 90% graph for the random holdout, and all of G6 for the temporal one.

- **The supervised training set.** The supervised models learn from an inner split. 10% of training edges are labels;
  features come from the remaining 90%, with 10 uniform negatives per label. The models are then applied to
  evaluation pairs with features computed on the full training graph.
- **Effort baseline.** Logistic regression on four features: log(1 + degree) of s and of t in the training graph,
  and log(1 + number of distinct reference citations mentioning s / t in v0.6). GBIF occurrence counts are not used,
  because they cannot be frozen at the v0.6 date.
- **Structure: RDPG.** A truncated SVD (rank 32) of each class's binary training adjacency. The score is u_s · v_t,
  with nothing fitted beyond the SVD.
- **Structure + taxonomy: gradient boosting** (HistGradientBoosting, default settings, early stopping off) on:
  - the four effort features;
  - the RDPG score;
  - taxonomic-neighbourhood counts in the training graph: links from s to t's genus and to t's family, from s's genus
    to t, from s's genus to t's genus, and from s's family to t's family, excluding the pair itself.
- **"Best" structural predictor.** Whichever of RDPG and the boosted model has the higher pooled AUROC on the random
  holdout. It is then fixed for the temporal holdout.

## 4. Hypothesis and decision rule

- **The advantage.** A = AUROC(best) − AUROC(effort), with all classes pooled. The statistic is the ratio
  ρ = A_temporal / A_random.
- **The interval.** A cluster bootstrap over introducing datasets (B = 1,000, seed 20261024). Positives are resampled
  by their dataset, for the random holdout by the namespace of their v0.6 records, and negatives are resampled iid.
- **The precondition.** If A_random's lower bound is at or below 0, the structural predictor does not beat effort
  even in the random holdout, and H1 is not testable.
- **H1 (the advantage at least halves on the future): ρ ≤ 0.5.**
  - **Supported** if ρ's upper bound is below 0.5.
  - **Refuted** if its lower bound is above 0.5.
  - **Otherwise Inconclusive.**

## 5. Secondary (reported, not confirmatory)

1. AUROC and AUPR for every predictor, on both holdouts, pooled and per class.
2. Degree-matched negatives.
3. Temporal positives split by whether the introducing dataset existed in v0.6, and the share of growth from new
   datasets.
4. A rolling origin, v0.8 → v0.11, if v0.8 downloads intact.
5. Cold start: temporal positives where either endpoint has degree 1 in G6.

## 6. Limits stated in advance

- **New GloBI edges arrive in bulk from newly indexed datasets,** so the temporal holdout partly measures dataset
  composition (hence secondary 3).
- **Name resolution can change between versions.** Requiring both species in G6 by name removes new names but not
  re-resolved pairs.
- **The effort baseline** uses only GloBI-internal effort, because GBIF counts were dropped for leakage.
- **Negatives are unobserved pairs,** not known absences.

## 7. Outputs

- `results/tables/`: `graph_summary.json`, `eval_sets_summary.json`, `primary.json`, `per_class.csv`.
- `results/figures/`.
- `deviations.md` records any change before the results it affects.
