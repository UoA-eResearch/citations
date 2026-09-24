# Superseded results (moved 2026-09-25)

* `ppc_full.csv`, `ppc_taus_full.npy`, `full_F9_ppc.*` -- the E5 posterior-predictive check of 2026-09-11. It compared
  PE-prior posterior medians of the real events with predictions built from likelihood-centred mock kernels (the
  measure mismatch described in deviations D19/D21). Replaced by the per-mass-bin comparison against the null mocks
  under matched measures (`results/tables/e5_mass_bins_full.csv`, figure F15).
* `e2_tau_full.v1_measure_mismatch.*` -- first E2 tau run (D19): real flat-theta medians against mock flat-internal
  medians. Superseded by the four-measure v2 (D21).
* `mock_stats_full_partial.csv` -- stage-05 rows for the real catalog and null mocks 0-1 before the reboot. Its rho_MAP
  and profile-LR columns are invalid (MAP bug, D20); its nautilus columns (ln Z of the two mock refit pairs) are valid
  and are quoted in D20.
