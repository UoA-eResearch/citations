# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Do US deaths fall in recessions? Across 2,304 defensible specifications, yes before 1992 and with the unemployment rate; post-2010 drug deaths show no reliable cyclical pattern | H1 S1 by window and measure; H2 S2_wcr 1.6% positive-significant | Supported | was 'drug deaths do not follow the cycle' (non-significance is not absence); now 'show no reliable cyclical pattern' |
| 2 | standfirst | US states and DC, 1976–2023. | plan.md panel | Supported |  |
| 3 | standfirst | Deaths come from NBER microdata to 1998, then CDC state counts, spliced and validated on the overlap years. | splice_validation.json; ledger M7 | Supported |  |
| 4 | standfirst | Economic weakness is the BLS unemployment rate or the negative employment-to-population ratio. | plan.md measures | Supported |  |
| 5 | standfirst | A preregistered specification multiverse varies the outcome, measure, weighting, trends, lags, sample window, estimator and controls, with wild cluster bootstrap inference by state. | plan.md multiverse dimensions | Supported |  |
| 6 | standfirst | The plan was committed before any panel was built. | git: plan committed before the panel build | Supported |  |
| 7 | verdict | **Verdict: H1 Inconclusive; H2 Refuted.** | primary.json H1 Inconclusive, H2 Refuted | Supported |  |
| 8 | verdict | **H1 (the procyclical coefficient is negative and significant in fewer than half of defensible specifications): Inconclusive.** | plan.md H1 | Supported |  |
| 9 | verdict | **47.4%** of the 2,304 total-mortality specifications are negative and significant under the wild cluster restricted bootstrap, inside the preregistered 40–60% band. 79% are negative; 1.7% are positive and significant. | primary.json S1_wcr 0.4744; share_negative 0.788; positive-significant 0.017 | Supported |  |
| 10 | verdict | **A joint test rules out chance.** Under the null, the median share significant is 1.8% (95th percentile 10%), against 49% observed (p < 0.002). | joint_test null median 0.018, p95 0.101, observed 0.492, p 0.000 | Supported |  |
| 11 | verdict | **The answer depends on two choices.** | decomposition r2_drop window 0.279, treat 0.106 | Supported |  |
| 12 | verdict | **The window.** In 1976–1991, 85% of specifications are negative and significant. | share_by_option window 1976-1991 0.847 | Supported |  |
| 13 | verdict | In 1992–2005 it is 1.4% (about 40% negative), and in 2006–2017, 13%. | 1992-2005 0.014 (negative share 0.419); 2006-2017 0.134 | Supported |  |
| 14 | verdict | The full-period windows owe their significance largely to the pre-1992 years. | 1976-1991 0.847 vs 1992-2005 0.014 and 2006-2017 0.134 within the full windows | Supported |  |
| 15 | verdict | **The measure.** With the unemployment rate, the long windows are 83–97% negative and significant. | specs_h1 ur x long windows 0.826-0.972 | Supported |  |
| 16 | verdict | With the employment-to-population ratio, 37–44%. | specs_h1 epop x long windows 0.368-0.444 | Supported |  |
| 17 | verdict | Together they account for most of what the choices explain. | r2_main_effects 0.43; window+measure drops 0.385 | Supported | was 'explain most of the variation' (main effects explain 43% of it) |
| 18 | verdict | The main effects of all eight choices explain 43% of the variation across specifications; dropping the window loses 28 points and dropping the measure 11. | decomposition r2_main_effects 0.4305; drops window 0.2786, treat 0.1058 | Supported |  |
| 19 | verdict | Weighting, lags, trends, outcome, estimator and controls lose 0.1–2 points each. | r2_drop outcome 0.010, weight 0.001, trend 0.009, lag 0.001, estimator 0.010, controls 0.021 | Supported |  |
| 20 | verdict | **The canonical Ruhm specification reproduces the classic result.** Log crude mortality falls 0.52% per point of unemployment for 1976–2017 (95% CI −0.92% to −0.13%; bootstrap p = 0.018). | canonical_by_window 1976-2017 beta -0.00523 (-0.00921 to -0.00126), p_wcr 0.018 | Supported |  |
| 21 | verdict | The sub-periods split: +0.21% in 1992–2005 (not significant) and −0.57% in 2006–2017. | 1992-2005 +0.00208 (p 0.30); 2006-2017 -0.00569 | Supported |  |
| 22 | verdict | **H2 (post-2010 drug-poisoning deaths are significantly countercyclical in most specifications): Refuted.** | plan.md H2; primary.json H2 Refuted | Supported |  |
| 23 | verdict | Only **1.6%** of 576 specifications are positive and significant; 3.5% are negative and significant. | H2 S2_wcr 0.0156; share_negative_significant 0.0347 | Supported |  |
| 24 | verdict | Half the estimates are positive, two thirds in 2011–2019 and one third in 2011–2023. | H2 share_positive 0.510; 2011-2019 0.670, 2011-2023 0.351 (specs_h2.csv) | Supported |  |
| 25 | verdict | For 1999–2010, 79% are positive but only 8% significant. | specs_drug_pre2011.csv: positive 0.788, positive-significant 0.083 (288 specs) | Supported |  |
| 26 | plain terms | For decades economists have reported a surprising pattern: in the United States, deaths fall during recessions and rise in booms. | ledger M1 (Ruhm 2000) | Supported |  |
| 27 | plain terms | Proposed reasons include fewer road crashes, less pollution, and better-staffed care homes when jobs are scarce. | ledger M4, M5 | Supported |  |
| 28 | plain terms | Later work suggested the pattern had faded, and that deaths from drug overdoses might move the other way. | ledger M2 (Ruhm 2015) | Supported |  |
| 29 | plain terms | We rebuilt the state-by-year data from 1976 to 2023. | panel 1976-2023 | Supported |  |
| 30 | plain terms | Instead of one analysis, we ran every combination of the reasonable choices a researcher could make, 2,304 analyses in all. | 2,304 specs (primary.json H1 specs) | Supported |  |
| 31 | plain terms | We then counted how many find the classic pattern. | S1 definition | Supported |  |
| 32 | plain terms | About half do, which our preregistered rule calls inconclusive. | S1 0.474 within the 40-60% band | Supported |  |
| 33 | plain terms | But the split is not random. | joint test p < 0.002; window and measure decomposition | Supported |  |
| 34 | plain terms | The pattern is strong in 1976–1991 and largely absent in 1992–2005. | 1976-1991 0.847; 1992-2005 0.014 | Supported |  |
| 35 | plain terms | It is also much stronger when the economy is measured by the unemployment rate than by the share of people in work. | ur 0.626 vs epop 0.323 overall; long windows 83-97% vs 37-44% | Supported |  |
| 36 | plain terms | Overdose deaths after 2010 did not reliably rise with unemployment in almost any analysis. | H2 positive-significant 1.6% | Supported |  |
| 37 | plain terms | So "deaths fall in recessions" holds for the late 1970s and 1980s, and mostly with one way of measuring the economy. | 1976-1991 0.847; ur vs epop | Supported | was 'recessions are good for health' (the study measures deaths, not health) |
| 38 | plain terms | It is not a stable law. | window shares 0.85 / 0.01 / 0.13 | Supported |  |
