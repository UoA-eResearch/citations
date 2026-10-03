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

## D2. Wider multi-start after independent review (2026-10-04 07:58 NZDT)

**What the reviewer found.** The first-round Norcia model-A fit was a local optimum of the training likelihood. A
refit from Visso-like starts raised the training log-likelihood by 173 nats (2.9477 vs 2.9432 per event). The three
starts used in round 1 were not enough.

**The fix.** Every fit (S2, A and B, in all 15 AVN configurations and the synthetic catalog) is re-run with a wider
multi-start:

- Stockman's clipped released parameters;
- 8 generic starts spanning c 1e-4 to 1 h, alpha 1.5 to 3.3, T_b 0.003 to 0.03 h and p 1.1 to 1.5;
- for AVN, the round-1 optima of the three primary configurations' A and B fits.

Each start is screened with a short Nelder-Mead run, and the best 3 are refined.

**Effect on the analysis.** The decision rule and the primary-model selection are unchanged; only the optimiser
changed. Model selection uses training data only, so adding starts cannot leak test information. Round-1 outputs are
kept in results/fits_round1/, results/pointwise_round1/, results/tables/primary_round1.csv and
cutoff_sweep_round1.csv.

## D3. Validation regenerated with the final code (2026-10-04 07:58 NZDT)

The committed validation tables predated the final numerical fixes. Two of them had no generating script in code/.

code/validation_all.py now regenerates every validation table with the final code and the wide multi-start. The
reviewer found that, with the earlier 1-start procedure, the model-B validation catalog converged to a degenerate
p -> 1 fit below the true-parameter likelihood. The outcome with the wide multi-start is reported in the results as
it comes out.

## D4. Secondary analyses added after review (2026-10-04 07:58 NZDT; code/secondary.py)

- Per-target A - NPP differences with block-bootstrap CIs.
- How concentrated A's gain over S0 is in the top 24-h blocks.
- A evaluated with S0's truncated history (information asymmetry).
- The cutoff sweep reported as log-likelihood differences, with G <= 0 rows flagged as having no defined R.

## D5. Correction to the plan's threats (2026-10-04 07:58 NZDT)

Plan section 6 says S0's beta was estimated from test magnitudes, a "beta leak". The reviewer showed that the released
beta equals the training-period beta to five decimals (Visso 2.74289, Norcia 2.56211, Campotosto 2.75732), so there
is no leak. Stockman's current code calls estimate_beta_value(M_test, ...), but the released files were evidently not
produced that way. The claim is withdrawn.

## D6. Kernel-approximation guard (2026-10-04 10:12 NZDT)

**The exploit.** The wider multi-start (D2) found a numerical exploit. In 4 of the 32 model-A fits (Norcia 1.2,
Norcia 1.5, Visso 1.5 and the synthetic catalog), the optimiser drove c towards 1e-294. There the
sum-of-exponentials (SOE) kernel approximation is 100% wrong (relative error 1.0). The compensating integral was then
underestimated, giving impossible training log-likelihoods of 15-19 nats per event.

**Why the earlier fits were unaffected.** Every other fit, including all round-1 primary fits, had an SOE error at or
below 7e-4.

**The fix.**

- Any parameter set whose SOE error exceeds 1e-3 is now rejected during fitting and refused at evaluation.
- c is bounded below at 1e-6 time units. The smallest legitimate fitted c is 5e-6.

All fits and the validation are re-run with this final code. The invalid round-2 fits are kept, for the record, in
results/fits_round2_invalid/.
