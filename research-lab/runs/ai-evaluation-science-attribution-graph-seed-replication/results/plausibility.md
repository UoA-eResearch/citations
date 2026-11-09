# Plausibility (G3)

- **The capital-city prompt** ("The capital of France is" → " Paris", set A). Projected onto the unembedding
  (`results/tables/g3.json`), 3 of the top-10 features' decoders promote related tokens:
  - layer 21: " French", "法国", " France";
  - layer 22: " city", " City", " CITY";
  - layer 23: " French", "French", " french".

  The rest, including the three layer-0 features, promote unrelated fragments (for example " choking", ".hy"). The
  most influential feature (layer 27) suppresses " Paris"; influence is unsigned.
- **Three random prompts traced** (seed 20261110; D4; `g3.json`): an induction prompt (target " candle"), a two-hop
  prompt (" Moscow") and a rebuilt arithmetic prompt ("4 + 3 = " → "7"). Top-3 features with influence, signed
  ablation effect and counterparts in B and C. Layer-0 position-1 features appear in the top 3 of two of them. In the
  induction prompt both have counterparts in B and C; in the arithmetic prompt neither has one in B (one has one in
  C), while the layer-27 feature at the final position (ablation −1.54 on the "7" logit) has counterparts in both.
- **Targets** (D4): every target token is the answer or a stated prefix of it, none is whitespace or punctuation
  (asserted in `select_prompts.py`); the first draft's 59 arithmetic targets were all the space token.
- **Each set reconstructs its own layers** (`results/tables/fidelity_d4.json`, 249,612 held-out tokens).
  - Sets A–D: FVU 0.239; replacement-model top-1 agreement 0.58 (KL 0.83–0.84) with position 0 kept true, as
    circuit-tracer does, and 0.52–0.54 with position 0 replaced too.
  - Public low-L0 set: FVU 0.39 (layer 2: 0.87), no skip term, encode–decode equal to the full forward; top-1 0.26
    with position 0 kept, 0.02 with it replaced. The first draft's "breaks the output" was mostly the position-0
    replacement.
- **Invariants**, asserted in `code/analyse.py`: every counterpart has an active candidate at cosine ≥ 0.7; subspace
  norms lie in [0, 1]; every top feature's own ablation effect is non-zero; 11,940 A/B/C rows = 199 prompts × 10
  features × 6 directions; the full rule re-read from the stored candidates at cosine 0.7 and magnitude 50% equals
  the stored counterpart flag in every row; 995 of 995 graphs and 19,900 of 19,900 match rows (`coverage.json`).
- **Ablation effects reproduce exactly** in an independent process (G4, 30 of 30).
