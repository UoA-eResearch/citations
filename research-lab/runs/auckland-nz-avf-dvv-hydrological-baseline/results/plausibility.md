# Plausibility gate (G3) — added after review (the study predates METHODS.md; the review found G3 missing)

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| dv/v range of scored pairs | 99.95% of days within ±2%; 53 of 108,773 scored-pair days at the grid edge | hydrological dv/v is typically ≤0.1–0.5% (Sens-Schönfelder & Wegler 2006) | yes after D1 | before D1, 3.0% of all rows sat at ±2% (KBAZ polarity flip, dead-channel block; review finding 1) |
| grid-edge rows overall | 1,904 (1.1%), almost all in unscored low-coherence pairs (WIAZ, MKAZ; median cc 0.29) | noise-dominated days hit the grid edge | yes | excluded from scoring by the coherence filter |
| noise floor (2 SD, 30-day smoothing) | model residual 0.076%; held-out data about its mean 0.074%; season-only residual 0.067% | measurement precision at Piton de la Fournaise better than 0.1% (Brenguier 2008) | yes | the three floors agree once KBAZ is fixed; the v1 0.136% was inflated by the KBAZ artefacts |
| median held-out R² | −0.27 (−0.35 to −0.15) | a model that tracks hydrology would give > 0; season-only gives −0.08 | yes | same direction as v1 and the review's variants |

## 2. Three units traced end to end (`code/handtrace.py`, seed 20261025; `results/tables/handtrace.json`)

| unit | raw input | intermediate values | output | matches the pipeline? |
|---|---|---|---|---|
| ETAZ-HBAZ 2021-07-08 | daily .npz correlations, 0.5–2 Hz, symmetric fold | reference from 2,560 training days, 11-day stack | dv/v −0.040% (trace) vs −0.035% (table); cc 0.693 vs 0.694 | yes, within one fine-grid step (0.005%) |
| AWAZ-ETAZ 2014-12-23 | as above | 889 reference days, 11-day stack | +0.010% vs +0.010%; cc 0.838 vs 0.838 | yes, exactly |
| ETAZ-RVAZ 2019-01-26 | as above | 659 reference days, 11-day stack | −0.005% vs −0.005%; cc 0.515 vs 0.516 | yes |

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| every attempted pair-day is ok or dropped with a reason | `coverage.json` (`tools/coverage.py` raises otherwise) | yes: 170,723 ok of 200,667; drops: segment with < 60 training days 26,738; outside segments 1,232; negative zero-stretch correlation 959; dead channel 852; < 5 days 163 |
| segments break on dip change and data gaps > 7 days | `code/dvv.py` segments(); `results/tables/segments.csv` | yes: KBAZ splits at 2014-08-25 and 2018-03-21 |
| no dead-channel day enters a reference or a stack | `code/dvv.py` (dead days removed from `have`) | yes |
| held-out windows use only segments seen in training | `code/model.py` (np.isin check) | yes |
