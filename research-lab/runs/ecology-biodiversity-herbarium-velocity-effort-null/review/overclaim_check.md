# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Two-thirds of the median herbarium plant range velocity is reproduced by sampling noise and shifting collecting effort alone: a fixed-range null gives 4.6 km/yr against an observed 6.9 | primary.json H1 4.608 vs 6.906, ratio 0.667 | Supported | 'median' added |
| 2 | standfirst | GBIF preserved-specimen records of vascular plants (2026-07-01 snapshot; 30.6 million records after cleaning) were thinned to 5-arcmin cells, and each species' centroid displacement between 1970–2000 and 2001–2024 was compared with 999 null replicates. | clean_summary.json 30,622,400 | Supported |  |
| 3 | standfirst | The replicates keep its range fixed and move only which records fall in which period, at random or according to where collectors worked in each period. | velocity.py nulls | Supported |  |
| 4 | standfirst | The plan, the cleaning, null and analysis code, and two pre-result fixes (D1, D2) were committed before any velocity was computed. | git order: plan f89982c 06:38, code and D1 de9a707, analyse 244079d, SDM code f2ef50e, D2 d28f614 09:14; first velocity output 09:15 | Supported |  |
| 5 | verdict | **Verdict: H1 Supported.** A null with fixed ranges reproduces 67% of the observed median velocity. | primary.json H1 ratio 0.6671 | Supported |  |
| 6 | verdict | **H1 (a noise-plus-effort null with fixed ranges reproduces at least half of the observed median velocity): Supported.** | plan.md H1 | Supported |  |
| 7 | verdict | Observed median velocity: **6.9 km/yr** for 69,596 species with at least 10 thinned cells in each period. | primary.json H1 median_observed 6.906, species 69,596 | Supported |  |
| 8 | verdict | Median of the species' null medians: **4.6 km/yr**. | primary.json H1 median_effort_null 4.608 | Supported |  |
| 9 | verdict | Ratio **0.67** (95% species bootstrap 0.66 to 0.67), against the preregistered bar of 0.5. | primary.json H1 ci 0.6613-0.673 | Supported |  |
| 10 | verdict | **Sampling noise alone** (records reassigned between periods at random) gives 2.8 km/yr: a ratio of 0.41 (0.40 to 0.41). | primary.json H1 noise 2.797, ratio 0.405 (0.4014-0.4088) | Supported |  |
| 11 | verdict | The rest of the null's velocity comes from the shift in where specimens were collected. | noise vs effort null construction (velocity.py) | Supported |  |
| 12 | verdict | **Movement beyond the null, in a minority.** | primary.json H1 exceed 0.3603 | Supported | 'Real movement' removed: excess may include unmodelled artefacts |
| 13 | verdict | 36% of species move farther than their own null's 95th percentile (5% would be expected if every range were fixed). | primary.json H1 exceed_effort_p95 0.3603; plan 5% | Supported |  |
| 14 | verdict | The typical species exceeds its null median by 1.9 km/yr (1.8 to 1.9). | primary.json H1 median_excess 1.8704 (1.8344-1.9094) | Supported |  |
| 15 | verdict | 53.6% of species move poleward, against 50.8% under the null (median poleward shift 9.4 km against 0.3 km). | primary.json direction 0.5364 / 0.5077; 9.42 / 0.28 km | Supported |  |
| 16 | verdict | **Robust.** The ratio stays between 0.64 and 0.71 across latitude bands, cell-count classes, thresholds of 20 and 50 cells, 30-arcmin thinning, 30-arcmin and 2° effort grids, arithmetic centroids, and cleaning without the dense-point rule. | primary.json by_latitude_band, by_cells, robustness: 0.642-0.710 | Supported |  |
| 17 | verdict | Every interval lies above 0.5. | robustness ci lower bounds >= 0.636 | Supported |  |
| 18 | verdict | **SDM-centroid variant** (1,000 species): modelling each period's range does not remove the effect. | sdm_variant.json ratio 0.7386 | Supported |  |
| 19 | verdict | Modelled-range centroids move at a median of 8.4 km/yr. | sdm_variant.json median_v_sdm_obs 8.439 | Supported |  |
| 20 | verdict | One fixed-range null replicate per species gives 6.2 km/yr: a ratio of 0.74 (0.68 to 0.82). | sdm_variant.json 6.233; ci 0.6764-0.8153 | Supported | one replicate per species, stated |
| 21 | verdict | **Reproduction.** Our observed median is 6.5–6.9 km/yr depending on the threshold, against Daru et al.'s 5.6 km/yr. | reproduction.csv 6.511-6.906; ledger A1 | Supported |  |
| 22 | verdict | At five cells per period we have 101,328 species, against their 109,242. | reproduction.csv 5 cells 101,328; ledger A1 | Supported |  |
| 23 | plain terms | A recent study used millions of museum plant specimens to estimate that over 100,000 plant species have shifted their ranges at a median of 5.6 km a year since the 1970s–1990s, faster than models predict for the coming decades. | ledger A1, A10 | Supported |  |
| 24 | plain terms | But the centre of a range estimated from a few dozen specimens moves around by chance. | noise-only null 2.8 km/yr; test_velocity.py | Supported |  |
| 25 | plain terms | Botanists also collect in different places from decade to decade. | ledger A3 (Daru et al. 2018) | Supported |  |
| 26 | plain terms | Both of these make ranges look as if they are moving even when they are not. | noise and effort nulls | Supported |  |
| 27 | plain terms | We rebuilt the measurement from the open GBIF data and found a somewhat higher figure: 6.9 km a year. | primary.json H1 6.906 vs 5.6 | Supported | was 'a similar figure' |
| 28 | plain terms | Then, for each of nearly 70,000 species, we kept its range exactly where it was and reshuffled which specimens counted as "early" and which as "late", 999 times. | velocity.py nulls (999) | Supported |  |
| 29 | plain terms | The reshuffles followed where collectors were actually working in each period. | effort null with LOSO 1-degree effort | Supported |  |
| 30 | plain terms | With no real movement at all, this produced 4.6 km a year: two-thirds of the observed figure. | primary.json H1 4.608 / 6.906 | Supported |  |
| 31 | plain terms | So most of the headline speed is noise and changing collecting effort. | primary.json H1 ratio 0.667 | Supported |  |
| 32 | plain terms | Real shifts are probably there: about a third of species moved more than chance and our model of effort can explain, with a slight tilt towards the poles. | primary.json H1 exceed 0.36; direction 0.536 vs 0.508 | Supported | 'probably' and 'our model of effort' added |
| 33 | plain terms | But a velocity like 5.6 km a year cannot be read as how fast plants are moving until it is compared with this baseline. | ratio 0.667 | Supported | was 'until this baseline is subtracted' |
