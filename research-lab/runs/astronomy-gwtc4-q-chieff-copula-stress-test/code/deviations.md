
### D17. Single-ingredient ablation of the LVK configuration (added 2026-09-11 21:45, runs after the main chain)
E4 shows the chi_eff-mean shift is robust to the pairing function (baseline_bpq_both: P(delta mu < 0) = 0.995) and to a
flexible 14-node spline primary-mass model (baseline_splm1_both: 0.985), yet it disappears under the LVK Broken Power
Law + 2 Peaks configuration (lvk_bpl2p_both: 0.80). That configuration bundles several ingredients: the mass shape
(a narrow ~10 Msun peak carrying ~56% of the population, m_high pinned at 300), a separate m2 taper (m2,low ~ 4 Msun
vs the shared m1 taper at ~5 Msun), and the log-uniform sigma_0 prior of Table 10. To attribute the change, four
models each alter ONE ingredient (all with both Linear-spin slopes free):
* `abl_plp_m2taper_both`      PowerLaw+Peak masses + separate m2 taper (m2,low ~ U(3, mmin), delta_m2 ~ U(0, 10));
* `abl_plp_lvkspin_both`      PowerLaw+Peak masses + log-uniform sigma_0 (ln sigma_0 ~ U(-5, 0));
* `abl_bpl2p_sharedtaper_both` LVK masses with the shared m1/m2 taper (no m2,low / delta_m2);
* `abl_bpl2p_plpspin_both`    LVK masses with the uniform sigma_0 in [0.02, 1].
Metric: the gate credibilities P(delta mu < 0) / P(delta ln sigma < 0) (no null variants are fitted; the evidence-based
E3 decomposition exists for the two end-points). `resolve_derived` now also derives m2,low for models with a directly
sampled mmin. Diagnostics write `slope_credibilities_full.csv` (every fitted model with both slopes free) and a table in
summary_full.md. Not preregistered; reported as an exploratory attribution of the E4 result.
