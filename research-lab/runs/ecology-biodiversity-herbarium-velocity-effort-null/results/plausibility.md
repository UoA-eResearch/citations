# Plausibility gate (G3)

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| median observed centroid velocity | 6.906 km/yr (69,596 species, at least 10 cells per period); 6.636 km/yr at 5 cells (101,328 species) | Daru et al. report 5.6 km/yr for 109,242 species (ledger A1) | yes | about 20% higher; different names (GBIF keys, not WCVP), no native-range restriction, and a newer snapshot |
| species count | 188,600 with at least one cell per period; 101,328 at 5 | 109,242 (Daru et al.) | yes | their threshold is not stated; ours brackets it between 3 and 5 cells |
| records kept after cleaning | 30,622,400 of 35,526,014 | Daru et al. used 16.2M after native-range filtering | yes | 3.0M records have no species key (rule 7) |
| noise-only null median | 2.797 km/yr | positive by construction: displacement between two random halves of a fixed sample; synthetic fixed-range species give about 1 km/yr for 300 km ranges (code/test_velocity.py) | yes | |
| effort null reproduces a pure effort shift | 97% (synthetic) | should approach 100% if the sampler is right (D1) | yes | the planned sampler gave 66% |
| exceedance of the null 95th percentile | 36.0% of species | 5% if every range were fixed; synthetic fixed ranges give 7.5% of 40 | yes | a real signal in a minority of species |
| effort weights falling back to theta = 1 | 0.003% of records | small: 1-degree cells with no other species' units in either period | yes | |

## 2. Three units traced end to end (`code/handtrace.py`, seed 20261026; `results/tables/handtrace.json`)

The trace recomputes cleaning rules 1-4 with plain pandas from the raw extract, then thinning, spherical-mean centroids
and haversine velocity independently of velocity.py.

| unit | raw input | intermediate values | output | matches the pipeline? |
|---|---|---|---|---|
| species 3157552 | 75 raw records in the snapshot extract | 68 after rules 1-4 (plain pandas), 68 in clean.parquet; 10 / 10 thinned cells; centroids [-15.2416, -39.3161] -> [-13.2523, -38.853] | 8.0989 km/yr (trace) vs 8.0989 (table); null median 1.8943, p95 4.0988 | yes, exactly |
| species 2927719 | 355 raw records in the snapshot extract | 353 after rules 1-4 (plain pandas), 353 in clean.parquet; 149 / 80 thinned cells; centroids [42.6232, -112.3338] -> [40.9451, -111.8457] | 6.8191 km/yr (trace) vs 6.8191 (table); null median 2.5056, p95 4.7171 | yes, exactly |
| species 7388346 | 40 raw records in the snapshot extract | 39 after rules 1-4 (plain pandas), 39 in clean.parquet; 19 / 13 thinned cells; centroids [-19.3129, 29.4547] -> [-20.1233, 31.7873] | 9.2951 km/yr (trace) vs 9.2951 (table); null median 5.7969, p95 12.7593 | yes, exactly |

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| every extracted record is kept or dropped with a reason | `coverage.json` records_clean; `clean.py` asserts kept + dropped = input | yes: 30,622,400 + 4,903,614 = 35,526,014 (after D2) |
| every species in the population gets both nulls | `coverage.json` nulls_primary | yes: 69,596 of 69,596 |
| observed and null velocities share one code path | `velocity.shift` (observed = shift on the true assignment) | yes; `code/test_velocity.py` checks shift against brute force |
| per-period record counts are preserved in every replicate | `velocity.nulls` (n1 selected by argpartition) | yes by construction |
| the focal species' own units are removed from its effort weights | `velocity.weights` (leave-one-species-out) | yes (G1) |
