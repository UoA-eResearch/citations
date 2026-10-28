# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Nothing we tried forecasts where an antibiotic-resistance gene will appear next better than knowing where people are sequencing | primary.json H1 Refuted (0.00 vs 0.08); variant_any.json: both models 0.00 vs null 0.10 under the first-appearance rule | Supported |  |
| 2 | standfirst | NCBI Pathogen Detection, 106 organism groups: 1.62 million isolates with uniform AMRFinderPlus calls, 264 species, 4,417 gene symbols. | build.json: 106 files, 1,621,194 isolates kept, 264 species, 4,417 genes | Supported |  |
| 3 | standfirst | Candidate (gene, species) pairs not yet established at the end of 2022 were ranked for appearance in 2023–2025 by a gradient-boosted model trained on the same task one period earlier (cutoff 2019), and by a sampling-effort null that knows only each gene's frequency and how many isolates of each species were sequenced in the forecast window. | plan.md section 0; task_test.json candidates 472,779 | Supported |  |
| 4 | standfirst | The plan was committed before any Pathogen Detection data were downloaded. | git: plan.md commit 16:41 precedes the first download | Supported |  |
| 5 | verdict | **Verdict: H1 Refuted; H2 Refuted.** | primary.json H1 Refuted, H2 Refuted | Supported |  |
| 6 | verdict | **H1 (the model's precision@100 is at least twice the null's): Refuted.** | primary.json H1 Refuted | Supported |  |
| 7 | verdict | The model's precision@100 is **0.00**; the null's is **0.08**. | primary.json precision_at_100 model 0.0, null 0.08 | Supported |  |
| 8 | verdict | Not one of the model's 100 most confident predictions emerged. | primary.json precision_at_100 model 0.0 | Supported |  |
| 9 | verdict | The ratio's 95% interval over gene resamples is 0.00–1.27. | primary.json ratio_ci 0.0-1.273 (210 of 2,000 draws undefined) | Supported |  |
| 10 | verdict | The null is a strong baseline, not a weak one: 0.08 against a base rate of 0.0018 is a 44-fold lift. | primary.json null precision_at_100 0.08; task_test.json base_rate 0.00179; 0.08/0.00179 = 45 | Supported |  |
| 11 | verdict | Where a gene newly appears is mostly where sequencing happens. | primary.json null 0.08 at a 0.0018 base rate; no model beats it at the top; posthoc.json top-100 median 24 horizon isolates vs 414 for emergent pairs | Supported |  |
| 12 | verdict | **H2 (ESM-2 protein embeddings add signal beyond co-occurrence and taxonomy): Refuted.** | primary.json H2 Refuted | Supported |  |
| 13 | verdict | Average precision is **0.076 with the embedding and 0.081 without it**; the paired difference is −0.005 (−0.013 to +0.001). | primary.json auprc full 0.076283, no_embedding 0.08092, difference -0.004637 (-0.0128 to 0.0009) | Supported |  |
| 14 | verdict | The embedding does not merely fail to help. | secondary.json ablations no_embedding precision_at_100 0.18 vs full 0.0 | Supported |  |
| 15 | verdict | **It is what breaks the model.** Removing it lifts precision@100 from 0.00 to 0.18, above the null's 0.08. | secondary.json ablations no_embedding 0.18; posthoc.json no_embedding_vs_null ratio 2.25 (2.0-23.0) | Supported |  |
| 16 | verdict | **But that repair does not survive the honest outcome definition.** Under the preregistered first-appearance variant, where a pair counts as emerging the first time any isolate carries it, **both models score 0.00 against the null's 0.10**. | variant_any.json no_embedding precision_at_100 0.0, null 0.1 | Supported |  |
| 17 | verdict | The no-embedding model's apparent win exists only under the primary rule. | variant_any.json vs secondary.json | Supported |  |
| 18 | verdict | **Why the primary rule flatters a model.** It requires two isolates from different BioProjects, to suppress outbreak clones. | plan.md section 0 (two-BioProject rule) | Supported |  |
| 19 | verdict | The side effect is that **705 of the 847 labelled emergences (83%) are pairs already observed at least once before 2023** (median first sighting 2019). | recomputed from pairs.parquet: 705 of 847 test emergences have first_year_any <= 2022 (median 2019); train 979 of 1,271 | Supported |  |
| 20 | verdict | They are confirmations, not first appearances. | same recomputation | Supported |  |
| 21 | plain terms | Genes that make bacteria resistant to antibiotics spread between species. | ledger A2 (Ellabaan et al. 2021) | Supported |  |
| 22 | plain terms | If we could forecast which gene will turn up in which species next, surveillance could watch the right places. | framing of the lead | Supported |  |
| 23 | plain terms | We tested whether that is possible using 1.6 million sequenced isolates that one pipeline has annotated the same way, scoring honestly: train only on data collected before a cut-off, then check against what actually appeared afterwards. | build.json isolates_kept 1,621,194; uniform AMRFinderPlus calls (ledger A1) | Supported | was 'the world's largest uniform collection' (unverified superlative) |
| 24 | plain terms | It is not, with these ingredients. | primary.json H1 Refuted; variant_any.json both models 0.00 | Supported |  |
| 25 | plain terms | A machine-learning model given gene frequencies, which species already carry related genes, bacterial family trees and a protein language model's view of each gene's product did no better than a simple calculation that knows only how common a gene is and how many samples of each species were sequenced. | primary.json precision_at_100 0.0 vs null 0.08; feature list in analyse.py | Supported |  |
| 26 | plain terms | On the strictest reading of "appeared for the first time", the model got none of its top 100 predictions right, while the simple calculation got one in ten. | variant_any.json full and no_embedding 0.00, null 0.10 | Supported |  |
| 27 | plain terms | One ingredient actively hurt. | secondary.json ablations no_embedding 0.18 vs full 0.0 | Supported |  |
| 28 | plain terms | The protein language model rates most resistance genes as near-identical to each other, because many are variants of the same gene family. | task_test.parquet: median nearest-neighbour emb_cos_max 0.971 across candidates, 0.995 among emergent | Supported |  |
| 29 | plain terms | That led the model to predict new appearances in species that are barely sequenced, where nothing can be detected. | posthoc.json/top100_annotated.csv: median 24 horizon isolates, 93 of 100 in two species | Supported |  |
| 30 | plain terms | Dropping that one feature turned the model from worse than the baseline to better than it — but only under the looser definition of "appeared". | secondary.json ablations; variant_any.json shows it does not hold under the first-appearance rule | Supported |  |
| 31 | plain terms | The honest summary is that surveillance intensity, not biology, is what these data mainly encode about where a resistance gene shows up next. | primary.json null 0.08 beats every model at the top; variant_any.json | Supported |  |
