# q-chi_eff copula stress test: results summary (smoke mode)

Events: 4; verdict (plan sec 7 logic): **CONFIRMED (artifact-consistent): ln BF < ln 3 and FPR > 5%**

## Preregistered endpoints

* E1 ln BF(Gaussian copula dependence vs independence, PLP m1) = -0.17 (threshold ln 3 = 1.10); SDDR cross-check = -0.12
* E2 FPR(Kendall tau) = 0.25, FPR(rho_MAP) = 0.5, FPR(LR) = 1.0 over 4 rho=0 mocks; observed tau = -0.3333333333333334

## Bayes-factor table

* E1: ln BF = -0.17 (Gaussian copula dependence vs independence (PLP m1))
* E3c: ln BF = +0.07 (mean + width slopes vs null)
* E4c: ln BF = -0.86 (broken pairing vs power-law pairing)

## Baseline (LVK Linear-model) chi_eff-q slopes (PowerLaw+Peak masses)

* delta mu_eff|q = +0.046 [-1.725, +1.732] (90%); P(<0) = 0.485 (LVK: 0.82; NUTS: 0.463)
* delta ln sigma_eff|q = -6.097 [-11.478, +1.919] (90%); P(<0) = 0.859 (LVK: 0.95; NUTS: 0.438)
* Gate (plan sec 4.1): **FAIL**

## LOO: 3 of 4 single-event removals flip the sign of the median rho; 1 change whether the 90% interval excludes 0; most influential event: GW190805_211137

## PPC per primary-mass bin (Kendall tau of observed medians vs posterior predictive)

* m1 in [2, 30) (n=3): observed +nan, predicted +nan [+nan, +nan], p=nan
* m1 in [30, 200) (n=1): observed +nan, predicted +nan [+nan, +nan], p=nan

## Calibration curve (fraction of mocks at least as extreme as observed)

* rho_true = +0.00 (n=4): tau 0.25, rho_MAP 0.5; median tau +0.000, median rho_MAP -0.358
* rho_true = -0.40 (n=2): tau 0.5, rho_MAP 0.5; median tau -0.333, median rho_MAP -0.000
* rho_true = +0.20 (n=2): tau 0.0, rho_MAP 0.0; median tau +0.667, median rho_MAP +0.950
