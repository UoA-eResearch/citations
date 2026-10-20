# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-20 21:33 NZDT — data coverage, a placebo year added, and the prior preprint

Recorded after the registration series was built and before any effect was interpreted.

1. **The register service runs to September 2026, not March.** NZTA's ArcGIS service is named `MVR_Mar26` but
   carries first registrations through September 2026, so the window is 2021-01 to 2026-09 (1,419,410 light-vehicle
   first registrations) rather than ending in early 2026. That is 2.5 years after the road-user-charge change,
   which lets the report follow the recovery as well as the shock.
2. **A fourth placebo year.** The plan named placebo difference-in-differences at 1 April 2022, 2023 and 2025. The
   code also runs 2026, because the window reaches it. It is reported with the others and, as it happens, is the
   largest of them.
3. **Closest prior work could not be read in full.** The novelty recheck found a 2026 Research Square preprint
   (rs-11080967) estimating the Clean Car Discount's removal by regression discontinuity in time, reported as an
   immediate and lasting fall of about 24 percentage points in battery-electric share. Only its title was
   retrievable, so this study compares against the figure reported in secondary sources and does not claim
   priority on the Clean Car Discount effect. Its "lasting" characterisation is testable here, because this window
   extends to September 2026.
4. **Everything else is as preregistered**: the groups, the two events, both hypotheses and their decision rules,
   the estimation window for the baseline, the donut around April 2024, and the block bootstrap.
