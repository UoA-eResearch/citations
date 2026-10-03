# Deviations and implementation details

The plan (plan.md) was committed in 795c015 at 2026-10-04 05:01 NZDT. Entries are timestamped with `date`.

## D1. Choices made during validation, before any AVN test evaluation (2026-10-04 05:24 NZDT)

Plan section 3 allows the fitting code to be fixed using synthetic data only. Everything below was settled on
simulated catalogs and Stockman's synthetic incomplete catalog, before any AVN fit was evaluated on its test period.

**S0 reproduction gate: passed.** The numba re-implementation reproduces Stockman's released standard-ETAS
target-event log-likelihoods exactly (mean absolute difference 0.0 for Visso, Norcia and Campotosto;
results/tables/s0_s1.csv). Giving S0 its full history (S1) changes the mean by -0.001, -0.005 and -0.037.

**Parameter bounds** (not specified in the plan):

- p in [1.0001, 4];
- K <= 1e5, c <= 50 (time units), alpha <= 5;
- mu <= 10 x the mean observed training rate;
- T_b <= 1 h;
- beta <= 10.

A first lower bound of p >= 1.02 was relaxed to 1.0001 because Stockman's fits sit at p of about 1 (synthetic
p = 1.000005). The 1.02 bound cost S2 about 0.003 nats per event on synthetic training data and 0.06 on its test
data.

**Numerical fixes** (both found because fitted likelihoods exceeded the true-parameter likelihood on simulated data):

- The model-A observed rate (1 - exp(-T_b x))/T_b underflowed to 0 as T_b -> 0, and the optimiser exploited the
  vanishing integral. It now uses -expm1(-T_b x)/T_b, with the series limit x when T_b x < 1e-12.
- Target intensities are floored at 1e-300 inside log(). Model B's observed fraction of M >= 3 events underflows when
  m_c(t) >> 3.

**Starting values.** Stockman's released parameters, clipped into the bounds, plus two generic starts. Each start
runs Nelder-Mead followed by L-BFGS-B, and the best result is kept.

**Validation results** (results/tables/validation*.csv):

- Simulated from A: model A wins on training log-likelihood. Over 8 seeds with imposed mainshocks the mean estimates
  are unbiased: mu 0.504 vs 0.5, K 0.207 vs 0.2, T_b 0.0100 vs 0.01. In one seed (seed 7) mu and K lie 3.1 and 2.1
  SE from truth. Without mainshocks T_b is weakly identified, as expected.
- Simulated from B: model B wins, and all parameters are within 2 SE or 10% of truth.
- Stockman's synthetic incomplete catalog (cutoff 2.0): mean test log-likelihood per target event.

  | Model | Mean test LL |
  |---|---|
  | B | -4.462 |
  | A | -4.576 |
  | S2 | -4.582 |
  | S0 | -4.487 |
  | NPP | -4.269 |

  B improves on S2, as the validation criterion requires. On this catalog the full-history evaluation itself costs
  about 0.09 nats compared with S0's truncated history: S0's parameters with full history score -4.581.
