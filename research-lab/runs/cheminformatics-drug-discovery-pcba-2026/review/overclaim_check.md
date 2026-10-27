# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | A leakage-audited virtual-screening benchmark from recent PubChem screens: memorization's advantage is a property of the split, pretrained embeddings never beat a fingerprint random forest, and method rankings barely replicate at all | primary.json H1/H2/H3; metrics.csv by split; folds_*.csv leakage shares | Supported |  |
| 2 | standfirst | PCBA-2026: 28 single-target confirmatory PubChem assays deposited from 2021 (12 from 2023 or later), 578,057 compounds, with analog-disjoint folds that remove any evaluation compound within Tanimoto 0.4 of its training set. | build_new.json targets 28, targets_2023plus 12; new.parquet 578,057 unique key14 | Supported |  |
| 3 | standfirst | Compared with LIT-PCBA as published and under the same procedure. | metrics.csv evals lit_pub and lit_cv | Supported |  |
| 4 | standfirst | Five methods: a parameter-free memorization baseline, ECFP4 + random forest, RDKit descriptors + LightGBM, and ChemBERTa and MoLFormer-XL embeddings with a linear head. | plan.md section 4; run.py METHODS | Supported |  |
| 5 | standfirst | The plan was committed before any activity outcome was downloaded. | git log: plan committed before fetch.py outcomes ran | Supported |  |
| 6 | verdict | **Verdict: H1 Inconclusive; H2 Supported; H3 Supported.** | primary.json verdicts | Supported |  |
| 7 | verdict | **The leakage LIT-PCBA was criticised for is real, and larger than in the new benchmark.** Before the audit, a training neighbour above Tanimoto 0.4 exists for **89%** of LIT-PCBA evaluation compounds and **62%** of PCBA-2026's. | folds_lit.csv nn>0.4 median 0.887; folds_new.csv 0.62 | Supported |  |
| 8 | verdict | Removing them leaves 12% of LIT's compounds scorable, against 40% of PCBA-2026's. | folds_lit.csv eval_kept_04/compounds median 0.117; folds_new.csv 0.395 | Supported |  |
| 9 | verdict | **H1 (memorization's advantage at least halves on the leakage-controlled benchmark): Inconclusive.** | primary.json H1 Q_ci [-1.474,3.383] spans the bar | Supported |  |
| 10 | verdict | Q = A_new / A_lit = 0.43, which meets the preregistered bar as a point estimate, but the interval is useless (−1.47 to 3.38): it is a ratio of two medians, one over only 15 LIT targets. | primary.json H1 Q 0.431, A_new 1.358, A_lit 3.15 | Supported |  |
| 11 | verdict | **The within-benchmark contrast is the clean evidence, and it is unambiguous.** Holding the data fixed and changing only the split, the memorization baseline's median EF1% falls from 11.4 (random) to 4.8 (analog- disjoint at 0.6) to **2.4** (at 0.4) on PCBA-2026, and from 27.8 to 8.3 to **3.5** on LIT-PCBA. | metrics.csv nn medians: new 11.43/4.83/2.36; lit_cv 27.83/8.34/3.46 | Exploratory-labelled | post hoc framing; the contrast itself is preregistered as the split sensitivity |
| 12 | verdict | So the memorization result is a property of how the benchmark is split, not of the chemistry, and LIT-PCBA's larger collapse matches its larger analog redundancy. | same data, only the split differs; folds_*.csv leakage shares | Exploratory-labelled | interpretation |
| 13 | verdict | **H2 (pretrained molecular embeddings do not beat ECFP4 + random forest): Supported.** | primary.json H2 S2 1.0 >= 0.70 | Supported |  |
| 14 | verdict | On **0 of 56** target-embedding pairs does an embedding's paired bootstrap interval exclude zero in its favour. | pairs_h2.csv emb_beats_rf 0 of 56 | Supported |  |
| 15 | verdict | The random forest's does on 9. | pairs_h2.csv rf_beats_emb 9 | Supported |  |
| 16 | verdict | Median ΔEF1% is −1.00 for ChemBERTa and −0.56 for MoLFormer-XL. | pairs_h2.csv median delta cb -0.997, mf -0.560 | Supported |  |
| 17 | verdict | On the primary split the medians are RF 5.65, LightGBM 5.32, ChemBERTa 4.36, MoLFormer 4.29, memorization 2.36. | metrics.csv new audit04 medians | Supported |  |
| 18 | verdict | **H3 (method rankings do not transfer from LIT-PCBA): Supported, but for a duller reason than it sounds.** | primary.json H3 ci [0.085,0.295] upper < 0.4 | Supported |  |
| 19 | verdict | Mean Kendall τ between a PCBA-2026 target's ranking and the LIT consensus is 0.20 (0.085–0.295), under the 0.4 bar. | primary.json H3 mean_tau 0.196 ci [0.085,0.295] | Supported |  |
| 20 | verdict | **But the split-half noise ceiling is 0.29.** Rankings of five closely matched methods barely replicate between two halves of the *same* target's data, so most of the disagreement is measurement noise rather than a real difference between benchmarks. | primary.json noise_ceiling mean_tau_split_half 0.287, 26 targets | Supported | preregistered secondary |
| 21 | plain terms | To judge a program that picks promising drug molecules, you hide some known answers and see how many it recovers. | background | Supported |  |
| 22 | plain terms | The catch is which molecules you hide. | metrics.csv by split | Supported |  |
| 23 | plain terms | Chemists make families of near-identical molecules, so if a close relative of a hidden molecule stays in the training set, a program can win by looking up the relative rather than understanding anything. | folds_*.csv near-neighbour shares; ledger L1 | Supported |  |
| 24 | plain terms | A 2025 audit showed the field's standard benchmark, LIT-PCBA, is full of such relatives. | ledger L1 (arXiv 2507.21404) | Supported |  |
| 25 | plain terms | We measured it: for about nine in ten of its test molecules, a near-twin sits in the training data. | folds_lit.csv nn_sim_sample_share_above_0_4 median 0.887 | Supported |  |
| 26 | plain terms | We then built a fresh benchmark from recent public screening experiments and removed the near-twins from scoring. | plan.md section 1; build_new.json | Supported |  |
| 27 | plain terms | Doing that, the pure look-up method's score collapses — from 28 to 3.5 on the old benchmark, and from 11 to 2.4 on ours. | metrics.csv nn: lit_cv 27.83->3.46, new 11.43->2.36 | Supported |  |
| 28 | plain terms | In other words, much of what the benchmark was measuring was look-up. | same | Exploratory-labelled | interpretation |
| 29 | plain terms | Two further results. | H2 and H3 | Supported |  |
| 30 | plain terms | Large pretrained "foundation" models for chemistry did not beat a plain 1990s-style molecular fingerprint with a random forest on a single target. | pairs_h2.csv 0 of 56 | Supported |  |
| 31 | plain terms | And which method looks best varies so much from target to target that the ranking is barely reproducible even when you split one target's own data in half. | primary.json H3 mean_tau 0.196; noise_ceiling 0.287 | Supported |  |
