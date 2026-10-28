# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | New Zealand's 10-year design rainfalls have been exceeded about 1.5 times as often as stated since HIRDS v4 was fitted, but nine years of clustered storms cannot rule out chance | primary.json H1 OE 1.492 (0.781-2.346); hedged 'cannot rule out chance' | Supported |  |
| 2 | standfirst | 201 council rain gauges in seven regions (open Hilltop servers), water years 2017/18–2025/26, after every HIRDS v4 fitting record. | primary.json H1 gauges 201; coverage.json; posthoc_auckland.json primary_min8 0 gauges | Supported | was 'eight regions (... and Auckland Council)': no Auckland gauge is in the primary |
| 3 | standfirst | Auckland Council's gauges were also harvested, but none met the preregistered inclusion rule. | posthoc_auckland.json primary_min8: 0 gauges; deviations.md D4 | Supported |  |
| 4 | standfirst | Annual-maximum 6-hour rainfall is compared with HIRDS v4's own depths at each gauge's coordinates, from ESNZ's HIRDS API. | code/depths.py (HIRDS API point report); D1 | Supported |  |
| 5 | standfirst | The plan was committed before any rainfall value or HIRDS depth was read. | git: plan.md commit precedes code/fetch.py and any data | Supported |  |
| 6 | standfirst | A data-reader bug found after the first full run was fixed and every series refetched (D5), and a physical screen later removed three impossible records (D6). | deviations.md D5, D6; results/tables/g4_raw_check.csv; v1_before_screen | Supported |  |
| 7 | verdict | **Verdict: H1 Inconclusive.** | primary.json H1 verdict Inconclusive | Supported |  |
| 8 | verdict | **H1 (6-hour, 10% AEP depths exceeded at least 1.3 times as often as stated, out of sample): Inconclusive.** | primary.json H1 verdict | Supported |  |
| 9 | verdict | 258 exceedances against 172.9 expected, over 1,729 complete gauge-years: **O/E 1.49**, with a 95% water-year block interval of **0.78 to 2.35**. | primary.json H1 O 258, E 172.9, gauge_years 1729, OE 1.492, ci 0.781-2.346 | Supported |  |
| 10 | verdict | The point estimate passes the 1.3 bar, but the interval includes 1.0. | primary.json H1 OE 1.492 >= 1.3; ci lower 0.781 < 1 | Supported |  |
| 11 | verdict | Nine water years give few independent blocks, and one storm season contributes much of the count. | secondary.json storm_cluster_bootstrap storms 71, largest 52; year_by_year.csv 2022/23 OE 3.81 | Supported |  |
| 12 | verdict | **The in-sample control holds.** Over the years HIRDS was fitted to (up to 2014/15), O/E is 0.89 (0.69–1.12): this harvest and HIRDS agree where they should. | primary.json sanity_in_sample OE 0.894 (0.689-1.124), holds | Supported |  |
| 13 | verdict | **Every duration and level points the same way.** | secondary.json 1h/6h/24h at 10% and 2%: all OE > 1 | Supported |  |
| 14 | verdict | At 1 hour: 1.52 (1.01–2.06). | secondary.json 1h_10pct 1.516 (1.011-2.056) | Supported |  |
| 15 | verdict | At 24 hours: 1.91 (1.06–2.87). | secondary.json 24h_10pct 1.905 (1.062-2.873) | Supported |  |
| 16 | verdict | At 2% AEP: 1.94, 1.65 and 2.49 for 1, 6 and 24 hours, with wide intervals. | secondary.json 1h_2pct 1.942, 6h_2pct 1.648, 24h_2pct 2.493 | Supported |  |
| 17 | verdict | None of these is confirmatory. | plan.md section 3 (secondary analyses) | Supported |  |
| 18 | verdict | **The excess sits in four storm seasons.** It is concentrated in 2017/18, 2021/22, 2022/23 (O/E 3.8, mostly Cyclone Gabrielle in Hawke's Bay) and 2025/26. | year_by_year.csv: 2017 2.15, 2021 2.58, 2022 3.81, 2025 2.02; others <= 1.01; Feb 2023: 48 HB exceedances (plausibility.md) | Supported | was 'the Auckland floods and Cyclone Gabrielle': Jan 2023 adds only 3 exceedances |
| 19 | verdict | Without January–February 2023, O/E is 1.17 (0.69–1.71). | secondary.json without_janfeb2023 1.168 (0.69-1.706) | Supported |  |
| 20 | verdict | **HIRDS's own mid-century depths fit the observations.** Against HIRDS v4's climate-adjusted depths for 2031–2050, the observed frequency is at the stated rate: O/E 1.01 under RCP4.5 and 0.97 under RCP8.5 (descriptive). | secondary.json against_rcp45_2031_2050 1.006, against_rcp85_2031_2050 0.972; descriptive secondary (D1, before data) | Supported |  |
| 21 | plain terms | Engineers size pipes, culverts and stormwater ponds from New Zealand's national "design rainfall" tables (HIRDS), which say how often big downpours should happen. | ledger R2 (HIRDS v4 report: design of flood-protection works and waterway structures) | Supported |  |
| 22 | plain terms | The current tables were built from rainfall records ending around 2016. | ledger R1 (data end 2015-2017) | Supported |  |
| 23 | plain terms | We checked what has happened since. | study design | Supported |  |
| 24 | plain terms | At 201 council rain gauges, a downpour the tables say should come once in ten years at a site has happened about 1.5 times as often as expected since 2017. | primary.json H1 OE 1.492 | Supported |  |
| 25 | plain terms | A similar or larger excess appears at 1-hour and 24-hour durations, and for rarer storms. | secondary.json 1h_10pct 1.52, 24h_10pct 1.91, 2% levels 1.65-2.49 | Supported | was 'It is the same at 1-hour and 24-hour durations' (24 h is larger) |
| 26 | plain terms | The same method finds no such excess in the years the tables were built from. | primary.json sanity_in_sample 0.894 (0.689-1.124) | Supported |  |
| 27 | plain terms | The observed rate also matches what HIRDS itself projects for the 2030s and 2040s under climate change. | secondary.json against RCP4.5/8.5 2031-2050 depths 1.01/0.97 (descriptive) | Supported |  |
| 28 | plain terms | But the evidence is not yet decisive. | primary.json H1 Inconclusive, ci includes 1.0 | Supported |  |
| 29 | plain terms | Nine years is short, and a few huge storms, above all Cyclone Gabrielle in February 2023, hit many gauges at once. | secondary.json storm clusters (largest 52 of 258); ledger R6 | Supported |  |
| 30 | plain terms | Our statistical range, from 0.8 to 2.3 times the stated rate, still includes "no change". | primary.json H1 ci 0.781-2.346 | Supported |  |
| 31 | plain terms | Auckland's own gauges could not be scored on the preregistered rules. | posthoc_auckland.json primary_min8: 0 gauges | Supported |  |
| 32 | plain terms | Too many of their recent years are still unaudited, and HIRDS used Auckland data into 2017, which shortens Auckland's test window. | maxima: Auckland 2021-2022 complete share 0.07-0.33 primary vs 0.93-0.94 with 2xx kept; primary.json g1_oos_start_moved 46 Auckland gauges; ledger R1 | Supported |  |
