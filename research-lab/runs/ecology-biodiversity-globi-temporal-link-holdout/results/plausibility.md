# Plausibility gate (G3) — added in D2 (the study predates METHODS.md)

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| effort AUROC with uniform negatives | 0.9509 random, 0.8801 temporal | high: most random species pairs are implausible, and degree separates them | yes | |
| effort AUROC with degree-matched negatives | 0.5009 random, 0.514 temporal | about 0.5 by construction, if degree is matched | yes (after D2) | the first version's broken sampler gave 0.682 and 0.568 |
| negatives' mean log degree product, matched sampler | within 0.13 of the positives' in every class and holdout | equal if matched | yes | `degree_matched_sampler` in primary.json |
| share of temporal positives from one dataset | 44.7% (trophiCH) | a few large data products dominate GloBI growth | flagged | inferred links (D2) |
| records kept by the build | 13.7M of 20.0M (v0.6), 8.1M of 24.5M (v0.11) | species-level, class-mapped records only | yes | `coverage.json` |

## 2. Three units traced end to end

The independent review recomputed these from the raw files (`review/reviewer_checks/`):

| unit | raw input | intermediate values | output | matches the pipeline? |
|---|---|---|---|---|
| raw record counts | v0.6 and v0.11 interactions.tsv.gz | line counts minus header against DuckDB rows read, with store_rejects | 19,981,541 and 24,453,954 rows, 0 rejects | yes |
| weighted AUROC | the study's scores and bootstrap weights | `model.auroc` against sklearn's weighted roc_auc_score | equal to 1e-15 | yes |
| re-resolved positives | verbatim names and taxon IDs behind every positive | 1.1% have a v0.6 record behind them; all 2,077 verbatim matches were genus-level in v0.6 | A_temporal 0.0662 to 0.0658 without them | yes, negligible |

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| every raw record is kept or dropped with a reason | `coverage.json` build_v0.6, build_v0.11 | yes |
| temporal positives are absent from the v0.6 class graph | model.py evaluate (index isin) | yes |
| negatives exclude edges in either snapshot | model.py forbid sets | yes |
| degree-matched negatives fill every decile, without replacement | MATCH_REPORT (decile_fill all 1.0) | yes (D2) |
