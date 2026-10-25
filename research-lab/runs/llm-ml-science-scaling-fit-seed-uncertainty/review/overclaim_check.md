# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Training-seed noise in scaling-law forecasts: one seed per size moves the 2.8B forecast by 0.12 nats, mostly because of two unstable runs, and averaging three seeds did not clearly help | primary W1 0.123; posthoc W1 excl. two runs 0.051; shrinkage 0.16 (-0.10 to 0.81) | Supported | was 'three seeds barely help' (H2 Inconclusive; interval reaches 0.81) |
| 2 | standfirst | PolyPythias: ten training seeds at each of five sizes, 14M to 410M, eight checkpoints each, 400 checkpoints in all. | losses.csv 400 checkpoints | Supported |  |
| 3 | standfirst | Each was evaluated in fp32 on 5.0M tokens of Pile validation. | eval_corpus.json 5.0M tokens; fp32 | Supported |  |
| 4 | standfirst | The Chinchilla law was fitted to 2,000 random single-seed ladders and to 2-, 3- and 5-seed averaged ladders, each extrapolated to Pythia-2.8B. | ladders_single.csv 2,000; W keys 1,2,3,5 | Supported |  |
| 5 | standfirst | The plan was committed before any model was evaluated. | git: plan before evaluation | Supported |  |
| 6 | standfirst | The evaluation precision changed (D1) before any fit. | deviations.md D1 timestamp vs first fit | Supported |  |
| 7 | verdict | **Verdict: H1 Inconclusive; H2 Inconclusive.** | primary H1, H2 Inconclusive | Supported |  |
| 8 | verdict | **H1 (single-seed ladders are too noisy: the 5th–95th percentile range W₁ of the 2.8B forecast exceeds 0.05 nats): Inconclusive.** | plan.md H1 | Supported |  |
| 9 | verdict | W₁ = **0.123 nats**. | primary W.1 0.1234 | Supported |  |
| 10 | verdict | The seed bootstrap interval is 0.038–0.160, so its lower end is below the bar. | W1_ci 0.038-0.160 | Supported |  |
| 11 | verdict | The distribution is bimodal. 1,578 of the 2,000 ladders avoid two 410M runs whose loss jumps late in training, and they have W₁ = 0.051 (post hoc). | posthoc W1_excluding_410m_seeds_3_4: 1,578 ladders, W1 0.0514 (labelled post hoc) | Supported |  |
| 12 | verdict | Those jumps are properties of the released checkpoints, not of the evaluation. 410M seed 4 sits at 2.41–2.43 nats at steps 141k–143k against 1.98 for seed 0, and a batch-size-1 re-evaluation reproduces it exactly (post hoc). | spike_check.csv; batch-size-1 re-evaluation (post hoc) | Supported |  |
| 13 | verdict | **H2 (averaging three seeds per size at least halves the width): Inconclusive.** | plan.md H2 | Supported |  |
| 14 | verdict | The shrinkage is **0.16**, with an interval from −0.10 to 0.81: W₃ = 0.103 against W₁ = 0.123. | shrinkage 0.1628 (-0.0978 to 0.815); W3 0.1033 | Supported |  |
| 15 | verdict | Five seeds give 0.088. | W.5 0.0875 | Supported |  |
| 16 | verdict | Averaging dilutes a bad run rather than removing it, so the heavy tail survives. | W3 0.103 vs W1 0.123 with the two-run tail (posthoc) | Supported |  |
| 17 | verdict | Independent Gaussian noise would predict a shrinkage of 0.42. | 1 - 1/sqrt(3) = 0.42 | Supported |  |
| 18 | verdict | **Every route overshoots the real 2.8B loss.** | accuracy_2p8b median errors > 0 for all n | Supported |  |
| 19 | verdict | 98% of single-seed forecasts lie above the actual 1.704 nats; the median error is +0.068. | accuracy_2p8b n1 median_error 0.0677; overshoot share 98% (ladders_single) | Supported |  |
| 20 | verdict | Averaging seeds does not fix this (+0.066 with three). | accuracy_2p8b n3 median_error 0.0657 | Supported |  |
| 21 | verdict | Fitting only checkpoints up to step 64k narrows the spread (W₁ 0.086) but overshoots by 0.13 (post hoc). | posthoc cut64k_n1 W 0.086, median_error 0.130 (post hoc) | Supported |  |
| 22 | verdict | The bias is shared across seeds, so it reflects the fitting form and range rather than seed choice. | averaging leaves the bias (+0.066); cut64k overshoots 100% | Supported |  |
| 23 | verdict | **Fitting choices interact with seeds.** In a seed × procedure decomposition of the forecast, the seed accounts for 69% of the variance, the procedure 2% and their interaction 29%. | procedure_vs_seed shares 0.691 / 0.021 / 0.289 | Supported |  |
| 24 | verdict | A 16-start grid instead of 64 widens the spread from 0.118 to 0.185. | width_by_procedure base 0.118, grid16 0.185 | Supported |  |
| 25 | plain terms | Before training a large AI language model, labs train a ladder of small ones and fit a "scaling law" to predict how good the big one will be. | background | Supported |  |
| 26 | plain terms | Each small model starts from a random seed, and different seeds give slightly different models. | background | Supported |  |
| 27 | plain terms | We asked how much that luck moves the prediction. | question | Supported |  |
| 28 | plain terms | Using a public set of models trained ten times each with different seeds, we fitted thousands of ladders, each using one seed per size. | PolyPythias (ledger Q1); 2,000 ladders | Supported |  |
| 29 | plain terms | Which seeds you happen to get moves the prediction for a model 7 times larger by about 0.12 in the loss units used. | W1 0.123; 2.8B / 410M = 6.8x | Supported |  |
| 30 | plain terms | That is more than the real gap between the 1.4-billion and 2.8-billion-parameter models (0.09). | ledger Q6: 1.794 - 1.704 = 0.090 | Supported |  |
| 31 | plain terms | Most of that comes from just two training runs that went wrong late in training. | posthoc W1 0.051 without the two runs vs 0.123 | Supported |  |
| 32 | plain terms | Averaging three seeds per size helped little here, though that estimate is very uncertain. | shrinkage 0.16 (-0.10 to 0.81) | Supported | was 'a common suggestion, helped little' (unsourced; uncertainty not stated) |
| 33 | plain terms | Every approach also predicted the big model would be worse than it actually was. | median errors +0.066 to +0.071 for every n; cut64k +0.13 | Supported |  |
| 34 | plain terms | The practical lesson is to look at the training curves of the small models and drop or rerun unstable ones, rather than trusting averaging. | posthoc W1 0.051 excluding the unstable runs | Supported |  |
| 35 | plain terms | Even then, the formula itself, fitted to this narrow range, was biased. | accuracy_2p8b overshoot for all routes | Supported |  |
