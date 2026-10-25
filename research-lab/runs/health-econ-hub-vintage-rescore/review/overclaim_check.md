# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Re-scoring FluSight forecasts against the data forecasters actually saw barely changes the leaderboard, except in 2024–25, when first reports ran low and the top model changed at two horizons in about half of resamples | reversal_share 0.062; 2024-25 best changed at h1, h2 with bootstrap 0.61, 0.53 | Supported | was 'the top model changed' (fragile: about half of resamples); qualified |
| 2 | standfirst | FluSight weekly influenza hospital-admission forecasts, 2022–23 to 2024–25 (33–51 models a season, 563,252 scored forecasts), were scored by WIS twice: against each location-week's first-reported value, taken from the git history of the hub's truth file, and against the finalised value. | mean_wis forecasts 563,252; 33-51 models per season | Supported |  |
| 3 | standfirst | The plan and scoring code were committed before any forecast was scored. | git: plan and scoring code before scoring | Supported |  |
| 4 | verdict | **Verdict: H1 Refuted; H2 Supported.** | primary H1 Refuted, H2 Supported | Supported |  |
| 5 | verdict | **H1 (first-report scoring reverses at least 20% of within-season pairwise model orderings): Refuted.** | plan H1 | Supported |  |
| 6 | verdict | **6.2%** of 8,441 model pairs reverse (95% bootstrap over reference dates 4.9% to 7.4%). | reversal_share 0.0624 (0.0487-0.0737); pairs 8,441 | Supported |  |
| 7 | verdict | By season: 0.7% (2022–23), 3.0% (2023–24) and 10.6% (2024–25). | per_season_horizon sums: 12/1,708; 79/2,611; 436/4,122 | Supported |  |
| 8 | verdict | Rank agreement between the two scorings is high: the Spearman correlation of relative WIS is 0.85–1.00 across season × horizons. | rank_agreement 0.852-1.000 | Supported |  |
| 9 | verdict | **H2 (the best non-ensemble model changes in at least one season × horizon): Supported, narrowly.** | plan H2; primary H2 Supported | Supported |  |
| 10 | verdict | In 2024–25, the leader at 1 week ahead changes from PSI-PROF (first report) to PSI-PROF_beta (finalised), two variants from the same team. | best 2024-25 h1 PSI-PROF -> PSI-PROF_beta | Supported |  |
| 11 | verdict | At 2 weeks ahead it changes from CEPH-Rtrend_fluH to PSI-PROF_beta. | best 2024-25 h2 CEPH-Rtrend_fluH -> PSI-PROF_beta | Supported |  |
| 12 | verdict | These changes appear in 61% and 53% of bootstrap resamples. | best_changed_bootstrap_share h1 0.612, h2 0.528 | Supported |  |
| 13 | verdict | No other season changes its leader. | best first == final in all other season x horizons | Supported |  |
| 14 | verdict | **Revisions explain where it matters.** | heading (revision bias, rows 15-17) | Supported |  |
| 15 | verdict | In 2024–25, first reports were a median 4.1% below final values, and 36% of location-weeks were revised by more than 10%. | revision 2024-25 median_signed -4.13%, share_over_10pct 0.357 | Supported |  |
| 16 | verdict | In 2022–23, 27% were revised by more than 10% but with no net bias (median 0%), and only 0.7% of pairs reversed (2023–24: 10%). | revision 2022-23 share_over_10pct 0.274, median_signed 0; reversals 0.7%; 2023-24 0.102 | Supported | added at the gate (2022-23 heavy but unbiased revisions) |
| 17 | verdict | So the downward bias of first reports, not the size of revisions, goes with reversals. | 2022-23 (unbiased, 27% revised) 0.7% vs 2024-25 (biased) 10.6% | Supported |  |
| 18 | verdict | Mean WIS is 144 against first reports and 156 against final values: forecasts sat closer to what was first reported. | mean_wis first 144.0, final 155.6 | Supported |  |
| 19 | plain terms | Each week during flu season, dozens of teams forecast how many people will be admitted to hospital with flu in every US state. | background | Supported |  |
| 20 | plain terms | The CDC's FluSight hub collects the forecasts and ranks the teams. | background | Supported |  |
| 21 | plain terms | The ranking uses the final hospital counts, but those counts are often revised in the weeks after they are first reported. | revision table | Supported |  |
| 22 | plain terms | Forecasters only ever saw the first, provisional numbers. | design premise (first reports were what forecasters saw) | Supported |  |
| 23 | plain terms | We re-scored three seasons of forecasts against the first-reported numbers. | design | Supported |  |
| 24 | plain terms | In most seasons, almost nothing changed: fewer than 1 in 30 head-to-head comparisons between teams flipped. | 2022-23 0.7%, 2023-24 3.0% (< 1 in 30) | Supported |  |
| 25 | plain terms | In 2024–25, when early reports ran several percent low and were often revised substantially, about 1 in 10 flipped, and the top-ranked model changed at two of four forecast horizons (at one of them, between two variants from the same team). | 2024-25 10.6%; median signed -4.1%; 36% revised >10% | Supported | was 'the top-ranked team changed' (one change is between two variants of the same team) |
| 26 | plain terms | So hub leaderboards are mostly not an artefact of data revisions. | reversal_share 6.2%; rank agreement >= 0.85 | Supported | was 'leaderboards mostly reflect forecasting skill' (skill not measured) |
| 27 | plain terms | When first reports are biased, as in 2024–25, the close calls at the top can depend on which version of the truth is used. | 2024-25 best changes at h1/h2 under biased first reports | Supported | was 'when the data are revised heavily' (2022-23 was heavily revised without effect) |
