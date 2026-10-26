# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | A taxonomy-aware species-interaction predictor keeps its edge over "who gets studied" on GloBI's future records, though nearly half of those records come from one dataset of mostly inferred links | primary.json rho 1.68; without_trophiCH; trophiCH 44.7% | Supported | was 'its advantage grows, not shrinks' (review 1) |
| 2 | standfirst | GloBI's interpreted interaction snapshots: v0.6 (2023-08-25) as the past and v0.11 (2026-09-10) as the future. | framing; plan.md; build.py | Supported |  |
| 3 | standfirst | Species-level trophic, pollination and host–parasite pairs. | framing; plan.md; build.py | Supported |  |
| 4 | standfirst | Three predictors: effort only (degree and citation counts), a structural embedding (RDPG), and gradient boosting on taxonomic-neighbourhood features. | framing; plan.md; build.py | Supported |  |
| 5 | standfirst | Each is evaluated on a random holdout within v0.6 and on 411,702 pairs first recorded in v0.11 between species already in v0.6. | framing; plan.md; build.py | Supported |  |
| 6 | standfirst | The plan was committed before any graph was built. | framing; plan.md; build.py | Supported |  |
| 7 | standfirst | This version includes fixes made after independent review (D2): the dominant dataset is disclosed and tested, the degree-matched negatives are corrected, and coverage accounting is added. | deviations.md D2 | Supported |  |
| 8 | verdict | **Verdict: H1 Refuted.** The advantage of taxonomy-aware prediction does not halve out of time: it holds. | primary.json H1 Refuted; rho 1.68 | Supported | 'it holds' replaces 'grows' |
| 9 | verdict | **H1 (the structural advantage over effort at least halves on future records): Refuted.** | plan.md H1 | Supported |  |
| 10 | verdict | The best structural predictor, taxonomy + structure, beats effort by **+0.040 AUROC** on the random holdout (0.991 against 0.951; 95% cluster bootstrap +0.029 to +0.054). | primary.json A_random 0.0401 (0.0288-0.0542) | Supported |  |
| 11 | verdict | On the temporal holdout it beats effort by **+0.067** (0.947 against 0.880; +0.052 to +0.075). | primary.json A_temporal 0.0673 (0.0519-0.075) | Supported |  |
| 12 | verdict | The ratio is **1.68** (1.10 to 2.31), against the hypothesis of at most 0.5. | primary.json rho 1.6767 (1.0953-2.308) | Supported |  |
| 13 | verdict | **Nearly half the future records come from one dataset of mostly inferred links (D2).** | primary.json temporal_clusters largest_share 0.4467 | Exploratory-labelled | added (review 1) |
| 14 | verdict | 183,892 of the 411,702 temporal positives (45%) are from trophiCH, a Swiss national metaweb. | primary.json without_trophiCH trophiCH_positives 183,892 | Exploratory-labelled | added (review 1) |
| 15 | verdict | Only 30% of its species-level links are documented; the rest are inferred from coarser taxonomic records. | ledger L9 (trophiCH abstract) | Supported | added (review 1) |
| 16 | verdict | Without trophiCH, the advantage is +0.059 (+0.050 to +0.068) and the ratio is **1.46 (1.05 to 2.08)**. | primary.json without_trophiCH A 0.0585 (0.0502-0.0681), rho 1.4574 (1.0537-2.0804) | Exploratory-labelled | added (review 1) |
| 17 | verdict | H1 is still Refuted. | primary.json without_trophiCH rho_ci lower 1.05 > 0.5 | Exploratory-labelled | added |
| 18 | verdict | That the advantage grows out of time is only narrowly supported once the inferred dataset is set aside. | without_trophiCH rho_ci lower bound 1.05 | Exploratory-labelled | added (review 1) |
| 19 | verdict | **What shrinks under uniform negatives is effort.** | primary.json auroc: effort 0.951 -> 0.880, taxgb 0.991 -> 0.947 | Supported |  |
| 20 | verdict | Prior degree and citation counts lose 0.07 AUROC going from a random to a temporal holdout; the taxonomic model loses 0.04. | primary.json auroc | Supported |  |
| 21 | verdict | The structural embedding by itself (RDPG) is worse than effort on both holdouts. | primary.json rdpg 0.942/0.805 vs effort 0.951/0.880 | Supported |  |
| 22 | verdict | **With degree-matched negatives (corrected in D2), effort falls to chance:** | primary.json degree_matched; degree_matched_sampler decile_fill 1.0 | Exploratory-labelled | was 'grows with degree-matched negatives' (review 2) |
| 23 | verdict | effort scores 0.50 random and 0.51 temporal; | primary.json degree_matched effort 0.5009 / 0.514 | Exploratory-labelled | corrected sampler (D2) |
| 24 | verdict | the taxonomic model scores 0.93 random and 0.83 temporal; | primary.json degree_matched taxgb 0.9301 / 0.8306 | Exploratory-labelled | corrected sampler (D2) |
| 25 | verdict | the advantage still shrinks out of time, from 0.43 to 0.32 (a ratio of 0.74, still above the hypothesis's 0.5). | primary.json degree_matched: 0.9301-0.5009=0.429; 0.8306-0.514=0.317; ratio 0.74 | Exploratory-labelled | was 'grows' (review 2) |
| 26 | verdict | **The edge holds where it matters most:** | primary.json temporal_subsets | Supported |  |
| 27 | verdict | for pairs introduced by datasets indexed after v0.6 (72% of the future pairs): 0.940 against 0.870; | primary.json new_dataset 298,259; 0.9402 vs 0.8702 | Supported |  |
| 28 | verdict | for species with a single prior link: 0.881 against 0.718; | primary.json cold_start 0.8812 vs 0.7184 | Supported |  |
| 29 | verdict | in 24 of the 26 datasets with at least 1,000 future pairs. | per_dataset.csv 24 of 26 positive | Exploratory-labelled | added (review 5) |
| 30 | verdict | **Name changes do not drive the result.** The independent review found that 1.1% of positives have an old record behind them under another name; dropping them changes nothing. | review/review.md finding 4 (1.1%; A 0.0662 -> 0.0658) | Supported | was 'some new pairs may be re-resolved old ones' (review 4) |
| 31 | verdict | The 26–42% of v0.6 pairs missing from v0.11 are mainly pairs removed, refuted or re-typed. | review/review.md finding 4; turnover.json | Supported | added (review 4) |
| 32 | plain terms | Scientists use machine learning to guess which species interact, such as who eats whom, which insect pollinates which plant, or which parasite lives on which host, so that field work can be pointed at likely pairs. | framing; plan.md; build.py | Supported |  |
| 33 | plain terms | A worry is that these models mostly learn which species scientists already study a lot, and would be no better than simply betting on well-studied species. | framing; plan.md; build.py | Supported |  |
| 34 | plain terms | We used two archived snapshots of GloBI, a global database of species interactions, three years apart. | framing; plan.md; build.py | Supported |  |
| 35 | plain terms | We trained models on the older snapshot and asked how well they picked out interactions that appeared in the newer one. | framing; plan.md; build.py | Supported |  |
| 36 | plain terms | A simple "popularity" guess, based on how many interactions and studies a species already had, did well. | primary.json effort 0.880 temporal | Supported |  |
| 37 | plain terms | A model that also uses what related species do did clearly better, on the new records as much as on a random test drawn from the old one. | primary.json A 0.067 temporal vs 0.040 random (uniform); matched 0.32 vs 0.43 | Supported | was 'its advantage was bigger on the new records' |
| 38 | plain terms | That held for interactions contributed by newly added studies and for species that had been recorded only once before. | primary.json temporal_subsets new_dataset, cold_start | Supported |  |
| 39 | plain terms | There is a catch. | without_trophiCH; ledger L9 | Supported | added (review 1) |
| 40 | plain terms | Almost half of the new records come from one Swiss database, most of whose links were inferred from records made at the genus level rather than observed for each species. | ledger L9; trophiCH 45% of positives | Supported | added (review 1) |
| 41 | plain terms | Without it the taxonomy-aware model still wins, by a similar margin. | without_trophiCH A 0.059 vs 0.067 | Supported | added |
| 42 | plain terms | So in this database, taxonomy-aware prediction is not just repeating "who gets studied", but a large part of the "future" it is tested on was itself produced by taxonomic reasoning. | trophiCH 45% of positives; about 70% of its links inferred (L9) | Supported | added |
