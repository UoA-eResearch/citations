# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | A rainfall-and-season model does not predict seismic velocity changes under the Auckland Volcanic Field: no hydrological baseline at 0.5–2 Hz, and a noise floor near 0.14% | primary.json median_heldout_r2 -0.124, share >=0.5 = 0; median_resid_2sd_pct 0.136 | Supported | was 'Rainfall and season do not predict...' (Overstated: the report says hydrology's effect is not excluded); narrowed to 'A rainfall-and-season model' |
| 2 | standfirst | Daily ambient-noise cross-correlations for 55 vertical-component pairs of 11 GeoNet stations, 2013 to September 2026. dv/v is measured by stretching the coda at 0.5–2 Hz. | pairs.csv 55 ZZ pairs; 11 stations; correlate.log 2013-01-01 onward; dvv_daily.parquet | Supported |  |
| 3 | standfirst | A rainfall-diffusion, annual and drift model is fitted on 2013–2020 and tested, unchanged, from 2021. | plan.md section 2; fit.csv (train 2013-2020, held out from 2021, no refit) | Supported |  |
| 4 | standfirst | The plan was committed before any waveform was correlated. | git: plan 18fd367 10:38, correlation code 0d69233 10:40; correlate.log starts after | Supported |  |
| 5 | verdict | **Verdict: H1 Refuted.** | primary.json verdict Refuted | Supported |  |
| 6 | verdict | **H1 (the hydrological model explains most of the held-out dv/v): Refuted.** | plan.md H1 definition | Supported |  |
| 7 | verdict | The median held-out R² across the 32 scored pairs is **−0.12** (95% pair bootstrap −0.67 to −0.03). | primary.json -0.1238 (-0.6712 to -0.0281), 32 pairs | Supported |  |
| 8 | verdict | No pair reaches 0.5. | primary.json share_pairs_r2_ge_0_5 = 0 | Supported |  |
| 9 | verdict | The model explains little even in training: median R² 0.19. | secondary.json coherence.median_train_r2_scored 0.188 | Supported |  |
| 10 | verdict | **It is not one modelling choice.** All of these leave the median between −0.12 and −0.14: | secondary temperature -0.134; every_epoch -0.124; posthoc_drift -0.137; posthoc_kernel -0.123 | Supported |  |
| 11 | verdict | temperature in place of the annual sinusoid; | secondary.json temperature.median_heldout_r2 -0.134 | Supported |  |
| 12 | verdict | every sensor-epoch boundary treated as a break; | secondary_every_epoch.json -0.124 | Supported |  |
| 13 | verdict | holding the drift term fixed (post hoc); | posthoc_drift.json -0.137 (labelled post hoc) | Supported |  |
| 14 | verdict | a draining instead of a cumulative rainfall kernel (post hoc). | posthoc_kernel.json -0.123 (labelled post hoc) | Supported |  |
| 15 | verdict | **The noise floor is 0.14%,** twice the held-out residual SD as a median across pairs, and 0.09% even with every sensor change treated as a break. | primary 0.136%; every_epoch 0.094% | Supported |  |
| 16 | verdict | That is above the roughly 0.1% velocity resolution reported at Piton de la Fournaise (Brenguier et al. 2008). | attribution A12 (Brenguier 2008 text: perturbations as small as 0.1%) | Supported | replaces 'nearly three times the 0.05% the lead hoped for' (the 0.05% source claim failed G6, A2) |
| 17 | verdict | The lead's 0.05% target is not supported by that source: the 0.05% figure does not appear in its text (G6). | attribution A2 (not found in abstract or preprint text) | Supported |  |
| 18 | verdict | **Neither the March 2020 lockdown nor the record-wet January–February 2023 shows up.** | primary.json lockdown 2/32 beyond 2 SD; secondary jan_feb_2023 1/18; attribution A8 (NIWA: wettest month on record) | Supported |  |
| 19 | verdict | Lockdown: median step +0.007%; 2 of 32 pairs beyond twice their residual SD. | primary.json lockdown median_step 0.0068%, 2 pairs | Supported |  |
| 20 | verdict | 2023 storms: median held-out residual +0.017% in 18 pairs; 1 beyond twice its residual SD. | secondary.json jan_feb_2023 median 0.0173%, 18 pairs, 1 beyond | Supported |  |
| 21 | plain terms | Volcanoes can announce themselves by subtly changing how fast seismic waves travel through the ground. | attribution A1 (Brenguier 2008: velocity decreases before five eruptions) | Supported |  |
| 22 | plain terms | Background "noise" from waves, wind and traffic can be used to track those changes day by day. | attribution A5 (AVF noise sources: ocean microseism and cultural noise) | Supported |  |
| 23 | plain terms | Before such a signal can warn of anything under Auckland, we need to know how much it moves for ordinary reasons, mainly rain soaking into the ground and the seasons. | attribution A3, A4 (rain and groundwater drive dv/v elsewhere) | Supported |  |
| 24 | plain terms | We processed 13 years of continuous recordings from 11 GeoNet seismometers across Auckland's volcanic field. | 2013-01 to 2026-09 (13.7 years); 11 stations | Supported |  |
| 25 | plain terms | We built a model of how rain and the seasons should change the wave speeds, trained it on 2013–2020, and checked whether it predicted 2021–2026. | plan.md; fit.csv | Supported |  |
| 26 | plain terms | It did not. | primary.json Refuted; 25 of 32 pairs negative held-out R2 | Supported |  |
| 27 | plain terms | On 25 of the 32 station pairs with clean enough signals, the model predicted the later years worse than simply guessing their average. | fit.csv: 25 of 32 scored pairs heldout_r2 < 0 | Supported | was 'On the 32 station pairs ... worse than guessing the average' (true of 25, not all 32) |
| 28 | plain terms | The wave speeds wander by about 0.14% for reasons the model cannot account for. | primary.json median_resid_2sd_pct 0.136 (two residual SDs) | Supported |  |
| 29 | plain terms | Even the very wet 2023 summer, including Cyclone Gabrielle, left no clear mark. | secondary.json jan_feb_2023 1 of 18 beyond 2 SD; attribution A8 | Supported |  |
| 30 | plain terms | A volcanic signal would need to stand out above that level to be seen with this method, so Auckland's monitoring cannot yet rely on a simple rain-and-season baseline at these frequencies. | noise floor 0.136% at 30-day smoothing; plain conditional on these frequencies | Supported |  |
