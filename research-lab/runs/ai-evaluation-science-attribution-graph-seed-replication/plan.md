# Plan (preregistration): do circuit-tracing explanations survive retraining the transcoders with a different seed?

Lead: `ai-evaluation-science-attribution-graph-seed-replication`. Written 2026-11-05, before any model, transcoder,
dataset shard or prompt result was downloaded or computed.

**Seen before this plan:**
- **The lead's text.**
- **Public descriptions** of circuit-tracer and of attribution graphs (Ameisen et al. 2025).
- **A web search for prior seed-replication work.** It found none at the level of attribution graphs; the related
  work is listed in the lead.
- No model output.

**Compute.** A guest A100 80 GB on a colleague's VM. Only open data and models are used.

## 0. Hypotheses

**Model.** Qwen/Qwen3-0.6B (28 layers, d_model 1,024), in bf16 for activations.

**Transcoders.** Four per-layer transcoder (PLT) sets cover all 28 MLPs. Each maps the MLP's input (the normalised
residual entering the MLP) to its output.
- **The recipe.** Width 32,768; TopK activation with k = 64; unit-norm decoder columns; the auxiliary-k dead-feature
  loss with coefficient 1/32. Adam at lr 2e-4 with linear warm-up over 1% and cosine decay; 300M tokens of
  FineWeb-Edu (sample-10BT) in 1,024-token sequences. All 28 layers are trained jointly from the same forward passes.
- **The four sets:**
  - A, B and C differ only in initialisation seed (0, 1, 2), with data-order seed 0;
  - D has initialisation seed 0 and data-order seed 1.
- **Fallback.** If circuit-tracer cannot load TopK transcoders, the four sets are retrained as ReLU transcoders with an
  L1 penalty tuned on set A to a mean L0 of 64 ± 10, and the change is recorded in deviations.md before any graph is
  built.
- **Fidelity is reported per set and is not a gate:** fraction of variance unexplained (FVU), dead-feature fraction,
  and the replacement model's KL and top-1 agreement against the true model on 1M held-out tokens. The public
  `mwhanna/qwen3-0.6b-transcoders-lowl0` set is reported alongside, as an out-of-recipe comparator.

**Prompts.** Six families are generated from fixed templates and word lists in `code/prompts.py`, written before the
model is run:
- factual recall (countries and capitals, elements and symbols);
- two-hop (the capital of the country where a landmark is);
- multilingual antonyms;
- indirect object identification (IOI);
- induction and copying;
- small arithmetic.

A prompt is kept if Qwen3-0.6B's top-1 next token is the target, with a logit margin of at least 2 over the
runner-up. At least 150 are needed, with at least 15 per family. If fewer survive, more templates are added and the
change is recorded as a deviation before any graph is built.

**Graphs.**
- **Construction.** circuit-tracer attribution graphs for every kept prompt under each set, with identical settings:
  the target logit is the answer token, node threshold 0.8 and edge threshold 0.98 (the library's defaults), and at
  most 8,192 feature nodes before pruning.
- **The top 10** of a graph are its 10 feature nodes with the largest influence on the target logit after pruning.

**Counterpart.** For a top-10 feature f in set X's graph for prompt p, a counterpart in set Y is a feature g that
meets all of:
- g is active on p at the same token position;
- g is in the same layer, with decoder cosine(f, g) ≥ 0.7;
- zero-ablating g at that position changes the target logit with the same sign as zero-ablating f does in X, and by
  at least 50% of the magnitude.

**H1 (the lead): node replication across seeds is below 0.6.**
- **The statistic.** For each prompt, the share of the top-10 features with a counterpart, averaged over the ordered
  pairs among A, B and C (6 directions); then the median over prompts.
- **Intervals.** Bootstrap over prompts, stratified by family, 2,000 resamples.
- **Rule.** *Supported* if the median is below 0.6 and its 95% upper bound is below 0.6. *Refuted* if the lower bound
  is at least 0.6. Otherwise *Inconclusive*.

**H2: concepts replicate better than features.**
- **Subspace replication.** A top-10 feature f in X is subspace-replicated in Y if the projection of its decoder onto
  the span of Y's 30 most influential same-layer decoders for that prompt has norm at least 0.7 (unit decoders).
- **Rule.** *Supported* if the paired difference (subspace replication minus node replication, per prompt) has a 95%
  interval above 0. *Refuted* if it lies below 0 or within ±0.05 of 0. Otherwise *Inconclusive*.

## 1. Secondary analyses (reported, not confirmatory)

1. **Data order against initialisation:** D against A, compared with the A, B and C pairs.
2. **Claim replication.** For each prompt, a mediating node is the feature on the strongest path whose zero-ablation
   moves the target logit most. Does Y have a counterpart path with a same-sign effect?
3. **Graph-level similarity:** weighted Jaccard of influence over matched nodes, and the correlation of
   influence-by-layer profiles.
4. **Matching by activation correlation** (Pearson ≥ 0.7 on 1M held-out tokens) instead of decoder cosine.
5. **By prompt family and layer depth**, with a mixed-effects model (family as a random effect) for node replication.
6. **The public lowl0 set** against set A.
7. **Seeds needed:** how many transcoder seeds a claim would need for a stable top-10, from the A, B and C overlap
   curve.

## 2. Leakage audit (G1)

- **No transcoder sees the prompts during training,** beyond chance overlap with FineWeb-Edu, which is not filtered.
- **Prompt selection uses only the model, never the transcoders.**
- **All settings are fixed above;** graph settings are identical across sets.
- **No LLM or agent labels any feature.** Concept checks are automatic (decoder geometry).

## 3. Other gates

- **G2:** `results/tables/coverage.json`, covering prompts generated, kept and dropped by reason; graphs built and
  failed; features matched.
- **G3:** `results/plausibility.md`:
  - three prompts traced end to end;
  - a sanity check that set A's top features for a capital-city prompt project onto relevant vocabulary;
  - a check that each set reconstructs its own layer outputs.
- **G4:** for 30 random top-10 features, the decoder-cosine match is compared with the activation-correlation match
  (agreement, with its denominator), and the ablation effects are re-run independently.
- **G5 and G6:** at write-up.
- **G7:** does not apply.

## 4. Limits stated in advance

- **One small model and one recipe.** Diffuse small-model mechanisms can lower replication for reasons other than
  seeds; results are stratified by graph sparsity and error-node share.
- **Three seeds bound, but do not map, the seed distribution.**
- **The 0.7 thresholds and the top-10 cut are conventions;** sensitivity to them is reported.
- **Thresholds were set before data.** If fidelity is poor (for example top-1 agreement below 0.5), replication may
  measure the transcoders' failure rather than their seed-dependence. That is reported, not hidden.
