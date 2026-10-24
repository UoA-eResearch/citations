# Plan (preregistration): does provenance leakage inflate SAGE's presence-absence evaluation?

Lead: `ecology-biodiversity-sdm-provenance-leakage`. Written before any overlap between training records and
evaluation plots was computed and before any model was trained.

**Seen before this plan:**
- SAGE's paper abstract, code (cleaning, aggregation and RF scripts) and Zenodo README;
- the list of datasets in SAGE's GBIF download, with record counts;
- the evaluation plot metadata's source-database counts (89 GIVD databases; for example France_sophy 7,670 rows,
  Netherlands 1,090, Czechia_nvd 1,143).

No species-level, cell-level or AUROC quantity has been computed.

## 0. Question and hypotheses

SAGE trains on GBIF presence-only records and evaluates on sPlotOpen vegetation plots, assuming the two are
independent. Some GBIF datasets republish the very vegetation-plot databases that supply sPlotOpen plots.

- **H1 (causal, primary).** On test plots from provenance-shared source databases, removing provenance-shared
  training records lowers mean per-species AUROC by at least 0.02 more than removing an equal number of other
  training records of the same species in the same countries.
  - Statistic: DiD = mean over species of [AUROC(random removal, averaged over 5 draws) − AUROC(provenance removal)],
    with a species bootstrap (2,000 resamples).
  - **Supported** if DiD ≥ 0.02 and its 95% lower bound is above 0.
  - **Refuted** if the 95% upper bound is below 0.02.
  - **Inconclusive** otherwise.
- **H2 (audit).** At least 10% of test-plot presences (species × 1 km cell) from provenance-shared source databases
  have a provenance-shared training record of the same species in the same 1 km cell.
  - **Supported** if the share's 95% lower bound (bootstrap over plots) is above 10%.
  - **Refuted** if the upper bound is below 10%.
  - **Inconclusive** otherwise.

## 1. Data

- **SAGE processed benchmark** (Zenodo 21297133): 1 km training targets, predictors, target-group background index,
  native-range masks, evaluation targets, `eval_plot_metadata.csv` (GIVD_ID and Dataset per evaluation plot), and the
  fixed validation/test split from the SAGE repository (commit ce4a70e).
- **GBIF record attributes.**
  - SAGE's download (doi:10.15468/dl.jd7xfa) is served at about 60 KB/s and could not be fetched in reasonable time.
  - Instead, the same columns come from GBIF's public monthly Parquet snapshot of 2026-02-01, 19 days before that
    download was created: dataset key, species and taxon keys, coordinates, country, basis of record, date.
  - Rows are filtered with the download's own predicate (TAXON_KEY in its 5,863 keys) and with SAGE's two simple
    filters (cleaning_gbif.r): basisOfRecord in HUMAN_OBSERVATION, OBSERVATION, PRESERVED_SPECIMEN, and coordinate
    uncertainty at most 1 km or missing.
  - Records added after the snapshot are absent. SAGE presences without any snapshot record are treated as not
    provenance-shared, which biases toward the null.
- **GBIF registry metadata** for all 11,621 datasets in the download.

## 2. Provenance flags (frozen before step 3)

- **Core flag.** A GBIF dataset is core-flagged if its registry metadata (title, description, publisher, citation)
  identify it as a republication of a vegetation-plot database that supplies SAGE evaluation plots. Identification
  is by GIVD code, database name, or the database's custodian publishing its relevés.
- **Broad flag (sensitivity only).** Aggregators or atlases whose metadata say they include such relevés among
  other data (for example national flora aggregators).
- **Freezing.** Every flag decision is recorded with its evidence in `results/tables/provenance_flags.csv` and
  committed before any record-to-plot overlap is computed. "Source databases" means the GIVD sources with at least one
  core-flagged GBIF dataset, and "source plots" are test plots from those databases.

## 3. Mapping records to SAGE cells

- GBIF records are snapped to SAGE's grid with SAGE's own definition (geo_utils.py): EPSG:6933, cell = floor(x /
  1000 m), floor(y / 1000 m).
- A species × cell presence in SAGE's 1 km training targets is **provenance-only** if every snapshot record of that
  species (matched by GBIF species key to SAGE's name list) in that cell comes from core-flagged datasets.
  Presences with no matched record are not provenance-only.

## 4. Conditions and model

- **C0, original:** SAGE's 1 km training targets as distributed.
- **C1, provenance removal:** provenance-only presences are removed. A training cell that keeps no species is also
  removed from target-group backgrounds.
- **C2–C6, matched random removal (5 draws, seeds 1–5).** For each species and country (the majority GBIF country of
  the cell's records), remove the same number of presences as C1 removes. They are drawn at random among that
  species' presences in that country that are not provenance-only. Where too few exist, all are removed and the
  shortfall is reported.
- **Model.** SAGE's single-species Random Forest baseline, reimplemented from its code, with fixed settings:
  - imbalanced-learn BalancedRandomForestClassifier, 1,000 trees, max_features 7, sampling_strategy "all", no
    replacement;
  - presences capped at 10,000 (random, seed 0);
  - target-group background: in-range training cells minus presences, capped at 10,000;
  - SAGE's predictor normalisation; no location features; seed 0 in every condition.
- **Not done.** SAGE's per-species mtry tuning and multi-seed averaging are not repeated. The DeepSDM is not
  retrained (the GPU is occupied by a shared service).
- **Species population.** Species with at least 10 presences and at least 10 absences among range-masked source
  plots in SAGE's test split. If there are more than 2,000, a random 2,000 (seed 20261025) are used.
- **Evaluation.** Per-species AUROC on range-masked test plots, computed:
  - on source plots (primary);
  - on non-source plots;
  - on all test plots (secondary).

## 5. Secondary and descriptive

- H2 shares by source database and country.
- The exact-coordinate match share (record coordinates within 10 m of the plot) and the same-date share.
- The share of SAGE's training presences that are provenance-only, overall and per source country.
- The DiD by source database (only for databases with at least 50 species), and on non-source plots (expected near 0).
- A broad-flag sensitivity, for the audit only.

## 6. Limits stated in advance

- **Snapshot.** Snapshot records are not SAGE's exact download (19 days apart), and SAGE's cleaning
  (CoordinateCleaner and native-range filtering) is not replayed. A presence counts as provenance-only only if no
  unflagged snapshot record supports it, which biases toward the null.
- **Flagging.** Flagging is partly manual. Relevés republished through aggregators the metadata do not disclose will
  be missed.
- **Model.** RF with fixed mtry and one seed. Effects on the DeepSDM may differ.
- **Matching.** Random removal matches counts per species and country but not spatial structure. Some of the C1
  effect may come from losing systematic vegetation-plot sampling (legitimate domain similarity) rather than
  duplication. The exact-coordinate audit helps separate the two.
