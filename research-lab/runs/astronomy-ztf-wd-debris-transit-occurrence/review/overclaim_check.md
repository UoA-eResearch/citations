# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | How common are debris transits around white dwarfs? Published systems and candidates imply about 1 in 5,000 within 500 pc after correcting for what ZTF can detect, confirmed transiters alone about 1 in 24,000, and nearly 1,000 unvetted candidates leave the rate poorly bounded above | primary.json rate_lower 2.10e-4, rate_upper 1.38e-2; posthoc_review.json tiered_lower_rates confirmed_only 4.19e-5 | Supported | D3: 'unbounded' -> 'poorly bounded' above (confirmation pass) |
| 2 | standfirst | 108,493 Gaia white dwarfs within 500 pc with at least 100 good ZTF g and r epochs were searched blind with two preregistered rules: recurring faint outliers (hour-scale dips) and runs of faint 30-day bins (day- to year-scale dimming). | primary.json (g+r) eligible_stars 108493 | Supported |  |
| 3 | standfirst | The 20 published debris-transiting white dwarfs and candidates were compiled from the discovery papers and committed before detection was run (their Gaia IDs were corrected afterwards; D1). | git: known_systems.csv before detect.parquet; IDs corrected after (D1), disclosed | Supported |  |
| 4 | standfirst | Completeness comes from 150,000 injected signals. | inject.parquet 150,000 rows | Supported |  |
| 5 | standfirst | The plan was committed before any light curve was fetched. | git: plan.md before fetch_lc | Supported |  |
| 6 | standfirst | Revised after an independent review (publish with edits; D2). | D2 | Supported |  |
| 7 | verdict | **Verdict: H1 Inconclusive.** The rate of ZTF-detectable debris transits lies between the rate implied by published systems (2.1 × 10⁻⁴) and the rate with every unvetted candidate counted (1.4 × 10⁻²). | primary.json (g+r) rates combined | Supported |  |
| 8 | verdict | The bar of 5 × 10⁻⁴ falls between them. | primary.json (g+r) H1 | Supported |  |
| 9 | verdict | The design made this outcome all but certain: Supported needs at most about 25 flags in total, and Refuted needs about 50 recovered known systems, against 18 in the sample. | review finding 5 (Poisson limits at sum C ~72k) | Supported |  |
| 10 | verdict | **H1 (the occurrence of ZTF-detectable debris transits, all classes combined, is below 5 × 10⁻⁴): Inconclusive.** | primary.json H1 | Supported |  |
| 11 | verdict | **Lower rate**, by how well established the recovered systems are (completeness-weighted sample 71,572): Ten of the 15 come from a paper titled "Six New Candidates" or from an unrefereed preprint. | posthoc_review.json tiered_lower_rates; known_systems.csv sources | Supported |  |
| 12 | verdict | So 2.1 × 10⁻⁴ is the rate implied by published systems and candidates, not a floor of real systems. | review finding 1 | Supported |  |
| 13 | verdict | **Upper rate:** adding the 970 unexplained candidates gives **1.4 × 10⁻²** (1.29–1.46 × 10⁻²). | primary.json (g+r) candidates 970, rate_upper_ci | Supported |  |
| 14 | verdict | **The i band.** The first draft pooled ZTF i-band epochs into eligibility and both rules, against the plan's g and r. | review finding 2; D2 | Supported |  |
| 15 | verdict | This revision uses g and r, as preregistered. | detect.py FILTERS | Supported |  |
| 16 | verdict | With i included: 109,074 eligible, 914 flagged, the same 15 of 18 known systems, and an upper rate of 1.2 × 10⁻². | withzi_primary.json | Supported |  |
| 17 | verdict | H1 is Inconclusive either way. | primary.json (g+r); withzi_primary.json | Supported |  |
| 18 | verdict | **The positive controls.** 18 of the 20 published systems are in the sample (one is fainter than G = 20, one beyond 500 pc), and the rules flag 15 of them. | known_systems.csv; detect.parquet | Supported |  |
| 19 | verdict | **SDSS J0107+2107** shows continuous shallow dips. | known_systems.csv dip_type; detect.parquet | Supported |  |
| 20 | verdict | **WD 1054−226** has dips of a few per cent and only 207 epochs. | detect.parquet n_epochs 207 | Supported |  |
| 21 | verdict | **SBSS 1232+563** was missed because ZTF sampled its defining 2023 dimming sparsely. | posthoc_d3.json sbss_like_for_like; review confirm_sbss (5 bins >= 5% deep with < 5 epochs) | Supported |  |
| 22 | verdict | After April 2023 (MJD 60068 on) the stored light curve has 32 good g and r epochs, one or two per 30-day bin, and a fresh query keeping every ZTF object finds 34. | posthoc_d3.json sbss_like_for_like stored 32 (25 g, 7 r), IRSA 34 (27 g, 7 r) | Supported | D3: like-for-like counts (was 29 vs 35) |
| 23 | verdict | The two it adds come from a second field's g object, which loses to the most-epochs object, and would lift one event bin from 2 to 3 epochs. | posthoc_d3.json sbss_like_for_like irsa_not_stored oid 1824102200002193 (MJD 60092, 60423); review confirm_sbss | Supported | D3 |
| 24 | verdict | The dimming is visible, but only one bin reaches the 5-epoch minimum, so only one low bin qualifies, and the rule needs two. | review confirm_sbss (g rel flux 0.56-0.91 in MJD 60073-60250; one low bin 13.8% deep, 7.3 se) | Supported |  |
| 25 | verdict | Of the 15 recovered, three are flagged by the short-dip rule alone, six by the long-dip rule alone, and six by both. | detect.parquet x known_systems: 3 / 6 / 6 | Supported |  |
| 26 | verdict | **Completeness.** Injected signals are recovered 65% of the time for WD 1145-like hour-scale dips, 48% for J0139-like day-scale dips and 53% for one-off dimming lasting 30–400 days. | primary.json (g+r) injection_recovery_by_class | Supported |  |
| 27 | verdict | Recovery falls for fainter stars (F2). | F2; inject.parquet by G bin | Supported |  |
| 28 | verdict | **The candidates are mostly long-dip flags, and many track survey-wide trends.** | candidates.csv 769 of 970 long; posthoc_d3.json calendar_null 454 vs 215 (196-238) | Supported | D3: 'mostly systematics' -> 'many' (was Overstated) |
| 29 | verdict | 1,006 stars are flagged; 21 are CVs in Gaia DR3's variability classification. | primary.json (g+r) flagged 1006, gaia_variables_removed 21 | Supported |  |
| 30 | verdict | That leaves 970 candidates besides the 15 known systems. | primary.json (g+r) candidates 970 | Supported |  |
| 31 | verdict | The long-dip rule is sensitive to its threshold: at 3 standard errors it flags 7,598 stars, at 7 it flags 159. | primary.json (g+r) threshold_variants_flagged | Supported |  |
| 32 | verdict | **Calendar test** (post hoc). 454 of the 769 long-dip candidates have a low bin in the same ten 30-day windows, and 140 in June 2020 alone. | posthoc_review.json 454 of 769; largest window 140 at MJD 59010 | Supported |  |
| 33 | verdict | In those windows, 2,000 random unflagged stars are also faint, by a median 0.1–0.7% against −0.02% overall. | posthoc_review.json quiet_star_median_depth | Supported |  |
| 34 | verdict | If each candidate's low bins fell at random among its own well-sampled bins, about 215 (196–238) would land in those windows by coverage alone. | posthoc_d3.json calendar_null null_median 215, null_95 196-238 | Supported | D3 |
| 35 | verdict | So about 240 of the 769 long-dip flags are explained by survey-wide trends beyond what coverage produces: many, not most. | posthoc_d3.json calendar_null excess_over_null 239 | Supported | D3 |
| 36 | verdict | **The g/r coincidence check** promised as a G4 mitigation barely discriminates, however it is read. | posthoc_d3.json g4 (all three readings) | Supported | D3 |
| 37 | verdict | As preregistered (dip epochs coincide in g and r within a night), 23 of 26 testable random flags pass, as do 81% of all testable flags and all 14 testable known systems. | posthoc_d3.json g4 plan_rule_night_coincidence random_30 23/26, all_flags 771/946, known 14/14 | Supported | D3: the plan's own rule |
| 38 | verdict | At the bin level, 94% of the candidates' low bins with at least 3 g and 3 r epochs are more than 2.5% low in both bands, and 71% are at least 5% low in both, the rule's depth. | posthoc_d3.json g4 share_2.5pct 0.941 (1728/1836), share_5pct 0.706 (1296/1836) | Supported | D3: both thresholds stated |
| 39 | verdict | The list is not vetted. | design | Supported |  |
| 40 | verdict | It is in `results/tables/candidates.csv` (Gaia DR3 source IDs, public facts). | candidates.csv | Supported |  |
| 41 | verdict | **Implied geometry.** If a quarter to a half of white dwarfs are metal-polluted, the published-systems rate implies a transit probability × duty cycle of 4 × 10⁻⁴ to 8 × 10⁻⁴ among polluted stars (descriptive). | primary.json (g+r) geometric_times_duty | Supported |  |
| 42 | plain terms | When a white dwarf, the dense remnant of a star like the Sun, tears apart an asteroid or small planet, the dusty debris can pass in front of it and make it dim. | background (A3) | Supported |  |
| 43 | plain terms | About twenty such stars are known, most found in the last five years in data from the Zwicky Transient Facility (ZTF), a telescope that photographs the northern sky every few nights. | known_systems.csv discovery years; ledger A3-A10 | Supported |  |
| 44 | plain terms | How common are they? | question | Supported |  |
| 45 | plain terms | We took about 108,000 white dwarfs within 500 parsecs (about 1,600 light-years) that ZTF has observed at least 100 times. | primary.json (g+r) eligible 108,493 | Supported |  |
| 46 | plain terms | We searched each one's brightness record with two simple rules fixed in advance: repeated sudden faint measurements, and months-long stretches of dimming. | detect.py rules | Supported |  |
| 47 | plain terms | The rules found 15 of the 18 published debris-transit stars and candidates in our sample. | primary.json (g+r) known_recovered 15 | Supported |  |
| 48 | plain terms | By planting fake dimming events into real light curves, we measured how often the rules would catch such a star: about half to two-thirds of the time. | primary.json injection recovery 0.50-0.66 | Supported |  |
| 49 | plain terms | Counting the published systems and candidates, and correcting for what the search can catch, about 1 in 5,000 of these white dwarfs shows detectable debris transits; counting only the three firmly confirmed ones, about 1 in 24,000. | posthoc_review.json tiered rates 2.1e-4, 4.2e-5 | Supported |  |
| 50 | plain terms | The rules also flagged nearly 1,000 other stars. | primary.json (g+r) candidates 970 | Supported |  |
| 51 | plain terms | Many are probably slow drifts in the measurements rather than debris, but until each is checked, the true rate could be anywhere from about 1 in 5,000 to about 1 in 70. | posthoc_d3.json calendar_null; primary.json rate_upper 1.38e-2 (1/73) | Supported | D3: 'Most' -> 'Many'; 1 in 80 -> 1 in 70 |
| 52 | plain terms | So the study cannot say whether the rate is below the 1-in-2,000 bar the lead proposed. | primary.json H1 | Supported |  |
