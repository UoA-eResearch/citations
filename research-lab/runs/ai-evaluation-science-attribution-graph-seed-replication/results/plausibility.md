# Plausibility (G3)

- **The capital-city prompt** ("The capital of France is" → " Paris", set A). The top-10 features' decoders,
  projected onto the unembedding (`results/tables/g3.json`), promote sensible tokens:
  - layer 21: " French", "法国", " France";
  - layer 22: " city", " City", " cities";
  - layer 23: " French", " french".

  The most influential feature (layer 27) suppresses " Paris": ablating it raises the logit by 3.2. Influence is
  unsigned.
- **Three prompts traced** (factual, IOI, arithmetic; `g3.json`): top-3 features with influence, signed ablation
  effect and counterparts in B and C. A layer-0 feature at position 1 is in the top 3 for both the factual and the IOI
  prompt, a generic early feature of the kind that dominates the low-replication early layers.
- **Each set reconstructs its own layers** (`results/tables/fidelity.json`, 998,448 held-out tokens).
  - Sets A–D: FVU 0.236 for each; replacement-model top-1 agreement 0.52–0.54 and KL 1.21–1.40 per token.
  - Public lowl0 set: FVU 0.39 and top-1 agreement 0.02. Replacing all 28 MLPs with its transcoders breaks the
    output.
- **Invariants.**
  - All 1,060 graphs were built.
  - The 12,720 A/B/C feature-direction rows are 212 prompts × 10 features × 6 directions.
  - Ablation effects reproduce exactly in an independent process (G4, 30 of 30).
