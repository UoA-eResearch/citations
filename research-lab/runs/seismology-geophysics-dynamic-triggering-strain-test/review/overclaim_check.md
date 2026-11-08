# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | After distant M7+ earthquakes, day-scale rises in local events at about 1,500 long-running western-US stations are about as common as at matched random times; an excess as large as the half-point bar cannot be ruled out, and no rise with strain is seen | comparable.json pseudo_rule all +0.00004 (-0.008, +0.008); E by quintile flat; H1 Inconclusive | Supported |  |
| 2 | standfirst | QuakeScope's 2026 PhaseNet picks for western-US stations (2.1 billion picks, 2002–2025) were turned into a catalogue-free local-event proxy: P–S pairs confirmed at 3 stations within 50 km. | coverage.json picks_fetch 2,088,914,320 | Supported |  |
| 3 | standfirst | For each global M ≥ 7 earthquake at least 1,000 km away, each station's count in the 24 hours after the surface waves was tested against its 7-day baseline. | windows.py test; plan.md section 3 | Supported |  |
| 4 | standfirst | The rate of significant rises was compared with the same station's rate at 500 matched random times. | windows.py station (500 pseudo) | Supported |  |
| 5 | standfirst | The plan and all analysis code were committed before any pick was counted. | git: plan e0e884d, code before proxy outputs | Supported |  |
| 6 | verdict | **Verdict: H1 Inconclusive; H2 Inconclusive on comparable arms (corrected primary, post hoc); H2 Refuted as preregistered.** The preregistered null was drawn only at times away from other large earthquakes, while the real triggers were not. | comparable.json pseudo_rule H1/H2; primary.json primary H2 Refuted | Supported |  |
| 7 | verdict | Comparing like with like, there is no excess, but the interval reaches the half-point bar. | comparable.json pseudo_rule all CI [-0.00795, 0.00847] | Supported |  |
| 8 | verdict | **Why the preregistered comparison is not like for like** (found in review). | section heading | Supported |  |
| 9 | verdict | Pseudo-triggers were rejected within 10 days of any global M ≥ 7 and 3 days of any M ≥ 6.5. | windows.py near7/near65 rule | Supported |  |
| 10 | verdict | Real triggers were not: 282 of the 350 fail that rule. | comparable.json triggers_failing_pseudo_rule 282 of 350 | Supported |  |
| 11 | verdict | Pairs with another M ≥ 6.5 between the origin and the end of the post window carry that earthquake's surface-wave detection shadow and aftershock masking, which the null never sees. | primary.json instant (detection shadow -1.4 pp); review finding 1 | Supported |  |
| 12 | verdict | Their mean excess is −0.013 (−0.019 to −0.006). | comparable.json post_contam all -0.01319 (-0.019, -0.00641) | Supported |  |
| 13 | verdict | This contamination grows with strain, from 16% of pairs in the lowest strain quintile to 33–36% in the top two, because big triggers have big early aftershocks. | comparable.json post_contam_share_by_quintile 0.163 -> 0.36/0.332 | Supported |  |
| 14 | verdict | **H2 (remote triggering produces an excess of significant local-event rises): Inconclusive on comparable arms.** | comparable.json pseudo_rule H2 Inconclusive | Supported |  |
| 15 | verdict | **Corrected primary:** the null's own exclusion rule applied to real triggers leaves 68 triggers and 43,771 station × trigger pairs. | comparable.json pseudo_rule triggers 68, pairs 43771 | Supported |  |
| 16 | verdict | The mean excess is **+0.000** (95% two-way bootstrap −0.008 to +0.008). | comparable.json pseudo_rule all 0.00004 [-0.00795, 0.00847] | Supported |  |
| 17 | verdict | **No other M ≥ 6.5 inside a pair's own windows** (109 triggers, 72,189 pairs): +0.004 (−0.002 to +0.011), Inconclusive. | comparable.json clean_windows 109 / 72189; 0.00415 [-0.0024, 0.01109] | Supported |  |
| 18 | verdict | **Preregistered, all 350 triggers** (228,963 pairs, 1,496 stations): 15,042 significant rises against 15,742 expected; mean excess −0.003 (−0.007 to +0.001), Refuted by the preregistered rule. | primary.json primary pairs 228963, observed 15042, expected 15742.2, all -0.00306 | Supported |  |
| 19 | verdict | Every preregistered robustness variant gives the same verdict, but all share the same mismatch. | primary.json variants all H2 Refuted; all use the same pseudo rule | Supported |  |
| 20 | verdict | **H1 (the excess is at least 3 times larger in the top strain quintile, and absent in the bottom): Inconclusive** in the corrected primary, the preregistered analysis and every preregistered variant. | comparable.json H1 per class; primary.json variants | Supported |  |
| 21 | verdict | The contaminated baseline-only subset gives Refuted. | comparable.json base_only H1 Refuted | Supported |  |
| 22 | verdict | Corrected primary: top quintile −0.003 (−0.024 to +0.023), bottom +0.002 (−0.015 to +0.020). | comparable.json pseudo_rule E_ci95 5 [-0.024, 0.023], 1 [-0.015, 0.020] | Supported |  |
| 23 | verdict | Preregistered: top −0.007 (−0.015 to +0.002), bottom +0.002 (−0.006 to +0.009). | primary.json primary E_ci95 5 and 1 | Supported |  |
| 24 | verdict | Nothing rises with strain in either. | comparable.json pseudo_rule E by quintile; primary.json primary E | Supported |  |
| 25 | verdict | The intervals are too wide to exclude a 3-times contrast. | comparable.json pseudo_rule E5_minus_3E1_ci95 [-0.066, 0.048] | Supported |  |
| 26 | verdict | **What the design can detect.** The proxy catches about half of the M ≥ 1 events near a station (46%; 52% at M ≥ 3), and a significant rise needs roughly a doubling of a station's weekly rate within a day. | proxy_validation.json recall 0.46 / 0.52; beta >= 2 rule (review finding 3) | Supported |  |
| 27 | verdict | So the test is for triggered swarms that double a station's rate for a day, not for a few extra tiny events. | beta rule; review finding 3 | Supported |  |
| 28 | verdict | **During the surface waves themselves** (exploratory), detections fall, by 1.4 percentage points in significant rises. | primary.json instant -0.014 | Supported |  |
| 29 | verdict | Instantaneous triggering, where most published cases sit, cannot be tested here. | review finding 3; Not shown bullet | Supported |  |
| 30 | verdict | **The stations are about 1,500 long-running ones,** 16% of the 9,336 with proxy data, chosen because every station-day in a pair's 9-day window had to be available. | coverage.json 1,496 of 9,336; windows.py loaded-day rule | Supported |  |
| 31 | verdict | The rule is the same for real and random times. | windows.py test() used for both | Supported |  |
| 32 | verdict | Each station's null rests on a median of 212 valid random times, so single-station excesses are mostly noise. | null_primary.parquet population median pseudo_valid 212 | Supported |  |
| 33 | verdict | **Per trigger, apparent triggering is common and uninformative.** | trigger_dispersion.json | Supported |  |
| 34 | verdict | Per trigger, the spread of observed minus expected is 10 times the variance that independent station outcomes would give. | trigger_dispersion.json ratio 10.0 | Supported |  |
| 35 | verdict | 39 of 350 triggers sit more than 3 standard errors above expectation, and 55 more than 3 below. | trigger_dispersion.json: ratio 10.0; z>3: 39; z<-3: 55 | Supported | quantified after the draft |
| 36 | verdict | A single trigger's excess cannot be read as triggering without a null that shares its timing across stations. | trigger_dispersion.json: ratio 10.0; z>3: 39; z<-3: 55 | Supported | quantified after the draft |
| 37 | plain terms | When a very large earthquake strikes anywhere on Earth, its surface waves travel around the planet. | framing; ledger S1-S4; primary results | Supported |  |
| 38 | plain terms | Some studies have claimed that these waves set off small earthquakes thousands of kilometres away, in places like California. | framing; ledger S1-S4; primary results | Supported |  |
| 39 | plain terms | Others have argued that most such "triggering" is coincidence: small earthquakes happen all the time, so some will always follow a big distant one by chance. | framing; ledger S1-S4; primary results | Supported |  |
| 40 | plain terms | We used AI-detected earthquake arrivals at about 1,500 western-US seismometers with long, continuous records (of about 9,000 in the catalogue) over 24 years. | population stations 1,496; 9,336 with proxy data | Supported | was 'about 9,000 seismometers' |
| 41 | plain terms | For each of 350 distant earthquakes of magnitude 7 or more, we checked whether small local earthquakes picked up at each station in the following day. | framing; ledger S1-S4; primary results | Supported |  |
| 42 | plain terms | Then we checked how often the same station shows such a pick-up at random times. | framing; ledger S1-S4; primary results | Supported |  |
| 43 | plain terms | The answer is: about as often, though not a firm "no". | comparable.json pseudo_rule | Supported |  |
| 44 | plain terms | Our first comparison suggested slightly less often, but the random moments had been chosen away from other big earthquakes, and the real ones had not. | primary.json primary -0.003; review finding 1 | Supported |  |
| 45 | plain terms | Big earthquakes come with big aftershocks, whose waves hide small local events. | comparable.json post_contam_share_by_quintile; primary.json instant | Supported |  |
| 46 | plain terms | Compared fairly, small local earthquakes followed the distant giants about as often as random moments, within an uncertainty of under a percentage point either way. | comparable.json pseudo_rule all [-0.008, 0.008] | Supported |  |
| 47 | plain terms | The rate also did not rise with the strength of the passing waves, as real triggering should. | framing; ledger S1-S4; primary results | Supported |  |
| 48 | plain terms | Some single big earthquakes do look as if they set things off (39 of 350), but even more look as if they did the opposite (55), and on average they match chance. | trigger_dispersion.json 39 vs 55 | Supported | was 'just as readily by chance' |
| 49 | plain terms | Triggering may still occur in particular places, during the waves themselves, or for very small events this method misses. | proxy recall; instant window; Not shown | Supported |  |
| 50 | plain terms | A widespread effect across the western US large enough for this method to detect is not seen, though a small one at the size of our preregistered bar cannot be ruled out. | comparable.json pseudo_rule upper 0.0085 > 0.005 bar | Supported |  |
