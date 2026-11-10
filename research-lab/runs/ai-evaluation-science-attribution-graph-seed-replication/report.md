# Do attribution graphs replicate across transcoder seeds? Close to 60% of a graph's top features have a functional counterpart under a new seed, too close to call; generic first-token features replicate less than half the time, later-layer features mostly do

*Four sets of per-layer transcoders were trained on Qwen3-0.6B with one fixed recipe. Three differed only in their
initialisation seed and one in data order. Attribution graphs were built with circuit-tracer for 199 prompts in six
families under every set. Each graph's ten most influential features were then matched across sets by layer,
position, decoder direction and ablation effect. The plan was committed before any transcoder was trained. Revised
after the independent review found that the arithmetic prompts explained the wrong token (D4).*

**Verdict: H1 Inconclusive; H2 Supported.**

- **H1 (node replication across initialisation seeds is below 0.6): Inconclusive.**
  - Per prompt, the share of the top-10 features with a counterpart in another seed's graph has a median of
    **0.583** (95% family-stratified bootstrap 0.567 to 0.600) over the 6 ordered pairs of A, B and C; the mean is
    0.587. The upper bound reaches 0.6, so the rule gives Inconclusive (under 20 other bootstrap seeds as well).
  - A counterpart must be active at the same layer and position, with decoder cosine ≥ 0.7, and its zero-ablation
    must move the target logit the same way by at least half as much.
  - **The first draft said Supported (0.567) on a bug.** All 59 arithmetic prompts attributed the space before the
    answer, because Qwen3 splits " 7" into " " and "7". With the answer digit as target (46 prompts pass selection),
    arithmetic still replicates least (median 0.43).
  - **Some targets are not what the model predicts in the graphs.** Under the BOS-prefixed tokens circuit-tracer
    uses, 28 of the 199 targets (26 of them arithmetic) are not the model's top-1 token, so for those the graph
    explains a logit the model does not predict. The arithmetic prompts, which end with a space as the natural
    "a + b = c" tokenisation needs, are the ones most affected. Restricted to the 171 prompts whose target is top-1, H1 is
    0.600 (0.567 to 0.633), Inconclusive, and arithmetic 0.48 (20 prompts).
  - **The verdict turns on choices the plan fixed** (post hoc): without arithmetic, Refuted (0.633); families with at
    least 15 prompts only, Supported (0.567); top-1 features only, Refuted; cosine 0.8 or magnitude 70%, Supported;
    cosine 0.6 or magnitude 30%, Refuted. A bootstrap that also resamples features, which recur across prompts, gives
    0.51 to 0.66.
- **What drives non-replication: generic first-token features** (post hoc).
  - 44% of all top-10 entries sit at position 1, the first token after the BOS token, all in layers 0–2 (87% in layer 0).
    Top features recur across prompts: 47 feature directions (a set's feature) appear in the top ten of at least 20
    prompts and make up 55% of the rows.
  - They replicate at 0.37. All other top features replicate at 0.76, and without position-1 features the median per
    prompt is 0.74. In layers 14–27, node replication is 0.82.
  - The public low-L0 transcoders put none of their top features at position 1, against 40–47% for our four sets.
    Our sets reconstruct the first token after BOS about as well as later tokens (normalised error in
    layers 0–2: 0.33–0.35 against 0.35–0.36), while the public set reconstructs it poorly (0.66 against 0.38), so its
    first-token signal goes to error nodes rather than features. That is a likely reason for the contrast, not a
    tested one.
- **H2 (top features lie in the span of the other set's top same-layer decoders more often than they have a
  counterpart): Supported.**
  - A top feature is subspace-replicated if its unit decoder has norm ≥ 0.7 in the span of the other set's 30 most
    influential same-layer decoders for that prompt. That holds for **90%** of top features, against 59% node
    replication; the paired difference is **+0.32** (0.31 to 0.33).
  - **The criterion is permissive** (post hoc nulls): the span of another prompt's top-30 catches 37% of features
    when the prompt is from a different family and 65% when it is from the same family. Subspace replication exceeds
    the different-family null by 0.53 (0.52 to 0.55), the same-family null by 0.26 (0.24 to 0.28; positive for 83% of
    prompts), and cosine-only node replication by 0.19. For arithmetic and position-1 features the same-family null
    nearly equals the statistic (0.91 against 0.92; 0.84 against 0.86), and for IOI it is close (0.87 against 0.97), so
    there the criterion barely discriminates. It shows shared directions, not that the same concept is used.
- **Data order and initialisation make no consistent difference.** Set D shares A's initialisation but sees the data
  in a different order. A's top features find a counterpart in D 3.3 points more often than in B or C (paired +0.033,
  0.022 to 0.046), but D's top features find one in A 2.1 points less often than B's and C's do (−0.021, −0.036 to
  −0.005). Both directions together: +0.006 (−0.005 to +0.016). The public low-L0 set against A: median 0.30.
- **Fidelity.** Each of our sets explains 76% of MLP-output variance (FVU 0.24). With every MLP output replaced
  except at position 0, which circuit-tracer also leaves alone, the replacement model's top-1 prediction matches the
  true model on 58% of held-out tokens (KL 0.83 per token); replacing position 0 as well, as the first draft did,
  gives 52–54%. The public set has no skip term, and its encode-decode path equals its full forward, so the first
  draft's 2% top-1 agreement for it came mostly from replacing position 0. Left alone, it is 26%: still poor, chiefly
  because its layer-2 transcoder explains little (FVU 0.87).

## In plain terms

Attribution graphs are a popular way to explain what a language model is doing on a given input. A smaller,
interpretable model called a transcoder stands in for parts of the network, and the graph shows which of its
"features" drive the answer. Researchers read these graphs as evidence for mechanisms, but the transcoder is trained
with randomness. Would a second transcoder, trained the same way with a different random seed, tell the same story?

We trained four transcoders for a small open model, Qwen3-0.6B, identically except for the random seed or data order.
We built graphs for about 200 short prompts with each, then checked whether each graph's ten most important features
had a match in the others: same place, same direction, and the same effect when switched off. About 58% did, which is
too close to our 60% threshold to call either way. The first version of this study said "fewer than 60%", but one in
four of its prompts had been set up to explain the wrong word; fixing that moved the answer to the threshold.

About two-thirds of the features that fail to match are generic features on the first word of the prompt, early in
the network, and the same few of them turn up again and again. Features later in the network, the kind people usually interpret, matched about 80% of the time.
So a single feature in an attribution graph is fairly stable if it sits in the later layers, and should not be trusted
if it is one of these early, generic ones.

## What was asked

The lead (`ai-evaluation-science-attribution-graph-seed-replication`) asked whether attribution-graph conclusions
survive retraining the transcoders with a different seed. It predicted node replication below 0.6.
- **Attribution graphs** trace a target logit through a replacement model built from transcoder features (Ameisen et
  al. 2025); circuit-tracer implements the method.
- **Transcoders** replace MLPs with sparse, interpretable maps (Dunefsky et al. 2024). TopK sparsity and the
  auxiliary-k loss follow Gao et al. (2024).
- **Seed variance in sparse autoencoders** is known: different seeds learn different features (Paulo and Belrose
  2025). It had not been measured for the transcoder attribution graphs used to make mechanistic claims.

## How it was done

- **Model:** Qwen3-0.6B (28 layers; Qwen3 technical report), bf16.
- **Transcoders** (`code/train_transcoders.py`): width 32,768, TopK k = 64 (top-k values are kept with their sign, in
  training and in circuit-tracer), unit-norm decoders, auxiliary-k loss; 300M FineWeb-Edu tokens (Penedo et al.
  2024), all 28 layers jointly, about 17 hours per set on an A100. Sets A, B and C use initialisation seeds 0, 1 and
  2; D uses seed 0 with data-order seed 1.
- **Prompts** (`code/prompts.py`, `code/select_prompts.py`): 488 generated from fixed templates in six families,
  kept if Qwen3-0.6B's top-1 next token is the target with a margin of at least 2. 199 were kept: factual 31, antonym
  10, IOI 18, induction 91, arithmetic 46, two-hop 3. Two families fell short of the planned 15 (D1). Every target is
  the answer or a stated prefix of it (D4); nine antonym targets are first-token prefixes such as "f" for "froid".
  With the BOS token the graphs use, 171 of the 199 targets are still top-1 (28 are not, 26 of them arithmetic), and
  142 clear the margin.
- **Graphs** (`code/graphs.py`, circuit-tracer): the target logit is the answer, at most 8,192 feature nodes,
  pruning at 0.8 (nodes) and 0.98 (edges). The top 10 are the most influential kept features.
- **Coverage (G2):** all 995 graphs were built (199 prompts × 5 sets), and all 19,900 match rows were written
  (`results/tables/coverage.json`).
- **Matching** (`code/match.py`): counterparts as stated above. Zero-ablation effects come from circuit-tracer's
  feature intervention, in float32 (D2). Every candidate at cosine ≥ 0.5 is ablated and stored, so the rule can be
  re-read at other thresholds (D4).
- **Statistics** (`code/analyse.py`): per-prompt shares averaged over directions; the median over prompts, with a
  bootstrap over prompts stratified by family (2,000). Post hoc sensitivities are labelled as such.

## Results

| comparison | median node replication | mean node | mean subspace |
|---|---|---|---|
| **A, B, C (initialisation seeds; H1, H2)** | **0.583 (0.567–0.600)** | 0.587 | 0.905 |
| A vs D (data order) | 0.650 | 0.595 | 0.905 |
| public low-L0 set vs A | 0.300 | 0.275 | 0.651 |

| layers | top features | node | subspace |
|---|---|---|---|
| 0–6 | 6,374 | 0.38 | 0.83 |
| 7–13 | 16 | 1.00 | 1.00 |
| 14–20 | 1,372 | 0.87 | 0.99 |
| 21–27 | 4,178 | 0.81 | 0.99 |

| sensitivity (post hoc) | median | 95% | verdict |
|---|---|---|---|
| without arithmetic | 0.633 | 0.600–0.650 | Refuted |
| families with ≥ 15 prompts | 0.567 | 0.550–0.583 | Supported |
| without antonym (prefix targets) | 0.567 | 0.550–0.600 | Inconclusive |
| prompts clearing the margin with BOS (142) | 0.600 | 0.575–0.633 | Inconclusive |
| prompts whose target is top-1 with BOS (171) | 0.600 | 0.567–0.633 | Inconclusive |
| without position-1 features | 0.744 | 0.724–0.763 | Refuted |
| top-1 / top-3 / top-5 features | 0.83 / 0.61 / 0.60 | | Refuted / Inconclusive / Inconclusive |
| cosine ≥ 0.6 / 0.8 (magnitude 50%) | 0.633 / 0.533 | | Refuted / Supported |
| magnitude ≥ 30% / 70% (cosine 0.7) | 0.617 / 0.517 | | Refuted / Supported |
| two-way bootstrap (prompts and features) | 0.583 | 0.505–0.664 | (34% of replicates ≥ 0.6) |

- **By family** (median node replication): factual 0.60, IOI 0.63, induction 0.63, arithmetic 0.43; antonym 0.67
  (prefix targets) and two-hop 0.95 (3 prompts) are too thin or too compromised to read.
- **By direction:** from 0.50 (A→B) to 0.70 (C→A).
- **By the graph's error-node share** (terciles; mean over top-10 features): 0.54, 0.58, 0.65.
- **Of set A's top-10 features,** 44% have counterparts in both other seeds, 18% in one and 38% in neither.
- **Fidelity** (`results/tables/fidelity.json`, `fidelity_d4.json`):

  | set | FVU | top-1 agreement (KL), position 0 kept | top-1, position 0 replaced | error at position 1 / later, layers 0–2 |
  |---|---|---|---|---|
  | A | 0.239 | 0.581 (0.83) | 0.526 | 0.33 / 0.36 |
  | B | 0.239 | 0.580 (0.84) | 0.518 | 0.35 / 0.35 |
  | C | 0.239 | 0.580 (0.84) | 0.529 | 0.34 / 0.36 |
  | D | 0.239 | 0.581 (0.84) | 0.537 | 0.33 / 0.35 |
  | public low-L0 | 0.387 | 0.256 (3.52) | 0.023 | 0.66 / 0.38 |

  On 249,612 held-out tokens (D4). Fewer than 0.05% of top-k values are negative, all in layer 0, so counting a
  feature as fired when it is in the top k (as training did) or when it is positive (as the first draft did) gives the
  same dead fraction to the fourth decimal: 38% never fire
  on these tokens, against 24% on the first draft's 998,448. Training's 0.05% used a 10M-token window; the fall with
  window length is consistent with many features firing less than once per million tokens.

- **G4** (`results/tables/g4.json`, rerun in D4): for 30 random top features of A against B (12 at position 1),
  decoder cosine and activation correlation over held-out text pick the same B feature in 25 of the 29 that fire on
  that text. The study's own rule finds a counterpart for 18 of the 30; the best active-feature cosine clears 0.7 for
  22 and the best correlation for 27. The 4 disagreements are all classed genuine by the rule fixed beforehand (the
  cross scores, now stored, are 0.81 and 0.14, and 0.53 and 0.10), but three are the same layer-0, position-1 feature
  drawn on three prompts, an instance of the recurrence above; the 30 draws cover 23 distinct features, and two
  agreeing rows rest on 6 and 10 active held-out tokens. All 30 ablation effects reproduce exactly in a fresh
  process.

## What this does and does not show

- **Whether a top feature survives a new seed depends mostly on what kind of feature it is.** Generic first-token
  features in the first layers do so less than half the time (0.37), and they make up almost half of the top tens. Other top features
  mostly do (0.76; 0.82 in layers 14–27). The headline median mixes the two, which is why it sits near the threshold
  and moves with every analysis choice.
- **The shared-span result is weaker than it looks.** Nine in ten top features lie in the span of the other set's
  top same-layer features, but two-thirds lie in the span for a different prompt of the same family. It is evidence
  of shared directions, not of the same concept being used on the same input.
- **Matching rules decide the number.** Within reasonable thresholds the verdict runs from Supported to Refuted. A
  single replication figure for attribution graphs needs its matching rule stated.
- **Fidelity limits the reading.** Our replacement models agree with the true model's top-1 prediction on 58% of held-out
  tokens. Low replication could partly reflect transcoder error rather than seed alone. Sets A–D have equal fidelity,
  though, so the comparison between them is fair.
- **Not shown:**
  - **Other models or recipes,** or larger transcoders.
  - **Mediating-path ("claim") replication, graph-level similarity and full activation-correlation matching,** which
    were not run (D3).
  - **The full seed distribution.** Three seeds bound it; they do not map it.

## Process and deviations

- **Preregistration:** `plan.md`, committed before any transcoder was trained. Prompts were frozen, and the graph,
  matching and analysis code was committed before any matching result (set A's graph build started four minutes
  before `graphs.py` was committed; D2).
- **Deviations** (`deviations.md`): D1, extra prompt templates (two families below the minimum); D2, ablation in
  float32 with propagation, BOS tokens and TopK loading; D3, secondaries not run or reduced, and the dead-fraction
  definition; D4, after the independent review: the arithmetic target bug fixed and every graph and match rebuilt,
  the target invariant, stored candidate effects, subspace nulls and deduplication, the labelled post hoc
  sensitivities, fidelity diagnostics, random G3 traces, the G4 rerun with error classes, and provenance fixes.
- **Quality gates:** G1 (plan section 2), G2 (`results/tables/coverage.json`), G3 (`results/plausibility.md`), G4
  (`results/tables/g4.json`), G5 (`review/overclaim_check.md`) and G6 (`results/attribution_ledger.csv`). G7 does not
  apply (no labelling).
- **Compute:** a colleague's A100 used as a guest (about 70 GPU-hours for training, 6 for the first graphs, fidelity
  and matching, and about 1.5 for the D4 rebuild).
- **Independent review:** fix first; the fixes are in D4. **Confirmation pass:** publish with edits; the edits are in
  D5.

## Reproducing it

1. `code/prompts.py`, `code/select_prompts.py`, `code/data_prep.py`, `code/act_check.py`.
2. `code/run_sets.sh` (trains A–D with `code/train_transcoders.py`).
3. `code/graphs.py build <set>` for A, B, C, D and public; `code/fidelity.py`; `code/match.py` (D4: `code/run_d4.sh`
   runs selection, graphs, matching and `code/fidelity_d4.py`; `code/run_d4b.sh` runs G3 and G4).
4. `code/analyse.py`; `code/g3.py`, `code/g4.py`.
