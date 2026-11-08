# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Do attribution graphs replicate across transcoder seeds? Only about 57% of a graph's top features have a functional counterpart in a retrained transcoder, but 90% of them lie in the span of its top features | primary.json H1 median 0.5667; H2 mean_subspace 0.9031 | Supported |  |
| 2 | standfirst | Four sets of per-layer transcoders were trained on Qwen3-0.6B with one fixed recipe. | train_transcoders.py; plan.md recipe | Supported |  |
| 3 | standfirst | Three differed only in their initialisation seed and one in data order. | run_sets.sh (A,B,C seeds 0-2; D data-order 1) | Supported |  |
| 4 | standfirst | Attribution graphs were built with circuit-tracer for 212 prompts in six families under every set. | coverage.json graphs 1060; prompts.jsonl 212 | Supported |  |
| 5 | standfirst | Each graph's ten most influential features were then matched across sets by layer, position, decoder direction and ablation effect. | match.py | Supported |  |
| 6 | standfirst | The plan was committed before any transcoder was trained. | git: plan before training | Supported |  |
| 7 | verdict | **Verdict: H1 Supported; H2 Supported.** | primary.json H1, H2 | Supported |  |
| 8 | verdict | **H1 (node replication across initialisation seeds is below 0.6): Supported, narrowly.** | primary.json H1 Supported; ci upper 0.5835 | Supported |  |
| 9 | verdict | Per prompt, the share of the top-10 features with a counterpart in another seed's graph has a median of | primary.json H1 | Supported |  |
| 10 | verdict | **0.567** (95% family-stratified bootstrap 0.567 to 0.584) over the 6 ordered pairs of A, B and C. | primary.json H1 median 0.5667 ci [0.5667, 0.5835] | Supported |  |
| 11 | verdict | The mean is 0.591. | primary.json H1 mean 0.591 | Supported |  |
| 12 | verdict | A counterpart must be active at the same layer and position, with decoder cosine ≥ 0.7, and its zero-ablation must move the target logit the same way by at least half as much. | match.py COS 0.7, FRAC 0.5; D2 | Supported |  |
| 13 | verdict | Of set A's top-10 features, 43% have counterparts in both other seeds, 19% in one and 38% in neither. | primary.json A_top10_replicated_in | Supported |  |
| 14 | verdict | **H2 (concepts replicate better than features): Supported.** | primary.json H2 Supported | Supported |  |
| 15 | verdict | A top feature is subspace-replicated if its decoder lies mostly (norm ≥ 0.7) in the span of the other set's 30 most influential same-layer decoders for that prompt. | match.py SUB 0.7, top30 | Supported |  |
| 16 | verdict | That holds for **90%** of top features, against 59% node replication. | primary.json H2 mean_subspace 0.9031, node 0.591 | Supported |  |
| 17 | verdict | The paired difference is **+0.31** (0.30 to 0.32). | primary.json H2 diff 0.312 [0.3025, 0.3214] | Supported |  |
| 18 | verdict | **Where replication fails.** | section | Supported |  |
| 19 | verdict | **Early layers.** Layers 0–6 hold 56% of the top features, and only 38% of those replicate as nodes (84% as subspaces). | primary.json by_layer_depth 0-6 7136 of 12720, node 0.3842, subspace 0.8367 | Supported |  |
| 20 | verdict | In layers 14–27, node replication is 85–87%. | primary.json by_layer_depth 14-20 0.8681, 21-27 0.8506 | Supported |  |
| 21 | verdict | **Initialisation, more than data order.** Set D shares A's initialisation but sees the data in a different order. | run_sets.sh D | Supported |  |
| 22 | verdict | A against D gives a median of 0.65, above the 0.57 between different initialisations. | primary.json data_order_A_D 0.65 | Supported |  |
| 23 | verdict | **A different recipe.** The public low-L0 transcoders against A: median 0.20. | primary.json public_vs_A 0.2 | Supported |  |
| 24 | verdict | **Matching is sensitive to its thresholds.** On decoder cosine alone, without the ablation condition, the median is 0.80 at a 0.6 cut, 0.68 at 0.7 and 0.58 at 0.8. | primary.json cosine_only_0.6/0.7/0.8 | Supported |  |
| 25 | verdict | The G4 audit found that activation correlation over held-out text clears 0.7 for more features (27 of 30) than decoder cosine does (20 of 30). | g4.json cosine 20, correlation 27 | Supported |  |
| 26 | verdict | So decoder-based node replication may understate functional replication. | g4.json (interpretation, hedged) | Supported |  |
| 27 | verdict | **Fidelity is moderate and reported, not a gate.** Each of our sets explains 76% of MLP-output variance (FVU 0.236). | fidelity.json fvu_mean 0.236 | Supported |  |
| 28 | verdict | With all 28 MLPs replaced, the model's top-1 prediction matches the true model on 52–54% of held-out tokens (KL 1.2–1.4 per token), near the plan's marker of poor fidelity (0.5). | fidelity.json top1 0.522-0.538, kl 1.21-1.40 | Supported |  |
| 29 | plain terms | Attribution graphs are a popular way to explain what a language model is doing on a given input. | background (R1, R4) | Supported |  |
| 30 | plain terms | A smaller, interpretable model called a transcoder stands in for parts of the network, and the graph shows which of its "features" drive the answer. | background (R1) | Supported |  |
| 31 | plain terms | Researchers read these graphs as evidence for mechanisms, but the transcoder is trained with randomness. | background | Supported |  |
| 32 | plain terms | Would a second transcoder, trained the same way with a different random seed, tell the same story? | question | Supported |  |
| 33 | plain terms | We trained four transcoders for a small open model, Qwen3-0.6B, identically except for the random seed or data order. | run_sets.sh | Supported |  |
| 34 | plain terms | We built graphs for 212 short prompts with each, then checked whether each graph's ten most important features had a match in the others: same place, same direction, and the same effect when switched off. | graphs.py; match.py | Supported |  |
| 35 | plain terms | Only about 57% did. | primary.json H1 0.567 | Supported |  |
| 36 | plain terms | But when we asked the looser question, whether the same concept was represented somewhere among the other transcoder's top features, 90% were. | primary.json H2 0.903 | Supported |  |
| 37 | plain terms | So individual features in an attribution graph should not be read as stable facts about the model; about four in ten would change with a new seed. | primary.json 1 - mean 0.591 | Supported |  |
| 38 | plain terms | The broader concepts are much more stable. | primary.json H2 | Supported |  |
| 39 | plain terms | Claims built on single features, especially early in the network, should be checked against retrained transcoders. | primary.json by_layer_depth (recommendation) | Supported |  |
