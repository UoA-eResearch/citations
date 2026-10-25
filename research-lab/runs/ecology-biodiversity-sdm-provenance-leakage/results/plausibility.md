# Plausibility gate (G3)

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| per-species AUROC as distributed (C0), source cells | mean 0.854 (1,745 species) | 0.7–0.9 for presence-only SDMs tested on presence-absence plots (lab's prior; SAGE's abstract ranks Random Forest among the best models, its per-species AUROC appears only in figures) | yes | non-source cells 0.845, similar |
| provenance-only share of training presences | 2.0% (1.12M of 57.1M) | small: the flagged datasets hold 17.0M of the download's records, many in cells also recorded by others | yes | 897k of them in the Netherlands, the largest flagged dataset (9.9M records) |
| H2 co-location share | 8.3% overall; Netherlands 87.8%, TAVA 87.4%, France SOPHY 0.0% | high where a national database is republished whole, near zero where it is not | yes | SOPHY's flagged GBIF dataset holds only 77k records |
| H1 DiD on non-source cells | 0.000 (−0.0005 to +0.0005) | ≈ 0 if the effect is local to source cells | yes | placebo |
| largest per-species DiD | 0.38 | single species with few source presences can swing widely | yes | 53% of species positive |
| TAVA drop C0 → C1 | 0.836 → 0.685 | large only if the removed presences are a big share of the species' training data near the test cells | yes | hand-traced species 2924 loses 90 of 317 presences, AUROC 0.891 → 0.584 |

## 2. Three units traced end to end

| unit | raw input | intermediate values | output | matches the pipeline? |
|---|---|---|---|---|
| species 2924 (a TAVA West Africa species), C0 and C1 | SAGE training targets, subsample index, predictors, range-masked source test cells | presences 317 (C0) and 227 (C1); fresh BalancedRandomForest fit, cache bypassed (`code/handtrace.py`) | AUROC on source cells 0.8909 (C0), 0.5836 (C1) | yes, exactly (`results/tables/handtrace.json`) |
| species 1008 (random pick, seed 20261025), C0 and C1 | as above; presences capped at 10,000 in both conditions | the cap draws a different 10,000 after removal | AUROC 0.8647 (C0), 0.9017 (C1) | yes, exactly; shows why capped species can move either way |
| two Dutch test presences, H2 and C1 (`code/handtrace_audit.py`, seed 20261026) | GBIF snapshot rows for the species in the 1 km cell (`data/work/core`), SAGE's training targets | cell recomputed from coordinates in EPSG:6933 independently of cells.py; flagged dataset 740df67d (Dutch Vegetation Database); support counts | (1) eval cell 24460, species 5063: 1 flagged record, no other; SAGE training presence present; removed by C1. (2) seeded random pick: 4 flagged records, no other, but no SAGE training cell at that grid cell | yes for both: recomputed cells match and C1 status matches its definition. (2) showed that H2 counts records SAGE's own cleaning dropped (post hoc 3: 8.3% falls to 6.1%) |

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| every fit attempted is completed or dropped with a reason | `results/tables/coverage.json` (`tools/coverage.py`) | yes: 12,215 of 12,215; 609 undefined AUROCs on non-source cells only |
| C1 removes exactly the provenance-only presences | `results/tables/removals.json` vs `audit.json` | yes: 1,115,257 in both |
| random draws never remove more than C1 per species and country | `code/rf.py` removals (shortfall recorded) | yes: 145,229 presences short in every draw, none over |
| identical training inputs give identical fits | cache keyed on a hash of the inputs, seed 0 | yes: 1,178 reused fits; refits in the hand trace match exactly |
| test-cell labels enter only scoring | `code/rf.py` (G1 audit, D2) | yes |
