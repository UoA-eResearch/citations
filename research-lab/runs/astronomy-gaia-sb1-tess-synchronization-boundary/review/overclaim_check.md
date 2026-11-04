# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Tidal synchronization in Gaia's close binaries shows up clearly in TESS light curves, but too diluted by measurement to test where it stops; the apparent step at the Kraft break appears to follow spot detectability | posthoc2.json chance 0.09/0.05 vs observed 0.22/0.12; credible 0.42/0.37 overlapping; g4_check.json 16/30 incoherent | Supported | hedged ('appears to'); rewritten in D2 |
| 2 | standfirst | Gaia DR3 SB1 orbits (181,529) were cut to 49,960 main-sequence binaries. | coverage.json orbits 181,529 -> 49,960 | Supported |  |
| 3 | standfirst | Rotation periods for the 23,577 with orbits shorter than 12 days and a TIC match came from 70,531 TESS-SPOC full-frame-image light curves. | coverage.json tic_match 23,577; lc_index 70,531 TESS-SPOC | Supported |  |
| 4 | standfirst | A rotation counts as synchronized if it lies within 10% of the orbital (or pseudo-synchronous) period. | plan.md section 0; classify.py | Supported |  |
| 5 | standfirst | The plan was committed before any data were downloaded. | git: plan.md commit precedes the first download | Supported |  |
| 6 | standfirst | This version follows an independent review that returned "fix first" (D2). | review/review.md verdict fix first; deviations.md D2 | Supported |  |
| 7 | verdict | **Verdict: H1 Refuted; H2 Inconclusive.** | primary.json H1 Refuted, H2 Inconclusive | Supported |  |
| 8 | verdict | **H1 (more than 70% synchronized below 6,200 K, under 30% above 6,500 K, a transition under 400 K wide): Refuted.** | primary.json H1 Refuted (f_cool CI 0.187-0.225 < 0.70) | Supported |  |
| 9 | verdict | Among cool binaries (4,000–6,200 K, P_orb < 10 d) with a detected period, **20.5%** are synchronized (95% interval 18.7–22.5%, completeness-weighted); among hot binaries (6,500–7,500 K), **9.3%** (6.9–12.1%). | primary.json f_cool 0.205 (0.187-0.225), f_hot 0.093 (0.069-0.121) | Supported |  |
| 10 | verdict | These are about 6.5% of all cool binaries with light curves, since only 29% have a usable period. | stars.parquet: cool with light curves 6,552, detected 1,895 (28.9%), synchronized 424 (6.5%) | Supported | review finding 10 |
| 11 | verdict | **Synchronization is real, at well above chance.** Pairing each detected period with a random orbital period gives 0.09 (cool) and 0.05 (hot), against observed shares of 0.22 and 0.12 (unweighted). | posthoc2.json chance_cool 0.093 vs 0.224, chance_hot 0.048 vs 0.123 | Supported | post hoc (D2) |
| 12 | verdict | **There is no clear step at the Kraft break once the signal is credible.** | posthoc2.json credible cool 0.42 (0.38-0.46) vs hot 0.37 (0.27-0.46) | Supported | softened to 'no clear step' |
| 13 | verdict | The full sample's step from 0.21 to 0.09 appears to track how detectable spots are rather than tides. | posthoc2.json credible shares overlap; posthoc.json share by sectors/Tmag | Supported | hedged |
| 14 | verdict | Restricted to credible signals (amplitude above 2 ppt, seen in at least two sectors), the shares are **0.42** (0.38–0.46, n 614) for cool and **0.37** (0.27–0.46, n 104) for hot binaries, with overlapping intervals. | posthoc2.json credible_cool n 614 share 0.423 (0.384-0.463); credible_hot n 104 0.365 (0.269-0.462) | Supported |  |
| 15 | verdict | These credible-signal results are post hoc (D2). 38 of the 104 hot signals exceed 20 ppt, the scale of ellipsoidal variation in F stars; without them the hot share is 0.42 (n 66). | stars.parquet hot credible 104, 38 above 20 ppt; share among the other 66 = 0.424 | Supported | confirmation |
| 16 | verdict | The hot interval still allows a drop of up to a third. | posthoc2.json credible_hot ci 0.269-0.462 vs cool 0.423: a drop to ~0.28 is inside the interval | Supported | caveat added at confirmation |
| 17 | verdict | **H2 (synchronization extends to longer orbital periods than circularization): Inconclusive.** | primary.json H2 Inconclusive | Supported |  |
| 18 | verdict | The synchronized share never reaches one half, so P_sync,50 is undefined. | primary.json H2 bins: P_sync50 at the fit bound | Supported |  |
| 19 | verdict | This is most likely a symptom of the dilution above rather than a property of the binaries. | posthoc.json share rises with sectors (0.10-0.40); hedged 'most likely' | Supported | softened |
| 20 | verdict | The plan's circular criterion, e < 0.05, also fails, because Gaia's eccentricities are biased upward by noise. | posthoc.json eccentricity medians 0.07-0.14; circular share max 0.38 | Supported |  |
| 21 | verdict | With a noise-aware criterion (e consistent with zero; post hoc), the circularization cutoff is 4.1–5.9 days across the three Teff bins, rising with Teff. | posthoc2.json h2_noise_aware P_circ50 4.08 / 5.29 / 5.94 d | Supported | post hoc |
| 22 | verdict | That is the opposite of Bashi et al. | ledger A1 (Bashi et al. 2023); confirmation pass check | Supported | caveat added at confirmation |
| 23 | verdict | (2023), who found 6.5 falling to 2.5 d on the same orbits, and the indicator depends on Gaia's error estimates, so this cutoff is not reliable. | Bashi et al. 2023 cutoffs per the confirmation pass (6.5 -> 2.5 d); indicator uses eccentricity_error | Supported | the post hoc cutoff is marked unreliable |
| 24 | plain terms | In close pairs of stars, tides are expected to lock each star's spin to its orbit, the way the Moon always shows Earth the same face. | framing | Supported |  |
| 25 | plain terms | Theory says this should happen readily for cooler, Sun-like stars, and much less for hotter stars above about 6,200 K. | textbook theory (Kraft break); framing | Supported |  |
| 26 | plain terms | We tested this on about 17,000 binaries whose orbits Gaia measured, reading each star's spin from starspot dimming in TESS light curves. | coverage.json light_curves ok 17,112 | Supported |  |
| 27 | plain terms | Locked spins are clearly there, at two to three times the rate chance would give. | posthoc2.json observed/chance 2.4 (cool) and 2.6 (hot) | Supported |  |
| 28 | plain terms | But our automatic period finder also picked up many signals that are not the star's spin: noise and, probably, light from neighbouring stars. | g4_check.json visual 16/30 incoherent; RUWE sync 1.09 vs sub 1.17 ('probably') | Supported |  |
| 29 | plain terms | These dilute the locked fraction to about a fifth. | primary.json f_cool 0.205 | Supported |  |
| 30 | plain terms | When we keep only clear, repeated signals, about two in five binaries look locked, with no clear difference between hot and cool. | posthoc2.json credible 0.42 cool / 0.37 hot, overlapping; hot without >20 ppt 0.42 (n 66) | Supported | 'hot or cool alike' softened at confirmation |
| 31 | plain terms | The drop we first reported above 6,200 K appears to come from hot stars' spots being harder to detect, not from weaker tides. | posthoc2.json credible shares overlap; hedged 'appears to' | Supported |  |
| 32 | plain terms | So the test we planned could not be done cleanly with these data. | H1 refuted on a diluted measurement; H2 not estimable | Supported |  |
| 33 | plain terms | It needs either vetted light curves, as earlier eclipsing-binary studies used, or spin measured from spectral line broadening. | ledger A2 (Lurie et al. visually vetted EBs); Gaia vbroad as a spectroscopic route | Supported |  |
