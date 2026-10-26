# Plausibility gate (G3) — added in D3 (the study predates METHODS.md)

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| canonical effect, 1976–1991 | −0.41% per point (−0.53% to −0.29%) | Ruhm (2000): about −0.5% per point, 1972–1991 (ledger M1) | yes | a replication |
| canonical effect, 1992–2005 | +0.21% (not significant) | weakening reported by Ruhm (2015, ledger M2) | yes | |
| joint-test null median share | 1.8% | about 2.5% for one-sided tests at 5% if the specifications were independent; correlated specifications vary more | yes | 0 of 500 null draws reach 49% |
| H2 canonical-type 1999–2010 | +5.6% per point (+2.4 to +8.8) | countercyclical poisoning before 2010 (ledger M2) | yes | |

## 2. Three units traced end to end (independent review, `review/reviewer_checks/`)

| unit | raw input | intermediate values | output | matches the pipeline? |
|---|---|---|---|---|
| US yearly deaths, 1976–2004 | NBER microdata (restatus ≠ 4, state of residence) | totals by year | equal to the published US totals in 27 of 29 years (the other two within 0.004%) | yes |
| six specifications | panel rebuilt independently in pandas | pyfixest CRV1 fits | betas equal to 1e-7; SE differences exactly the fixed-effect counting convention | yes |
| wild cluster restricted bootstrap | two real specifications | brute-force bootstrap with 999 shared draws | p 0.4474 = 0.4474 and 0.0000 = 0.0000 | yes |

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| every specification has n equal to the window's state-years minus planned drops | posthoc_review.json; D3 | yes, except the documented 1977 drop (240 specifications) |
| no bootstrap resample fails | closed-form WCR | yes |
| weekly coverage complete 2014–2022 | build.py; review check | yes (365/366 days) |
