# Deviations from plan.md

## D1 — 2026-11-05 19:50 NZDT — more prompt templates, before any graph was built

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

## D2 — 2026-11-08 16:45 NZDT — ablation details, before any matching result

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
