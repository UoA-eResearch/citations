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
