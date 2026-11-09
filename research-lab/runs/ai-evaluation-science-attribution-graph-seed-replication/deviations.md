# Deviations from plan.md

## D1 — 2026-11-05 19:02 NZDT — more prompt templates, before any graph was built

(Committed in 444f92f at 19:02; the first draft stamped it 19:50.)

**What happened.** The first selection kept 111 of 223 candidate prompts, short of the plan's minimum of 150 with at
least 15 per family.

| family | kept |
|---|---|
| factual | 25 |
| two-hop | 0 |
| antonym | 1 |
| IOI | 14 |
| induction | 35 |
| arithmetic | 36 |

**Change.** As the plan provides, templates were added:
- one worked example in each two-hop and antonym prompt (the example is never itself a target);
- 90 more IOI prompts with a second template.

Selection was rerun with the same rule (top-1 = target, margin ≥ 2). No transcoder or graph had been computed.

**Round 2** (same day, still before any graph). The second selection kept 127. Two-hop (3) and antonym (10) stayed
below 15 even with a worked example: Qwen3-0.6B cannot do them reliably. More prompts were added in the families it
handles: 60 induction sequences (second seed), 36 subtraction prompts, and 30 more capitals.

**Analysis rule.** Two-hop and antonym prompts that pass selection are kept and reported, but marked as below the
plan's per-family minimum. The family-level secondary analyses use only families with at least 15 prompts.

## D2 — 2026-11-08 16:26 NZDT — ablation details, before any matching result

(Committed in 01aa521 at 16:26; the first draft stamped it 16:45. Set A's graph build started at 16:21:55, about four minutes before `graphs.py` was committed at 16:26:10, so the
commit records the code after the build had begun; no later commit changes the graph settings.)

1. **Ablation effects in float32.** In bf16, a target logit near 19 moves in steps of 0.125, coarser than many
   single-feature effects. The counterpart rule compares signs and magnitudes, so ablation effects are measured with
   the replacement model loaded in float32. Graph construction stays in bf16, with identical settings across sets.
2. **Ablation setting.** Zero-ablation uses circuit-tracer's `feature_intervention` at the feature's layer and
   position with `freeze_attention=False`, so effects propagate through the replacement model. The setting is the
   same for every set. The plan did not specify it.
3. **Tokens.** Interventions use the same BOS-prefixed token ids as graph construction (`ensure_tokenized`).
4. **Loading.** circuit-tracer cannot load a local TopK set through `from_pretrained`. Sets are loaded with
   `load_transcoder_set(activation="topk", k=64)` and `from_pretrained_and_transcoders`; no fallback to ReLU was
   needed.

## D3 — 2026-11-08 — secondaries not run or reduced (after the primary results)

- **Not run:** claim replication of mediating paths (secondary 2), graph-level weighted Jaccard and layer-profile
  correlation (secondary 3), activation-correlation matching for all features (secondary 4), and the mixed-effects
  model (secondary 5; plain tables by family and layer depth are reported instead). Activation-correlation matching
  was run only for the 30 G4 features.
- **Seeds needed** (secondary 7) is reported as the share of A's top-10 features with counterparts in both, one or
  neither of B and C, not as a fitted curve.
- **Dead fraction.** Fidelity counts a feature as dead if it never fires on the 998,448 held-out tokens (about 24%
  per set). Training's running dead-feature measure was much lower (0.05%); the two measures differ.

## D4 — 2026-11-10 — fixes after the independent review (verdict: fix first)

1. **Arithmetic targets were the space token** (finding 1; a bug fix, made before any rebuilt result was read).
   Qwen3 tokenises " 7" as " " + "7", and `select_prompts.py` took the target's first token, so all 59 kept arithmetic
   prompts attributed the logit of " " (id 220): the graphs explained predicting a space after "=". `prompts.py` now
   ends each arithmetic prompt with that space and targets the digit, which is the token sequence of the natural
   "a + b = c". Selection was rerun on all 488 candidates with the frozen rule: the non-arithmetic selection is
   unchanged (199 − 46 = 153 prompts, identical), and 46 arithmetic prompts are kept (of 72; 59 before). Prompts now
   carry a stable index "i"; the 153 kept prompts keep their old index, so their graphs and match rows are reused, and
   the 46 new ones are 212–257. The first run's 59 arithmetic graphs per set are kept in `data/graphs_v1_arith/`.
   Graphs (all five sets), own-effects, and matching for every pair were then rebuilt (`code/run_d4.sh`).
2. **Target invariant** (G3): every target token is the answer or a stated prefix of it, and none is whitespace or
   punctuation (`prompt_selection.json` D4: 187 whole answers, 12 prefixes; asserted in `select_prompts.py`). Nine of
   the ten antonym targets are first-token prefixes such as "f" for "froid" (finding 4); the family is kept but left
   out of family-level statements.
3. **BOS prefix.** Selection tokenised without the BOS token that circuit-tracer prepends. With it, 142 of the 199
   prompts still have the target as top-1 with a margin of at least 2 (arithmetic 15 of 46). H1 restricted to those
   142 is reported as a sensitivity.
4. **match.py stores every candidate's effect** (finding 3): each candidate at decoder cosine ≥ 0.5 is ablated and
   stored as [index, cosine, effect], so the full rule can be re-read at other thresholds; at 0.7 and 0.5 it equals
   the stored counterpart flag exactly. Matching rows are in `data/match_d4/` (`results/match_d4/`); the first run's
   are kept in `results/match/`.
5. **Subspace replication** (finding 5): duplicate indices in Y's top-30 are removed before the QR (mean norm 0.896
   against 0.897 with duplicates), and two nulls are computed: the same feature projected onto Y's same-layer top-30
   for a different prompt of a different family, and of the same family.
6. **Post hoc sensitivities in `analyse.py`** (findings 2, 3 and 8; labelled, not the preregistered verdict): family
   exclusions, the BOS-margin restriction, the position-1 stratification and each set's position-1 share, a two-way
   bootstrap over prompts and feature-direction units, top-k and full-rule threshold grids with verdicts, replication
   by direction, the paired A-vs-D difference with the same X = A lists, and the error-share terciles labelled as row
   means.
7. **Fidelity diagnostics** (finding 6; `code/fidelity_d4.py`): skip terms, dead features counted as never in the top
   k and as never positive, the share of negative top-k values, the replacement model with position 0 replaced and
   with position 0 kept true (as circuit-tracer does), and reconstruction error at position 1 against later
   positions on the BOS-prefixed prompts.
8. **G3 and G4** (findings 7 and 9): G3 traces three seeded-random prompts; G4 is rerun on the D4 prompt set with the
   study's own rule as a column and every disagreement classed by a rule fixed before the rerun (artefact: fewer than
   10 active held-out tokens; split: each method's pick scores at least 0.6 on the other method; genuine otherwise).
9. **Provenance** (finding 9): D1 and D2 stamps corrected; ledger row R8 (Ameisen et al. 2025); a G2 coverage line in
   the report.
10. **Results after D4.** H1: median 0.583 (0.567–0.600), Inconclusive (all of 20 other bootstrap seeds); H2:
    +0.317 (0.308–0.327), Supported. Rebuilt arithmetic median 0.43. Position-1 features: 44% of top-10 rows,
    replicating at 0.37 against 0.76, and two-thirds of all non-replicating rows; the public set has none. Subspace
    nulls: 37% (different family) and 65% (same family). A vs D paired +0.033 (0.022–0.046). Fidelity: no skip term in
    the public set and encode–decode equal to the full forward; with position 0 kept true, top-1 agreement 0.58 for
    A–D and 0.26 for the public set (0.02 with position 0 replaced); no top-k value is negative, so the two dead-feature
    counts agree (38% on 249,612 tokens). G4 rerun: the two methods pick the same B feature in 25 of 29; the study's
    rule finds 18 of 30; all 4 disagreements classed genuine, three of them one recurring layer-0 position-1 feature.
    Prompt-level reconstruction error is no worse at position 1 than later in our sets (0.33–0.35 against 0.35–0.36 in
    layers 0–2), but much worse in the public set (0.66 against 0.38).

