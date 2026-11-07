# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Re-scoring FluSight forecasts against first-reported data reverses 6% of model pairings; in 2024–25, when first reports ran about 8% low, the top model changed at short horizons, but no more often than it wobbles under a single truth | primary.json reversal_share 0.0624; revision 2024-25 median_signed -8.04; best_changed h1,h2; posthoc_review.json leader_instability 0.55-0.65 | Supported | retitled after review |
| 2 | standfirst | FluSight weekly influenza hospital-admission forecasts, 2022–23 to 2024–25 (33–51 models a season, 563,252 scored forecasts), were scored by WIS twice: against each location-week's first-reported value, taken from the git history of the hub's truth file, and against the finalised value. | mean_wis forecasts 563,252; 33-51 models per season | Supported |  |
| 3 | standfirst | The plan and scoring code were committed before any forecast was scored. | git: plan and scoring code before scoring | Supported |  |
| 4 | verdict | **Verdict: H1 Refuted; H2 Supported under the preregistered name rule, but not robust to that rule and not distinguishable from the leader's sampling instability.** | primary.json H1 Refuted, H2 Supported; posthoc_review.json eligibility and leader_instability | Supported | qualified after review |
| 5 | verdict | **H1 (first-report scoring reverses at least 20% of within-season pairwise model orderings): Refuted.** | plan H1 | Supported |  |
| 6 | verdict | **6.2%** of 8,441 model pairs reverse (95% bootstrap over reference dates 4.9% to 7.4%). | reversal_share 0.0624 (0.0487-0.0737); pairs 8,441 | Supported |  |
| 7 | verdict | By season: 0.7% (2022–23), 3.0% (2023–24) and 10.6% (2024–25). | per_season_horizon sums: 12/1,708; 79/2,611; 436/4,122 | Supported |  |
| 8 | verdict | **Late first reports do not change this.** For 8.1% of 2023–24 and 4.6% of 2024–25 scored forecasts, the location-week's first hub version came more than 7 days after the week's end. | primary.json scored_forecasts_on_late_first_reports 0.0812, 0.0461 | Supported |  |
| 9 | verdict | Most of these first appeared a month or more later, when the values were largely settled: first and final are identical for 84–98% of such weeks. | truth.parquet new hub, late target weeks: >30 days for 68-100%, first==final 84-98% | Supported | softened |
| 10 | verdict | Dropping them gives 6.4% (4.9% to 7.6%), post hoc. | primary_late7.json reversal_share 0.0641 [0.0494, 0.0759] | Supported |  |
| 11 | verdict | Rank agreement between the two scorings is high: the Spearman correlation of relative WIS is 0.85–1.00 across season × horizons. | rank_agreement 0.852-1.000 | Supported |  |
| 12 | verdict | **H2 (the best non-ensemble model changes in at least one season × horizon): Supported under the name rule.** | primary.json H2 Supported (preregistered rule) | Supported | scoped to the name rule |
| 13 | verdict | **Under the preregistered rule** (ensembles and baselines excluded by name), the 2024–25 leader changes at 1 week ahead, from PSI-PROF (first report) to PSI-PROF_beta (finalised), two variants from the same team. | primary.json best 2024-25 h1 | Supported |  |
| 14 | verdict | It also changes at 2 weeks ahead, from CEPH-Rtrend_fluH to PSI-PROF_beta. | primary.json best 2024-25 h2 | Supported |  |
| 15 | verdict | No other season changes its leader. | best first == final in all other season x horizons | Supported |  |
| 16 | verdict | **The rule excludes the strongest model** (post hoc). | posthoc_review.json eligibility overall_lowest 2024-25 | Supported |  |
| 17 | verdict | NEU_ISI-AdaptiveEnsemble is a single team's submission, removed only because its name contains "ensemble". | score.py is_excluded (name contains 'ensemble') | Supported |  |
| 18 | verdict | It has the lowest relative WIS in 2024–25 at h1–h3 under first-report truth (0.73, 0.65, 0.62), and at h2–h3 under final truth. | posthoc_review.json eligibility NEU_ISI first 0.726/0.649/0.621; overall_lowest_final h2,h3 | Supported |  |
| 19 | verdict | If only the hub's own models (FluSight-*) and baselines are excluded, the leader changes only at h1 (NEU_ISI-AdaptiveEnsemble → PSI-PROF_beta). | posthoc_review.json changed_under_hub_and_baseline_rule ['2024-25 h1'] | Supported |  |
| 20 | verdict | The name rule is also inconsistent: MIGHTE-Nsemble and the hub's FluSight-lop_norm, -trained_mean and -trained_med are ensembles that it does not catch. | relative_wis.csv model list; score.py is_excluded | Supported |  |
| 21 | verdict | **The leader is just as unstable under a single truth** (post hoc). | posthoc_review.json leader_instability 2024-25 | Supported |  |
| 22 | verdict | In bootstrap resamples, the 2024–25 leader at h0–h2 differs from its own point estimate in 55–63% of resamples under first-report truth and 59–65% under final truth. | posthoc_review.json leader_instability h0-h2 first 0.545-0.625, final 0.59-0.645 | Supported |  |
| 23 | verdict | The first-report and final leaders differ from each other in 50–77% of resamples. | posthoc_review.json leader_instability first_vs_final 0.495-0.77 | Supported |  |
| 24 | verdict | So the change is a near-tie at the top, not evidence that revisions pick the winner. | posthoc_review.json leader_instability (interpretation) | Supported | interpretation, stated as such |
| 25 | verdict | **Revisions: bias, not size, goes with reversals** (computed per scoring hub on forecast target weeks; corrected after review). | primary.json revision per hub | Supported | recomputed per hub |
| 26 | verdict | 2022–23 revisions were as large as 2024–25's, without a median bias, and 0.7% of pairs reversed. | primary.json revision 2022-23 share_over_10pct 0.4753, median_signed 0.0; reversals 12/1708 | Supported |  |
| 27 | verdict | In 2024–25, first reports ran a median 8% below final values and 10.6% reversed. | primary.json revision 2024-25 median_signed -8.04; reversals 436/4122 | Supported |  |
| 28 | verdict | Across three seasons this is an observation, not a test. | three seasons (design) | Supported |  |
| 29 | verdict | Mean WIS is 144 against first reports and 156 against final values: forecasts sat closer to what was first reported. | mean_wis first 144.0, final 155.6 | Supported |  |
| 30 | plain terms | Each week during flu season, dozens of teams forecast how many people will be admitted to hospital with flu in every US state. | background | Supported |  |
| 31 | plain terms | The CDC's FluSight hub collects the forecasts and ranks the teams. | background | Supported |  |
| 32 | plain terms | The ranking uses the final hospital counts, but those counts are often revised in the weeks after they are first reported. | revision table | Supported |  |
| 33 | plain terms | Forecasters only ever saw the first, provisional numbers. | design premise (first reports were what forecasters saw) | Supported |  |
| 34 | plain terms | We re-scored three seasons of forecasts against the first-reported numbers. | design | Supported |  |
| 35 | plain terms | In most seasons, almost nothing changed: fewer than 1 in 30 head-to-head comparisons between teams flipped. | 2022-23 0.7%, 2023-24 3.0% (< 1 in 30) | Supported |  |
| 36 | plain terms | In 2024–25, when early reports ran several percent low and were often revised substantially, about 1 in 10 flipped, and the top-ranked model changed at two of four forecast horizons (at one of them, between two variants from the same team). | 2024-25 10.6%; median signed -4.1%; 36% revised >10% | Supported | was 'the top-ranked team changed' (one change is between two variants of the same team) |
| 37 | plain terms | But the top few models were so close that the leader also changed in more than half of reshuffled versions of the same season scored against a single truth. | posthoc_review.json leader_instability 2024-25 0.55-0.65 | Supported |  |
| 38 | plain terms | So hub leaderboards are mostly not an artefact of data revisions. | reversal_share 6.2%; rank agreement >= 0.85 | Supported | was 'leaderboards mostly reflect forecasting skill' (skill not measured) |
| 39 | plain terms | When first reports are biased, as in 2024–25, the order of near-tied models can depend on which version of the truth is used, and the rule for which models are eligible matters as much. | primary.json best_changed; posthoc_review.json changed_under_hub_and_baseline_rule | Supported |  |
