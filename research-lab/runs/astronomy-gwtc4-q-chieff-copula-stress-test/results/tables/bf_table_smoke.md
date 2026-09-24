| endpoint | model | reference | ln BF | description |
|---|---|---|---|---|
| E1 | copula_gauss_plp | copula_indep_plp | -0.17 | Gaussian copula dependence vs independence (PLP m1) |
| E3c | baseline_plp_both | baseline_plp_null | +0.07 | mean + width slopes vs null |
| E4c | baseline_bpq_both | baseline_plp_both | -0.86 | broken pairing vs power-law pairing |

| model | dims | ln Z | max ln L | inj n_eff (min/median) | frac var<1 | wall (min) |
|---|---|---|---|---|---|---|
| baseline_plp_both | 13 | -119.95 | -112.40 | 16/92 | 0.89 | 0.4 |
| baseline_plp_null | 11 | -120.02 | -111.73 | 16/85 | 0.88 | 0.3 |
| copula_gauss_plp | 19 | -120.26 | -111.24 | 16/75 | 0.72 | 0.5 |
| copula_indep_plp | 18 | -120.09 | -112.11 | 17/85 | 0.87 | 0.3 |
| baseline_bpq_both | 15 | -120.81 | -111.95 | 16/76 | 0.85 | 0.3 |
| copula_indep_splm1 | 18 | -124.55 | -115.40 | 17/137 | 0.98 | 0.4 |
