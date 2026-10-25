# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | A rainfall-and-season model does not predict seismic velocity changes under the Auckland Volcanic Field: no hydrological baseline at 0.5–2 Hz, and month-scale wander of about 0.08% | primary -0.083; floors nomodel 0.077%, season 0.075% | Supported | was 'a noise floor near 0.14%' (v1 residual, inflated by KBAZ artefacts) |
| 2 | standfirst | Daily ambient-noise cross-correlations for 55 vertical-component pairs of 11 GeoNet stations, 2013 to September 2026. dv/v is measured by stretching the coda at 0.5–2 Hz. | pairs.csv; 11 stations | Supported |  |
| 3 | standfirst | A rainfall-diffusion, annual and drift model is fitted on 2013–2020 and tested, unchanged, from 2021. | plan.md; fit.csv | Supported |  |
| 4 | standfirst | The plan was committed before any waveform was correlated. | git order (review: provenance clean) | Supported |  |
| 5 | standfirst | This version includes fixes made after independent review (D1): a sensor polarity flip and a dead-channel block at KBAZ, and the noise-floor framing. | deviations.md D1 and addendum | Supported |  |
| 6 | verdict | **Verdict: H1 Refuted.** | primary verdict Refuted | Supported |  |
| 7 | verdict | **H1 (the hydrological model explains most of the held-out dv/v): Refuted.** | plan.md H1 | Supported |  |
| 8 | verdict | The median held-out R² across the 33 scored pairs is **−0.08** (95% pair bootstrap −0.19 to −0.01). | primary -0.0829 (-0.1909 to -0.0130), 33 pairs | Supported |  |
| 9 | verdict | 24 of the 33 are negative, and no pair reaches 0.5. | pairs_negative_r2 24; share >= 0.5 = 0 | Supported |  |
| 10 | verdict | The model explains little even in training: median R² 0.19. | coherence median_train_r2_scored 0.188 | Supported |  |
| 11 | verdict | **It is not one modelling choice.** Every variant of the full model leaves the median negative: | every_epoch -0.145, temperature -0.073, drift -0.115, kernel -0.104, gap7 -0.265 | Supported |  |
| 12 | verdict | every sensor-epoch boundary as a break, with references recomputed (−0.15); | secondary_every_epoch -0.1451 (references recomputed) | Supported |  |
| 13 | verdict | temperature in place of the annual sinusoid (−0.07); | secondary temperature -0.0725 | Supported |  |
| 14 | verdict | the drift held fixed (−0.12, post hoc); | posthoc_drift -0.1152 | Supported |  |
| 15 | verdict | a draining rainfall kernel (−0.10, post hoc); | posthoc_kernel -0.1044 | Supported |  |
| 16 | verdict | segments split at data gaps of more than 7 days instead of 90 (−0.27). | secondary_gap7 -0.2651 | Supported |  |
| 17 | verdict | **Even a season-only model,** without rain or drift, is slightly worse than the held-out mean (median −0.02). | floors_d1 median_season_only_r2 -0.018 | Supported |  |
| 18 | verdict | It beats the full model on 17 of 33 pairs. | fit.csv season_only_r2 > heldout_r2 for 17 of 33 | Supported |  |
| 19 | verdict | **How much dv/v wanders.** At 30-day smoothing, the held-out dv/v varies by **0.077%** (2 SD about its own mean, median across pairs). | floors_d1 median_nomodel_2sd_pct 0.0768 | Supported |  |
| 20 | verdict | The preregistered residual floor (2 SD of the model residual) is 0.088%. | median_resid_2sd_pct 0.0884 | Supported |  |
| 21 | verdict | A season-only model leaves 0.075%. | median_season_only_2sd_pct 0.0745 | Supported |  |
| 22 | verdict | Pre-eruptive velocity decreases at Piton de la Fournaise were of the order of 0.05% (Brenguier et al. 2008), so a precursor of that size would sit inside Auckland's ordinary month-scale wander at these frequencies. | ledger A2 (published abstract: decreases of order 0.05%) | Supported | replaces the pre-review gate's wrong 'not supported' sentence |
| 23 | verdict | **Neither the March 2020 lockdown nor the record-wet January–February 2023 shows up.** | lockdown 2/33 beyond; 2023 0/19 beyond | Supported |  |
| 24 | verdict | Lockdown: the median step is +0.001% (−0.002% with a 15-day guard against the smoother), and 2 of 33 pairs lie beyond twice their residual SD. | lockdown median 0.0010%, guarded -0.0015%; 2 beyond | Supported |  |
| 25 | verdict | 2023 storms: the median held-out residual is +0.025% in 19 pairs, with none beyond twice its residual SD. | jan_feb_2023 19 pairs, median 0.0246%, 0 beyond | Supported |  |
| 26 | verdict | **Review fixes (D1).** | heading | Supported |  |
| 27 | verdict | KBAZ flipped polarity across a 2014–2018 data gap and had a 52-day dead-channel block, both of which entered the first version's references. | review finding 1; coverage dead channel 852; segments.csv KBAZ splits | Supported |  |
| 28 | verdict | Segments now break on dip changes and on data gaps of more than 90 days. | dvv.py segments (gap_days 90) | Supported |  |
| 29 | verdict | Dead and polarity-mismatched days are dropped and counted, and stretching uses a cubic spline. | coverage.json drops; dvv.py cubic spline | Supported |  |
| 30 | verdict | A first fix that split segments at gaps of more than 7 days cut many records at routine outages and gave −0.27. | secondary_gap7.json -0.2651; confirmation finding 9 | Supported |  |
| 31 | verdict | It is kept as a sensitivity. | secondary_gap7.json | Supported |  |
| 32 | verdict | The first version (median −0.12, floor 0.136%) is kept in `results/tables/v1_pre_review/`. | v1_pre_review/primary.json -0.1238, 0.136% | Supported |  |
| 33 | plain terms | Volcanoes can announce themselves by subtly changing how fast seismic waves travel through the ground. | ledger A1 | Supported |  |
| 34 | plain terms | Background "noise" from ocean waves and city traffic can be used to track those changes day by day. | ledger A5 (ocean noise) and A6 (cultural noise) | Supported |  |
| 35 | plain terms | Before such a signal can warn of anything under Auckland, we need to know how much it moves for ordinary reasons, mainly rain soaking into the ground and the seasons. | ledger A3, A4 | Supported |  |
| 36 | plain terms | We processed 13 years of continuous recordings from 11 GeoNet seismometers across Auckland's volcanic field. | 2013-01 to 2026-09; 11 stations | Supported |  |
| 37 | plain terms | We built a model of how rain and the seasons should change the wave speeds, trained it on 2013–2020, and checked whether it predicted 2021–2026. | plan.md | Supported |  |
| 38 | plain terms | It did not. | primary Refuted | Supported |  |
| 39 | plain terms | On 24 of the 33 station pairs with clean enough signals, the model predicted the later years worse than simply guessing their average. | pairs_negative_r2 24 of 33 | Supported | recounted (was 25 of 32 in v1) |
| 40 | plain terms | Averaged over a month, the wave speeds wander by about 0.08% for reasons the model cannot account for, the same order as the changes seen before eruptions at a much-studied French volcano. | nomodel 0.077%; ledger A2 (0.05% precursors) | Supported |  |
| 41 | plain terms | Even the very wet 2023 summer, including Cyclone Gabrielle, left no clear mark. | jan_feb_2023 0 of 19 beyond 2 SD | Supported |  |
| 42 | plain terms | So Auckland's monitoring cannot yet rely on a simple rain-and-season baseline at these frequencies. | primary Refuted; season-only -0.02 | Supported |  |
