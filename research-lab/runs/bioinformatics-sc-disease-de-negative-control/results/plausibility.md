# Plausibility gate (G3)

## 1. Positive control: male against female healthy donors

The plan's control runs the same exceedance test on a comparison that is unambiguously real: male against female
normal donors in the largest primary dataset (brain oligodendrocytes, 144 male and 115 female donors, m = 115 per
group, 25 real draws against 200 label-permuted nulls).

| statistic | real median | null median | null 95th percentile | p | detected? |
|---|---|---|---|---|---|
| DE genes at BH FDR < 0.05 | 219 | 0 | 0 | 0.005 | yes |
| π1 | 0.102 | 0.010 | 0.243 | 0.254 | **no** |

A sex difference with 219 DE genes is exactly what a working test must find. The DE-gene count finds it; π1, the
preregistered primary statistic, does not. This is the same failure the synthetic power check shows, on real data,
and it is why the report leads with the DE-gene count (D2).

## 2. Synthetic power check (`results/tables/power_check.json`)

A twofold change injected into 5% of expressed genes in the pseudo-disease donors of 100 null draws across 20
contrasts, run through the identical pipeline and tested against each contrast's own null:

| statistic | power at p < 0.05 | injected median | null median |
|---|---|---|---|
| DE genes | 0.87 | 217 | 0 |
| mean abs logFC of the top 100 | 0.50 | 1.081 | 0.704 |
| π1 | 0.08 | 0.110 | 0.038 |

## 3. Three contrasts traced end to end

| contrast | disease / tissue / cell type | m per group | DE genes, full size | DE genes, matched real | null median / 95th | q | reading |
|---|---|---|---|---|---|---|---|
| c0760 | dementia, brain, L2/3-6 intratelencephalic neuron | 23 | 11,261 | 2 | 0 / 0 | 0.073 | a very large full-size result that the matched comparison does not reproduce; the full run uses every donor, the matched one 23 a side |
| c0289 | dementia or schizophrenia, brain, oligodendrocyte | 64 | 0 | 0 | 0 / 0 | 1.000 | nothing at either size |
| control_sex | normal, brain, oligodendrocyte (male vs female) | 115 | — | 219 | 0 / 0 | p 0.005 | the positive control above |

## 4. Headline numbers against expectation

| quantity | value | expectation | plausible? |
|---|---|---|---|
| null median DE genes | 0 | matched healthy donors should mostly give nothing | yes |
| null 95th percentile above 100 DE genes | 8.9% of contrasts | donor heterogeneity should sometimes be large | yes |
| median full-size DE genes | 52 | published single-cell contrasts commonly report tens to hundreds | yes |
| cross-study null-signature correlation | 0.03, against 0.30 for real pairs | matched nulls should not share a signature across studies | yes |

## 5. Invariants

| invariant | where | holds? |
|---|---|---|
| cells pseudobulked equal the Census metadata count per dataset | coverage.json `pseudobulk`; 43 of 43 datasets | yes |
| every counted donor is eligible and has at least 10 cells | coverage.json `contrast_donors` | yes |
| no contrast keeps more than 10% failed null fits | analyse.py drop rule | yes (none dropped) |
| real and null draws use the same group sizes within a contrast | draws.py; m per group | yes |
