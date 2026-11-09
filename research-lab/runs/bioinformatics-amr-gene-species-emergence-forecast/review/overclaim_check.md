# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | For first appearances of antibiotic-resistance genes in new species, sampling effort beats a trained model at the top of the list; for confirmations, the model ranks about four times better overall | d3.json (D3c) first_appearance null p@100 0.15 vs model ~0; primary auprc_ratio_by_seed 3.65-4.36 | Supported |  |
| 2 | standfirst | NCBI Pathogen Detection, 106 organism groups: 1.62 million isolates with uniform AMRFinderPlus calls, 264 species, 4,417 gene symbols. | build.json: 106 files, 1,621,194 kept, 264 species, 4,417 genes | Supported |  |
| 3 | standfirst | Candidate (gene, species) pairs not yet established by the end of 2022 were ranked for appearance in 2023–2025. | plan.md section 0; task_test.json candidates 472,779 | Supported |  |
| 4 | standfirst | Two rankings were compared: a gradient-boosted model trained on the same task one period earlier, and a sampling-effort null that knows only each gene's frequency and how many isolates of each species were sequenced in the forecast window. | plan.md section 0; analyse.py; d3_fixes.log_null | Supported |  |
| 5 | standfirst | Isolates are dated by collection, so this is a retrospective test, not a real-time forecast. | hindsight.json: 45.3% of isolates collected by 2022 deposited after 2022 | Supported |  |
| 6 | standfirst | The plan was committed before any data were downloaded. | git: plan.md commit precedes the first download (review verified) | Supported |  |
| 7 | standfirst | This version follows an independent review and a confirmation pass that both returned "fix first" (deviations D3 and D3b), and a second confirmation pass (publish with edits; D3c). | D3, D3b, D3c; review/review.md | Supported |  |
| 8 | verdict | **Verdict: H1 Refuted by the preregistered rule; H2 Inconclusive.** | d3.json H1_d3 verdict Refuted (ratio 0, CI 0-0.459); primary.json H2 Inconclusive | Supported |  |
| 9 | verdict | **For genuine first appearances the effort null wins at the top of the list.** Under the preregistered variant, in which one isolate is enough to count as a first appearance: | d3.json first_appearance null_log p@100 0.1517; full_p@100_by_seed ~0 at 9/10 | Supported | C4: now leads |
| 10 | verdict | the null puts about **15 true first appearances in its top 100** (precision 0.150); | d3.json (D3c) first_appearance null_log p@100 0.15 | Supported |  |
| 11 | verdict | the model puts none at nine of ten seeds; | d3.json first_appearance full_p@100_by_seed [0.002, 0, 0.005, 0, 0, 0, 0, 0, 0.13, 0] | Supported | 'none' = <=0.005 expected at 9 seeds |
| 12 | verdict | over the whole list, the model's average precision is 1.4–2.4 times the null's. | d3.json first_appearance auprc_ratio_by_seed 1.43-2.37 | Supported |  |
| 13 | verdict | **H1 (the model's precision@100 is at least twice the null's): Refuted.** | d3.json H1_d3 Refuted | Supported |  |
| 14 | verdict | At the preregistered seed the model scores **0.00** against the null's **0.070** (ratio 0, 95% interval 0 to 0.50). | d3.json (D3c) H1_d3 ratio 0, ci [0, 0.5] | Supported |  |
| 15 | verdict | That fit is the worst of ten. | d3.json primary full_p@100_by_seed: preregistered 0.00 is the minimum | Supported |  |
| 16 | verdict | At the other nine seeds the ratio is 1.4–2.7, and five clear the 2× bar. | d3.json (D3c) H1_d3 ratio_by_seed 1.43-2.71 (5 >= 2) | Supported |  |
| 17 | verdict | **For confirmations the model is better overall.** Under the primary two-BioProject rule, its average precision is | d3.json primary auprc_ratio_by_seed 4.08-4.88 | Supported |  |
| 18 | verdict | **3.7–4.4 times** the null's at every seed (0.075–0.090 against 0.021). | d3.json (D3c) primary auprc_ratio_by_seed 3.65-4.36; null auprc 0.0206 | Supported |  |
| 19 | verdict | **H2 (ESM-2 protein embeddings add signal): Inconclusive.** | primary.json H2 Inconclusive (D3 relabel) | Supported |  |
| 20 | verdict | The paired difference in average precision is −0.005 (−0.013 to +0.001). | primary.json auprc difference -0.004637, CI -0.0128 to +0.0009 | Supported |  |
| 21 | verdict | The first draft mislabelled this Refuted. | primary.json H2_as_first_coded Refuted | Supported |  |
| 22 | verdict | Across seeds the embedding adds a little at seven of ten. | d3.json auprc_diff_by_seed positive at 7 of 10 | Supported |  |
| 23 | verdict | **What the primary rule rewards.** It needs two isolates from different BioProjects. | plan.md section 0 (two-BioProject rule) | Supported |  |
| 24 | verdict | Of its 847 emergences, 705 (83%) already had a carrier collected before 2023, but only 316 (37%) had one deposited, and so public, by then. | hindsight.json 705 collected / 316 deposited by 2022 of 847 | Supported |  |
| 25 | verdict | The contrast between the two rules suggests that much of the model's skill is in ranking confirmations of pairs that already existed, often unpublished at the cutoff. | inference from the rule contrast, worded as a suggestion | Supported |  |
| 26 | verdict | **The scoring of the null was fixed twice.** | deviations.md D3 item 1 and D3b item 1 | Supported |  |
| 27 | verdict | Its probability saturates at 1.0 for thousands of candidates, and row order then decided the first draft's 0.08. | d3.json null_old_saturated_at_1 4,727; null_old_p@100_row_order 0.08 | Supported |  |
| 28 | verdict | The first fix (log P of two or more) saturated at 0.0 in the same place and gave 0.033. | amr_d3_v1 (first D3 run): null_log p@100 0.0333 with logsf; deviations D3b | Supported |  |
| 29 | verdict | The second fix (log P of at most one, via `logcdf`) still underflowed for about 200 of the most heavily sequenced candidates, which tied them. | D3b log; review second confirmation C1 | Supported |  |
| 30 | verdict | Computed in closed form, log P(≤1) = (n−1)·log1p(−f) + log1p((n−1)·f), the score stays finite. | d3_fixes.log_null (closed form) | Supported |  |
| 31 | verdict | The null then has 988 distinct scores in its top 1,000 and precision@100 0.070 (D3c). | d3.json (D3c) primary null_distinct_scores_top1000 988, null p@100 0.07 | Supported |  |
| 32 | plain terms | Genes that make bacteria resistant to antibiotics spread between species. | ledger A2 (Ellabaan et al. 2021) | Supported |  |
| 33 | plain terms | We asked whether it is possible to forecast which gene will turn up in which species next, using 1.6 million sequenced isolates that one pipeline has annotated the same way. | build.json isolates_kept 1,621,194; uniform AMRFinderPlus calls (ledger A1) | Supported |  |
| 34 | plain terms | Any forecast has to beat a simple baseline that knows only how common each gene is and how many samples of each species are being sequenced. | plan.md null definition | Supported |  |
| 35 | plain terms | For a gene's very first appearance in a species, it does not: the baseline puts about 15 real first appearances in its top 100 guesses, and the trained model almost never puts any. | d3.json first_appearance null p@100 0.152 (~15/100) vs model ~0 at 9/10 seeds | Supported |  |
| 36 | plain terms | Where the model does better, about four times better over its whole list, is in predicting which gene–species pairs will be confirmed by a second, separate study. | d3.json (D3c) primary auprc ratios ~3.7-4.4 | Supported |  |
| 37 | plain terms | Many confirmed pairs had already been sampled before the cutoff, often not yet published. | hindsight.json: of 847 primary emergences 705 collected but only 316 deposited by 2022 | Supported | softened at D3b |
| 38 | plain terms | Our first draft got several things wrong. | deviations D3, D3b | Supported |  |
| 39 | plain terms | It relied on the one model run, of ten, that did worst. | d3.json preregistered seed p@100 0.00, minimum of ten | Supported |  |
| 40 | plain terms | It also scored the baseline in a way that let the order of rows in a file decide its result. | d3.json null_old_p@100_row_order 0.08 vs expected 0.028 (row order decided the top 100) | Supported |  |
| 41 | plain terms | An independent review caught both. | review/review.md findings 1 and 2 | Supported |  |
