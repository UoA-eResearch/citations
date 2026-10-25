# Plausibility gate (G3) — added after review (the study predates METHODS.md; the review found G3 missing)

Numbers are for the final D1 segmentation: dip changes and station data gaps of more than 90 days.

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| dv/v range of scored pairs | 119 of 117,718 scored-pair days (0.1%) at the ±2% grid edge | hydrological dv/v is typically ≤0.1–0.5% (Sens-Schönfelder & Wegler 2006) | yes after D1 | before D1, 3.0% of all rows sat at ±2% (KBAZ polarity flip and dead-channel block; review finding 1) |
| grid-edge rows overall | 3,103 (1.7%), almost all in unscored low-coherence pairs | noise-dominated days hit the grid edge | yes | excluded from scoring by the coherence filter |
| month-scale wander (2 SD, 30-day smoothing) | no model 0.077%; season-only residual 0.075%; model residual 0.088% | measurement precision at Piton de la Fournaise better than 0.1%; precursors of order 0.05% (Brenguier 2008) | yes | the v1 0.136% was inflated by the KBAZ artefacts |
| median held-out R² | −0.08 (−0.19 to −0.01); 7-day-gap sensitivity −0.27 | a model that tracks hydrology would give > 0; season-only gives −0.02 | yes | same direction in every variant |

## 2. Three units traced end to end (`code/handtrace.py`, seed 20261025; `results/tables/handtrace.json`)

| unit | raw input | intermediate values | output | matches the pipeline? |
|---|---|---|---|---|
| ETAZ-WTAZ 2013-11-06 | daily .npz correlations, 0.5–2 Hz, symmetric fold | reference from 2,917 training days, 11-day stack | dv/v -0.035% (trace) vs -0.035% (table); cc 0.896 vs 0.896 | yes, exactly |
| AWAZ-EPAZ 2023-07-09 | daily .npz correlations, 0.5–2 Hz, symmetric fold | reference from 2,855 training days, 11-day stack | dv/v -0.085% (trace) vs -0.085% (table); cc 0.797 vs 0.797 | yes, exactly |
| AWAZ-RVAZ 2015-10-20 | daily .npz correlations, 0.5–2 Hz, symmetric fold | reference from 2,336 training days, 11-day stack | dv/v +0.150% (trace) vs +0.150% (table); cc 0.608 vs 0.608 | yes, exactly |

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| every attempted pair-day is ok or dropped with a reason | `coverage.json` (`tools/coverage.py` raises otherwise) | yes: 186,439 ok of 200,667; drops: segment with < 60 training days 9,360; negative zero-stretch correlation 2,346; outside segments 1,232; dead channel 852; < 5 days 438 |
| segments break on dip change and data gaps > 90 days | `code/dvv.py` segments(); `results/tables/segments.csv` | yes: KBAZ splits at 2014-08-25 and 2018-03-21 |
| no dead-channel day enters a reference or a stack | `code/dvv.py` (dead days removed from `have`) | yes |
| held-out windows use only segments seen in training | `code/model.py` (np.isin check) | yes |
