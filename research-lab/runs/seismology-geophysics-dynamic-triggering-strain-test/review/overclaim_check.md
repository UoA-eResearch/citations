# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | No detectable remote dynamic triggering in the western US: after 350 distant M7+ earthquakes, rises in local events are no more common than at matched random times, and they do not grow with strain | primary.json primary H2 Refuted; E by quintile | Supported |  |
| 2 | standfirst | QuakeScope's 2026 PhaseNet picks for western-US stations (2.1 billion picks, 2002–2025) were turned into a catalogue-free local-event proxy: P–S pairs confirmed at 3 stations within 50 km. | coverage.json picks_fetch 2,088,914,320 | Supported |  |
| 3 | standfirst | For each global M ≥ 7 earthquake at least 1,000 km away, each station's count in the 24 hours after the surface waves was tested against its 7-day baseline. | windows.py test; plan.md section 3 | Supported |  |
| 4 | standfirst | The rate of significant rises was compared with the same station's rate at 500 matched random times. | windows.py station (500 pseudo) | Supported |  |
| 5 | standfirst | The plan and all analysis code were committed before any pick was counted. | git: plan e0e884d, code before proxy outputs | Supported |  |
| 6 | verdict | **Verdict: H2 Refuted; H1 Inconclusive.** There is no excess of significant rises overall. | primary.json primary H1 Inconclusive, H2 Refuted | Supported |  |
| 7 | verdict | None appears at high strain either, but the strain test's intervals are too wide to rule out a strain dependence by the preregistered rule. | primary.json primary E5 -0.0066 (-0.0147 to 0.0021); E5-3E1 CI includes 0 | Supported |  |
| 8 | verdict | **H2 (remote triggering produces an excess of significant local-event rises): Refuted.** | plan.md H2 | Supported |  |
| 9 | verdict | Across 228,963 station × trigger pairs (350 triggers, 1,496 stations), 15,042 rises were significant against 15,742 expected from each station's own rate at random times. | primary.json primary pairs, triggers 350, stations 1,496, observed 15,042, expected 15,742.2 | Supported |  |
| 10 | verdict | The mean excess is **−0.003** (95% two-way bootstrap −0.007 to +0.001), below the half-percentage-point bar. | primary.json primary E all -0.00306 (-0.00667, 0.00059) | Supported |  |
| 11 | verdict | **H1 (the excess is at least 3 times larger in the top strain quintile, and absent in the bottom): Inconclusive.** | plan.md H1 | Supported |  |
| 12 | verdict | The top-quintile excess is **−0.007** (−0.015 to +0.002), and the bottom quintile's is +0.002 (−0.006 to +0.009). | primary.json primary E5, E1 and CIs | Supported |  |
| 13 | verdict | Nothing rises with strain. | primary.json primary E1..E5 point estimates | Supported |  |
| 14 | verdict | Because the bottom quintile's excess is uncertain, though, the 3-times contrast (E5 − 3·E1: −0.012, −0.034 to +0.012) cannot be excluded. | primary.json primary E5_minus_3E1 -0.01185 (-0.03405, 0.01165) | Supported |  |
| 15 | verdict | **Every robustness variant agrees** (H2 Refuted, H1 Inconclusive): | primary.json sp5, conf07, base24h, post6h, no_geothermal, no_m8: all Inconclusive/Refuted | Supported |  |
| 16 | verdict | S−P of 0.8–5 s; confidence ≥ 0.7; | primary.json sp5, conf07, base24h, post6h, no_geothermal, no_m8: all Inconclusive/Refuted | Supported |  |
| 17 | verdict | a 24-hour baseline; a post window from 6 h after the surface waves; | primary.json sp5, conf07, base24h, post6h, no_geothermal, no_m8: all Inconclusive/Refuted | Supported |  |
| 18 | verdict | geothermal and volcanic areas excluded; triggers above M 8 excluded. | primary.json sp5, conf07, base24h, post6h, no_geothermal, no_m8: all Inconclusive/Refuted | Supported |  |
| 19 | verdict | **A masking artefact, checked post hoc (D1).** | deviations.md D1; primary.json exposure, no_m8 | Exploratory-labelled |  |
| 20 | verdict | The slight fall in excess with strain comes mainly from the proxy's removal of picks near predicted teleseismic arrivals. | deviations.md D1; primary.json exposure, no_m8 | Exploratory-labelled |  |
| 21 | verdict | Great earthquakes' aftershocks remove more of the post window. | deviations.md D1; primary.json exposure, no_m8 | Exploratory-labelled |  |
| 22 | verdict | Correcting each window for the time removed moves the overall excess to −0.001 (−0.004 to +0.003) and the top quintile to −0.002 (−0.011 to +0.006). | primary.json exposure: all -0.00067 (-0.00423, 0.00284); E5 -0.00228 (-0.01091, 0.00634) | Exploratory-labelled |  |
| 23 | verdict | **During the surface waves themselves** (exploratory), local-event detections fall, by 1.4 percentage points in significant rises, rather than rise. | primary.json instant: all -0.01386 | Exploratory-labelled | exploratory, labelled |
| 24 | verdict | Large waves hide small local events. | primary.json instant: all -0.01386 | Exploratory-labelled | exploratory, labelled |
| 25 | verdict | **Per trigger, apparent triggering is common and uninformative.** - Per trigger, the spread of observed minus expected is 10 times the variance that independent station outcomes would give. | trigger_dispersion.json: ratio 10.0; z>3: 39; z<-3: 55 | Supported | quantified after the draft |
| 26 | verdict | 39 of 350 triggers sit more than 3 standard errors above expectation, and 55 more than 3 below. | trigger_dispersion.json: ratio 10.0; z>3: 39; z<-3: 55 | Supported | quantified after the draft |
| 27 | verdict | A single trigger's excess cannot be read as triggering without a null that shares its timing across stations. | trigger_dispersion.json: ratio 10.0; z>3: 39; z<-3: 55 | Supported | quantified after the draft |
| 28 | plain terms | When a very large earthquake strikes anywhere on Earth, its surface waves travel around the planet. | framing; ledger S1-S4; primary results | Supported |  |
| 29 | plain terms | Some studies have claimed that these waves set off small earthquakes thousands of kilometres away, in places like California. | framing; ledger S1-S4; primary results | Supported |  |
| 30 | plain terms | Others have argued that most such "triggering" is coincidence: small earthquakes happen all the time, so some will always follow a big distant one by chance. | framing; ledger S1-S4; primary results | Supported |  |
| 31 | plain terms | We used AI-detected earthquake arrivals at about 1,500 western-US seismometers with long, continuous records (of about 9,000 in the catalogue) over 24 years. | population stations 1,496; 9,336 with proxy data | Supported | was 'about 9,000 seismometers' |
| 32 | plain terms | For each of 350 distant earthquakes of magnitude 7 or more, we checked whether small local earthquakes picked up at each station in the following day. | framing; ledger S1-S4; primary results | Supported |  |
| 33 | plain terms | Then we checked how often the same station shows such a pick-up at random times. | framing; ledger S1-S4; primary results | Supported |  |
| 34 | plain terms | The answer is: no more often. | framing; ledger S1-S4; primary results | Supported |  |
| 35 | plain terms | Small local earthquakes followed the distant giants at the same rate as they follow random moments. | framing; ledger S1-S4; primary results | Supported |  |
| 36 | plain terms | The rate also did not rise with the strength of the passing waves, as real triggering should. | framing; ledger S1-S4; primary results | Supported |  |
| 37 | plain terms | Some single big earthquakes do look as if they set things off (39 of 350), but even more look as if they did the opposite (55), and on average they match chance. | trigger_dispersion.json 39 vs 55 | Supported | was 'just as readily by chance' |
| 38 | plain terms | Triggering may still occur in particular places or for very small events this method misses. | proxy_validation.json recall 46% (very near and sparse-network events missed) | Supported |  |
| 39 | plain terms | It is not a widespread effect across the western US that this method can detect. | framing; ledger S1-S4; primary results | Supported | 'that this method can detect' added |
