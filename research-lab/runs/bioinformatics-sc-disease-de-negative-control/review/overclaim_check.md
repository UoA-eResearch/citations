# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | At matched group sizes, three quarters of single-cell disease signatures in a cell atlas cannot be told apart from comparing healthy donors with each other | primary.json H1 by_n_de_power_selected S1 0.7384 [0.5652,0.8393] | Supported | title qualified to matched sizes |
| 2 | standfirst | 799 disease × tissue × cell-type contrasts from 25 datasets in the CZ CELLxGENE Census (42 diseases, 161 cell types). | primary.json H1 contrasts_evaluable 799, datasets 25, diseases 42; contrasts.csv cell types 161 | Supported |  |
| 3 | standfirst | Each was compared with 500 matched healthy-donor-only contrasts drawn from the same dataset, tissue and cell type, through an identical limma-voom pipeline on donor pseudobulk. | plan.md section 0; draws.py B_NULL 500 | Supported |  |
| 4 | standfirst | The plan was committed before any expression value was read. | git log: plan committed before pb_h5ad ran | Supported |  |
| 5 | verdict | **Verdict: H1 Supported; H2 Inconclusive.** | primary.json H1 verdict Supported (both statistics); H2 verdict Inconclusive | Supported |  |
| 6 | verdict | **H1 (more than half of contrasts are indistinguishable from their matched healthy-vs-healthy null): Supported.** | primary.json H1 ci95 lower 0.565 > 0.5 | Supported |  |
| 7 | verdict | On the number of differentially expressed genes, the statistic the power check selects (below), **74%** of the 799 contrasts do not exceed their own null at BH q < 0.05 (95% CI 57–84%, cluster bootstrap over the 25 datasets). | primary.json by_n_de_power_selected S1 0.7384 ci [0.5652,0.8393] | Supported |  |
| 8 | verdict | Real and null are compared at the same group sizes, a median of 13 donors against 13. | draws.py m per group; contrasts.csv m median 13 | Supported | added after tracing (G3) |
| 9 | verdict | On π1, the preregistered primary statistic, 82% (71–89%). | primary.json H1 S1 0.8185 ci [0.7149,0.8881] | Supported |  |
| 10 | verdict | **But π1 detects a real twofold change in 5% of genes only 8% of the time**, so that figure is nearly uninformative; the DE-gene count detects it 87% of the time (D2, `results/tables/power_check.json`). | power_check.json power_by_statistic pi1 0.08, n_de 0.87 | Supported |  |
| 11 | verdict | Weighting every disease equally gives the same answer: 74%. | primary.json by_n_de_power_selected S1_equal_weight_per_disease 0.7397 | Supported |  |
| 12 | verdict | **The DE-gene count a practitioner reports barely predicts whether the contrast beats its null.** | contrasts.csv bands: 0%, 0%, 12%, 42%, 64% | Supported | was 'not evidence of disease signal' |
| 13 | verdict | At full size, using every donor (median 100 per contrast), a practitioner would report at least one DE gene in 69% of these contrasts, with a median of 52. | primary.json share_full_with_any_de 0.6909, median_n_de_full 52; contrasts.csv n_disease+n_normal median 100 | Supported |  |
| 14 | verdict | Among contrasts reporting 11–100 DE genes, only **12%** exceed their own matched null. | contrasts.csv band 11-100: 85 contrasts, 0.118 exceed | Supported |  |
| 15 | verdict | Among those reporting 101–1,000, only 42%; above 1,000, 64%. | contrasts.csv bands 101-1000 0.42, >1000 0.64 | Supported |  |
| 16 | verdict | **The two are not the same comparison.** The null test is run at matched group sizes, a median of 13 donors against 13, because a null needs two disjoint healthy groups and no dataset has enough healthy donors to mirror a full-size comparison. | draws.py m = min(n_disease, n_normal//2); contrasts.csv medians | Supported | added after tracing (G3) |
| 17 | verdict | So part of this gap is donor count, not signal. | contrasts.csv full-size 100 donors vs matched 26 | Supported | hedge added |
| 18 | verdict | Comparing healthy donors with healthy donors is not quiet: in 8.9% of contrasts the null's 95th percentile is above 100 DE genes. | contrasts.csv n_de_null_q95 > 100 in 8.9% | Supported |  |
| 19 | verdict | **A positive control confirms the power problem on real data.** Comparing male with female healthy donors in the largest dataset (115 per group, brain oligodendrocytes) gives 219 DE genes and is detected against permuted nulls at p = 0.005. π1 misses it (p = 0.25). | plausibility.md; control_sex stats.csv n_de p 0.005, pi1 p 0.254 | Supported |  |
| 20 | verdict | **It varies by disease.** Of the eight most common diseases, 0% of schizophrenia (37 contrasts) and 0% of tauopathy (35) contrasts exceed their null, against 62% of interstitial lung disease (32) and 63% of pulmonary fibrosis (27). | contrasts.csv by disease: schizophrenia 0.00, tauopathy 0.00, ILD 0.62, pulmonary fibrosis 0.63 | Supported |  |
| 21 | verdict | COVID-19 (86) is 45%. | contrasts.csv disease COVID-19 n 86 exceed 0.45 | Supported |  |
| 22 | verdict | **Disease-gene enrichment is weak.** Comparing the Open Targets scores of each contrast's 100 strongest genes with the same statistic on its nulls, 9.9% of 575 contrasts beat their null at raw p < 0.05, against 5% expected by chance. | contrasts.csv ot_p share<0.05 0.099 of 575; primary.json ot_enrichment share_enriched_q05 0.0 | Supported |  |
| 23 | verdict | None survives BH correction. | primary.json H1 ot_enrichment share_enriched_q05 0.0 | Supported |  |
| 24 | verdict | **H2 (cross-study replication follows donor count rather than cell count): Inconclusive.** | primary.json H2 verdict Inconclusive (d_minus_c_ci spans 0) | Supported |  |
| 25 | verdict | Across 335 cross-collection pairs (94 disease × tissue × cell-type groups, 9 diseases), the median Spearman correlation between two studies' t statistics is 0.19. | primary.json H2 pairs 335, groups 94, diseases 9, median_rho 0.1922 | Supported |  |
| 26 | verdict | More donors does predict better replication: β = 0.061 per doubling (95% CI 0.021–0.095). | primary.json H2 bootstrap group beta_d_ci [0.0211,0.0952] | Supported |  |
| 27 | verdict | But it is not detectably better than cell count: the paired difference is 0.030 (−0.032 to 0.084), so the hypothesis as preregistered is Inconclusive. | primary.json H2 d_minus_c_ci [-0.0321,0.0844] | Supported |  |
| 28 | verdict | Those pairs span only 9 diseases. | primary.json H2 diseases 9 | Supported |  |
| 29 | verdict | Bootstrapping over diseases instead widens every interval to include zero. | primary.json H2 bootstrap disease: every CI spans 0 | Supported |  |
| 30 | verdict | **The nulls share the real contrasts' confounding.** Where both sides of a pair have null draws, the null signatures correlate across studies at 0.03 against 0.30 for the real ones, so the matched null is not simply reproducing a batch effect common to all data. | primary.json H2 null_baseline median_null_rho 0.0299 vs real 0.2961, 33 pairs | Supported |  |
| 31 | plain terms | Single-cell studies compare sick and healthy people one cell type at a time, and report the genes that differ. | background | Supported |  |
| 32 | plain terms | The trouble is that people differ from each other anyway. | contrasts.csv null distributions | Supported |  |
| 33 | plain terms | With a dozen donors per group, some genes will always look different. | contrasts.csv n_de_null_q95 > 100 in 8.9% | Supported |  |
| 34 | plain terms | We took a large public atlas of such data and, for each disease comparison, built 500 fake comparisons from healthy donors only: same study, same tissue, same cell type, same numbers, matched for sex and age. | plan.md sections 1-3 | Supported |  |
| 35 | plain terms | Then we ran the identical analysis on all of them and asked whether the real comparison stood out from its own fakes. | de.R: one pipeline for real, null and full | Supported |  |
| 36 | plain terms | Three quarters did not. | primary.json by_n_de_power_selected S1 0.7384 | Supported |  |
| 37 | plain terms | In most of these comparisons, the disease result is no more striking than what you get by splitting healthy people into two arbitrary groups of the same size and comparing them. | primary.json S1 0.74 at matched sizes | Supported | qualified to same-size groups |
| 38 | plain terms | A caveat we cannot remove: the fake comparisons can only be as large as the healthy donors allow, so the test runs at about a dozen donors a side, while a researcher using every donor in the study has about a hundred. | draws.py m rule; contrasts.csv medians 13 vs 100 | Supported | added after tracing (G3) |
| 39 | plain terms | Part of what we call "indistinguishable" is therefore the smaller comparison, not only the weaker signal. | same | Supported | hedge added |
| 40 | plain terms | That is not a claim that the diseases have no effect on these cells. | power_check.json; limits | Supported |  |
| 41 | plain terms | It means these particular datasets, at this size, cannot show it. | power_check.json power 0.87 for a 2x change in 5% of genes | Supported |  |
| 42 | plain terms | Lung fibrosis comparisons mostly do stand out; schizophrenia and tauopathy comparisons, in these data, never did. | contrasts.csv pulmonary fibrosis 0.63, ILD 0.62, schizophrenia 0.00, tauopathy 0.00 | Supported |  |
