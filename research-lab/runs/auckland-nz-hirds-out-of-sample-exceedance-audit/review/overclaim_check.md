# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | New Zealand's 10-year design rainfalls have been exceeded about 1.5 times as often as stated since HIRDS v4 was fitted, but nine years of clustered storms cannot separate that from chance | primary.json H1 OE 1.497; studentized ci 0.678-2.822; hedged 'cannot separate from chance' | Supported | 'rule out chance' -> 'separate from chance' (review finding 1: the preregistered interval covers 83%) |
| 2 | standfirst | 197 council rain gauges in seven regions (open Hilltop servers), water years 2017/18–2025/26, after every HIRDS v4 fitting record. | primary.json H1 gauges 197; coverage.json; posthoc_auckland.json primary_min8 0 gauges | Supported |  |
| 3 | standfirst | Auckland Council's gauges were also harvested, but none met the preregistered inclusion rule. | posthoc_auckland.json primary_min8: 0 gauges; deviations.md D4 | Supported |  |
| 4 | standfirst | Annual-maximum 6-hour rainfall is compared with HIRDS v4's own depths at each gauge's coordinates, from ESNZ's HIRDS API. | code/depths.py (HIRDS API point report); D1 | Supported |  |
| 5 | standfirst | The plan was committed before any rainfall value or HIRDS depth was read. | git: plan.md commit precedes code/fetch.py and any data | Supported |  |
| 6 | standfirst | Three rounds of data faults were found and fixed, the last after the independent review (D5–D7). | deviations.md D5, D6, D7 | Supported |  |
| 7 | verdict | **Verdict: H1 Inconclusive.** | primary.json H1 verdict Inconclusive | Supported |  |
| 8 | verdict | **H1 (6-hour, 10% AEP depths exceeded at least 1.3 times as often as stated, out of sample): Inconclusive.** | primary.json H1 verdict | Supported |  |
| 9 | verdict | 254 exceedances against 169.7 expected, over 1,697 complete gauge-years: **O/E 1.50**. | primary.json H1 O 254, E 169.7, gauge_years 1697, OE 1.497 | Supported |  |
| 10 | verdict | The preregistered water-year block interval is **0.78 to 2.36**. | primary.json H1 ci 0.782-2.357 and ci_bootstrap_t 0.678-2.822; review finding 1 (83% coverage in simulation) | Supported | studentized interval added; no sentence leans on the preregistered one |
| 11 | verdict | The independent review showed that with nine blocks this interval covers 83% rather than 95%, so a studentized interval is reported beside it: | review/review.md finding 1: simulated coverage 83% for the 9-block percentile bootstrap | Supported |  |
| 12 | verdict | **0.68 to 2.88**. | primary.json H1 ci_bootstrap_t 0.678-2.822 | Supported |  |
| 13 | verdict | The verdict is Inconclusive under both. | primary.json H1 verdict; both intervals include 1.0 | Supported |  |
| 14 | verdict | **The in-sample control holds.** Over the years HIRDS was fitted to (up to 2014/15), O/E is 0.89 (0.69–1.12; studentized 0.69–1.20). | primary.json sanity_in_sample 0.889 (0.689-1.115; t 0.691-1.198); ratio 1.497/0.889 = 1.68 | Supported |  |
| 15 | verdict | The out-of-sample ratio is 1.68 times the in-sample one, which is the cleaner comparison, because both sides carry this harvest's downward biases. | primary.json 1.497 / 0.889 = 1.684 | Supported |  |
| 16 | verdict | **The stated rate is not quite 1.0.** HIRDS's own standard error on a 10-year 6-hour depth is about 10% of it. | hirds_depths: median historical_se / 10-yr 6-h depth = 0.099; convexity argument, review finding 10 | Supported | added after the review |
| 17 | verdict | Exceedance probability is convex in depth, so a gauge whose depth is unbiased but uncertain is exceeded a little more often than 10% of the time: the expected O/E under a correct HIRDS is around 1.1, not 1.0. | median historical_se / 10-yr 6-h depth = 0.099; review finding 10 | Supported |  |
| 18 | verdict | **Other durations and levels point the same way, but not independently.** | secondary.json 1h/6h/24h at 10% and 2%; 177 of 254 6-h exceedances are also 24-h | Supported | 'every duration points the same way' qualified (review finding 4) |
| 19 | verdict | 1 hour: 1.54 (studentized 0.87–2.40); 24 hours: 1.91 (0.82–3.34). | secondary.json 1h_10pct 1.537, t 0.874-2.397; 24h_10pct 1.910, t 0.817-3.342 | Supported |  |
| 20 | verdict | At 2% AEP: 1.87, 1.56 and 2.46 for 1, 6 and 24 hours, with very wide intervals. | secondary.json 1h_2pct 1.873, 6h_2pct 1.562, 24h_2pct 2.455 | Supported |  |
| 21 | verdict | These are largely the same storms: 177 of the 254 six-hour exceedances are also 24-hour exceedances at the same gauge and year. | recomputed: 177 of 254 six-hour exceedances are also 24-hour exceedances at the same gauge-year | Supported |  |
| 22 | verdict | No calibrated interval here excludes 1. | secondary.json: every ci_bootstrap_t at 1 h, 6 h and 24 h includes 1.0 | Supported | review finding 1: the preregistered 1-h and 24-h lower bounds do not survive calibration |
| 23 | verdict | **The excess sits in four storm seasons.** O/E is above 2 in 2017/18, 2021/22, 2022/23 (3.8, mostly Cyclone Gabrielle in Hawke's Bay) and 2025/26, and at or below 1 in the other five years. | year_by_year.csv: 2017 2.19, 2021 2.58, 2022 3.84, 2025 2.04; others 0.26-0.98; secondary.json without_wy2022_23 1.201 | Supported |  |
| 24 | verdict | Dropping the 2022/23 water year gives 1.20. | secondary.json without_wy2022_23 1.201 (0.672-1.806) | Supported |  |
| 25 | verdict | **HIRDS's own mid-century depths are close to the observed frequency.** Against HIRDS v4's climate-adjusted depths for 2031–2050, O/E is 1.01 (RCP4.5) and 0.97 (RCP8.5). | secondary.json against_rcp45 1.008 (0.52-1.64), rcp85 0.972 | Supported | was 'fit the observations' (review finding 4) |
| 26 | verdict | Both intervals are wide, so this is a consistency check, not evidence that mid-century depths are right for today. | secondary.json against_rcp45 ci 0.52-1.64, rcp85 0.48-1.55 | Supported | was 'ahead of schedule' framing (review finding 4) |
| 27 | plain terms | Engineers size pipes, culverts and stormwater ponds from New Zealand's national "design rainfall" tables (HIRDS), which say how often big downpours should happen. | ledger R2 (HIRDS v4 report: design of flood-protection works and waterway structures) | Supported |  |
| 28 | plain terms | The current tables were built from rainfall records ending around 2016. | ledger R1 (data end 2015-2017) | Supported |  |
| 29 | plain terms | We checked what has happened since. | study design | Supported |  |
| 30 | plain terms | At 197 council rain gauges, a downpour the tables say should come once in ten years at a site has happened about 1.5 times as often as expected since 2017. | primary.json H1 OE 1.497 | Supported |  |
| 31 | plain terms | The same method finds no such excess in the years the tables were built from, which is the main reason to take the comparison seriously at all. | primary.json sanity_in_sample 0.889 | Supported |  |
| 32 | plain terms | But the evidence is not decisive, and we do not claim it is. | primary.json H1 Inconclusive; studentized ci includes 1 | Supported |  |
| 33 | plain terms | Nine years is short, and a few huge storms, above all Cyclone Gabrielle in February 2023, hit many gauges at once. | secondary.json storm clusters (largest 52 of 258); ledger R6 | Supported |  |
| 34 | plain terms | Our calibrated range runs from 0.7 to 2.9 times the stated rate, which includes "no change". | primary.json H1 ci_bootstrap_t 0.678-2.822 | Supported | was the preregistered 0.8-2.3 (review finding 1) |
| 35 | plain terms | The tables are themselves uncertain by about 10%, and that alone would produce a ratio near 1.1. | median historical_se / depth = 0.099; convexity (review finding 10) | Supported |  |
| 36 | plain terms | Auckland's own gauges could not be scored on the preregistered rules, because too many of their recent years are still unaudited. | posthoc_auckland.json primary_min8: 0 gauges | Supported |  |
