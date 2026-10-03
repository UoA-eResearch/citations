# Deviations and implementation details

The plan (plan.md) was committed in 311bd7e at 2026-10-03 21:44 NZDT, before any outcome analysis. Entries are
timestamped with `date`.

## D1. Negative-binomial check fitted in two steps (2026-10-03 21:46 NZDT)

The direct NB2 maximum-likelihood fit, with about 120 week dummies, did not converge: it returned a ratio of 1.21 with
undefined standard errors. The check is therefore fitted in two steps:

1. Estimate the dispersion alpha from a Poisson fit of the same model, using the Cameron-Trivedi auxiliary
   regression (alpha = 0.171).
2. Fit a negative-binomial GLM with that alpha, with standard errors clustered by site.

This is a secondary analysis and has no verdict.

## D2. Fewer sites after August 2023 (2026-10-03 21:46 NZDT)

ESR stopped sampling many small sites during 2023. After 20 Aug 2023 only 26 of the 57 sites contribute, so the
estimates for that period and the H2 interaction rest on fewer sites. The plan did not anticipate this. No rule was
changed; it is reported.

## D3. Case counts are integer-rounded daily averages (2026-10-03 22:13 NZDT, after review)

- **The rounding.** Every value of case_7d_avg in the ESR files is a whole number, a rounded daily average. A
  recorded 0 therefore means 0-3 cases that week, and a recorded 1 means 4-10.
- **Where it bites.** 19.1% of eligible site-weeks are recorded zeros, concentrated in small and more deprived towns.
  The plan's sentence "the 0.5 handles weeks with zero cases" was written without knowing this; in fact it handles
  weeks with 0-3 cases. The plan is unchanged.
- **Sensitivity** (code/review_checks.py, results/tables/review_checks.csv):

  | Treatment of the rounded counts | H1 ratio |
  |---|---|
  | Pseudo-count 0.25 / 1 / 3.5 | 0.83 / 0.89 / 0.95 |
  | Bin midpoint | 0.92 |
  | Interval-censored negative binomial, alpha 0.171 / 0.5 / 1.0 | 0.89 / 0.85 / 0.83 |
  | Dropping recorded-zero weeks (an upper bound, because it selects on the outcome) | 1.00 |

  Every confidence interval includes 1.

## D4. H2 omits post x region (2026-10-03 22:13 NZDT, after review)

Plan section 4 asks for post x each covariate. Region x post is not identified after the 2023 site reductions:
Otago has no post-period site, and Hawke's Bay, Taranaki and Wellington have one each. H2 therefore interacts post
with sampler, log population and share 65+ only. This omission was not declared before the review.

## D5. Variant eras and the 2024-2026 descriptive (2026-10-03 22:13 NZDT)

- **Variant eras.** The repository holds only the last two weeks of variant data, so the calendar-half fallback in
  plan section 5 was used.
- **2024-2026 descriptive: dropped.** Only 2 of the 12 sites still sampled after June 2024 (Rotorua, Christchurch) are
  in the analysis sample; the rest are metro sites. A deprivation comparison is not possible.

## D6. Inference and other checks added after review (2026-10-03 22:13 NZDT)

- **Small-sample intervals.**
  - With CR2 (Bell-McCaffrey) standard errors and 17.1 degrees of freedom, the H1 interval is 0.64-1.17.
  - The restricted wild-cluster bootstrap gives 0.64-1.13.
  - The preregistered CR1 interval (0.68-1.09) is the optimistic one. The verdict rule stays on CR1 as preregistered.
- **Other checks:**
  - 500 gc/L quantification-floor weeks (329 site-weeks): 0.89 without them;
  - 11 sites whose flow normalisation is an assumed constant: 0.84 with a flag, 0.86 without them;
  - adjustment ladder: 0.94 with week fixed effects only, 1.03 after adding log population, 0.91 after the 65+ share,
    0.86 in the full model;
  - two-step site-level regressions: 0.85-0.90.
- **Power.** The power to detect the preregistered ratio of 0.85 was 0.27; the minimum detectable ratio at 80% power
  was 0.71. The H2 interaction could only have detected about 0.67 on the log scale, roughly a two-fold change in the
  gradient.
- **Holiday towns (exploratory, post hoc).** Dropping them gives 0.79 (0.63-1.00). This is not a headline result.
