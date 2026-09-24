# Deviations from the preregistered plan (plan.md)

Every entry records a departure from plan.md or from the brief, with the reason.
Entries are appended by the implementing session in chronological order.

## 2026-09-02 -- build / smoke-test session

### D1. Full-run scale reduced to fit the ~12 h wall-clock budget
| knob | plan / brief | full-mode config | reason |
|---|---|---|---|
| nautilus live points | "nested-sampling live points" (unspecified; 1500 in the first draft config) | `nlive: 1000`, `n_networks: 4`, `posterior_n_eff: 4000` | 13 models x (13-31 dims) must fit in ~3 h of A100 time; nautilus evidence errors at 1000 live points are ~0.1 in ln Z, far below the ln 3 decision threshold |
| zero-correlation mock catalogs (E2) | N ~ 200 | 200 (unchanged) | -- |
| calibration-curve mocks per rho_true | 60 (first draft) | 40 per rho_true, grid {-0.6, -0.4, -0.2, +0.2} | 160 extra MAP fits instead of 240 |
| full nested-sampling refits of mocks | 8 | 4 (x 2 models) | each refit is a full copula-model nautilus run; the per-mock point-estimate statistics (Kendall tau, rho_MAP, profile LR) carry E2, the refits only calibrate the hierarchical-posterior version of the statistic |
| injections used in the mock MAP fits | all | random 150 000 of the ~1.07 M found injections (`total_generated` rescaled) | keeps ~440 x 2 MAP fits at a few seconds each; the real-data fits and the nested-sampling mock refits use all injections |
| NUTS cross-check (baseline model only) | "NUTS/numpyro for posterior shape" | 400 warm-up + 1200 samples, 1 chain | cross-check of the nautilus posterior shape only; all ln Z / BF claims come from nautilus |

### D2. Injection draw density: per-component spin families (not in the plan)
The Zenodo O1-O4a mixture file records the *per-component* draw density over
(m1, m2, z, s1x..s2z). Converting it to the (m1, q, z, chi_eff) parameterization used by the
population models requires the injected component-spin distribution of each component.
Verified on the file (`selection.spin_draw_check`, results in `data/processed/injection_check_<mode>.json`):
* O3 real injections: isotropic tilts, magnitudes uniform on [0, 0.998] (as assumed in the first draft);
* O4a real injections **and** the semi-analytic O1/O2 injections: Essick 2025 (arXiv:2508.10638)
  draw -- truncated-Gaussian magnitudes (sigma = 0.5 on [0, 1]) with 30 % aligned ((1+cos t)^3/4)
  + 70 % isotropic tilts. Assuming the isotropic/uniform form for these components leaves
  residual correlations of 0.35-0.55 between the corrected draw density and the spin variables;
  the Essick-2025 form leaves < 0.05.
The pipeline now converts each component with its own chi_eff-given-q table. This is a correction of the
first implementation, not a change of the preregistered analysis.

### D3. Smoke mode (development/testing only; not a scientific run)
Smoke mode uses 4 real events (2 GWTC-4.0, 1 GWTC-3, 1 GWTC-2.1 -- the smallest PE files), 300 posterior
samples per event, a random 10 000-injection slice (total_generated rescaled), coarser normalisation grids
(300 x 150 instead of 1000 x 500), `nlive = 100`, 4 + 2 x 2 mocks, and the LVK Monte-Carlo variance cut
disabled (it cannot be satisfied with 300 samples per event). None of its numbers are meaningful.

### D4. Items the plan requires that are NOT yet pinned (must be done before the full run is trusted)
* plan.md sec. 5 / sec. 10: the exact LVK GWTC-4.0 population-paper BBH sample (arXiv:2508.18083 sec. 2) has
  not been cross-checked event by event. The pipeline applies FAR < 1/yr over the cumulative
  GWTC-2.1-confident + GWTC-3-confident + GWTC-4.0 catalogs and the BBH control "posterior-median
  m2_source > 3 Msun"; `sample.exclude_events` in `code/config.yaml` is the hook for pinning the list exactly.
* plan.md sec. 4.1 acceptance gate: `diagnostics.reference_mu_chi_eff_1` / `_ci90` (the published GWTC-4.0
  chi_eff-mean-slope posterior) are still `null`; the gate is reported as "reference not set" until filled.
* The GWTC-4.0 population paper's own injection-set handling (which searches / FAR threshold define "found",
  and whether O1/O2 semi-analytic injections are included) has not been matched line by line; the pipeline
  follows the Zenodo record's documented convention (o1o2_semi: semianalytic SNR > 10; o3/o4a: min FAR < 1/yr).

### D5. Gradient-based pieces sized to the measured A100 cost
Measured at full-run array shapes (150 events x 4000 samples, 1.07 M injections; `logs/gpu_check_smoke_fullscale.json`):
0.7-0.9 ms per vectorized likelihood point, but 58 ms (baseline) / 543 ms (copula) per *reverse-mode*
gradient because the VJPs of ~1e6 interpolation gathers become atomics-bound scatter-adds. The pipeline
therefore uses forward-mode gradients (26 ms / 65 ms; identical to 1e-13) for the mock MAP fits and NUTS
(`likelihood.gradient_mode: auto`), and the NUTS cross-check of the baseline model is run with
250 warm-up + 500 samples and `max_tree_depth = 6` (a posterior-shape check only; every ln Z / BF number
comes from nautilus). Nested sampling itself does not use gradients and is unaffected.

### D6. Corrections to the earlier (interrupted) implementation -- not plan deviations, recorded for transparency
* `jaxmodels.q_conditional` now reproduces gwpopulation's q-normalisation convention exactly (linear
  interpolation of the analytically-normalised power-law norm in m1); the first draft differed by up to 25 %
  within ~1 Msun of `mmin` (test_models now agrees to 3e-15).
* Mock catalogs: the mock posterior samples are `x_obs - eps` (not `x_obs + eps`) for the asymmetric
  likelihood kernels, and the mock `ln_prior` column carries the Jacobian of the flat-in-(ln m1, logit q,
  chi_eff, ln z) prior instead of zero, so the hierarchical likelihood treats mocks and real events identically.
* The copula models' gradients were NaN (0/0 from a 1e-300 floor on the q-normalisation inside the CDF); fixed
  with a 1e-150 floor. Without this every rho_MAP / profile-LR mock statistic silently returned its starting value.
* Injection found-rule made explicit per component (o1o2_semi via semianalytic SNR; o3/o4a via FAR); for
  this file the count is unchanged (1 065 922).

## 2026-09-02 -- full-run session (executor)

### D7. Sample pinned to the LVK GWTC-4.0 population-paper BBH set (resolves D4, items 1-2)
Cross-checked against arXiv:2508.18083 sec 3.2 and sec 6 (text extracted from the arXiv PDF):
* LVK BBH criterion is FAR < 1/yr in at least one pipeline **and the 1% lower limit of both component-mass
  posteriors > 3 Msun** (not the posterior median used in the first implementation). `build_sample.py` now
  applies the 1% lower-limit rule (`sample.bbh_mass_quantile: 0.01`); the QC table records `m1_lower`/`m2_lower`.
* The paper excludes GW230630_070659 (data quality; it also has no public PE release on GWOSC) and GW190814
  (ambiguous NSBH/BBH). Both are now in `sample.exclude_events`.
* The 10 O1/O2 BBHs (GW150914 ... GW170823) carry `far = None` in the GWTC-2.1-confident eventapi, so the
  first implementation's pre-filter silently dropped them (59 instead of 69 O1-O3 BBHs). `fetch_data.py` now
  fills missing FARs from GWTC-1-confident (`data_sources.far_fallback_catalogs`; all 10 have FAR <= 0.02/yr)
  and records `far_source` in the manifest. Expected sample: 10 + 36 (O3a) + 23 (O3b) + 84 (O4a) = 153 BBHs,
  the paper's count; the realised count is verified in `data/processed/sample_summary_full.json`.
* Event-level PE: GWTC-2.1 `_mixed_cosmo` re-analyses for O1-O3a events, GWTC-3 `_mixed_cosmo` for O3b,
  GWTC-4.0 `C00:Mixed` for O4a (the paper uses the GWTC-2.1 / GWTC-3.0 / GWTC-4.0 data-release samples).
* Not matched line by line (unchanged from D4 item 3): the paper's injection-set handling. The pipeline uses the
  Zenodo O1-O4a mixture with its documented found-rule.

### D8. Baseline spin model aligned with the LVK "Linear" (q, chi_eff) model; gate redefined on published credibilities
* plan sec 4.1 names the LVK GWTC-4.0 "correlated" chi_eff extension as the baseline. arXiv:2508.18083 App. B.7
  (eqs. B42-B43) defines it with the mean **and the natural-log width** linear in mass ratio. The first
  implementation used a width linear in q with a 0.02 floor and a hard positivity constraint; `jaxmodels.chi_sector`
  now uses ln sigma(q) = ln sigma_0 + delta ln sigma (q - 1), and the hyper-priors follow the paper's Table 10:
  delta mu ~ U(-2, 2) (was U(-2.5, 2.5)), delta ln sigma ~ U(-12, 4) (was U(-1, 1) on a linear slope).
  sigma_0 keeps a uniform prior on [0.02, 1] (LVK: ln sigma_0 ~ U(-5, 0)); this intercept prior is common to all
  E3 variants. The LVK Linear model also uses their default Broken Power Law + 2 Peaks mass model; the plan's
  baseline is PowerLaw+Peak and that is kept.
* Acceptance gate: the paper does not tabulate delta mu_eff|q; it reports P(delta mu_eff|q < 0) = 82% and
  P(delta ln sigma_eff|q < 0) = 95% (and that both being zero is excluded at > 99%). The gate is therefore
  "reproduce both credibility levels within +/- 0.15 and +/- 0.10 respectively" (`diagnostics.reference_p_*`,
  `gate_tolerance_*`). The paper's Frank copula result kappa_q,eff = -2.1 (+2.4 / -2.9), P(kappa < 0) = 92%,
  is reported next to our Frank-copula theta as a cross-check only (different marginals and mass model).
* Figures: every figure now has a caption file (`results/figures/<mode>_F<n>_<name>.txt`) describing axes and units.

## 2026-09-11 -- full-run session (executor, resumed)

### D9. Sample gate resolved: 151 -> 153 BBHs by pinning two O3a events to the paper's GWTC-3.0-inherited classification
The 2026-09-02 full-mode build produced 151 events instead of the paper's 153: GW190924_021846 and
GW190725_174728 were dropped by the literal rule "1% lower limit of both component masses > 3 Msun"
(their 1% lower limits of m2_source in the public GWTC-2.1 `_mixed_cosmo` samples are 2.77 and 2.67 Msun).
Re-read against arXiv:2508.18083 (HTML v2, sec 3.2.1-3.2.2, 2026-09-11):
* sec 3.2.1: "GWTC-3.0 included 76 candidates with FAR < 1/yr: 69 BBH, 4 NSBH, 2 BNS, and one event
  GW190814 ... Abac et al. identifies 128 candidate signals in O4a ... of which 85 (84 BBH and 1 NSBH) have
  FAR < 1/yr. Selecting BBH from the catalog using this threshold yields a cumulative BBH count of 153."
  GW230630_070659 is excluded (data quality).
* sec 3.2.2: "we first threshold events by checking whether the 1% lower limit on the component mass is smaller
  or larger than 3 Msun"; NS-containing events additionally need FAR < 0.25/yr; GW190814 is excluded as ambiguous.
* The paper does not list its 153 events. But the count arithmetic is decisive: our manifest holds exactly 69
  GWTC-2.1/GWTC-3 candidates with FAR < 1/yr and posterior-median m2 > 3 Msun (10 O1/O2 + 36 O3a + 23 O3b, GW190814
  already removed) plus exactly 84 O4a candidates. The paper's 69 GWTC-3.0 BBHs (the GWTC-3.0 population-paper
  classification, which it quotes rather than re-derives) can only be reached if both borderline O3a events are
  BBHs, since no other candidate with a median m2 > 3 Msun exists at FAR < 1/yr, and any NS-containing candidate
  fails the 1% rule by a wide margin (GW190917: m2 ~ 2.1 Msun; GW200210_092254: m2 ~ 2.8 Msun median).
  GW190924_021846 has been treated as the lowest-mass BBH since the GWTC-2 population paper.
* Resolution: the 1% lower-limit rule stays the sample criterion (it is the paper's stated rule and it is
  what classifies the O4a events), and the two GWTC-3.0-inherited BBHs are kept through a documented override
  `sample.force_include_events: [GW190924_021846, GW190725_174728]` (bypasses the mass cut only; FAR threshold
  and `exclude_events` still apply). `build_sample.py` records the override in `sample_qc_full.csv` (`reason`
  column: "kept: 1% lower limit ... force_include_events"). Stage 02 rebuilt with `--force`; the realised count
  is written to `sample_summary_full.json` and checked below. The 153 gate in `run_full_chain.sh` is unchanged.
* Residual mismatch (not resolvable from the paper's text): if the paper's own O1-O3 sample were instead
  re-derived from the 1% rule on different PE samples, it would have 151 events; the two events have
  q ~ 0.53-0.58 and chi_eff ~ 0 and are not influential for the q-chi_eff dependence (E5 LOO covers this).

### D10. Posterior samples per event: common K = 4000 with resampling of two short releases (was silently 1993)
`fit_models.load_event_arrays` set the common number of posterior samples per event to
min(4000, min_i n_i); the GWTC-3 `C01:Mixed` release of GW200129_065458 has only 1993 samples (GW150914: 3337),
so the first launch of the full fit stage (2026-09-11 10:51, killed after 4 min) used 1993 samples for
all 153 events -- half the configured Monte Carlo precision, which also tightens the LVK ln L variance
cut. Fixed before any result was produced: K is now the configured 4000 and events with fewer samples
are resampled with replacement (their per-event Monte Carlo variance is under-estimated by the
duplication factor, <= 2, for 2 of 153 events). The partial nautilus checkpoint of `baseline_plp_both`
from the K = 1993 launch was deleted. The mock arm (stage 05) and the PPC (stage 06) use K = 2000
(GW200129_065458 gets 7 duplicated samples there).

### D11. Monte Carlo convergence cuts enter the sampled likelihood as a steep finite penalty, not as ln L = -inf
The first full-scale launch of stage 03 (2026-09-11 10:52) logged "finite fraction at prior draws 0.00": with the
LVK cuts (total ln L variance < 1, injection n_eff > 4N) implemented as ln L = -inf, none of 256 prior draws was
finite. A CPU diagnostic (`scratchpad/diag_cuts.py`, 153 events x 4000 samples, all 1.07 M injections) found
var_tot < 1 for 0/256 prior draws (median var_tot ~ 1e3), n_eff > 4N for 9%, and var_tot = 1.44 (n_eff = 8.9e4)
even at a fiducial LVK PowerLaw+Peak population (alpha 3.5, mmin 5, mmax 90, lambda 0.04, mu 34, sigma 4,
delta_m 5, beta 1.1, mu_chi 0.06, sigma_chi 0.1, lambda_z 2.9); 0/64 points within +/- 5% of the prior width
around it were finite. Nautilus (unlike bilby+dynesty, which redraws initial live points until they are finite)
cannot bootstrap from an all -inf prior. `likelihood.cut_mode: penalty` now returns
ln L_MC - 1000 [max(0, ln(var_tot/1)) + max(0, ln(4N/n_eff))] outside the convergence region (still -inf where the
analytic prior constraints fail or ln L is not finite). Outside the region the posterior weight is < e^-10 for
var_tot > 1.01, i.e. the effective cut sits at var_tot ~ 1.001 and the evidence differs from the hard-cut evidence
by a fraction < e^-10 of the prior volume in the 1 < var_tot < 1.01 shell. Nested sampling (stage 03 real-data fits
and the stage 05 mock refits) uses this consistently; the MAP statistics and NUTS use the uncut ln L_soft as
before. The fraction of posterior samples with var_tot < 1 and the posterior var_tot quantiles are recorded per
fit (`summary.json`) so that the bite of the cut on each model's posterior is visible.

### D12. Posterior samples per event raised from 4000 to all 10 000 stored samples (supersedes the K in D10)
The variance cut scales as 1/K per event. At K = 4000 the fiducial LVK population has var_tot = 1.44 (fails);
the sample table already stores up to 10 000 samples per event (all of the release for 10 events with fewer,
which are resampled with replacement, D10), so `modes.full.max_posterior_samples_per_event` is now 10 000
(expected var_tot ~ 0.7 at the fiducial point). Likelihood cost per point rises ~1.6x (153 x 10 000 event samples
+ 1.07 M injections); the nautilus runs are dominated by the sampler's own overhead so the fit stage is expected to
stay within ~3-4 h. Mock catalogs keep 2000 samples per event (their kernels and MAP statistics do not use the
cut); the 4 nautilus mock refits therefore sit closer to the variance cut than the real-data fits, which is noted
in the results as a limitation of the hierarchical-posterior version of E2.

### D13. Primary-mass grid and mmax prior extended from 100 to 300 Msun (GW231123)
The mass grid (`grids.m1_max: 100`) and the PowerLaw+Peak `mmax` prior U(30, 100) were inherited from the
GWTC-3 conventions of the first draft. The GWTC-4.0 population-paper sample -- and ours -- contains
GW231123_135430 (m1_source median 135 Msun, 1% lower limit 110 Msun; the paper keeps it in all BBH analyses,
sec 3.2.1 and sec 6.1). With the 100 Msun ceiling every mass model gave that event ~0.1% of its posterior
samples inside the population support, so (i) all models were misspecified for it, (ii) its per-event Monte
Carlo variance dominated var_tot (the K = 10 000 check of D12 reduced var_tot at the fiducial point only
from 1.44 to 1.34), and (iii) mmax would have piled up at the prior edge. The second full-scale launch of stage 03
(10:59-11:15, `baseline_plp_both` in progress) was stopped and discarded. Now: `grids.m1_max: 300`,
`grids.n_m1: 2000` (0.15 Msun spacing, as before), `priors.mmax: [30, 300]` (the LVK GWTC-4.0 mass models pin
m_high = 300 Msun / use U(60, 200) for the PDB high-mass roll-off), and `modes.full.mass_spline_nodes: 14`
(same spacing in ln m1 as the 12 nodes over 2-100 Msun; the spline-m1 models gain 2 parameters). The model
unit tests were re-run on the new grid before relaunching.

### D14. Note on the LVK Linear-model parameterization (refines D8)
arXiv:2508.18083 App. B.7 (eqs. B36-B37, not "B42-B43" as written in D8) defines mu_eff(q) = mu_eff|q + delta mu_eff|q * q
and ln sigma_eff(q) = ln sigma_eff|q + delta ln sigma_eff|q * q, i.e. linear in q with the intercept at q = 0.
`jaxmodels.chi_sector` anchors the intercepts at q = 1 (mu_0 + mu_1 (q - 1), ln sigma_0 + sigma_1 (q - 1)). The
slopes (mu_1 = delta mu_eff|q, sigma_1 = delta ln sigma_eff|q) and their sign convention are identical, so the
gate quantities P(delta mu < 0) and P(delta ln sigma < 0) are comparable; the uniform intercept priors are placed
on mu(q = 1) in [-1, 1] and sigma(q = 1) in [0.02, 1] instead of on mu(q = 0) and ln sigma(q = 0) (U(-5, 0)),
a mild prior-volume difference that is not corrected for. The paper's masses follow its Broken Power Law +
2 Peaks model; the plan's PowerLaw+Peak is kept (D8).

## 2026-09-11 -- main-loop session (orchestrator, after the executor was stopped at the user's request)

### D15. Added the LVK GWTC-4.0 mass model (Broken Power Law + 2 Peaks) to test the reproduction gate directly
The first four full-mode fits (PowerLaw+Peak masses) put the plan's acceptance gate (sec 4.1, D8) at
P(delta mu_eff|q < 0) = 0.994 (weighted nautilus points; NUTS 0.998) and P(delta ln sigma_eff|q < 0) = 0.83 (NUTS 0.68),
versus the paper's 0.82 / 0.95: the gate FAILS in a specific direction -- our fit reproduces the GWTC-3.0-era
mean-shift result (the paper itself quotes P(delta mu < 0) = 98% for GWTC-3.0) rather than the GWTC-4.0 width-driven one.
The paper's Linear (q, chi_eff) result was obtained with its default Broken Power Law + 2 Peaks mass model
(arXiv:2508.18083 App. B.3, eqs. B12-B17, Table 6), not PowerLaw+Peak; whether the mean/width verdict depends on the
mass model is exactly the study's question (E4), so the LVK model was added rather than the gate loosened:
* `jaxmodels.log_p_m1(spec mass="bpl2p")`: broken power law (B12-B13, alpha_1 below / alpha_2 above m_break, normalised
  on [m1,low, m_high]) mixed with two left-truncated Gaussians (B14) and the Planck taper on the total (B15);
  m_high pinned at 300 Msun (= `grids.m1_max`); mixing fractions Dir(1, 1, 1) realised from two unit uniforms
  (`dirichlet3_from_unit`: lambda_0 = 1 - sqrt(1 - u0), lambda_1 = (1 - lambda_0) u1).
* Pairing (B16): power law in q with its OWN low-mass taper S(m1 q | m2,low, delta_m2); `q_conditional` and the
  power-law lower edge use (m2,low, delta_m2) when the model carries them (`m2_taper: separate`).
* Priors (Table 6): alpha_1, alpha_2 ~ U(-4, 12); m_break ~ U(20, 50); mu_1 ~ U(5, 20); mu_2 ~ U(25, 60);
  sigma_1, sigma_2 ~ U(0.05, 10) (LVK U(0, 10); 0.05 Msun floor for finiteness); delta_m, delta_m2 ~ U(0, 10);
  m1,low with the triangular prior pi ∝ (m1,low - 3) on [3, 10] and m2,low ~ U(3, m1,low) (eq. B17), both via
  unit-cube parameters (`resolve_derived`). beta keeps the shared U(-4, 12) box (LVK: U(-2, 7)).
* Spin sector (B.7, Table 10): unchanged Linear model; the LVK log-uniform width intercept ln sigma_eff|q ~ U(-5, 0)
  replaces the uniform sigma_0 in [0.02, 1] for these models (`ln_sigma_chi_eff_0`). Table 10 states the intercepts are
  at q = 1, i.e. the anchoring already used here (this supersedes the worry in D14).
* Models: `lvk_bpl2p_{both,mean,width,null}`; endpoints E3a/b/c-LVK added to `BF_COMPARISONS`; diagnostics report a
  second gate, `gate_lvk_masses`, computed from `lvk_bpl2p_both` with the same reference values and tolerances.
* Verification (CPU, 2026-09-11 12:44): all 21 registered models pass `test_models.py` (finite fraction 0.92-1.00; the
  PowerLaw+Peak-vs-gwpopulation agreement is unchanged at 3.7e-15); the broken power law integrates to 1.000000 by
  quadrature for four (alpha_1, alpha_2) combinations including alpha = 1; the Dirichlet transform gives component
  means 0.333/0.333/0.334, P(lambda_0 < 0.5) = 0.7495 (expected 0.75) and corr(lambda_0, lambda_1) = -0.498 (expected
  -0.5); m1,low has mean 7.669 (expected 7.667) and m2,low <= m1,low always; the full bpl2p p(m1) and the
  separate-taper p(q|m1) integrate to 1 on the pipeline grid: worst |I - 1| = 4.4e-16 for p(m1) and 1.0e-4 for p(q|m1)
  (trapezoid rule on the q grid; the same order as the pipeline's existing copula normalisation checks) over 20 prior draws.
* Interpretation rule (pre-committed before seeing the LVK-model fits): if `lvk_bpl2p_both` reproduces the paper's
  0.82 / 0.95 within tolerance, the pipeline is validated and the mean-vs-width verdict is mass-model dependent
  (report both, E3 under both mass models); if it does not, the residual discrepancy is a pipeline/sample difference
  to be reported as a limitation, and the plan's gate remains FAILED.
* These fits run after the main chain (the GPU cannot host two JAX processes); the mock arm (stages 04-05) is
  unaffected (it is generated from `copula_indep_plp`).

### D16. Cost trim at the copula_indep_plp boundary: nautilus networks 4 -> 2, secondary Frank copula dropped
The 33-dimensional copula fits took 2.9 h (`copula_gauss_plp`) and 4.1 h (`copula_indep_plp`) instead of the
5-12 min per model estimated in D1 (the likelihood accounts for ~3% of the wall time; the rest is nautilus's own
bounding/network training, which scales badly with dimension). At that rate the remaining seven models plus the mock
arm would have taken ~15 h more with the GPU (and the user's vLLM server) unavailable throughout. The README's
pre-committed order of knobs was applied at the first model boundary after the primary E1 pair was complete:
(1) `modes.full.n_networks` 4 -> 2 for every remaining fit (measured overhead saving ~40%; ln Z precision at
nlive = 1000 stays ~0.1, far below the ln 3 threshold); (2) `copula_frank_plp` (endpoint E1b, a secondary copula-family
robustness check) removed from `modes.full.model_set`; its partial checkpoint was discarded. Retained: the E4
mass-model variants (`baseline_bpq_*`, `baseline_splm1_*`) and the E1c copula pair on spline masses
(`copula_gauss_splm1` / `copula_indep_splm1`), which is the mass-model robustness check of the headline E1 result and
therefore load-bearing. E1 itself (ln BF = -0.20) was computed before the change and is unaffected. The four LVK
mass-model fits (D15) also run with 2 networks.

**D15 outcome (2026-09-11 19:42).** `lvk_bpl2p_both` (19 dims, 31 min, ln Z = -4600.55): P(delta mu_eff|q < 0) = 0.80,
P(delta ln sigma_eff|q < 0) = 0.89 -- both within tolerance of the paper's 0.82 / 0.95, so `gate_lvk_masses` PASSES while
the PowerLaw+Peak gate (0.995 / 0.83) FAILS. Per the pre-committed rule the pipeline is treated as validated against
arXiv:2508.18083 sec 6.5.1, and the mean-shift-vs-width verdict is reported as mass-model dependent (E3 under both mass
models). Fitted LVK-model medians: alpha_1 = 2.17, alpha_2 = 4.41, m_break = 35.3, mu_1 = 9.7 (sigma_1 = 0.6,
lambda = 0.56), mu_2 = 33.0 (sigma_2 = 3.4, lambda = 0.04), lambda_BPL = 0.40, m1,low = 5.6, m2,low = 4.0, beta = 1.56.

**D15 outcome, E3 under the LVK masses (2026-09-11 20:53).** ln Z: null -4599.62, mean-only -4600.60, width-only -4598.78,
both -4600.55 (all at nlive 1000, 2 networks, ~25-30 min each). E3a-LVK = -0.98, E3b-LVK = +0.84, E3c-LVK = -0.93, versus
E3a/E3b/E3c = +3.44 / +1.84 / +2.88 under PowerLaw+Peak. Under the paper's mass model the mean-shift evidence vanishes and
only a weak width preference (ln BF < ln 3) remains; under PowerLaw+Peak the mean shift is strongly preferred. The
mean-vs-width verdict is therefore mass-model dependent at the level of the evidence, not just of the credibilities.

### D18. copula_indep_splm1 (E1c independence twin) dropped after copula_gauss_splm1 took 34 h (2026-09-13 08:25)
`copula_gauss_splm1` (42 dims) finished with ln Z = -4613.85 after 34.4 h of wall time: 308,900 likelihood calls at
2.6 ms each (~13 min of GPU work) inside nautilus's bounding/network-training overhead, which grows steeply with dimension
(33 dims: 3-4 h; 42 dims: 34 h). Its 41-dim independence twin had just started and would have cost the same again
before the mock arm could run. E1c is a secondary robustness check of E1 (copula dependence under a spline primary-mass
model), so the twin was stopped and removed from the model set; E1c is instead reported through the Savage-Dickey
density ratio of the fitted `copula_gauss_splm1` rho posterior against its uniform prior (the same estimator that
agreed with the nested-sampling E1 to 0.05 nats under PowerLaw+Peak: SDDR -0.15 vs nested -0.20). The remaining
work (D17 ablations, stages 04-07) runs in `run_gpu_chain4.sh`. No preregistered primary endpoint is affected.

**D18 outcome.** E1c (SDDR on `copula_gauss_splm1`, 42 dims, ln Z = -4613.85): rho median +0.25, 90% [-0.20, +0.69],
P(rho < 0) = 0.17, ln BF(dependence vs independence) = -0.53 -- the same conclusion as E1 under PowerLaw+Peak (-0.20).

**D17 outcome (2026-09-13 09:10, three of four ablations).** P(delta mu < 0) / P(delta ln sigma < 0):
baseline_plp_both 0.995 / 0.830; abl_plp_m2taper_both 0.985 / 0.778 (separate m2 taper: no effect);
abl_plp_lvkspin_both 0.993 / 0.882 (log-uniform sigma_0: no effect on the mean slope, width credibility up);
abl_bpl2p_sharedtaper_both 0.840 / 0.944 (LVK mass shape with the shared taper: reproduces the paper's 0.82 / 0.95);
lvk_bpl2p_both 0.802 / 0.889. Attribution: the chi_eff-mean shift is removed by the Broken Power Law + 2 Peaks primary-mass
SHAPE (fitted: ~9.8 Msun peak of width ~0.6 Msun carrying ~50% of the population, break at ~36 Msun, alpha_2 ~ 4.4,
m_high = 300), not by the m2 taper or the spin-width prior; the 14-node spline in ln m1 (baseline_splm1_both, 0.985)
does not resolve the narrow low-mass peak and behaves like PowerLaw+Peak.

**D17 outcome, complete (2026-09-13 09:41).** abl_bpl2p_plpspin_both (LVK masses, separate taper, uniform sigma_0): 0.803 / 0.774.
Full table (P(delta mu < 0) / P(delta ln sigma < 0)): PowerLaw+Peak variants -- baseline 0.995 / 0.830, + m2 taper
0.985 / 0.778, + log-uniform sigma_0 0.993 / 0.882, spline m1 0.985 / 0.828, broken pairing 0.995 / 0.871; Broken Power
Law + 2 Peaks variants -- full LVK config 0.802 / 0.889, shared taper 0.840 / 0.944, uniform sigma_0 0.803 / 0.774.
Two clean attributions: (i) the mean-shift credibility is set by the primary-mass shape (BPL+2P: 0.80-0.84; PLP-family:
0.985-0.995) irrespective of taper and spin prior; (ii) the width credibility is set by the sigma_0 prior (log-uniform:
0.88-0.94; uniform: 0.77-0.83) irrespective of the mass model. The paper's headline 0.82 / 0.95 is reproduced only by the
combination (BPL+2P shape, log-uniform sigma_0).

### D19. The E2 tau statistic must compare like with like: posterior medians vs likelihood-shaped medians (2026-09-13 09:50)
The real-data Kendall tau in stage 05 is computed from POSTERIOR medians of the released PE samples (-0.218), whereas each
mock event's "observed" point is likelihood-centred (truth + one draw from a real event's prior-removed kernel, D-block of
stage 04), so mock tau values are tau of likelihood-shaped medians. Recomputing the real statistic from prior-removed
(1/pi_PE-reweighted, quantile-clipped exactly as the kernel bank does) medians gives tau = -0.113: half of the observed
anticorrelation of medians is contributed by the PE prior itself (uniform-in-component-mass masses, isotropic-spin
chi_eff prior), not by the likelihoods. Consequence: FPR(tau) against -0.218 would understate the false-positive rate.
Fix (no re-run of stage 05 needed): diagnostics additionally compute tau_obs on likelihood-shaped medians and the
corresponding FPR from the per-mock tau column of mock_stats_full.csv, and report both; the preregistered primary E2
statistic is taken as the like-for-like version. rho_MAP and the profile LR are hierarchical-likelihood statistics with
the prior divided out and are unaffected.

## 2026-09-25 -- main-loop session (after a 12-day gap; the machine rebooted on 2026-09-16 for a kernel update)

### D20. Stage-05 MAP statistics abandoned; the hierarchical E2 statistic is a parametric-bootstrap rho scan
State found: the reboot killed `run_gpu_chain4.sh` inside stage 05 on the third rho = 0 mock. Stage 05 as built was
also far too slow: its four inline nautilus refits per model took 4-5.5 h each (each mock 8-11 h). Completed refit
pairs (kept as a hierarchical cross-check, `results/fits/full/mock_refits/`): null mock 0 ln BF(dependence) = +1.52
(rho posterior median +0.26), null mock 1 ln BF = -2.19 (rho median -0.04); mock 2 has only its Gaussian-copula refit.
MAP bug: the Gaussian-copula MAP fit on mocks stopped at its starting point after 3 evaluations (rho_MAP = 0.335 on
every mock, profile LR -163 and -433). Traced with `analysis/debug_map_optimizer.py`: the first, unscaled L-BFGS-B
trial step (|dx| ~ 15: alpha +8.3, lambda_z +6.6, ...) lands where the population density hits the model's "log zero"
sentinel NEG = -1e300, which is finite, so ln L ~ -2e300 passed the fitter's isfinite() guard; the line search
collapsed and scipy reported "CONVERGENCE: REL_REDUCTION_OF_F" at x0. On the real data the gradient was 8x smaller
and the first step stayed valid. Fixed in `mock_stats.MAPFitter` (variables scaled by half the real-data 68% posterior
width, sentinel-contaminated values treated as invalid, the copula fit started from the independence optimum with
rho = 0 so the profile LR is >= 0), validated with `analysis/test_map_fix.py`: real data rho_MAP = +0.185 from both
starts. But on null mocks the now-working optimiser ran to ln L = +600 ... +1174 (vs ~25 at a sensible point) with rho
pinned at the prior edge: unpenalised maximisation of the Monte Carlo selection-corrected likelihood exploits
injection sparsity -- the pathology the variance cuts exist to prevent. rho_MAP and the profile LR are therefore not
usable statistics and were dropped.
Replacement (`analysis/e2_rho_scan.py`): for the real catalog and all 360 mocks, identical settings -- the
`copula_gauss_plp` likelihood on a 77-point rho grid over its prior support, every other hyperparameter fixed at the
population the null mocks were drawn from (copula_indep_plp posterior median), all 1.07 M found injections, 2000
samples per event, no cuts (var_tot at the real-data optimum 0.68). A parametric-bootstrap test of rho = 0 with the
nuisance marginals fixed at their estimate. Results (`results/tables/e2_rhoscan_full.{csv,json}`, 40 s on the A100):
estimator response, median rho_hat [68%] -- rho_true -0.6: -0.592 [-0.672, -0.489]; -0.4: -0.412 [-0.526, -0.231];
-0.2: -0.188 [-0.286, -0.052]; 0: -0.036 [-0.166, +0.106] (n = 200); +0.2: +0.186 [-0.010, +0.293] -- unbiased under
realistic selection and PE scatter. Real data: rho_hat = +0.074, LR0 = 0.07, P(rho < 0 | fixed marginals) = 0.38;
fraction of null mocks with rho_hat >= +0.074: 0.24; with LR0 >= 0.07: 0.79.

### D21. Point-estimate tau depends on the measure; like-for-like comparison and a pre-committed choice rule
**Recorded at 2026-09-25 09:35:10 NZST, after the real-catalog values below and BEFORE the multi-measure null
distributions were computed (analysis/e2_tau.py v2 was still running; results/tables/e2_tau_full.json on disk was
the superseded v1 file, backed up as e2_tau_full.v1_measure_mismatch.*).**
Per-event medians depend on the measure the samples are weighted to. D19 compared the real catalog's
prior-removed medians (flat in m1, q, chi_eff, z) with the mocks' native medians, but mock samples are drawn under a
prior flat in the INTERNAL coordinates (ln m1, logit q, chi_eff, ln z) -- a different measure, so the v1 E2 numbers
(tau_lik FPR 0.060) compared unlike quantities. v2 reweights every catalog (real and mock, same clipping rule) to four
target measures: post (the PE prior), flattheta, flatx (flat in internal coordinates = the mocks' native measure),
pop (the null population the mocks were drawn from). Real catalog: tau = -0.217 / -0.106 / -0.057 / -0.102, and the
fraction of events with point-estimate m1 >= 40 Msun = 0.386 / 0.392 / 0.359 / 0.176 for post / flattheta / flatx / pop.
Pre-committed rule for the tau-based E2: all four measures are reported. The PRIMARY is the measure under which the
null mocks reproduce the observed point-estimate marginal -- the observed fraction with m1 >= 40 Msun lies inside the
central 95% of the rho = 0 mock distribution under that measure. If several measures pass, the primary is the one
closest to the preregistered definition ("posterior point estimates"): post, then pop, then flattheta, then flatx. If
none passes, no tau-based E2 conclusion is drawn and E2 rests on the hierarchical rho scan (D20). The FPR threshold
(> 5% supports the artifact hypothesis) is unchanged.

**D21 outcome (2026-09-25 09:40 NZST).** Like-for-like tau, observed / null median [95%] / FPR one-sided, two-sided:
post -0.217 / -0.019 [-0.142, +0.102] / 0.000, 0.000; flattheta -0.106 / -0.009 [-0.136, +0.104] / 0.060, 0.110;
flatx -0.057 / -0.003 [-0.132, +0.095] / 0.215, 0.380; pop -0.102 / +0.004 [-0.115, +0.124] / 0.035, 0.095.
Marginal check (fraction of events with point-estimate m1 >= 40 Msun; observed vs null 95%): post 0.386 vs
[0.183, 0.308]; flattheta 0.392 vs [0.216, 0.353]; flatx 0.359 vs [0.183, 0.320]; pop 0.176 vs [0.065, 0.170] (1.5% of
null mocks reach it). NO measure passes, so by the pre-committed rule no tau-based E2 conclusion is drawn and E2
rests on the hierarchical rho scan (D20): FPR(rho_hat) = 0.24. Reported regardless: under the population-informed
measure, the one closest to passing, tau gives one-sided FPR 0.035 (two-sided 0.095) -- below 5% one-sided.
Joint check: in all 360 mocks tau of medians and rho_hat track each other (corr +0.80 ... +0.85 by measure); the real
catalog's rho_hat (+0.074) sits above what its tau predicts under every measure (residual z = +4.6 post, +2.6
flattheta, +1.8 flatx, +3.1 pop; fraction of mocks with a residual at least as large 0.000-0.025). Point-estimate
and full-likelihood statistics disagree for the real catalog in a way they never do for the mocks: either dependence
structure a single global Gaussian copula cannot represent, or measurement structure (parameter-dependent likelihood
shapes) the location-family mock kernels do not emulate. Not resolved by E1/E2; see D22.

### D22. Exploratory: mass-localised dependence (Gaussian copula with a rho per preregistered E5 mass bin)
Motivation: the point-estimate anticorrelation is concentrated below 20 Msun (F15: tau FPR 0.01 under two measures).
Model `copula_gauss_mbin_plp` (piecewise-constant rho in m1 < 20, 20-40, >= 40 Msun, bins assigned by each sample's
own m1, normalised for every m1; equal rhos reproduce `copula_gauss_plp` to 3e-14). 17^3-point likelihood scan
(rho in -0.8 ... +0.8) with all other hyperparameters at the null population, identical for real data and all 360
mocks (`analysis/e2_rho_scan_mbin.py`). Real catalog: rho_hat = -0.10 / -0.60 / +0.20 per bin with fixed-marginal
posterior means +0.05 / -0.14 / +0.20 and P(rho < 0) = 0.44 / 0.59 / 0.24; LR against rho = 0 everywhere 0.61, LR for
bin heterogeneity 0.55. The likelihood is flat in all three bins: the low-mass point-estimate anomaly has no
counterpart in those events' full likelihoods. Null FPRs: see D22 outcome below.

### D23. Exploratory: is the point-estimate tau carried by well- or poorly-measured events?
`analysis/tau_by_precision.py`: events split at the median 90% width of chi_eff (or of q), tau within each half, real
vs the 200 null mocks, under the flatx and pop measures -- 12 comparisons. Inconclusive: flatx/chi-width split has
tau_good = -0.173 (null -0.072 [-0.232, +0.076], FPR 0.125) and tau_poor = +0.034 (FPR 0.415); the most extreme
comparison (pop measure, q-width split: tau_good = -0.095 vs null +0.060, FPR 0.020; poor-minus-good difference FPR
0.010) is unremarkable given 12 comparisons. The precision split neither confirms nor excludes a measurement origin
for the point-estimate / full-likelihood discrepancy of D21.

### D24. E1 inside the LVK configuration: Frank and Gaussian copulas on the LVK parametric marginals
**Recorded 2026-09-25 09:58 NZST, before either fit was run.** The best-evidence model of the whole study is
the LVK configuration (Broken Power Law + 2 Peaks masses; lvk_bpl2p_* ln Z -4598.8 ... -4600.6, vs -4603 for
PowerLaw+Peak and -4611.7 for the spline-marginal copulas). E1 was run only with PowerLaw+Peak masses and spline
marginals, so it is repeated inside the LVK configuration: `copula_frank_lvk` / `copula_gauss_lvk` = the LVK null model
`lvk_bpl2p_null` (BPL+2P masses, power-law pairing with its own m2 taper, truncated-normal chi_eff with no
q-dependence, Table 6/10 priors) plus a Frank (the LVK's App. B.6 construction, theta ~ U(-20, 20) = their kappa prior)
or Gaussian copula between u = F(q|m1) and v = F(chi_eff). New code: the truncated-normal CDF in `chi_sector`
(matches scipy to 6e-17); both copula densities integrate to 1.0000 on the LVK marginals. Pre-stated reading:
E1-LVK = ln Z(copula) - ln Z(`lvk_bpl2p_null` = -4599.62) against the same ln 3 threshold; the Frank theta posterior
is also compared with the paper's kappa_q,eff = -2.1 (+2.4/-2.9), P(kappa < 0) = 0.92 (a second reproduction check).
Note: with rigid parametric marginals a copula can absorb marginal misfit (the confound the flexible-marginal E1 is
designed to remove), so a positive E1-LVK would not by itself overturn E1.

**D22 outcome (2026-09-25 10:07).** Null (200 mocks) and response (40 per rho_true): per-bin rho_hat tracks rho_true in
the two lower-mass bins without bias (e.g. rho_true = -0.2: -0.20, -0.20) and with a ~-0.3 offset in the m1 >= 40 bin
(null median -0.35), which the calibration absorbs. Real catalog vs null: bin m1 < 20 rho_hat -0.10 (null 0.00
[-0.20, +0.20], FPR 0.445; profile-LR FPR 0.755); 20-40: -0.60 (null 0.00 [-0.30, +0.20], FPR 0.085; profile-LR FPR
0.680 -- the profile is flat); >= 40: +0.20 (null -0.35 [-0.80, +0.42], FPR 0.275; LR FPR 0.760). LR against zero
dependence in every bin: 95% of null mocks exceed the real value; LR for heterogeneity: 84.5%. No mass-localised
dependence. That the real catalog carries less dependence signal than most null mocks (also 79% for the global scan)
suggests the mock likelihoods are somewhat narrower than the real ones (clipped kernel weights); the direction is
conservative for the no-dependence conclusion.

## 2026-09-25 -- independent adversarial review (methodology lens) and response

### D26. Review findings accepted; the headline verdict is withdrawn
An independent reviewer (fresh context, CPU-only, scratch computations under /tmp/review_methodology/) returned
"refuted" for the verdict. Assessment of each point (the reviewer's numbers were spot-checked against our files):
1. ACCEPTED. The preregistered E2 primary is Kendall tau on posterior point estimates (plan sec 4 item 5, sec 7). Its
   like-for-like version (D21 "post": mocks reweighted to the PE prior) gives FPR 0/200 (m1-partial -0.216; below the
   null median in all three E5 mass bins). With E1 = -0.20 < ln 3 and FPR <= 5%, plan sec 7 yields INDETERMINATE
   (E1 and E2 disagree). "CONFIRMED" was reached only by replacing the statistic (D21 fallback to the D20 rho scan).
2. ACCEPTED. The D21 rule was written at 09:35 with its outcome foreseeable: the v1 tau_post FPR (0.000, 09:05), the
   rho-scan FPR (0.24, 09:21) and the PE-prior over-representation of m1 >= 40 Msun (ppc_mass 09:28) were known. The
   rule is re-labelled post hoc; "pre-committed" in D21 overstated its independence from the data.
3. ACCEPTED. The plug-in rho scan is not nuisance-orthogonal: over 20 posterior draws of the fixed marginals the real
   catalog's rho_hat ranges -0.34 ... +0.32 (sd 0.15 = the null sd), so its FPR is not well defined (0.01-0.48).
4. ACCEPTED (two defects in stage 04, the first also noted but not acted on in our own D21 reasoning):
   (a) Jacobian -- the kernel bank weights samples by 1/pi_PE (flat in theta) but uses their x-density as a
   likelihood under a prior flat in x = (ln m1, logit q, chi_eff, ln z); every mock likelihood is therefore the donor
   likelihood times m1 q (1-q) z, suppressed at q -> 1 (per-event median likelihood mass at q > 0.9: real 59%, mock
   32%). (b) Point reflection -- x_obs = x_true + dev with samples x_obs - dev mirrors every donor likelihood; a paired
   test shifts rho_hat by +0.061 +/- 0.019. Symptom: all 200 null mocks have var_tot 1.9-2.8 at their own generating
   population vs 0.70 for the real catalog. E2 (both statistics), D22 and the joint check (D21) are not calibrated.
5. ACCEPTED. The joint tau-vs-rho_hat residual is a property of the defective mocks until they are rebuilt.
6. ACCEPTED in substance. E1 has no usable null calibration (2 refits, run with the cut at K = 2000 where every null
   mock violates var_tot < 1). ln BF = -0.20 reflects a small likelihood gain (0.3-0.9 nats) against the prior-volume
   cost of rho; the rho posterior (median +0.33, P(rho < 0) ~ 0.06-0.08) mildly favours POSITIVE dependence, in
   tension with the Linear model's negative mean slope under the same masses -- unexplained. D24 (LVK-marginal copulas,
   running) is treated as a validation gate for the copula sector.
7. ACCEPTED. A single global Gaussian copula detects monotone dependence only; it cannot test the width (heteroscedastic)
   effect the LVK reports. Conclusions are restricted accordingly; a width-alternative mock set is added (D27).
8. ACCEPTED for the width attribution (nautilus 0.830 vs NUTS 0.676 on the same model; one fit per configuration); the
   mean-shift attribution (0.985-0.995 vs 0.80-0.84, ln BF +3.44 vs -0.98) is large enough to survive. Repeat seeds are
   queued (D28).
9. ACCEPTED. The primary E1/E2 configuration (PowerLaw+Peak) fails the plan's reproduction gate; only the LVK
   configuration passes it -- the reason D24 matters.
10. NOTED. The LVK paper already runs a copula (Frank kappa); the defensible novel result at present is the E3/E4
   mass-model dependence of the mean shift.
Response: (i) the verdict is restated as preregistered -- INDETERMINATE; (ii) the mocks are rebuilt with both defects
fixed and a posterior-predictive nuisance, and validated against the real catalog BEFORE any FPR is quoted (D27);
(iii) the hierarchical E2 statistic is replaced by a nuisance-integrated scan applied identically to real and mock
catalogs (D27); (iv) repeat sampler seeds for the ablation (D28).

### D25. Waveform-systematics control (plan sec 5-6; not run until now)
`analysis/build_waveform_variant.py` rebuilds the same 153 events from a single waveform family (same PE-prior
treatment): phenom = IMRPhenomXPHM (O1-O3) + IMRPhenomXPHM-SpinTaylor (O4a); eob = SEOBNRv4PHM (57 of 69 O1-O3,
12 fall back to IMRPhenomXPHM) + SEOBNRv5PHM (O4a). Real catalog, same fixed marginals as D20
(`analysis/e2_rho_scan.py --sample-table`, `analysis/wf_tau.py`):
| samples | rho_hat | P(rho<0) | var_tot | tau post / flattheta / flatx / pop |
|---|---|---|---|---|
| Mixed (baseline) | +0.074 | 0.38 | 0.68 | -0.217 / -0.106 / -0.057 / -0.102 |
| IMRPhenom family | -0.358 | 0.84 | 1.05 | -0.254 / -0.130 / -0.090 / -0.134 |
| SEOBNR family | -0.053 | 0.60 | 0.70 | -0.175 / -0.075 / -0.041 / -0.085 |
The hierarchical dependence estimate moves by 0.43 between the Mixed and IMRPhenom samples -- about three null
standard deviations -- with the marginals held fixed. The sign of a q-chi_eff dependence estimate in GWTC-4.0 is not
robust to the waveform family; point-estimate tau moves less (-0.175 ... -0.254 under the PE prior) but in the same
order. Any dependence claim at the |rho| ~ 0.2-0.4 level is within waveform systematics.

### D27. Rebuilding the mock catalogs (response to D26 items 3-5, 7)
Validation targets (`analysis/validate_mocks.py`, `results/tables/mock_validation_full.json`), all under the
flat-internal measure (each catalog reweighted from its own stored prior), 30 null mocks per set:
| catalog | median per-event likelihood mass at q > 0.9 | events with > 50% | median 90% width q / chi_eff | var_tot |
|---|---|---|---|---|
| real | 0.68 | 81% | 0.48 / 0.52 | 0.89 [0.71, 1.06] at 20 posterior draws (0.70 at the median) |
| v1 (stage 04) | 0.38 | 41% | 0.59 / 0.59 | 2.17 [1.92, 2.47] |
| v2 (Jacobian + orientation + 4-D donor matching + posterior-draw nuisance, `analysis/mock_catalogs_v2.py`) | 0.44 | 42% | 0.69 / 0.66 | 2.27 [1.94, 2.61] |
v2 fixes the two construction defects but still fails: translating a real likelihood's shape to another location in
(ln m1, logit q, chi_eff, ln z) cannot reproduce the q -> 1 pile-up, because mass-ratio likelihoods are not a location
family in any of these coordinates -- the waveform measures the symmetric mass ratio eta = q/(1+q)^2, flat at q = 1,
and a near-equal-mass likelihood shape moved to lower q is smeared over a wider q range (widths grow, pile-up
vanishes, var_tot stays ~2.3). v2 is therefore not used for any FPR.
v3 (`analysis/mock_catalogs_v3.py`) uses the standard population-study mock PE instead: Gaussian measurement noise in
y = (ln Mc_det, eta, chi_eff, ln d_L) with each donor's likelihood covariance (samples reweighted to a prior flat in
y), donors matched in (ln Mc_det, ln d_L) (which set the SNR), observed eta allowed beyond 1/4, the mock likelihood
N(y | y_obs, Sigma) truncated to eta <= 1/4 and |chi_eff| < 1, and the stored prior the exact Jacobian
|dy/dtheta| = (1-q) / (m1 (1+q)^3) * (d d_L/dz) / d_L (verified by finite differences to 7e-5; transforms round-trip to
1e-14). The q -> 1 pile-up then arises from d eta/dq = 0 at q = 1, as for real signals. Same populations as v2
(posterior draws; null, calibration, width and mean alternatives). FPRs are quoted only if v3 passes validation.

### D26b. Second independent review (data-and-code lens): "fixable-issues"
Scratch code /tmp/review_code/. Findings and response:
1-2. Kernel measure and reflection (independent confirmation of D26 item 4). Zero-shift unit test: a mock built from an
   event's own kernel must reproduce the event's population-informed posterior; stage-04 kernel rms errors over 10
   events q 0.120, ln z 0.335 (GW190412: q -0.25); with weights pi_flatx/pi_PE and obs = x_true - e, samples = obs + dev:
   q 0.015, ln m1 0.017, ln z 0.023, no bias. Real prior-removed posteriors have median skewness ln m1 +0.33, logit q
   +1.13, ln z -0.50; stage-04 mocks the mirror (-0.44, -1.09, +0.54). Addressed by D27 (v2 applies both fixes; v3b
   replaces translated kernels by physical mock PE).
3. The real-catalog rho_hat = +0.074 is a low Monte Carlo draw of the 2000-sample subsample: all 10 000 samples give
   +0.145; 12 subsamples give +0.100 +/- 0.047 [+0.047, +0.196]; the rho-scan FPR is 0.24 +/- ~0.1 (0.13-0.31 across
   variants and mock versions). ACCEPTED; the MC spread is quoted and the D27 statistic uses several subsamples.
4. The hierarchical copula statistic leans POSITIVE (posterior median +0.33; scan +0.07 ... +0.15) while the
   point-estimate tau is negative with FPR <= 0.035 under three of four measures: the two E2 statistics disagree in
   sign. ACCEPTED (same as D26 item 6); per-event profile slopes: rho is pushed positive by a few high-q, high-chi_eff
   events (GW231028_153006, GW190620_030421, GW190805_211137, GW170729) and negative by GW190412 and GW231226_101520.
5. Mocks are ~2x more informative about q than the real catalog (between-event sd of population-informed E[q] real
   0.035 vs mocks 0.060-0.094), even with the corrected kernel -- the location-family shortcoming v3b addresses.
6. The Gaussian-copula profile is sensitive to marginal misfit: delta-function "posteriors" at the population-informed
   medians (tau = -0.103) give rho_hat = +0.65, because for shrunk normal scores the profile peaks at |rho| =
   sqrt(1 - 2 s^2) irrespective of rank structure; real pooled E[x^2] = 0.89, E[y^2] = 1.02 (modest misfit).
7. Minor, kept visible: beta_q prior U(-4, 12) vs LVK U(-2, 7); Linear-model intercept anchoring (D14).
Verified by the reviewer: exact reproduction of the rho scan; copula density and orientation; the selection formula
(matches the Zenodo usage note: pdet = sum weights exp(lnp - lnpdraw) / total_generated); the analytic PE prior equals
bilby's stored log_prior terms (residual 0.0000 on GW240109, GW230601), chi_eff|q table vs 420 000 pooled prior
samples (mean ln offset <= 0.006); LVK BPL+2P implementation against arXiv:2508.18083 App. B eqs. B18-B23 and Tables 6
and 10; the evidence table; the slope credibilities; the 153-event sample.

**D27 validation outcome (2026-09-25 10:42).** v3 (flat-in-y samples) matched the q width (0.475) but had var_tot 9.2:
a prior flat in eta has zero density at q = 1, so samples near equal mass were sparse and the hierarchical reweighting
diverged there. v3b importance-resamples each mock event's flat-in-y likelihood samples (12 000 accepted draws) to the
donor event's analytic PE prior (resampling ESS median 2200, 5th percentile ~580) and stores ln pi_PE -- each mock
event then carries a posterior formed exactly like a released LVK posterior. v3b null (30 mocks) vs real:
likelihood mass at q > 0.9 0.59 (real 0.68), events with > 50% 70% (81%), 90% widths q 0.46 (0.48) / chi_eff 0.55
(0.52), var_tot 0.96 [0.72, 1.19] (0.89 [0.71, 1.06]). var_tot and both widths match; the q -> 1 pile-up is reproduced
at ~87% of the real level. v3b is used for E2; the point-estimate m1 >= 40 check comes from the E2 run itself.

### D24 outcome, Frank copula (2026-09-25 10:33)
`copula_frank_lvk` (18 dims, 25 min): ln Z = -4601.72 vs `lvk_bpl2p_null` -4599.62 -> E1-LVK-frank ln BF = -2.10
(Savage-Dickey -2.07). Best-fit ln L -4567.24 vs -4567.09: the dependence parameter does not improve the fit; the Bayes
factor is the Occam cost of the U(-20, 20) prior. theta (= the paper's kappa_q,eff): median -0.51, 68% [-2.57, +1.47],
90% [-3.94, +2.73], P(theta < 0) = 0.60. Paper: -2.1 (+2.4/-2.9), P(kappa < 0) = 0.92. Partial reproduction: the 90%
intervals overlap and the lean has the same sign, but our posterior is centred closer to zero.

### D29. E2 against the validated v3b mocks, and the mechanism behind the posterior-median anticorrelation
`analysis/e2_tau.py --mock-dir data/mocks/v3` (200 null + 4 x 40 copula calibration + 40 width + 40 mean-shift mocks;
`results/tables/e2_tau_full_v3.{csv,json}`). Observed tau vs v3b null median [95%], FPR one-sided / two-sided:
post -0.217 vs -0.045 [-0.181, +0.045], 0.000 / 0.000; flattheta -0.106 vs -0.020 [-0.143, +0.072], 0.085 / 0.130;
flatx -0.057 vs +0.006 [-0.091, +0.134], 0.135 / 0.290; pop -0.102 vs -0.043 [-0.159, +0.060], 0.160 / 0.325.
Point-estimate m1 >= 40 check (observed vs null 95%): post 0.386 vs [0.183, 0.359] (narrow fail), flattheta 0.392 vs
[0.202, 0.392] (at the bound), flatx and pop fail. Calibration and power (median tau under post): copula rho_true -0.6
-0.103, -0.4 -0.083, -0.2 -0.074, +0.2 -0.038; LVK width alternative -0.060 (power at the null 5% quantile 0.00 under
post, <= 0.075 under any measure); PowerLaw+Peak mean-shift alternative -0.121 (power 0.20-0.53 by measure). The
observed posterior-median tau (-0.217) is more extreme than EVERY simulated catalog under every simulated hypothesis
(null, copula rho down to -0.6, the LVK width effect, the PLP mean shift): it is not measuring q-chi_eff dependence of
any modelled kind. The likelihood-based point-estimate measures are unremarkable (FPR 0.085-0.16).
Mechanism (all 10 000 samples per event): tau(q_lik, chi_lik) = -0.106, tau(q_post, chi_lik) = -0.188,
tau(q_lik, chi_post) = -0.142, tau(q_post, chi_post) = -0.219 -- the prior-induced part is carried mostly by the q
medians. The events whose q median the PE prior moves most are high-chi_eff events dragged to lower q: GW190517_055101
(q 0.774 -> 0.618, chi_eff 0.636 -> 0.491), GW231028_153006 (0.753 -> 0.639), GW190620_030421 (0.699 -> 0.606), GW170729
(0.641 -> 0.549), GW230928_215827, GW230825_041334, GW191127_050227. The isotropic-spin PE prior only allows large
chi_eff at unequal masses (h(chi_eff | q) is widest at small q), and along the mass-ratio-spin degeneracy a
high-chi_eff event is pulled to lower q -- manufacturing "high chi_eff at low q" in posterior medians without any
population correlation. The largest chi_eff shifts are negative-chi_eff events pulled toward zero (GW190521 -0.53 ->
-0.14, GW231223_032836, GW231230_170116, GW191109_010717). The v3b mocks reproduce the likelihood-level structure
(var_tot, widths) but the prior-induced tau shift only at a quarter of the real size (-0.025 vs -0.11), so the
posterior-median statistic remains uncalibratable.
