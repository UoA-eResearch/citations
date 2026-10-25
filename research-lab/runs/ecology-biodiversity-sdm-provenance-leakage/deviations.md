# Deviations from plan.md

None yet. Notes before any overlap or model result:

- The lead lists a Czech Vegetation Database dataset (5b514765) among GBIF republications; it is not in SAGE's download, so
  Czechia_nvd plots have no provenance-shared GBIF dataset.
- 953 of the 11,621 download datasets (4.7M records) returned no registry metadata through the search pages; their titles
  were screened with the same patterns, which found one broad-tier candidate (Taiwan).

## D1 (2026-10-25 18:21 NZDT; implementation details settled before any RF result; the H2 audit had been run)

1. **Evaluation unit.** SAGE evaluates on 1 km evaluation cells (53,336, aggregating 77,444 plot records), not single
   plots.
   - "Source plots" are therefore *source cells*: test cells with at least one plot from a core-flagged source
     database (7,466 test cells).
   - H2's bootstrap resamples cells.
   - A cell with plots from several databases counts for each in the by-source breakdown.
2. **Training subsample.** SAGE's RF configuration (configs/data/datamodule.yaml) restricts training presences and
   backgrounds to its occurrence subsample (train_indices_10000_1km.npy, 3.27M of 4.10M cells). This is applied
   before the 10,000 caps, as in SAGE's get_data. 99.5% of provenance-only presences lie in the subsample.
3. **Background construction** follows SAGE exactly: in-range training cells minus the *capped* presences.
   Random draws are seeded per species (SAGE uses one global stream).
4. **Matched random removal** is drawn per species and majority GBIF country of the cell, over all species (not only
   the RF population), so that emptied cells are comparable.
   - Shortfall: 145,229 of 1,115,257 presences (13%) could not be matched. These are mainly species-country groups,
     such as Dutch ones, with fewer non-provenance presences than provenance-only ones.
   - Emptied cells: 4,923 for C1 and about 9,700 per random draw.
5. **Exact-coordinate audit:** a core record of the same species within 10 m of a source plot in the same cell,
   with the same date for the date share.
6. **Fit cache.** A condition that leaves a species' presences and background unchanged reuses that species'
   seeded C0 fit (identical inputs give identical fits).

## D2 (2026-10-25 19:11 NZDT; RF retraining running, no RF result read) — lab quality gates adopted today (METHODS.md)

**G1 leakage audit.** Fields that correlate with the outcome, and how the pipeline is kept blind to them:
- **Evaluation targets and test-cell membership** (SAGE's fixed test_indices.npy) enter only the scoring step.
  Models see training cells and the target-group background only.
- **Spatial co-location of training and evaluation records** is the leak under study. It is measured by the audit
  and removed by C1.
- **Provenance flags** were decided from GBIF registry metadata alone and frozen (commit before any overlap) without
  reference to evaluation overlap.
- **Matched random removal** draws from the same species and countries, so data loss is not confounded with
  provenance.
- **Species ordering and fit caching** cannot leak labels: the cache key hashes only the training inputs.
- No LLM or agent judges any unit, so no order-swap probe is needed.

**G2 coverage.** analyse.py now writes `results/tables/coverage.json`: per AUROC subset, fits completed and species
with an undefined AUROC, which the contrast drops. No statistic changes.

**Remaining gates.** G3 (`results/plausibility.md`), G5 (overclaim check) and G6 (attribution ledger, starting
with the lead's claims; its Czech Vegetation Database claim is already known to be false) run before review. G4 and
G7 do not apply, as there is no labelling or classifier validation.

## D3 (2026-10-26 06:24 NZDT; after the H1 and H2 results)

- **Job order (execution only).** At 2026-10-25 18:42, before the fit run started (18:45), `rf.py fit` was changed to
  run every species' C0 first, so that unchanged conditions could reuse the seeded C0 fit under parallel workers.
  Fits are seeded and cached by input hash, so order cannot change any result. The change was not committed before
  the run; it is committed now.
- **POST HOC 1, distance to plots** (`code/posthoc_distance.py`, `results/tables/posthoc_distance.json`).
  - Asked after seeing the TAVA effect: are the co-located flagged records copies of the evaluated plots?
  - Measures, per source database, the minimum distance from the species' flagged records to the database's plots in
    the cell, against the same number of records placed at random in the cell (20 draws).
  - Also measures the share of co-located presences that C1 actually removes.
  - Result: flagged records are no closer to the plots than random points (TAVA median 375 m against 357 m; plots
    located to 5 m). Removed by C1: Netherlands 41%, TAVA 91%, Ukraine 82%.
  - The draft read this as "not duplicated plots". The same script's later date check (same day, any distance:
    Netherlands 79%, Ukraine 84%; TAVA undated on the GBIF side) and POST HOC 4 showed that reading was wrong. The
    two copies of a relevé carry different coordinates, so distance cannot detect duplication.
- **POST HOC 2, removal shortfall** (`code/posthoc_shortfall.py`, `results/tables/posthoc_shortfall.json`).
  - The random arms removed 24.4 presences per species against C1's 29.2.
  - Restricted to the 1,690 species where random removal reached 90% of C1's, the DiD is +0.0052 (+0.0039 to
    +0.0067), against +0.0063 for all species.
- **POST HOC 3, co-location by SAGE training presence** (`code/posthoc_h2_training.py`,
  `results/tables/posthoc_h2_training.json`).
  - Asked after the G3 audit trace (`code/handtrace_audit.py`) found a Dutch test presence with four flagged snapshot
    records in its cell but no SAGE training cell there.
  - H2 counts snapshot records, as planned, so it is an upper bound on co-location with SAGE's actual training data.
  - Split: flagged snapshot record 8.3%; and a SAGE training presence 6.1%; and provenance-only 3.9%. A SAGE training
    presence from any source: 26.6%. TAVA: 87.4%, 84.0%, 79.9%, 84.5%.
  - H2's verdict (Refuted) is unchanged; the tighter counts are lower.
- **POST HOC 4, same relevé by species list** (`code/posthoc_same_releve.py`, `results/tables/posthoc_same_releve.json`).
  - Single-plot dated source test cells, comparing the plot's species list (the cell's evaluation targets) with the
    database's flagged GBIF records in the cell.
  - TAVA: 107 cells, median recall and precision 1.0, 87% with both at least 0.8, 8 species on each side. The test
    plots are in the training data.
  - Netherlands, same-day records: 464 cells, recall 1.0, precision 0.42.
  - Ukraine, same-day records: 24 cells, recall 0.73, precision 0.39.
- **G3:** `code/handtrace.py` refits two species under C0 and C1 in a fresh process, bypassing the cache; both
  reproduce the stored AUROC exactly. `results/plausibility.md` records this.
- **Figure:** `code/figures.py` (F1).
- No preregistered statistic or verdict changed.
