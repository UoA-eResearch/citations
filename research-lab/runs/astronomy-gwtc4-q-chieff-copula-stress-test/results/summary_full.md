# q-chi_eff copula stress test: results summary (full mode)

Events: 153; verdict (plan sec 7 logic): **INDETERMINATE: E1 ln BF = -0.20 < ln 3 but E2 FPR = 0.010 <= 5% [tau of PE-prior posterior medians vs v3c detection-consistent physical mock PE (D27c)] -- E1 and E2 disagree (plan sec 7); the E2 statistic sits at or beyond the edge of every simulated hypothesis and is dominated by a PE-prior effect the mocks cannot reproduce (D29, D27c)**

## Preregistered endpoints

* E1 ln BF(Gaussian copula dependence vs independence, PLP m1) = -0.20 (threshold ln 3 = 1.10); SDDR cross-check = -0.15
* E2 decision basis: tau of PE-prior posterior medians vs v3c detection-consistent physical mock PE (D27c); FPR = 0.01
* E2 vs v3c by measure (FPR one-sided): post -0.217 (0.010), pop -0.102 (0.185), flattheta -0.106 (0.190), flatx -0.057 (0.190)
* Hierarchical rho scan (nuisance-integrated, v3c mocks): rho_hat = +0.174, FPR 0.325; ln BF(flat rho) = -0.86, FPR 0.655
* Hierarchical rho scan (diagnostic; plug-in, v1 mocks): rho_hat = +0.074, FPR(rho_hat) = 0.24

## Bayes-factor table

* E1: ln BF = -0.20 (Gaussian copula dependence vs independence (PLP m1))
* E3a: ln BF = +3.44 (chi_eff mean slope only vs null)
* E3b: ln BF = +1.84 (chi_eff width slope only vs null)
* E3c: ln BF = +2.88 (mean + width slopes vs null)
* E4a: ln BF = +2.66 (mean + width slopes vs null (broken pairing))
* E4b: ln BF = +1.32 (mean + width slopes vs null (spline m1))
* E4c: ln BF = +0.03 (broken pairing vs power-law pairing)
* E4d: ln BF = -4.40 (spline m1 vs PowerLaw+Peak m1)
* E1-LVK-frank: ln BF = -2.10 (Frank copula dependence vs independence (LVK marginals))
* E1-LVK-gauss: ln BF = -0.98 (Gaussian copula dependence vs independence (LVK marginals))
* E3a-LVK: ln BF = -0.98 (chi_eff mean slope only vs null (LVK BPL+2P masses))
* E3b-LVK: ln BF = +0.84 (chi_eff width slope only vs null (LVK BPL+2P masses))
* E3c-LVK: ln BF = -0.93 (mean + width slopes vs null (LVK BPL+2P masses))

## Baseline (LVK Linear-model) chi_eff-q slopes (PowerLaw+Peak masses)

* delta mu_eff|q = -0.466 [-0.753, -0.182] (90%); P(<0) = 0.995 (LVK: 0.82; NUTS: 0.998)
* delta ln sigma_eff|q = -1.718 [-3.624, +1.664] (90%); P(<0) = 0.830 (LVK: 0.95; NUTS: 0.676)
* Gate (plan sec 4.1): **FAIL**

## Same Linear spin model on the LVK Broken Power Law + 2 Peaks masses (D15)

* delta mu_eff|q = -0.162 [-0.488, +0.179] (90%); P(<0) = 0.802 (LVK: 0.82)
* delta ln sigma_eff|q = -2.094 [-3.698, +1.940] (90%); P(<0) = 0.889 (LVK: 0.95)
* Gate with the LVK mass model: **PASS**

## Slope credibilities by mass/pairing/prior configuration (D17 ablation)

| model | ln Z | P(delta mu < 0) | P(delta ln sigma < 0) | median delta mu | median delta ln sigma |
|---|---|---|---|---|---|
| baseline_plp_both | -4603.02 | 0.995 | 0.830 | -0.466 | -1.72 |
| baseline_bpq_both | -4602.99 | 0.995 | 0.871 | -0.457 | -1.95 |
| baseline_splm1_both | -4607.42 | 0.985 | 0.828 | -0.403 | -1.65 |
| lvk_bpl2p_both | -4600.55 | 0.802 | 0.889 | -0.162 | -2.09 |
| abl_plp_m2taper_both | -4603.28 | 0.985 | 0.778 | -0.414 | -1.42 |
| abl_plp_lvkspin_both | -4601.61 | 0.993 | 0.882 | -0.471 | -2.02 |
| abl_bpl2p_sharedtaper_both | -4600.82 | 0.840 | 0.944 | -0.210 | -2.23 |
| abl_bpl2p_plpspin_both | -4601.69 | 0.803 | 0.774 | -0.158 | -1.64 |

## LOO: 0 of 153 single-event removals flip the sign of the median rho; 1 change whether the 90% interval excludes 0; most influential event: GW231226_101520

## E2 point-estimate tau by measure (D21; like-for-like, 200 null mocks)

| measure | observed tau | null median | FPR one-sided | FPR two-sided | passes marginal check |
|---|---|---|---|---|---|
| post | -0.217 | -0.019 | 0.000 | 0.000 | no |
| pop | -0.102 | +0.004 | 0.035 | 0.095 | no |
| flattheta | -0.106 | -0.009 | 0.060 | 0.110 | no |
| flatx | -0.057 | -0.003 | 0.215 | 0.380 | no |

## Hierarchical rho scan: estimator response (D20)

* rho_true = +0.00 (n=200): rho_hat median -0.036 [-0.166, +0.106]
* rho_true = -0.60 (n=40): rho_hat median -0.592 [-0.672, -0.489]
* rho_true = -0.40 (n=40): rho_hat median -0.412 [-0.526, -0.231]
* rho_true = -0.20 (n=40): rho_hat median -0.188 [-0.286, -0.052]
* rho_true = +0.20 (n=40): rho_hat median +0.186 [-0.010, +0.293]
