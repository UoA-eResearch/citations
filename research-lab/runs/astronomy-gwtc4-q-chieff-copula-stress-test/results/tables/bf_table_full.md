| endpoint | model | reference | ln BF | description |
|---|---|---|---|---|
| E1 | copula_gauss_plp | copula_indep_plp | -0.20 | Gaussian copula dependence vs independence (PLP m1) |
| E3a | baseline_plp_mean | baseline_plp_null | +3.44 | chi_eff mean slope only vs null |
| E3b | baseline_plp_width | baseline_plp_null | +1.84 | chi_eff width slope only vs null |
| E3c | baseline_plp_both | baseline_plp_null | +2.88 | mean + width slopes vs null |
| E4a | baseline_bpq_both | baseline_bpq_null | +2.66 | mean + width slopes vs null (broken pairing) |
| E4b | baseline_splm1_both | baseline_splm1_null | +1.32 | mean + width slopes vs null (spline m1) |
| E4c | baseline_bpq_both | baseline_plp_both | +0.03 | broken pairing vs power-law pairing |
| E4d | baseline_splm1_both | baseline_plp_both | -4.40 | spline m1 vs PowerLaw+Peak m1 |
| E3a-LVK | lvk_bpl2p_mean | lvk_bpl2p_null | -0.98 | chi_eff mean slope only vs null (LVK BPL+2P masses) |
| E3b-LVK | lvk_bpl2p_width | lvk_bpl2p_null | +0.84 | chi_eff width slope only vs null (LVK BPL+2P masses) |
| E3c-LVK | lvk_bpl2p_both | lvk_bpl2p_null | -0.93 | mean + width slopes vs null (LVK BPL+2P masses) |

| model | dims | ln Z | max ln L | inj n_eff (min/median) | frac var<1 | var_tot p50/p95 | wall (min) |
|---|---|---|---|---|---|---|---|
| baseline_plp_both | 13 | -4603.02 | -4571.91 | 28353/46445 | 1.00 | 0.68/0.94 | 12.5 |
| baseline_plp_mean | 12 | -4602.46 | -4572.50 | 28476/47072 | 1.00 | 0.67/0.94 | 11.5 |
| baseline_plp_width | 12 | -4604.06 | -4574.37 | 26718/59850 | 1.00 | 0.52/0.82 | 10.7 |
| baseline_plp_null | 11 | -4605.90 | -4579.51 | 33489/74758 | 1.00 | 0.42/0.70 | 8.4 |
| copula_gauss_plp | 33 | -4611.87 | -4571.45 | 26450/56394 | 1.00 | 0.72/0.96 | 171.4 |
| copula_indep_plp | 32 | -4611.67 | -4570.90 | 26259/56857 | 1.00 | 0.71/0.96 | 245.5 |
| baseline_bpq_both | 15 | -4602.99 | -4570.89 | 28152/46823 | 1.00 | 0.66/0.94 | 9.4 |
| baseline_bpq_null | 13 | -4605.65 | -4578.37 | 31664/74105 | 1.00 | 0.42/0.69 | 7.1 |
| baseline_splm1_both | 22 | -4607.42 | -4572.77 | 27668/58626 | 1.00 | 0.52/0.87 | 25.2 |
| baseline_splm1_null | 20 | -4608.74 | -4577.08 | 34921/87502 | 1.00 | 0.35/0.55 | 15.8 |
| copula_gauss_splm1 | 42 | -4613.85 | -4569.73 | 24908/54991 | 1.00 | 0.74/0.96 | 2065.3 |
| lvk_bpl2p_both | 19 | -4600.55 | -4564.56 | 25322/43313 | 1.00 | 0.66/0.94 | 30.8 |
| lvk_bpl2p_null | 17 | -4599.62 | -4567.09 | 26273/45967 | 1.00 | 0.63/0.93 | 21.7 |
| lvk_bpl2p_mean | 18 | -4600.60 | -4566.00 | 25734/47871 | 1.00 | 0.60/0.90 | 24.8 |
| lvk_bpl2p_width | 18 | -4598.78 | -4564.28 | 25552/43124 | 1.00 | 0.66/0.94 | 23.3 |
| abl_plp_m2taper_both | 15 | -4603.28 | -4571.97 | 28503/52519 | 1.00 | 0.60/0.92 | 10.6 |
| abl_plp_lvkspin_both | 13 | -4601.61 | -4571.84 | 29011/44127 | 1.00 | 0.71/0.96 | 7.7 |
| abl_bpl2p_sharedtaper_both | 17 | -4600.82 | -4563.93 | 25955/42460 | 1.00 | 0.68/0.93 | 22.9 |
| abl_bpl2p_plpspin_both | 19 | -4601.69 | -4563.95 | 25465/44514 | 1.00 | 0.64/0.93 | 31.9 |
