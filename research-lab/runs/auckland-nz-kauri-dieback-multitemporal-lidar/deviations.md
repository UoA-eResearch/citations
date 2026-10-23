# Deviations from the preregistration

The Overpass track query failed twice (a 502 and a truncated read). It succeeded on retry, and the response is cached in
data/raw/osm_tracks.json. `features.py` was edited once after its pre-computation commit, to add that retry; nothing
else changed.

## D1 — 2026-10-23 15:39 NZDT — changes after the independent review (review/review.md, "fix first")

1. **Duplicate merge.** The plan merges records within 2 m that have the same status. The code instead kept one
   record per 2 m grid cell, which leaves neighbours across a cell edge unmerged. The merge is now single-linkage
   within 2 m, by status. Records at the same place with different statuses are kept and counted.
2. **The AUC estimator.** The pooled out-of-fold AUC is biased downward under blocked cross-validation:
   - positives sit in 73 of 242 blocks, and test folds hold 18–110 positives;
   - a within-block label shuffle gives a pooled AUC of 0.36, not 0.5.

   **The fix.** AUC is computed within each test fold and averaged over folds and repeats. Its interval comes from a
   bootstrap over blocks of the per-fold AUCs, and the gain is paired. Every model is also compared with a
   within-block shuffle null (200 shuffles), so "chance" means that null. The verdict rules are unchanged.
3. **Wording:**
   - trees are dropped by the slip mask, not for invalid LiDAR;
   - the between-epoch canopy rise is height-dependent, which is consistent with a point-density difference;
   - 2014–15 positives and negatives are co-located at the feature scale, so the test is of this label geometry;
   - the 2021 contrast is not separable from a place effect.
