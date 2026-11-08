# Do attribution graphs replicate across transcoder seeds? Only about 57% of a graph's top features have a functional counterpart in a retrained transcoder, but 90% of them lie in the span of its top features

*Four sets of per-layer transcoders were trained on Qwen3-0.6B with one fixed recipe. Three differed only in their
initialisation seed and one in data order. Attribution graphs were built with circuit-tracer for 212 prompts in six
families under every set. Each graph's ten most influential features were then matched across sets by layer,
position, decoder direction and ablation effect. The plan was committed before any transcoder was trained.*

**Verdict: H1 Supported; H2 Supported.**

- **H1 (node replication across initialisation seeds is below 0.6): Supported, narrowly.**
  - Per prompt, the share of the top-10 features with a counterpart in another seed's graph has a median of
    **0.567** (95% family-stratified bootstrap 0.567 to 0.584) over the 6 ordered pairs of A, B and C. The mean is
    0.591.
  - A counterpart must be active at the same layer and position, with decoder cosine ≥ 0.7, and its zero-ablation
    must move the target logit the same way by at least half as much.
  - Of set A's top-10 features, 43% have counterparts in both other seeds, 19% in one and 38% in neither.
- **H2 (concepts replicate better than features): Supported.**
  - A top feature is subspace-replicated if its decoder lies mostly (norm ≥ 0.7) in the span of the other set's 30
    most influential same-layer decoders for that prompt. That holds for **90%** of top features, against 59% node
    replication. The paired difference is **+0.31** (0.30 to 0.32).
- **Where replication fails.**
  - **Early layers.** Layers 0–6 hold 56% of the top features, and only 38% of those replicate as nodes (84% as
    subspaces). In layers 14–27, node replication is 85–87%.
  - **Initialisation, more than data order.** Set D shares A's initialisation but sees the data in a different order.
    A against D gives a median of 0.65, above the 0.57 between different initialisations.
  - **A different recipe.** The public low-L0 transcoders against A: median 0.20.
- **Matching is sensitive to its thresholds.** On decoder cosine alone, without the ablation condition, the median
  is 0.80 at a 0.6 cut, 0.68 at 0.7 and 0.58 at 0.8. The G4 audit found that activation correlation over held-out
  text clears 0.7 for more features (27 of 30) than decoder cosine does (20 of 30). So decoder-based node
  replication may understate functional replication.
- **Fidelity is moderate and reported, not a gate.** Each of our sets explains 76% of MLP-output variance (FVU
  0.236). With all 28 MLPs replaced, the model's top-1 prediction matches the true model on 52–54% of held-out tokens
  (KL 1.2–1.4 per token), near the plan's marker of poor fidelity (0.5).

## In plain terms

Attribution graphs are a popular way to explain what a language model is doing on a given input. A smaller,
interpretable model called a transcoder stands in for parts of the network, and the graph shows which of its
"features" drive the answer. Researchers read these graphs as evidence for mechanisms, but the transcoder is trained
with randomness. Would a second transcoder, trained the same way with a different random seed, tell the same story?

We trained four transcoders for a small open model, Qwen3-0.6B, identically except for the random seed or data order.
We built graphs for 212 short prompts with each, then checked whether each graph's ten most important features had a
match in the others: same place, same direction, and the same effect when switched off. Only about 57% did. But
when we asked the looser question, whether the same concept was represented somewhere among the other transcoder's
top features, 90% were.

So individual features in an attribution graph should not be read as stable facts about the model; about four in
ten would change with a new seed. The broader concepts are much more stable. Claims built on single features,
especially early in the network, should be checked against retrained transcoders.

## What was asked

The lead (`ai-evaluation-science-attribution-graph-seed-replication`) asked whether attribution-graph conclusions
survive retraining the transcoders with a different seed. It predicted node replication below 0.6.
- **Transcoders** replace MLPs with sparse, interpretable maps (Dunefsky et al. 2024). TopK sparsity and the
  auxiliary-k loss follow Gao et al. (2024).
- **Seed variance in sparse autoencoders** is known: different seeds learn different features (Paulo and Belrose
  2025). It had not been measured for the transcoder attribution graphs used to make mechanistic claims.

## How it was done

- **Model:** Qwen3-0.6B (28 layers; Qwen3 technical report), bf16.
- **Transcoders** (`code/train_transcoders.py`): width 32,768, TopK k = 64, unit-norm decoders, auxiliary-k loss;
  300M FineWeb-Edu tokens (Penedo et al. 2024), all 28 layers jointly, about 17 hours per set on an A100. Sets A, B
  and C use initialisation seeds 0, 1 and 2; D uses seed 0 with data-order seed 1.
- **Prompts** (`code/prompts.py`): 488 generated from fixed templates in six families. 212 were kept (Qwen3-0.6B's
  top-1 is the target with a margin of at least 2): factual 31, antonym 10, IOI 18, induction 91, arithmetic 59,
  two-hop 3. Two families fell short of the planned 15 (D1).
- **Graphs** (`code/graphs.py`, circuit-tracer): the target logit is the answer, at most 8,192 feature nodes,
  pruning at 0.8 (nodes) and 0.98 (edges). The top 10 are the most influential kept features. All 1,060 graphs were
  built.
- **Matching** (`code/match.py`): counterparts as stated above. Zero-ablation effects come from circuit-tracer's
  feature intervention, in float32 (D2).
- **Statistics** (`code/analyse.py`): per-prompt shares averaged over directions; the median over prompts, with a
  bootstrap over prompts stratified by family (2,000).

## Results

| comparison | median node replication | mean node | mean subspace |
|---|---|---|---|
| **A, B, C (initialisation seeds; H1, H2)** | **0.567 (0.567–0.584)** | 0.591 | 0.903 |
| A vs D (data order) | 0.650 | 0.635 | 0.904 |
| public low-L0 set vs A | 0.200 | 0.219 | 0.648 |

| layers | top features | node | subspace |
|---|---|---|---|
| 0–6 | 7,136 | 0.38 | 0.84 |
| 7–13 | 16 | 1.00 | 1.00 |
| 14–20 | 1,372 | 0.87 | 0.99 |
| 21–27 | 4,196 | 0.85 | 0.99 |

- **By family** (median node replication): factual 0.60, antonym 0.67, IOI 0.63, induction 0.63, arithmetic 0.50,
  two-hop 0.95 (3 prompts).
- **By the graph's error-node share** (terciles): 0.55, 0.58, 0.65. Graphs that lean more on error nodes replicate
  slightly better.
- **Top 5 instead of top 10:** median 0.60.
- **Fidelity** (`results/tables/fidelity.json`):

  | set | FVU | dead (never active, held-out) | KL per token | top-1 agreement |
  |---|---|---|---|---|
  | A | 0.236 | 23.8% | 1.31 | 0.529 |
  | B | 0.236 | 23.7% | 1.40 | 0.522 |
  | C | 0.236 | 23.8% | 1.37 | 0.526 |
  | D | 0.236 | 23.4% | 1.21 | 0.538 |
  | public low-L0 | 0.389 | 17.6% | 8.73 | 0.024 |

- **G4** (`results/tables/g4.json`): for 30 random top features of A against B, the decoder-cosine and
  activation-correlation methods pick the same feature in 21 of the 28 that fire on held-out text. All 30 ablation
  effects reproduce exactly in a fresh process.

## What this does and does not show

- **Single features in attribution graphs are seed-dependent.** About four in ten top features have no functional
  counterpart under a new initialisation. Most of the loss is in early layers, where generic early features, such as one
  tied to the first token position, are common among the top ten.
- **The represented concepts are much more stable.** Nine in ten top features lie in the other seed's span of top
  features. Mechanistic claims phrased as subspaces or groups replicate; claims about one feature often do not.
- **The verdict is narrow.** The median sits just below 0.6, and it depends on the matching rule. A looser cosine
  cut, or activation-correlation matching, would raise it.
- **Fidelity limits the reading.** Our replacement models agree with the true model's top-1 prediction about half
  the time. Low replication could partly reflect transcoder error rather than seed alone. Sets A–D have equal
  fidelity, though, so the comparison between them is fair.
- **Not shown:**
  - **Other models or recipes,** or larger transcoders.
  - **Mediating-path ("claim") replication, graph-level similarity and full activation-correlation matching,** which
    were not run (D3).
  - **The full seed distribution.** Three seeds bound it; they do not map it.

## Process and deviations

- **Preregistration:** `plan.md`, committed before any transcoder was trained. Prompts were frozen, and the graph,
  matching and analysis code was committed before any matching result.
- **Deviations** (`deviations.md`): D1, extra prompt templates (two families below the minimum); D2, ablation in
  float32 with propagation, BOS tokens and TopK loading; D3, secondaries not run or reduced, and the dead-fraction
  definition.
- **Quality gates:** G1 (plan section 2), G2 (`results/tables/coverage.json`), G3 (`results/plausibility.md`), G4
  (`results/tables/g4.json`), G5 (`review/overclaim_check.md`) and G6 (`results/attribution_ledger.csv`).
- **Compute:** a colleague's A100 used as a guest (about 70 GPU-hours for training, 6 for graphs, fidelity and matching).
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. `code/prompts.py`, `code/select_prompts.py`, `code/data_prep.py`, `code/act_check.py`.
2. `code/run_sets.sh` (trains A–D with `code/train_transcoders.py`).
3. `code/graphs.py build <set>` for A, B, C, D and public; `code/fidelity.py`; `code/match.py`.
4. `code/analyse.py`; `code/g3.py`, `code/g4.py`.
