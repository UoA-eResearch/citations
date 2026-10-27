# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Which retrospective split predicts error on future bioactivity data? Random and scaffold splits understate it by about a third of a log unit; provenance and time splits are unbiased on average but miss by 0.15–0.22 per target, and no split recovers the model ranking | primary.json bias_rf (random -0.365, scaffold -0.274; abs 0.155-0.216 for provenance/time); H3 tau 0.35-0.41 | Supported |  |
| 2 | standfirst | 250 ChEMBL protein targets. | selection.json targets_used 250 | Supported |  |
| 3 | standfirst | Models were trained on ChEMBL 33 (2023) and tested on compounds first measured in documents from 2023 onward that appear only in ChEMBL 37 (2026). | plan.md section 2; selection.json | Supported |  |
| 4 | standfirst | Seven retrospective splitters and five model families. | plan.md sections 4-5; run.py | Supported |  |
| 5 | standfirst | The plan and all analysis code were committed before any ChEMBL table was read. | git log: plan ea58895 17:41, code f824ac7/eeb28e9 before data; targets written 03:49, training 03:51, commit before first fit | Supported | wording fixed |
| 6 | standfirst | The target list was written before training began and committed before any fit had finished. | selection.json/targets.csv mtime 03:49; run.log start 03:51; commit 05:0x with data/fits empty | Supported |  |
| 7 | verdict | **Verdict: H1 Supported; H2 Refuted; H3 Refuted.** | primary.json H1/H2/H3 verdicts | Supported |  |
| 8 | verdict | **H1 (random and scaffold splits understate prospective error by at least 0.25 log units): Supported.** | primary.json H1 by_splitter both Supported | Supported |  |
| 9 | verdict | The primary model is a random forest on ECFP4. | plan.md section 0 | Supported |  |
| 10 | verdict | Its median signed bias (retrospective RMSE − prospective RMSE) over 250 targets is −0.37 (95% CI −0.42 to −0.33) for random splits and −0.27 (−0.32 to −0.22) for scaffold splits. | primary.json bias_rf random -0.3653 [-0.4169,-0.3304]; scaffold -0.2742 [-0.3249,-0.2243] | Supported |  |
| 11 | verdict | The median prospective RMSE is 1.07 pChEMBL units. | primary.json median_prospective_rmse_rf 1.0674 | Supported |  |
| 12 | verdict | A random split reports 0.68, and a scaffold split 0.78. | bias_long.csv median retro_rmse rf random 0.676, scaffold 0.776 | Supported |  |
| 13 | verdict | **H2 (document- and author-disjoint splits are nearly unbiased: median absolute bias ≤ 0.12): Refuted.** | primary.json H2 abs_ci lower 0.138 / 0.182 > 0.12 | Supported |  |
| 14 | verdict | On average they are close to unbiased: median signed bias −0.04 (document) and +0.03 (author). | primary.json bias_rf document -0.038, author +0.031 | Supported |  |
| 15 | verdict | Per target they miss by more than the bar: the median absolute bias is 0.17 (0.14–0.19) for document splits and 0.22 (0.18–0.23) for author splits. | primary.json median_abs_bias 0.167 [0.138,0.19], 0.216 [0.182,0.234] | Supported |  |
| 16 | verdict | Cluster, assay and within-release time splits behave the same: signed bias −0.05 to +0.01, absolute bias 0.16–0.19. | primary.json bias_rf cluster/assay/time signed -0.048..+0.009, abs 0.155-0.194 | Supported |  |
| 17 | verdict | **Not just noise (exploratory).** Sampling noise in each target's prospective RMSE would alone give a median absolute bias of about 0.05, so most of the per-target miss is real. | noise_check.json expected 0.045 vs observed 0.156-0.216 | Exploratory-labelled |  |
| 18 | verdict | **H3 (the split changes which model you pick: Kendall τ ≤ 0.6 for scaffold and ≥ 0.8 for document splits): Refuted.** | primary.json H3 verdict Refuted (document tau upper 0.42 < 0.8) | Supported |  |
| 19 | verdict | No splitter ranks the five model families the way later data do. | primary.json H3 mean_tau 0.347-0.410 | Supported |  |
| 20 | verdict | The mean τ is 0.35–0.41 under every splitter (scaffold 0.39, document 0.37). | primary.json H3 mean_tau scaffold 0.387, document 0.373 | Supported |  |
| 21 | verdict | The paired difference is −0.02 (−0.06 to +0.02). | primary.json H3 document_minus_scaffold -0.0178 [-0.0575,0.0235] | Supported |  |
| 22 | verdict | **The pattern holds for every model family and prospective definition.** | primary.json median_bias_all (primary and alldelta, all models) | Supported |  |
| 23 | verdict | It holds for random forest, LightGBM, Tanimoto SVR, kNN and MLP, and for all new activities from any year. | primary.json median_bias_all primary and alldelta (all models) random -0.31..-0.56, scaffold -0.22..-0.43 | Supported |  |
| 24 | verdict | The MLP is the most overconfident under random splits (−0.56). | primary.json median_bias_all primary mlp random -0.56 | Supported |  |
| 25 | verdict | On the lenient set (compounds already in ChEMBL 33 but new to the target), every splitter understates the error. | primary.json median_bias_all lenient (all models) all negative | Supported |  |
| 26 | plain terms | Chemists train machine-learning models on past experiments to predict how strongly new molecules will bind a drug target. | background (QSAR practice) | Supported |  |
| 27 | plain terms | Before trusting a model, they test it by hiding part of the past data and checking predictions against it. | background | Supported |  |
| 28 | plain terms | How that part is chosen matters. | primary.json bias_rf range across splitters | Supported |  |
| 29 | plain terms | Hide molecules at random, and the test molecules usually have close relatives in the training data. | fits/*.json nn_sim_median: random 0.80 vs prospective 0.43 | Supported |  |
| 30 | plain terms | That makes the test too easy. | primary.json random bias -0.37 | Supported |  |
| 31 | plain terms | We checked seven ways of hiding data against what actually happened next. | plan.md section 4 | Supported |  |
| 32 | plain terms | We trained on the 2023 edition of the public ChEMBL database and tested on molecules first published from 2023 on, which appear only in the 2026 edition. | plan.md sections 1-2 | Supported |  |
| 33 | plain terms | Random and "scaffold" tests made models look much better than they turned out to be. | primary.json random/scaffold bias | Supported |  |
| 34 | plain terms | Their typical error on the future molecules was about 1.1 units on a log scale, against 0.7–0.8 in those tests. | median pros RMSE 1.07; retro random 0.68, scaffold 0.78 | Supported |  |
| 35 | plain terms | Hiding whole papers, author groups, assays or the latest compounds gave about the right error on average, but could still be well off for any one target. | primary.json signed ~0, abs 0.16-0.22 | Supported |  |
| 36 | plain terms | And no test reliably picked the model that did best on the future data. | primary.json H3 tau ~0.4 | Supported |  |
