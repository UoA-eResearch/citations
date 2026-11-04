# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | TESS finds tidally synchronized rotation in a fifth of Gaia's close binaries, not most, and the share steps down at the Kraft break; but much of the shortfall looks like measurement | primary.json f_cool 0.205, f_hot 0.093; posthoc.json T0 profile min 6300; posthoc.json share by sectors 0.10-0.40; g4_check.json visual 16/30 incoherent | Supported | softened to 'looks like' |
| 2 | standfirst | Gaia DR3 SB1 orbits (181,529) were cut to 49,960 main-sequence binaries. | coverage.json orbits 181,529 -> 49,960 | Supported |  |
| 3 | standfirst | Rotation periods for the 23,577 with orbits shorter than 12 days and a TIC match came from 70,531 TESS-SPOC full-frame-image light curves. | coverage.json tic_match 23,577; lc_index 70,531 TESS-SPOC | Supported |  |
| 4 | standfirst | A rotation counts as synchronized if it lies within 10% of the orbital (or pseudo-synchronous) period. | plan.md section 0; classify.py | Supported |  |
| 5 | standfirst | Shares are weighted by injection-recovery completeness. | analyse.py weights (1/C) | Supported |  |
| 6 | standfirst | The plan was committed before any data were downloaded. | git: plan.md commit precedes gaia.py's first run | Supported |  |
| 7 | verdict | **Verdict: H1 Refuted; H2 could not be estimated as planned (Inconclusive by the plan's rule).** | primary.json H1 Refuted; H2 Inconclusive with all bins at the fit bound | Supported |  |
| 8 | verdict | **H1 (more than 70% synchronized below 6,200 K, under 30% above 6,500 K, a transition under 400 K wide): Refuted.** | primary.json H1 verdict Refuted (f_cool CI 0.187-0.225 < 0.70) | Supported |  |
| 9 | verdict | Among cool binaries (4,000–6,200 K, P_orb < 10 d) with a detected period, **20.5%** are synchronized (95% interval 18.7–22.5%), far below the hypothesised 70%. | primary.json H1 n_cool 1,770, f_cool 0.205 (0.187-0.225) | Supported |  |
| 10 | verdict | Hot binaries (6,500–7,500 K) are at **9.3%** (6.9–12.1%), below 30% as hypothesised. | primary.json f_hot 0.093 (0.069-0.121) | Supported |  |
| 11 | verdict | The step between them is near where theory puts it. | posthoc.json T0_profile_delta_nll minimum at 6300 K (6200: 5.3, 6400: 0.9) | Supported | softened to 'near' |
| 12 | verdict | A profile likelihood places the transition at about 6,300 K, at the Kraft break, with a 10–90% width of about 300 K. | posthoc.json T0 profile min 6300; primary.json width_10_90 313.7 (43.9-423.3) | Supported |  |
| 13 | verdict | The preregistered fit's midpoint (6,200 K) sat on one of its starting values. | primary.json T0 estimate 6200.4 = a starting value of fit_teff | Supported |  |
| 14 | verdict | **H2 (synchronization extends to longer orbital periods than circularization): not estimable.** Neither share reaches one half at any period, so neither 50% cutoff exists. | primary.json H2 P_sync50 and P_circ50 at the 0.1 d bound in all bins | Supported |  |
| 15 | verdict | The synchronized share peaks at 0.34 (3–5 d) and the circular share at 0.38 (5–7 d). | posthoc.json sync_share_by_porb max 0.337 (3-5 d); circular_share_by_porb max 0.38 (5-7 d) | Supported |  |
| 16 | verdict | The plan's circular criterion, e < 0.05, does not suit Gaia orbits: noise biases their eccentricities upward (median 0.07–0.14 even below 3 d). | posthoc.json eccentricity_median_by_porb 0.072-0.135 below 7 d | Supported |  |
| 17 | verdict | **The 20% is better read as a floor than as a measurement.** | posthoc.json sync by sectors and Tmag; g4_check.json visual audit; Gaia agreement 41/135 | Supported | interpretation, hedged |
| 18 | verdict | The share rises steeply with data quality: 0.10 with one detecting sector, 0.27 with two, 0.35 with three, 0.40 with four or more; 0.26 for bright stars and 0.12 for faint ones. | posthoc.json sync_share_by_n_sectors 0.101/0.27/0.349/0.40; by Tmag 0.264/0.179/0.119 | Supported |  |
| 19 | verdict | In a visual audit of 30 classified light curves, 16 showed no coherent signal at the pipeline's period. | g4_check.json visual_audit no_visible_coherent_signal 16 of 30 | Supported | one rater, not blind |
| 20 | verdict | Of the 135 stars that also have a Gaia DR3 rotation period, only 30% agree with it. | g4_check.json with_a_tess_period 135, same 41 (30%) | Supported | denominator added |
| 21 | verdict | Kepler eclipsing binaries with P < 10 d are 79% synchronized (Lurie et al. 2017). | ledger A2 (Lurie et al. 2017 abstract) | Supported |  |
| 22 | plain terms | In close pairs of stars, tides are expected to lock each star's spin to its orbit, the way the Moon always shows Earth the same face. | framing | Supported |  |
| 23 | plain terms | Theory says this should happen readily for cooler, Sun-like stars, whose outer layers churn, and much less for hotter stars above about 6,200 K, where that churning layer thins out. | textbook theory (convective envelopes and the Kraft break); framing | Supported |  |
| 24 | plain terms | We tested this on about 17,000 binaries whose orbits Gaia measured, reading each star's spin from the dimming of starspots in TESS light curves. | coverage.json light_curves ok 17,112 | Supported | was 'tens of thousands' |
| 25 | plain terms | We found the step in the expected place: cool stars are about twice as likely as hot ones to be locked, and the change happens near 6,300 K. | primary.json f_cool 0.205 vs f_hot 0.093 (2.2x); posthoc.json T0 6300 | Supported |  |
| 26 | plain terms | But only about a fifth of the cool stars looked locked, not the large majority we expected. | primary.json f_cool 0.205 | Supported |  |
| 27 | plain terms | Much of that gap appears to come from the measurement rather than the stars. | posthoc.json; g4_check.json (hedged: 'appears to') | Supported |  |
| 28 | plain terms | Many of the "spin periods" our automatic method found are probably noise or light from neighbouring stars, and the locked fraction climbs towards half among the stars with the best data. | g4_check.json visual 16/30; Gaia agreement 30%; sync share rises with sectors and brightness (hedged: 'probably') | Supported |  |
| 29 | plain terms | A second test, comparing how fast circular orbits and locked spins give way at longer orbits, could not be done, because Gaia's orbit shapes are too noisy for the definition we chose in advance. | primary.json H2 not estimable; plausibility.md eccentricity noise | Supported |  |
