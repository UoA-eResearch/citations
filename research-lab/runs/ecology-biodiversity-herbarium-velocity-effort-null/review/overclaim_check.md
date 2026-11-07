# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | At least two-fifths of the median herbarium plant range velocity is sampling noise; a collecting-effort null reproduces two-thirds, but that null cannot tell collectors moving from plants moving together | primary.json noise ratio 0.405, effort ratio 0.667; absorption_test.json all-move ratio 1.03 | Supported | retitled after review |
| 2 | standfirst | GBIF preserved-specimen records of vascular plants (2026-07-01 snapshot; 30.6 million records after cleaning) were thinned to 5-arcmin cells, and each species' centroid displacement between 1970–2000 and 2001–2024 was compared with 999 null replicates. | clean_summary.json 30,622,400 | Supported |  |
| 3 | standfirst | The replicates keep the species' own records and move only which of them fall in which period: at random, or according to where all other species' records fell in each period. | velocity.py nulls (records reassigned; LOSO effort surface) | Supported | reworded |
| 4 | standfirst | The plan, the cleaning, null and analysis code, and two pre-result fixes (D1, D2) were committed before any velocity was computed. | git order: plan f89982c 06:38, code and D1 de9a707, analyse 244079d, SDM code f2ef50e, D2 d28f614 09:14; first velocity output 09:15 | Supported |  |
| 5 | verdict | **Verdict: H1 Supported under the preregistered rule (ratio 0.67 against a bar of 0.5), but the design does not identify what the rule was meant to test.** The effort null's effort surface is built from all other species' records, so it moves when ranges move together, as well as when collectors move. | primary.json H1 Supported 0.667; absorption_test.json | Supported | qualified |
| 6 | verdict | **What the data identify.** | section heading | Supported |  |
| 7 | verdict | **Sampling noise:** records reassigned between periods at random give **2.8 km/yr** against an observed | primary.json noise-only median 2.80 | Supported |  |
| 8 | verdict | **6.9 km/yr**, for 69,596 species with at least 10 thinned cells in each period. | primary.json observed 6.91, 69,596 species | Supported |  |
| 9 | verdict | That is a ratio of **0.41** (95% species bootstrap 0.40 to 0.41), so at least two-fifths of the median velocity is noise. | primary.json noise ratio 0.405 (0.401-0.409) | Supported |  |
| 10 | verdict | In synthetic worlds this null stays at the noise level whether or not ranges move. | absorption_test.json noise_null_med 1.89-1.92 in all worlds | Supported |  |
| 11 | verdict | **A poleward excess:** the median species moves 9.4 km poleward over 28 years (0.34 km/yr), against 0.3 km under the effort null and −0.6 km under the noise null; 53.6% of species move poleward, against 50.8% under the effort null. | nulls_primary.parquet pole_km median 9.4; effort_pole_med 0.3; noise_pole_med -0.6; share 0.536 vs 0.508 | Supported |  |
| 12 | verdict | The effort surface itself drifted only mildly poleward: its mean absolute latitude went from 30.6° to 31.8°, the tropical share fell from 34.5% to 32.3% and the boreal share rose from 10.9% to 13.2%. | effort_surface.json P1 30.56 / P2 31.79; tropical 0.345->0.323; boreal 0.109->0.132 | Supported |  |
| 13 | verdict | **What the effort null reproduces, and why it is not "fixed ranges".** | section heading | Supported |  |
| 14 | verdict | The noise-plus-effort null gives 4.6 km/yr: a ratio of **0.67** (0.66 to 0.67). | primary.json effort median 4.61, ratio 0.667 (0.661-0.673) | Supported |  |
| 15 | verdict | The preregistration and the first draft read this as "fixed ranges plus noise and effort reproduce two-thirds of the velocity". | plan.md H1; first-draft title | Supported |  |
| 16 | verdict | **That reading is not identified** (synthetic test, post hoc; `results/tables/absorption_test.json`). | absorption_test.json | Supported |  |
| 17 | verdict | Run through this study's own code with uniform, unchanging collecting effort, a world where every species really moves 1° north is scored by the effort null as fully reproduced (ratio 1.03; 5% exceed its 95th percentile). | absorption_test.json all move: ratio_effort 1.03, exceed_effort_p95 0.05 | Supported |  |
| 18 | verdict | When half the species move, the movers' ratio is 0.70; when a fifth move, 0.60. | absorption_test.json half movers 0.70; fifth movers 0.60 | Supported |  |
| 19 | verdict | The observed 0.67 is also what a world with shared real shifts and no effort change can produce. | absorption_test.json ratios 0.60-0.70 for partial shared shifts | Supported | softened |
| 20 | verdict | So the 26% between the noise floor and the effort null mixes changing collecting effort with range shifts that many species share. | primary.json 0.667 - 0.405; absorption_test.json | Supported |  |
| 21 | verdict | The design cannot apportion it. | absorption_test.json | Supported |  |
| 22 | verdict | The 0.5 bar was not demanding: with a noise floor of 0.41, almost any effort surface pushes the ratio past it. | primary.json noise ratio 0.405 | Supported |  |
| 23 | verdict | **Movement beyond the nulls.** | section heading | Supported |  |
| 24 | verdict | 52.8% of species move farther than their noise null's 95th percentile, and 36% farther than their effort null's. | nulls_primary.parquet exceed noise p95 0.528, effort p95 0.36 | Supported |  |
| 25 | verdict | Under shared real shifts the effort null's exceedance falls towards 5%, so 36% is a lower bound on species with real movement, not an estimate. | absorption_test.json exceed_effort_p95 0.05 (all move), 0.18-0.23 movers | Supported |  |
| 26 | verdict | Per species: the median of the species' own ratios is 0.68 and the mean 0.97; 25.8% of species move less than their effort null's median. | nulls_primary.parquet median ratio 0.678, mean 0.97, below null median 0.258 | Supported |  |
| 27 | verdict | **Robust as computed.** The effort-null ratio stays between 0.64 and 0.71 across latitude bands, cell-count classes, thresholds of 20 and 50 cells, 30-arcmin thinning, 30-arcmin and 2° effort grids, arithmetic centroids, and cleaning without the dense-point rule. | primary.json variants 0.64-0.71 | Supported |  |
| 28 | verdict | The same identification caveat applies to every row. | absorption_test.json | Supported |  |
| 29 | verdict | **SDM-centroid variant** (1,000 species): modelled-range centroids move at a median of 8.4 km/yr, and one effort-null replicate per species gives 6.2 km/yr (ratio 0.74, 0.68 to 0.82). | sdm_variant.json 8.44 / 6.23, ratio 0.74 (0.68-0.82) | Supported |  |
| 30 | verdict | **Reproduction.** Our observed median is 6.5–6.9 km/yr depending on the threshold, against Daru et al.'s 5.6 km/yr. | reproduction.csv 6.511-6.906; ledger A1 | Supported |  |
| 31 | verdict | At five cells per period we have 101,328 species, against their 109,242. | reproduction.csv 5 cells 101,328; ledger A1 | Supported |  |
| 32 | plain terms | A recent study used millions of museum plant specimens to estimate that over 100,000 plant species have shifted their ranges at a median of 5.6 km a year since the 1970s–1990s, faster than models predict for the coming decades. | ledger A1, A10 | Supported |  |
| 33 | plain terms | But the centre of a range estimated from a few dozen specimens moves around by chance. | noise-only null 2.8 km/yr; test_velocity.py | Supported |  |
| 34 | plain terms | Botanists also collect in different places from decade to decade. | ledger A3 (Daru et al. 2018) | Supported |  |
| 35 | plain terms | Both of these make ranges look as if they are moving even when they are not. | noise and effort nulls | Supported |  |
| 36 | plain terms | We rebuilt the measurement from the open GBIF data and found a somewhat higher figure: 6.9 km a year. | primary.json H1 6.906 vs 5.6 | Supported | was 'a similar figure' |
| 37 | plain terms | Then, for each of nearly 70,000 species, we reshuffled which of its specimens counted as "early" and which as "late", 999 times. | velocity.py NREP 999; 69,596 species | Supported |  |
| 38 | plain terms | Done at random, the reshuffles alone produced 2.8 km a year, about two-fifths of the observed figure: that much is pure chance. | primary.json noise 2.80 vs 6.91 | Supported |  |
| 39 | plain terms | Done so as to follow where all other plant specimens were collected in each period, they produced 4.6 km a year, two-thirds of it. | primary.json effort 4.61 vs 6.91 | Supported |  |
| 40 | plain terms | But that second baseline also moves when many species really shift together, so it cannot say how much of the gap is collectors and how much is plants. | absorption_test.json | Supported |  |
| 41 | plain terms | So a large share of the headline speed is noise, and an unknown part of the rest may be collecting effort. | primary.json noise ratio 0.405; absorption_test.json | Supported |  |
| 42 | plain terms | There is a small tilt towards the poles that neither baseline produces. | nulls_primary.parquet pole medians 9.4 vs 0.3 / -0.6 | Supported | 'real' removed |
| 43 | plain terms | A velocity like 5.6 km a year cannot be read as how fast plants are moving until it is compared with a baseline, and a better baseline needs a measure of collecting effort that does not move with the plants. | interpretation; Daru et al. 5.6 (ledger) | Supported |  |
