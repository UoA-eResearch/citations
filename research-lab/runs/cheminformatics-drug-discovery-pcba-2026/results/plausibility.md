# Plausibility gate (G3)

## 1. Headline numbers against expectation

| quantity | value | expectation and source | plausible? |
|---|---|---|---|
| LIT-PCBA evaluation compounds with a training neighbour above Tanimoto 0.4 | 89% | the 2025 audit (ledger L1) reports pervasive analog overlap and 2D-identical ligands across splits | yes, and it quantifies the audit's claim |
| memorization EF1% on LIT, random split | 27.8 | the audit's point: a parameter-free baseline competes with published methods | yes |
| memorization EF1% after the analog audit | 3.5 (LIT), 2.4 (PCBA-2026) | close to the 1.0 of a random scorer | yes |
| ECFP4 + RF against pretrained embeddings | RF ahead on both benchmarks | fingerprints matching or beating learned representations is widely reported (lead's lit_against) | yes |
| EF1% of a random scorer | 1.0 by construction | definition | verified in the metric unit test |
| BEDROC at α = 20 | 1.0 perfect, 0.0 worst, about 0.05 random | Truchon & Bayly | verified after the implementation was corrected (D2) |

## 2. Three targets traced end to end

| target | assay | compounds / actives | Butina clusters | evaluation kept after the audit | near neighbours before → after | hit rate / EF1% ceiling | EF1% memorization / RF |
|---|---|---|---|---|---|---|---|
| SNCA | AID 1671194 | 126,930 / 224 | 5,996 | 4,506 (78 actives) | 0.92 → 0.01 | 1.73% / 58 | 2.6 / 3.9 |
| ALOX12 | AID 1671190 | 474,716 / 5,938 | 11,449 | 7,203 (184 actives) | 0.86 → 0.07 | 2.55% / 39 | 5.4 / 13.6 |
| SYK | AID 1963824 | 5,843 / 2,864 | 2,962 | 4,040 (2,285 actives) | 0.32 → 0.01 | 56.6% / 2 | 1.4 / 1.7 |

SYK is the D2 case: a counterscreen where more than half the library is active, so EF1% cannot exceed about 2 and
no method can look good. It is kept in the preregistered analysis and excluded from the post hoc 19-target subset.

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| the analog audit leaves almost no evaluation compound with a training neighbour above 0.4 | folds_new.csv, folds_lit.csv | yes: median 3.2% (new) and 4.4% (lit), against 62% and 89% before |
| the size cap preserves each target's hit rate | subsample_check.json | yes: 1.30%→1.16%, 0.76%→0.77%, 0.79%→0.79% on the three largest |
| EF1% never exceeds min(100, 1/hit-rate) | metrics.csv | yes |
| every target scores all five methods on the primary split | coverage.json `scored_targets` | yes |
| substances in = kept + dropped, with reasons | coverage.json `substances` | yes (1,574,697 + 194,794 = 1,769,491) |
