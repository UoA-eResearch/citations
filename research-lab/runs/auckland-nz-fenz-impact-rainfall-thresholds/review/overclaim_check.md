# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Flood callouts track how rare the rain is for a place slightly better than its depth: the preregistered test passes, but on one held-out year whose margin comes from a single storm | primary.json H1 Supported, D_LL 3.92e-5 (6.1e-6 to 8.27e-5), S 1.076; posthoc.json without late June 2025 0.94e-5 (-0.53e-5 to 2.60e-5) | Supported |  |
| 2 | standfirst | FENZ incident records FY2017/18–2024/25 (679,485 exposures), geocoded to 954 suburbs with a council rain gauge within 10 km (gauges from eight councils): 2.65 million suburb-days. | fenz_rows.json kept_rows 679,485; panel_coverage.json panel_suburbs 954, panel_suburb_days 2,654,825 | Supported | was 'in eight regions' (suburbs span more regions; gauges come from eight councils) |
| 3 | standfirst | Rain comes from the HIRDS lead's gauge series. | code/rain_daily.py reads the HIRDS lead's series and rules | Supported |  |
| 4 | standfirst | Rarity is the day's maximum 6-hour rain divided by the gauge's HIRDS v4 median annual maximum, HIRDS's own index. | plan.md section 0; ledger F3 (HIRDS index = median annual maximum) | Supported |  |
| 5 | standfirst | Models were trained on FY2017/18–2023/24 and tested once on FY2024/25. | code/analyse.py (test = day > 2024-06-30); panel.py TRAIN_END | Supported |  |
| 6 | standfirst | The plan was committed before any FENZ outcome row was read. | git: plan.md commit (16:41) precedes build_fenz.py output | Supported |  |
| 7 | verdict | **Verdict: H1 Supported (preregistered rule), with a fragile margin.** | primary.json H1 Supported; posthoc.json D_LL without late June 2025 CI includes 0 | Supported |  |
| 8 | verdict | **H1 (rarity predicts flood callouts better than depth): Supported.** All three preregistered conditions hold: | primary.json D_LL CI excludes 0; S_condition true; loro wins 7/9 | Supported |  |
| 9 | verdict | **Held-out log-loss.** The rarity model's is lower: D_LL = 3.9×10⁻⁵ (95% storm-day interval 0.6×10⁻⁵ to 8.3×10⁻⁵), 3.4% of the depth model's log-loss. | primary.json LL_D 0.0011515, LL_R 0.0011123, D_LL 3.92e-5 (6.08e-6 to 8.27e-5) | Supported |  |
| 10 | verdict | **Skill.** Rarity's skill over a no-rain baseline is 1.076 times depth's (bar: 1.05). | primary.json skill_R 5.52e-4 / skill_D 5.13e-4 = 1.076 | Supported |  |
| 11 | verdict | **Regions.** Leave-one-region-out, rarity predicts better in 7 of 9 regions. | primary.json loro wins 7, n 9 | Supported |  |
| 12 | verdict | **The margin is thin.** | posthoc.json; primary.json test_floods 64 | Supported |  |
| 13 | verdict | **One storm.** The held-out year has 64 flood suburb-days, 24 of them in the Nelson–Tasman floods of 25–30 June 2025. | panel: 64 held-out flood suburb-days, 24 on 2025-06-25..30 | Supported |  |
| 14 | verdict | Without those six days, D_LL is 0.9×10⁻⁵ and its interval includes zero (post hoc). | posthoc.json D_LL_without_late_june_2025 9.36e-6, ci -5.3e-6 to 2.6e-5 (post hoc) | Exploratory-labelled |  |
| 15 | verdict | **The regions.** One of the 7 regional "wins" is the West Coast, which had no held-out flood. | primary.json loro West Coast test_floods 0, R_wins true | Supported |  |
| 16 | verdict | Without it rarity still wins 6 of 8. | primary.json loro: 6 wins among the 8 other regions | Supported |  |
| 17 | verdict | **The secondaries are mixed:** | secondary.json | Supported |  |
| 18 | verdict | **24-hour rain:** rarity is better (S 1.12, interval excluding zero). | secondary.json 24h D_LL 5.15e-5 (1.61e-5 to 9.67e-5), S 1.118 | Supported |  |
| 19 | verdict | **1-hour rain:** depth is marginally better (S 0.99). | secondary.json 1h D_LL -7.7e-6 (CI includes 0), S 0.986 | Supported |  |
| 20 | verdict | **Broader callout definitions,** adding flood-related water-removal callouts or natural-disaster dispatch codes: neither model is clearly better. | secondary.json outcome_v1 CI includes 0 (S 1.022); outcome_v2 CI includes 0 (S 0.953) | Supported |  |
| 21 | verdict | **Other rain measures:** the AEP form, the 5 km and inverse-distance assignments, and dropping unverified data all favour rarity, though not all meet every bar. | secondary.json aep_form S 1.053 (CI incl 0); within_5km S 1.045 (CI excl 0); idw S 1.075; quality_Q S 1.089 | Supported |  |
| 22 | plain terms | The same downpour can be routine in one place and a disaster in another. | framing; HIRDS depths vary by place (data/hirds_depths.parquet: 6-h median annual maximum 27-137 mm across the 336 panel gauges, 5th-95th percentile 36-83 mm) | Supported | was a claim about how NZ warnings trigger (unsourced) |
| 23 | plain terms | Using eight years of Fire and Emergency callout records, we tested whether flood callouts follow how unusual the rain is for a place (its depth compared with that place's typical yearly maximum) rather than the raw amount. | study design | Supported |  |
| 24 | plain terms | On the year we held back for testing, the "how unusual" version predicted callouts a little better, and it did so in most regions. | primary.json D_LL > 0; loro 7/9 | Supported |  |
| 25 | plain terms | That is what our preregistered test asked for. | plan.md section 0 | Supported |  |
| 26 | plain terms | But the test year had only 64 suburb-days with flood callouts, and about three-quarters of the advantage comes from one event, the Nelson–Tasman floods of late June 2025. | primary.json test_floods 64; posthoc.json without late June D_LL 0.94e-5 of 3.92e-5 (about a quarter remains) | Supported | was 'almost entirely from one event' |
| 27 | plain terms | Across all years, flood callouts become ten times more likely than on a dry day once six-hour rain reaches about a fifth of a place's typical yearly maximum. | onset.csv: R onset_10x 0.20 (model-based) | Supported |  |
| 28 | plain terms | On 27 January 2023, Auckland suburbs had 2.7 times their typical yearly maximum in six hours, and about a third of them called out the fire service for flooding. | posthoc.json Auckland 2023-01-27 median rarity 2.71, 55 of 174 (31.6%) | Supported |  |
