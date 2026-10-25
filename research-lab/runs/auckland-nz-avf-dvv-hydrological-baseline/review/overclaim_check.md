# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | A rainfall-and-season model does not predict seismic velocity changes under the Auckland Volcanic Field: no hydrological baseline at 0.5–2 Hz, and month-scale wander of about 0.07% | primary median R2 -0.265; floors_d1 nomodel 0.074%, season-only 0.067% | Supported | was 'a noise floor near 0.14%' (v1 residual of a failed model, inflated by KBAZ artefacts) |
| 2 | standfirst | Daily ambient-noise cross-correlations for 55 vertical-component pairs of 11 GeoNet stations, 2013 to September 2026. dv/v is measured by stretching the coda at 0.5–2 Hz. | pairs.csv; 11 stations | Supported |  |
| 3 | standfirst | A rainfall-diffusion, annual and drift model is fitted on 2013–2020 and tested, unchanged, from 2021. | plan.md; fit.csv | Supported |  |
| 4 | standfirst | The plan was committed before any waveform was correlated. | git order (review: provenance clean) | Supported |  |
| 5 | standfirst | This version includes fixes made after independent review (D1): a sensor polarity flip and a dead-channel block at KBAZ, and the noise-floor framing. | deviations.md D1 | Supported |  |
| 6 | verdict | **Verdict: H1 Refuted.** | primary verdict Refuted | Supported |  |
| 7 | verdict | **H1 (the hydrological model explains most of the held-out dv/v): Refuted.** | plan.md H1 | Supported |  |
| 8 | verdict | The median held-out R² across the 31 scored pairs is **−0.27** (95% pair bootstrap −0.35 to −0.15). | primary -0.2651 (-0.3458 to -0.1528), 31 pairs | Supported |  |
| 9 | verdict | 26 of the 31 are negative, and no pair reaches 0.5. | pairs_negative_r2 26; share >= 0.5 = 0 | Supported |  |
| 10 | verdict | The model explains little even in training: median R² 0.17. | secondary coherence median_train_r2_scored 0.168 | Supported |  |
| 11 | verdict | **It is not one modelling choice.** Every variant of the full model leaves the median between −0.18 and −0.27: | secondary_every_epoch -0.178; temperature -0.264; posthoc_drift -0.242; posthoc_kernel -0.232 | Supported |  |
| 12 | verdict | every sensor-epoch boundary as a break, with references recomputed (−0.18); | secondary_every_epoch.json -0.1775 (references recomputed, RULE=every_epoch) | Supported |  |
| 13 | verdict | temperature in place of the annual sinusoid (−0.26); | secondary temperature -0.2637 | Supported |  |
| 14 | verdict | the drift held fixed (−0.24, post hoc); | posthoc_drift -0.2422 (post hoc) | Supported |  |
| 15 | verdict | a draining rainfall kernel (−0.23, post hoc). | posthoc_kernel -0.2323 (post hoc) | Supported |  |
| 16 | verdict | **Even a season-only model,** without rain or drift, is worse than the held-out mean (median −0.08), though it beats the full model on 23 of 31 pairs. | floors_d1 median_season_only_r2 -0.083; season-only beats full on 23 of 31 (fit.csv) | Supported |  |
| 17 | verdict | **How much dv/v wanders.** At 30-day smoothing, the held-out dv/v varies by **0.074%** (2 SD about its own mean, median across pairs). | floors_d1 median_nomodel_2sd_pct 0.0737 | Supported |  |
| 18 | verdict | The preregistered residual floor (2 SD of the model residual) is 0.076%. | median_resid_2sd_pct 0.0763 | Supported |  |
| 19 | verdict | A season-only model leaves 0.067%. | median_season_only_2sd_pct 0.0671 | Supported |  |
| 20 | verdict | Pre-eruptive velocity decreases at Piton de la Fournaise were of the order of 0.05% (Brenguier et al. 2008), so a precursor of that size would sit inside Auckland's ordinary month-scale wander at these frequencies. | ledger A2 (published abstract: decreases of order 0.05%) | Supported | replaces the pre-review gate's wrong 'not supported' sentence (A2 corrected to the version of record) |
| 21 | verdict | **Neither the March 2020 lockdown nor the record-wet January–February 2023 shows up.** | lockdown 2/31 beyond; 2023 1/17 beyond | Supported |  |
| 22 | verdict | Lockdown: the median step is +0.005% (−0.000% with a 15-day guard against the smoother), and 2 of 31 pairs lie beyond twice their residual SD (3 with the guard). | lockdown median 0.0053%, guarded -0.0004%; 2 and 3 beyond | Supported |  |
| 23 | verdict | 2023 storms: the median held-out residual is +0.027% in 17 pairs, with 1 beyond twice its residual SD. | secondary jan_feb_2023 17 pairs, median 0.0265%, 1 beyond (AWAZ-HBAZ) | Supported |  |
| 24 | verdict | **Review fixes (D1).** KBAZ flipped polarity across a 2014–2018 data gap and had a 52-day dead-channel block, both of which entered the first version's references. | review finding 1; coverage.json dead channel 852; segments.csv KBAZ splits | Supported |  |
| 25 | verdict | Segments now break on dip changes and data gaps; dead and polarity-mismatched days are dropped and counted; stretching uses a cubic spline. | dvv.py D1; coverage.json | Supported |  |
| 26 | verdict | The first version (median −0.12, floor 0.136%) is kept in `results/tables/v1_pre_review/`. | results/tables/v1_pre_review/primary.json -0.1238, 0.136% | Supported |  |
| 27 | plain terms | Volcanoes can announce themselves by subtly changing how fast seismic waves travel through the ground. | ledger A1 | Supported |  |
| 28 | plain terms | Background "noise" from ocean waves and city traffic can be used to track those changes day by day. | ledger A5 (ocean noise) and A6 (cultural noise) | Supported | was 'waves, wind and traffic' (A5/A6 support ocean and cultural sources) |
| 29 | plain terms | Before such a signal can warn of anything under Auckland, we need to know how much it moves for ordinary reasons, mainly rain soaking into the ground and the seasons. | ledger A3, A4 | Supported |  |
| 30 | plain terms | We processed 13 years of continuous recordings from 11 GeoNet seismometers across Auckland's volcanic field. | 2013-01 to 2026-09; 11 stations | Supported |  |
| 31 | plain terms | We built a model of how rain and the seasons should change the wave speeds, trained it on 2013–2020, and checked whether it predicted 2021–2026. | plan.md | Supported |  |
| 32 | plain terms | It did not. | primary Refuted | Supported |  |
| 33 | plain terms | On 26 of the 31 station pairs with clean enough signals, the model predicted the later years worse than simply guessing their average. | pairs_negative_r2 26 of 31 | Supported | recounted after D1 (was 25 of 32) |
| 34 | plain terms | Averaged over a month, the wave speeds wander by about 0.07% for reasons the model cannot account for, the same order as the changes seen before eruptions at a much-studied French volcano. | nomodel 0.074%; ledger A2 (0.05% precursors) | Supported |  |
| 35 | plain terms | Even the very wet 2023 summer, including Cyclone Gabrielle, left no clear mark. | jan_feb_2023 1 of 17 beyond 2 SD | Supported |  |
| 36 | plain terms | So Auckland's monitoring cannot yet rely on a simple rain-and-season baseline at these frequencies. | primary Refuted; season-only also below 0 | Supported |  |
