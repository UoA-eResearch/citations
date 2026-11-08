# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | A sixth of SAGE's test presences share a 1 km cell with a republished survey record once two missed Australian republications are flagged, yet removing those records barely changes Random Forest scores; West African and Ukrainian test plots are the exception | audit.json H2 0.1656; republication_flags_added.csv; primary.json H1 -0.00645; by_source_db TAVA, Ukraine | Supported |  |
| 2 | standfirst | SAGE trains species distribution models on GBIF presence-only records and tests them on sPlotOpen vegetation plots, treating the two as independent. | arXiv:2609.31082 (ledger A1, A2) | Supported |  |
| 3 | standfirst | Several of the vegetation-plot databases that supply its test plots are also published in GBIF. | provenance_flags.csv; ledger A3-A7 | Supported |  |
| 4 | standfirst | The first draft flagged those GBIF datasets from registry metadata and froze the list. | provenance_flags_frozen.csv; flag_search.py | Supported |  |
| 5 | standfirst | The review showed that list missed the second-largest source. | review finding 1; republication_scan.csv (NSW BioNet 664 cells) | Supported |  |
| 6 | standfirst | This revision flags republications from the data instead, with a same-day, same-cell species-list scan of every dataset, and re-runs the audit and the Random Forest retraining for 2,000 species (D4, post hoc). | code/republication_scan.py | Supported |  |
| 7 | standfirst | The preregistered frozen-list results are reported beside the corrected ones. | frozen_flags_*.json; report table | Supported |  |
| 8 | verdict | **Verdict: H1 Refuted; H2 Supported (corrected flag list). | audit.json H2 Supported; primary.json H1 Refuted | Supported |  |
| 9 | verdict | As preregistered with the frozen list, both Refuted.** | frozen_flags_audit.json, frozen_flags_primary.json | Supported |  |
| 10 | verdict | **H2 (at least 10% of source-plot test presences have a provenance-shared record in the same 1 km cell): Supported with the corrected list.** | audit.json H2 | Supported |  |
| 11 | verdict | **16.6%** (95% cell bootstrap 16.0% to 17.2%) of 268,972 test presences in 13,622 source test cells. | audit.json H2 0.1656 [0.1595, 0.1722], 268,972, 13,622 | Supported |  |
| 12 | verdict | With the frozen list it was 8.3% (7.7% to 8.9%). | frozen_flags_audit.json | Supported |  |
| 13 | verdict | The list missed NSW BioNet and SA Flora, which republish the Australian source (5,383 single-plot dated test cells; 664 and 96 of them reproduced). | republication_flags_added.csv 664, 96; sample cells 5,383 | Supported |  |
| 14 | verdict | It also flagged the Danish nature-monitoring portal only as "broad", which the analysis never counted. | provenance_flags_frozen.csv (broad); audit.py (core only) | Supported |  |
| 15 | verdict | Counting only records that reached SAGE's training data: 14.8%. 13.1% of all test presences have such a record and no other record of the species in the cell (provenance-only). | posthoc_h2_training.json b 0.1477 | Supported |  |
| 16 | verdict | Any-source same-cell overlap, which SAGE accepts by design, is 29.3%. | posthoc_h2_training.json c 0.2926 | Supported |  |
| 17 | verdict | By source: Denmark 98.6%, Netherlands 87.8%, TAVA West Africa 87.4%, Australia 27.1%, Ukraine 11.9%, France's SOPHY 0%. | audit.json H2_by_source | Supported |  |
| 18 | verdict | The scan finds no dataset that republishes SOPHY relevés. | republication_scan.csv (no France_sophy hi cells) | Supported |  |
| 19 | verdict | The "broad" sensitivity now defines source cells from core and broad sources together: 15.6% (15.1% to 16.2%). | audit.json H2_broad_sensitivity 0.1565 | Supported |  |
| 20 | verdict | The first draft's version was vacuous by construction. | review finding 2 | Supported |  |
| 21 | verdict | **H1 (removing provenance-shared training records lowers AUROC on source plots by at least 0.02 more than matched random removal): Refuted.** | primary.json H1 Refuted | Supported |  |
| 22 | verdict | The difference-in-differences is **−0.006** (−0.009 to −0.004) across 2,000 species. | primary.json H1 did -0.00645 [-0.00903, -0.00402] | Supported |  |
| 23 | verdict | Removing the republished records hurts the scores slightly less than random removal does. | primary.json auroc_C1 0.8611 > auroc_random 0.8546 | Supported |  |
| 24 | verdict | **The random control falls short.** Many Australian species have too few other records in the country to match, so random removal removed only about half as many records (a mean 221 against 446 per species). | posthoc_shortfall.json mean_removed 446.1 vs 220.5; by_source Australia 0.47 | Supported |  |
| 25 | verdict | Restricted to the 1,656 species where random removal reached at least 90% of C1, the DiD is +0.001 (−0.001 to +0.003). | posthoc_shortfall.json did_matched 0.00094 [-0.00079, 0.00263] | Supported |  |
| 26 | verdict | With the frozen list it was +0.006 (+0.005 to +0.008), on 1,745 species. | frozen_flags_primary.json | Supported |  |
| 27 | verdict | **Two databases still exceed 0.02 on their own:** | primary.json by_source_db | Supported |  |
| 28 | verdict | **TAVA West Africa: DiD +0.128** (+0.097 to +0.163, 56 species). | primary.json TAVA 0.12806 [0.09694, 0.16252] | Supported |  |
| 29 | verdict | AUROC falls from 0.807 to 0.693 without the shared records but is 0.821 after random removal. | primary.json TAVA auroc_C0 0.807, C1 0.693, random 0.8211 | Supported |  |
| 30 | verdict | The West African test plots are themselves in the training data. | frozen_flags_posthoc_same_releve.json (TAVA species lists); review | Supported |  |
| 31 | verdict | **Ukrainian grasslands: DiD +0.050** (+0.037 to +0.064, 326 species). | primary.json Ukraine 0.05019 | Supported |  |
| 32 | verdict | **Not because removed records turn into pseudo-absences.** In C1 a removed presence can become a background cell for that species. | posthoc_neutral.json | Supported |  |
| 33 | verdict | A neutral variant keeps those cells out of the background and gives +0.118 (TAVA) and +0.052 (Ukraine), so the effect is lost information (post hoc). | posthoc_neutral.json TAVA 0.1177, Ukraine 0.0518 | Supported |  |
| 34 | verdict | The Netherlands: 88% co-located, DiD +0.017 (+0.009 to +0.025). | audit.json NL 0.8783; primary.json NL 0.01662 | Supported |  |
| 35 | verdict | Australia: −0.025, where the random control removed half as much. | primary.json Australia -0.02542; posthoc_shortfall.json ratio 0.47 | Supported |  |
| 36 | plain terms | New benchmarks for species distribution models train on millions of crowd-sourced and museum sightings from GBIF. | ledger A1 | Supported |  |
| 37 | plain terms | They then test the models on expert vegetation surveys, assuming the two sources are independent. | ledger A2 | Supported |  |
| 38 | plain terms | But some of those expert surveys are also published inside GBIF, so a model might be tested on places it has, in effect, already seen. | ledger A3-A7 | Supported |  |
| 39 | plain terms | Our first attempt to find those republished surveys used dataset descriptions and missed the second-largest one: Australian state flora databases that carry the same survey plots without saying so. | review finding 1; republication_flags_added.csv | Supported |  |
| 40 | plain terms | Checking the data directly, by looking for the same species list recorded on the same day in the same square kilometre, found them. | republication_scan.py method | Supported |  |
| 41 | plain terms | With them counted, about one in six test sightings has a republished survey record next to it. | audit.json H2 0.1656 | Supported |  |
| 42 | plain terms | We then retrained the benchmark's Random Forest model for 2,000 plant species without the republished records, and again without an equal number of other records. | population.csv 2,000; primary.json | Supported |  |
| 43 | plain terms | Overall, removing the republished surveys makes almost no difference. | primary.json H1 did -0.00645; posthoc_shortfall did_matched 0.00094 | Supported |  |
| 44 | plain terms | In West Africa, though, the score for the region's species drops sharply, from 0.81 to 0.69, because the test plots themselves are in the training data. | primary.json by_source_db TAVA C0 0.807, C1 0.693; posthoc_same_releve (first draft TAVA 87% exact lists) | Supported |  |
| 45 | plain terms | Ukrainian grasslands show a smaller drop. | primary.json Ukraine C0 0.738, C1 0.688 | Supported |  |
| 46 | plain terms | So the benchmark's overall Random Forest scores hold up, but its scores for West African species partly reward recalling the training data, and which surveys are republished cannot be read from metadata alone. | primary.json; republication_scan.py vs flag_search (interpretation) | Supported |  |
