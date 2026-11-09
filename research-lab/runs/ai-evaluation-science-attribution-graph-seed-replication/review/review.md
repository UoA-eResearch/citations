# Review: Do attribution graphs replicate across transcoder seeds? (ai-evaluation-science-attribution-graph-seed-replication)

Reviewer: Fable 5.1 (fresh independent reviewer), 2026-11-09.

## Verdict: **fix first**

The pipeline is mostly sound. Every headline number comes back exactly from the stored match rows, and the git timeline
holds. But the H1 verdict rests on a target-token bug. Every one of the 59 arithmetic prompts (28% of the battery)
attributes the logit of the space token " " (id 220), not the answer digit. Leave those prompts out and the same
preregistered rule gives **Refuted** (median 0.633, CI 0.600–0.650), not Supported. Two more problems shrink the
headline further. Half of all top-10 entries are a few dozen generic first-token features in layers 0–2, which recur
across prompts. Once that recurrence is allowed for, the H1 interval spans 0.6. The arithmetic graphs must be rebuilt
with the correct target before any H1 verdict can be published. That needs the A100.

Checks are in `reviewer_checks/` (scripts `c*.py`, outputs `c*.txt`). They were run on `results/match/*.jsonl`, which
is byte-identical to `data/match/` (checked with cmp), and on `data/graphs/*/NNN.json`.

## Findings

### 1. Critical — the arithmetic family attributes the space token, and H1 depends on it

- **Evidence:** `c5_g4_prompts.txt`, `c6_target_token.txt`.
- **The bug.** `select_prompts.py` takes `tok(target).input_ids[0]`. Qwen3 splits " 2" into " " + "2", so all 59 kept
  arithmetic prompts have `target_id` 220 (`target_token` " "). The prompt selection (top-1 = target, margin ≥ 2) and
  every arithmetic graph therefore concern predicting a space after "=", not arithmetic. G3's own arithmetic trace
  ("1 + 1 =" → " ") shows it, and nobody caught it.
- **The effect on H1.** Arithmetic is the only large family whose median is below 0.6 (0.50). Without it:
  - median 0.633, family-stratified CI [0.600, 0.650] → **Refuted** under the preregistered rule, for 5 of 5
    bootstrap seeds;
  - without arithmetic and antonym (see finding 4): Refuted for 4 of 5 seeds, Inconclusive for 1;
  - families with ≥ 15 valid prompts only: median 0.617, Inconclusive.
- **H2 is unaffected** (paired difference +0.27, CI 0.26–0.28, without arithmetic).
- **Fix:**
  - Rebuild the arithmetic prompts so that the next token is the digit: end each prompt with the space token, or
    target the digit directly and check the tokenisation. Then rerun selection, graphs (A–D, public), matching and
    `analyse.py`.
  - Record this as a D-entry (a bug fix, before results are re-read). Until it is done, report H1 as unresolved.
  - Add an invariant to G3: no target is whitespace or punctuation, and `target_token.strip()` equals the intended
    answer, or is a stated prefix of it.

### 2. Major — the top-10s are dominated by a few recurring first-token features, and the interval ignores this

- **Evidence:** `c2_graphs_effects.txt`, `c3_feature_concentration.txt`.
- **First-token features dominate.**
  - 46.9% of all A/B/C top-10 entries sit at position 1, the first token after BOS. All of them are in layers 0–6,
    almost all in layer 0.
  - Across A's 2,120 top-10 entries there are only 285 distinct (layer, index) features. Feature 0/3874 appears in
    195 of 212 prompts, and 0/30916 in 170.
  - The 96 feature-direction units seen in ≥ 20 prompts hold 59% of all H1 rows. Their outcomes are close to
    all-or-nothing: 39% of those rows are in units that replicate ≤ 10% of the time, and 21% in units at ≥ 90%. For
    example, A's 0/3874 never has a counterpart in B or C (0 of 195, twice).
  - Position-1 rows replicate at 0.37. All other rows replicate at 0.78, and the per-prompt median without
    position-1 features is **0.82**.
  - The public set has **0%** of its top-10 at position 1, against 43–48% for A–D. The report does not mention this
    contrast.
- **The interval is too narrow.** Because the same few features recur across prompts, a bootstrap over prompts alone
  treats one feature's outcome as ~200 independent observations. A two-way bootstrap that also resamples features gives
  **[0.50, 0.68]** for the H1 median (32% of replicates ≥ 0.6).
- **Small effects make matching noisy.** These features also have small ablation effects (median |effect| 0.09 logit
  in layers 0–6). Among candidates that pass the cosine test, the ablation condition passes 65% of the time in the
  smallest-effect quintile and 96% in the largest. The 50%-magnitude rule is therefore noisiest exactly where the
  failures are.
- **Fix:**
  - Report the position-1 share and the replication without position-1 features as a prominent stratification. The
    plan already promised stratification by graph sparsity, and this is the dominant structure.
  - Report a feature-clustered or two-way interval next to the preregistered one, and say the verdict is not robust
    to it.
  - Investigate why A–D, and not the public set, put first-token features at the top. Training skipped only sequence
    position 0 of packed 1,024-token windows, while graphs use a BOS-prefixed prompt. Check the per-position FVU at
    position 1 of the prompts.
  - Rewrite "about four in ten top features would change with a new seed" accordingly. Most non-replicating top
    features are a handful of generic first-token features. Content features in layers 14–27 replicate at 85–87%.

### 3. Major — "Supported" for H1 is not robust even before finding 1, and the report understates this

- **Evidence:** `c1_rederive.txt`.
- **Exact re-derivation.** The median 0.5667 (34/60), the CI [0.5667, 0.5835] (analyse.py's RNG stream) and the mean
  0.591 all reproduce exactly.
- **Other cut-offs.** Under the same rule:
  - top-5: median 0.600, Inconclusive;
  - top-3: Inconclusive; top-7: Inconclusive; top-1: Refuted;
  - equal family weight: median 0.633.
- **Bootstrap seeds and the lattice.** With other bootstrap seeds the upper bound is 0.5917 instead of 0.5835. The
  lower bound equals the median because 51% of bootstrap medians sit exactly on 34/60.
- **Cosine threshold.** The full rule's median at cosine ≥ 0.8 must lie between 0.38 and 0.52. At 0.6 its upper bound
  is 0.80, so the verdict at a looser cut is unknown. Effects of g are not stored, so this cannot be computed here.
- **Directions.** The six directions range from a median of 0.50 (A→B) to 0.70 (C→A).
- **Fix:**
  - State in the verdict block that H1 holds only for top-10, only at cosine 0.7, and only with the arithmetic family
    (finding 1).
  - Store g's effects in match rows so threshold sensitivity can be computed for the full rule.
  - Replace "Supported, narrowly" with the post-fix verdict and these qualifiers.

### 4. Moderate — the antonym targets are sub-word fragments

- **Evidence:** `c6_target_token.txt`.
- 9 of the 10 antonym targets are first-token prefixes: "f" for froid, "b" for bajo, "fa", "pet", "bl", "no", "rá" and
  so on. The single-letter ones say little about antonymy.
- The family is small (10) and already flagged below the minimum, so its effect on H1 is small.
- **Fix:** Note this in the report, or prepend the space/quote so that whole-word targets are single tokens. Exclude
  the family from family-level statements.

### 5. Moderate — H2's subspace criterion has no null, and "concepts" overreads it

- **Evidence:** `c2_graphs_effects.txt`, `c1_rederive.txt`.
- **No baseline.** Subspace replication drops both the ablation condition and the active-at-position condition, so it
  is easier to meet by construction. Against cosine-only node replication (0.7), the paired gap is still +0.20 per
  prompt (99.5% of prompts positive). So H2 survives as stated. But nothing shows what a non-matching subspace scores.
  - A random 30-dim span gives ≈ 0.17.
  - Y's top-30 decoders, though, span the very output directions both sets reconstruct on that prompt.
  - The public set (a different recipe, 5× wider) still scores 0.65, which suggests the criterion is permissive.
- **Duplicate columns.** About 12% of `top30_by_layer` entries are duplicate indices (the same feature at another
  position). The QR then adds spurious orthonormal directions. Simulated inflation is ≈ 0.004 in squared norm, which is
  negligible, but the code should deduplicate.
- **Fix:**
  - Add a null computed on the A100: the projection onto Y's same-layer top-30 from a different prompt, or onto
    random active features.
  - Deduplicate indices before the QR.
  - Phrase H2 as "lies in the span of the other set's top same-layer decoders", not "concepts replicate".

### 6. Moderate — fidelity anomalies were reported, not investigated (G3)

- **Evidence:** `c7_fidelity_timeline.txt` (per-layer fidelity; act_check commit message in its git log).
- **The public set.** Top-1 agreement 0.024, KL 8.73, and layer-2 FVU 0.886.
  - These figures contradict the study's own act_check commit, which reported public FVU 0.16–0.65 via `tc(x)`, and
    they contradict the set's routine use in circuit-tracer.
  - `fidelity.py` reconstructs through `encode`/`decode`, which likely omits any skip term the public transcoders
    carry.
  - "Replacing all 28 MLPs with its transcoders breaks the output" is probably a measurement artefact.
- **The dead fraction.** 24% of features never fire on 1M held-out tokens; training's running measure was 0.05%.
  - Training counts any feature in the top-k as fired, including negative values, because the trainer has no ReLU.
    Fidelity counts only `a > 0`, and its window is 10× shorter.
  - If circuit-tracer's TopK zeroes negative values, the graphs use a different transcoder from the one trained.
  - That cannot be decided without the weights and the training log, neither of which is stored here.
- **Fix:**
  - Recompute the public set's fidelity with the transcoder's full forward.
  - Compare the training-time and circuit-tracer FVU per layer, and the share of negative top-k values on held-out
    tokens.
  - Until then, drop the "breaks the output" sentence or mark it unverified.

### 7. Minor — G4 is thin and its inference is stretched

- **Evidence:** `c5_g4_prompts.txt`.
- **No error classes.** The 7 disagreements are not classed as artefact, noise or genuine, as METHODS G4 requires.
- **Not the study's rule.** G4's cosine is the best over *all* B features (20 of 30 clear 0.7). The study's rule uses
  B features active at that position (19), and only 17 of the 30 are counterparts.
- **Thin correlations.** Several correlations rest on few active tokens, for example 1 token (corr 1.000) and 4
  tokens. 16 of the 30 are position-1 features.
- **The inference.** "Decoder-based node replication may understate functional replication" is a weak inference from
  n = 30.
- **Fix:** Add the error classification and the study-rule column. Soften or drop the sentence.

### 8. Minor — the comparisons in the text are not like for like

- **Evidence:** `c1_rederive.txt`.
- **Data order.** "A vs D 0.65, above the 0.57 between different initialisations" compares 2 directions with 6. The
  paired difference with the same X = A lists is +0.041 (0.032–0.052), against A<->C 0.60 and A<->B 0.55.
- **Error share.** The tercile figures (0.55/0.58/0.65) are row means over features, but the text calls them medians
  per graph.
- **Title.** The title mixes a median (57%) with a mean (90%).
- **Fix:** Report the paired difference with its CI, label the statistics, and use the same statistic in the title.

### 9. Minor — the timeline and the record have small mismatches

- **Evidence:** `c7_fidelity_timeline.txt` (git log, deviation stamps, file mtimes); `c4_gate_tools.txt`.
- **Deviation times.** D1 is stamped 19:50 but was committed at 19:02. D2 is stamped 16:45 but was committed at
  16:26.
- **Graphs before code.** Set A's graphs started at 16:21:55, about 4 minutes before `graphs.py` was committed
  (16:26:10).
- **Missing citation.** The ledger lacks Ameisen et al. 2025, the attribution-graph method the plan cites.
- **Missing coverage line.** The report has no "Coverage —" line (G2 requires one).
- **G3 overstatement.** G3 says the capital prompt's top-10 decoders "promote sensible tokens". Only 3–4 of 10 do.
  The rest promote " choking", ".hy" and similar.
- **Fix:** Correct the stamps, add the ledger row and the coverage line, and soften the G3 sentence.

## Answers to the brief's numbered checks

1. **Recipe and training.**
   - TopK k = 64, width 32,768, unit-norm decoders, aux-k (k_aux 512, coefficient 1/32, 10M-token dead window), Adam
     2e-4 with warm-up and cosine to 10%, and 73,242 steps × 4 × 1,024 ≈ 300M tokens all match the plan.
   - Seeds: A/B/C use initialisation seeds 0/1/2 with order 0; D uses 0/1 (`run_sets.sh`).
   - The trainer applies no ReLU to the top-k values, so activations can be negative.
   - The dead discrepancy is unresolved (finding 6). It could not be checked without the weights and the training log
     (`logs/` and `data/sets/` are not stored here).
2. **Graph settings and top-10 selection.**
   - Settings are identical in code across sets.
   - The 8,192 cap is hit by 100% of A–D graphs (1.9% of public graphs). Top-10 lists are complete.
   - Influence is all positive (unsigned; minimum 0.0038), and the lists are sorted correctly.
   - Match rows agree with graph top-10s on (layer, pos, idx) for all 12,720 rows.
3. **Counterpart rule.**
   - The implementation matches the plan and D2: candidates are active features at (l, t), cosine ≥ 0.7, then the
     first candidate with the same sign and ≥ 50% magnitude.
   - Effects are in float32 and are never exactly 0. The G4 rerun reproduces 30 of 30, but with the same code.
   - freeze_attention=False is a reasonable choice, disclosed before matching.
   - The ablation condition is noisy for small effects (finding 2).
   - Subspace rule: QR of the top-30 indices, with duplicates (finding 5).
   - No defaulted subspace or cosine values (0 rows with norm 0 or null cosine).
4. **Statistics.**
   - Averaging over 6 directions is as planned.
   - The bootstrap is stratified with 3 two-hop prompts. Each family is resampled with replacement, so the 3 two-hop
     values contribute little variance.
   - The median on a 1/60 lattice makes the lower bound equal the median.
   - The prompt-only bootstrap ignores the recurrence of features (two-way CI 0.50–0.68).
5. **Robustness of "Supported".** It is not robust: it holds at top-10 only and flips without arithmetic (findings 1
   and 3). G4 suggests decoder cosine is the stricter matcher, so looser matching would raise replication further.
6. **Fidelity.** 0.52–0.54 top-1 is near the plan's 0.5 marker and is honestly stated. The public set's 0.02 looks
   like a measurement artefact (finding 6). Sets A–D have equal fidelity, so the comparisons between them are fair.
7. **Report numbers.**
   - Every number in the verdict block, the tables, the families, depths, error terciles, top-5, cosine-only, the
     both/one/none split, A–D, public, fidelity and G4 matches the tables (`c1`, `c5`).
   - Problems are in meaning, not arithmetic: the title, the plain terms and "Supported" (findings 1–3, 5 and 8).

**Git timeline:**
- The plan (11-05 18:47) precedes the trainer (19:23) and the first graph (11-08 16:21).
- The prompts were frozen at 11-05 19:02.
- `graphs.py`/`match.py` (16:26) and `analyse.py` (16:29) precede the first match file (`effects_A.json`, 21:17).
- `plan.md` was never edited after its commit.

**Gates:**
- **G1:** adequate. Selection uses the model only, and no agent labels. It missed the target tokenisation, which is a
  packaging issue in the broad sense.
- **G2:** coverage.json passes (1,060/1,060; 21,200/21,200), with no silent defaults, but the report lacks the coverage
  line.
- **G3:** partly hollow. It has no expected-range check. Its traces are the first prompt per family, not random. It
  missed the " " target. It did not investigate the public 0.02 or the dead fraction.
- **G4:** no error classes (finding 7).
- **G5:** `--verify` passes, but the labels are too generous (below).
- **G6:** `attribution.py check` passes (7 rows, identifiers resolve to the right titles); Ameisen et al. is missing.
- **G7:** not applicable.

## G5 re-labels

| # | sentence (short) | new label | why |
|---|---|---|---|
| 1 | title "only about 57% … 90% … in the span" | Overstated | H1 figure carried by space-token arithmetic graphs; median vs mean mixed |
| 7, 8, 10 | H1 Supported, narrowly; 0.567 (0.567–0.584) | Overstated | Refuted without the invalid family; not robust to top-k or feature-level resampling |
| 14, 16, 36, 38 | "concepts replicate" / "same concept represented" | Partially supported | geometric span with no null; not a concept test |
| 22 | A vs D 0.65 above 0.57 | Partially supported | unpaired; paired gap +0.04 |
| 26 | decoder matching may understate functional replication | Partially supported | n = 30, no error audit, different cosine than the rule |
| 35, 37 | "only about 57% did"; "four in ten would change" | Overstated | the loss is mostly a few recurring generic first-token features; content features replicate at 0.85–0.87 |
| 39 | single-feature claims, especially early, should be checked | Partially supported | true for early-layer features, which are mostly generic first-token features, not typical claim targets |

## What to do

1. Fix the arithmetic targets: the next token must be the digit. Rerun selection, graphs, matching and analysis for
   all sets, record a D-entry, and re-read H1 under the preregistered rule.
2. Add an invariant that every target is the intended answer token (or a stated prefix). Fix or caveat the antonym
   fragments.
3. Report the position-1 share, replication without position-1 features, and a feature-clustered interval. Explain
   the A–D versus public contrast.
4. Store counterpart effects so cosine and magnitude sensitivity can be computed for the full rule. Report top-k
   sensitivity with verdicts.
5. Add a null for subspace replication, deduplicate the top-30 indices, and rephrase H2 without "concepts".
6. Recheck the public-set fidelity (full forward with skip) and the dead-fraction discrepancy (negative top-k values;
   training versus circuit-tracer FVU).
7. Complete G4 error classes, the G2 coverage line, the G6 Ameisen row, the deviation timestamps and the G3
   expected-range check. Rerun G5 after the rewrite.

## In plain terms

The study asked whether the "important features" in an attribution graph survive retraining the transcoder with a
different random seed. The bookkeeping is careful, and every number in the report can be recomputed exactly from the
stored files.

But one in four test prompts was broken. For "1 + 1 =", the graphs explain why the model outputs a space, not why it
outputs "2", because the answer was cut to its first token. Those broken prompts are what pull the median below 0.6.
Without them, the study's own rule says the prediction "below 0.6" is refuted, not supported.

Separately, about half the "top features" are the same few generic features on the first word of every prompt. These
replicate poorly, and they repeat across prompts, which makes the result look more certain than it is. Features in the
later layers, which people usually interpret, replicate about 85% of the time.

The arithmetic prompts need to be rebuilt on the GPU, and the verdict re-read, before this is published.

**Not checkable here (needs the A100 files):**
- transcoder weights and training logs (the dead-fraction cause, TopK sign handling, training FVU);
- graph active-feature files and counterpart effects (full-rule threshold sensitivity, the subspace null);
- the public-set fidelity path;
- whether the BOS-prefixed prompts still meet the selection margin. Selection tokenised without a prefix.
