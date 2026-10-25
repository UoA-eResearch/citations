# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | A taxonomy-aware species-interaction predictor beats "who gets studied" on GloBI's future records too: its advantage grows, not shrinks, out of time | primary.json A_temporal 0.068 > A_random 0.040; rho 1.68 | Supported | was 'Species-interaction predictors beat...' (only the taxonomic model does; RDPG trails effort) |
| 2 | standfirst | GloBI's interpreted interaction snapshots: v0.6 (2023-08-25) as the past and v0.11 (2026-09-10) as the future. | plan.md; ledger L6, L7 | Supported |  |
| 3 | standfirst | Species-level trophic, pollination and host–parasite pairs. | plan.md classes; per_class.csv | Supported |  |
| 4 | standfirst | Three predictors: effort only (degree and citation counts), a structural embedding (RDPG), and gradient boosting on taxonomic-neighbourhood features. | plan.md predictors; primary.json auroc keys | Supported |  |
| 5 | standfirst | Each is evaluated on a random holdout within v0.6 and on 411,702 pairs first recorded in v0.11 between species already in v0.6. | primary.json n.temporal.pos 411,702 | Supported |  |
| 6 | standfirst | The plan was committed before any graph was built. | git: plan committed before build.py outputs | Supported |  |
| 7 | verdict | **Verdict: H1 Refuted.** | primary.json H1 Refuted | Supported |  |
| 8 | verdict | **H1 (the structural advantage over effort at least halves on future records): Refuted.** | plan.md H1 | Supported |  |
| 9 | verdict | The best structural predictor, taxonomy + structure, beats effort by **+0.040 AUROC** on the random holdout (0.991 against 0.951; 95% cluster bootstrap +0.029 to +0.054). | primary.json A_random 0.0401 (0.0288-0.0542); taxgb 0.991, effort 0.951 | Supported |  |
| 10 | verdict | On the temporal holdout it beats effort by **+0.068** (0.948 against 0.880; +0.053 to +0.075). | primary.json A_temporal 0.0675 (0.0526-0.0753); 0.948 vs 0.880 | Supported |  |
| 11 | verdict | The ratio is **1.68** (1.10 to 2.30), against the hypothesis of at most 0.5. | primary.json rho 1.683 (1.099-2.303) | Supported |  |
| 12 | verdict | **What shrinks is effort.** Prior degree and citation counts lose 0.07 AUROC going from a random to a temporal holdout; the taxonomic model loses 0.04. | effort 0.951->0.880 (-0.071); taxgb 0.991->0.948 (-0.043) | Supported |  |
| 13 | verdict | So most of the out-of-time loss falls on the effort baseline. | effort loses 0.071 vs taxgb 0.043 | Supported | was 'Future records favour neither the most-studied species nor the bare network structure' (unclear; effort still 0.88) |
| 14 | verdict | The structural embedding by itself (RDPG) is worse than effort on both holdouts. | rdpg 0.942 < 0.951 random; 0.805 < 0.880 temporal | Supported |  |
| 15 | verdict | **The edge holds where it matters most:** | temporal_subsets new_dataset and cold_start | Supported |  |
| 16 | verdict | for pairs introduced by datasets indexed after v0.6 (72% of the future pairs): 0.940 against 0.870; | new_dataset pos 298,259 / 411,702 = 72%; 0.940 vs 0.870 | Supported |  |
| 17 | verdict | for species with a single prior link: 0.882 against 0.718. | cold_start 0.882 vs 0.718 | Supported |  |
| 18 | verdict | **It grows with degree-matched negatives.** There effort falls to 0.568 on the temporal holdout and the taxonomic model stays at 0.850. | degree_matched temporal effort 0.568, taxgb 0.850 | Supported |  |
| 19 | verdict | **A caution on the records.** 26–42% of v0.6 species pairs, by class, are absent from v0.11 (name re-resolution and dataset changes), so some "new" pairs may be re-resolved old ones. | turnover.json host 0.360, pollination 0.416, trophic 0.264 (code/turnover.py) | Supported |  |
| 20 | plain terms | Scientists use machine learning to guess which species interact, such as who eats whom, which insect pollinates which plant, or which parasite lives on which host, so that field work can be pointed at likely pairs. | background framing | Supported |  |
| 21 | plain terms | A worry is that these models mostly learn which species scientists already study a lot, and would be no better than simply betting on well-studied species. | lead.gap (effort confound); ledger L1 | Supported |  |
| 22 | plain terms | We used two archived snapshots of GloBI, a global database of species interactions, three years apart. | v0.6 2023-08-25, v0.11 2026-09-10 (3 years) | Supported |  |
| 23 | plain terms | We trained models on the older snapshot and asked how well they picked out interactions that appeared in the newer one. | plan.md design | Supported |  |
| 24 | plain terms | A simple "popularity" guess, based on how many interactions and studies a species already had, did well. | effort AUROC 0.951 random, 0.880 temporal | Supported |  |
| 25 | plain terms | A model that also uses what related species do did clearly better, and its advantage was bigger on the records first seen in the newer snapshot than on a random test drawn from the old one. | A_temporal 0.068 > A_random 0.040 | Supported | was 'genuinely new records' (contradicted by the turnover caveat); now 'records first seen in the newer snapshot' |
| 26 | plain terms | That held for interactions contributed by newly added studies and for species that had been recorded only once before. | temporal_subsets new_dataset 0.940 vs 0.870; cold_start 0.882 vs 0.718 | Supported |  |
| 27 | plain terms | So in this database, taxonomy-aware prediction is not just repeating "who gets studied". | taxgb beats effort on all holdouts and subsets | Supported |  |
| 28 | plain terms | The test has a caveat: the database also renames species and changes its sources between versions, so some "new" records may be old ones under new names. | turnover.json 26-42% of v0.6 pairs absent from v0.11 | Supported | 'are old ones' -> 'may be old ones' (not measured) |
