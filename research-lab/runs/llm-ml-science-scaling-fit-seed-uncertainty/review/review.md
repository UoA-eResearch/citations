# Review: llm-ml-science-scaling-fit-seed-uncertainty

Reviewer: Fable (independent, adversarial), 2026-10-28. Scripts and outputs in `review/reviewer_checks/`
(`check_params.py`, `refit_N.py` + `refit_results.json` + `refit_n1_preds.csv`, `convergence.py` + `convergence.csv`
+ `convergence_summary.json`, `table_checks.py` + `table_checks.json`). CPU only, at most 4 processes.

## Verdict: FIX FIRST

The evaluation, the fitting code, the ladder construction, the seed bootstrap and the "two unstable runs" story all
check out, and every number in the report matches its table. But the N axis of every fit is not what the plan
preregistered. `evaluate.py:69` counts the parameters whose name does not contain "embed"; in the venv's transformers
5.20.2 the GPT-NeoX output head is named `lm_head.weight`, so N = non-embedding parameters + one 50304×d matrix for
all eight sizes (exact to the unit, `check_params.py`). At 14M that is 6.4× the preregistered count; at 2.8B 1.05×.
Re-fitting the same 2,000 ladders with the preregistered N moves W₁ from 0.123 to 0.103, halves the fitted α (0.25 to
0.10), collapses E (median 1.3 to 0.57, 5th percentile 0.16), and with the other common convention (total parameters)
the headline overshoot nearly disappears (+0.017, 33% of fits undershoot). The two preregistered verdicts almost
certainly stay Inconclusive, but the title number, the exponent secondary, the procedure-vs-seed decomposition and one
of the three headline claims (the shared overshoot "reflects the fitting form") have to be recomputed and rewritten.
The fix is mechanical and needs no GPU: correct the N column and re-run `fit.py`, `posthoc.py`, `figures.py`.

## Findings

### 1. MAJOR — N is non-embedding + one embedding matrix, not the preregistered non-embedding count

- **Evidence.** `plan.md:26` preregisters the non-embedding count. `evaluate.py:69` filters `"embed" not in n`.
  transformers 5.20.2 (`venv`) names the head `lm_head` (`modeling_gpt_neox.py:385`), so only `embed_in` is
  excluded. `check_params.py`: table N equals (L·(12d²+13d) + 2d) + 50304·d for every size:

  | size | N in table | non-embedding | ratio |
  |---|---|---|---|
  | 14M | 7,628,800 | 1,189,888 | 6.41 |
  | 31M | 17,616,896 | 4,739,072 | 3.72 |
  | 70M | 44,670,976 | 18,915,328 | 2.36 |
  | 160M | 123,689,472 | 85,056,000 | 1.45 |
  | 410M | 353,822,720 | 302,311,424 | 1.17 |
  | 2.8B | 2,646,430,720 | 2,517,652,480 | 1.05 |

  The distortion is size-dependent, so it compresses the small end of the log-N axis and changes the fitted curve, not
  just a label. This is neither the Kaplan (non-embedding) nor the Chinchilla (total) convention.
- **Effect** (`refit_N.py`, same 2,000 single-seed draws as `ladders_single.csv`, which it reproduces to 0.0; the
  n=3 draws replay from the same RNG and reproduce W₃ = 0.10332 exactly):

  | N convention | W₁ | median error vs 2.8B | share overshoot | α (5/50/95) | E (5/50/95) | W₁ excl. 410M seeds 3,4 |
  |---|---|---|---|---|---|---|
  | as run (one embedding) | 0.123 | +0.068 | 98% | 0.21 / 0.25 / 0.30 | 0.79–1.66 range | 0.051 |
  | non-embedding (plan) | 0.103 | +0.061 | 100% | 0.09 / 0.10 / 0.14 | 0.16 / 0.57 / 1.10 | 0.050 |
  | total (first 500 ladders) | 0.155 | +0.017 | 67% | 0.21 / 0.25 / 0.30 | 0.85 / 1.17 / 1.41 | — |

  3-seed, non-embedding N (first 1,000 draws): W₃ = 0.092 against W₁ = 0.104 on the same draws, shrinkage 0.115
  (reported 0.16). β is unaffected (median 0.88–0.92 under every convention).
- **Fix.** Replace the N column with the config count (the arithmetic above, or count parameters excluding both
  `embed_in` and `lm_head`/`embed_out`; do not rely on substring matching across transformers versions). Re-run
  `fit.py` (including the seed bootstrap and the procedure decomposition), `posthoc.py` and `figures.py`; update every
  N-dependent number in `report.md` (title 0.12, lines 23–29, 39, 78, 98–103, 115–119) and `overclaim_check.md`.
  Record this as D3 in `deviations.md`. Because the extrapolation error flips between conventions, report the total-N
  fit as a sensitivity beside the preregistered non-embedding fit.

### 2. MODERATE — the overshoot's attribution to "the fitting form and range" is not supported

- **Evidence.** `report.md:23–27, 45, 117` and `overclaim_check.md` rows 22 and 35 (labelled Supported) say the shared
  +0.07 overshoot is a property of the formula and range. The backing (it survives averaging; the 64k cut overshoots
  100%) shows only that the bias is shared across seeds, not what causes it. Finding 1 shows it depends on how N is
  counted: +0.061 under the preregistered convention, +0.017 with 33% undershoot under total N. Under the
  preregistered convention the asymptote E is poorly identified (5th percentile 0.16 nats, implausible for Pile), so
  the extrapolation rests on an ill-conditioned parameter. Two further untested contributors are not mentioned:
  (a) the D dimension is intermediate checkpoints of one cosine run, whose losses are not those of runs trained to that
  D (acknowledged for β at line 98 but not connected to the extrapolation bias); (b) near-duplication between Pile
  train and validation, which benefits the 2.8B target more than the ladder (see Finding 8).
- **Fix.** After the re-fit, state the overshoot under both N conventions, drop "reflects the fitting form and range"
  and "the formula itself ... was biased" unless the corrected fits still show it under both conventions, and list
  the N convention, the within-run D dimension and target-side memorisation as candidate causes. Re-label rows 22 and
  35 of the overclaim check as Partially supported until then.

### 3. MINOR (pass, one wording fix) — evaluation

- **Checked.** Token stream: documents in file order with EOS, packed and cut into 2,048-token sequences, 2,441
  sequences, 4,999,168 tokens (`eval_corpus.json`), 2,047 scored per sequence (`evaluate.py:75`, logits[:, :-1]
  against x[:, 1:]). D = step × 2,097,152 for all 405 rows. fp16 − fp32: 2.4×10⁻⁶ (1B), 5.9×10⁻⁵ (1.4B), so the fp16
  2.8B target is not a material problem. bf16 − fp32 on the full corpus reaches 4.6 nats at 14M, 1.7 at 70M, 0.42 at
  160M, 0.04 at 410M and 0 at 1B (`losses_bf16.csv` vs `losses.csv`), so D1 was necessary and the fp32 numbers are
  the right ones. Monotonicity: 410M seeds 0–2 and 7–9 fall monotonically; 70M runs still show late rises of up to
  0.087 in fp32, 160M at most 0.033 (`table_checks.json`, `late_rise_final_minus_min`), consistent with the report's
  line 73.
- **Evaluation noise.** `report.md:108` says the 0.047 document-bootstrap SD bounds how precisely a forecast can be
  scored against the target. That is the SD of a single corpus-level loss. The forecast and the target are scored on
  the same tokens, so the relevant quantity is the paired SD of the difference: 0.0076 for (2.8B − 410M seed 0),
  0.0026 for (2.8B − 1.4B), 0.0094 for (410M seed 4 − seed 0) (`table_checks.json`, `doc_bootstrap_sd`, 300 paired
  document resamples on `data/seqloss`). The overshoot is therefore robust to evaluation noise, by a wide margin; the
  sentence should say so and quote the paired figure instead.

### 4. MINOR (pass, one framing fix) — fits converge; the 16-start result is under-optimisation, not a procedure

- **Checked.** `fit.py:37–52`: Huber on log L against the log-sum-exp of the three terms, analytic gradient via the
  softmax weights (correct, including the linear-space branch); `fit.py:55–63`: 64 fixed starts, best objective
  kept. `convergence.py` on 40 ladders: every one of the 64 starts reports L-BFGS-B success; a median of 5 starts
  reach within 1% of the best; no best-start parameter sits on a bound; a 512-start grid lowers the objective by
  >10⁻⁶ relative in 7/40 ladders but moves the 2.8B prediction by at most 0.0010 (median 3×10⁻⁵), and W over the 40
  is unchanged (0.1254 vs 0.1254). Exponents in `ladders_single.csv` are interior: α 0.175–0.347, β 0.674–1.208
  (208/2,000 above 1), E 0.79–1.66.
- **Framing.** `report.md:29` presents the 16-start grid (W 0.185 vs 0.118) as a fitting choice interacting with
  seeds. Since the 64-start fits are at the optimum and denser grids do not change them, the 16-start widening is
  the sparse grid stopping in worse local optima. Say so; do not present it alongside Huber δ as an equivalent choice.

### 5. MINOR (pass) — ladders, width and seed bootstrap

- **Checked.** `fit.py:98–99` draws one seed per size without replacement within size; n-seed ladders average per
  (size, step) (`fit.py:80–88`); W is the 5th–95th range (`fit.py:102–103`). `refit_N.py` replays the RNG and
  reproduces the saved draws and W₃. The pseudo-seed mapping (`fit.py:131–140`) is a valid cluster bootstrap over
  seeds within size. Monte Carlo noise of a 500-ladder replicate with no seed resampling: W₁ in 0.116–0.130, W₃ in
  0.101–0.105, shrinkage 0.11–0.21 (SD 0.025), so the reported intervals (W₁ 0.038–0.160; shrinkage −0.10 to 0.81)
  are dominated by seed resampling and do reflect only 10 seeds per size.
- **Verdicts.** Inconclusive on both hypotheses is fair under the preregistered rules. With the preregistered N, W₁ =
  0.103 and the outlier-free subset gives 0.050, straddling the 0.05 bar, so H1 will stay Inconclusive after the fix;
  the corrected shrinkage (0.115 on 1,000 draws) keeps H2 Inconclusive. Re-run the bootstrap anyway (Finding 1).

### 6. MINOR (supported, two sentences to add) — the "two unstable runs" story

- **Checked.** The 410M seed explains 73% of the forecast variance across the 2,000 ladders; ladders using 410M seed
  3 or 4 have median forecasts 1.856 and 1.843 against 1.762–1.772 for the other eight seeds
  (`table_checks.json`, `pred_by_seed_at_size`). `spike_check.csv` shows neighbouring checkpoints agree (seed 4:
  2.43/2.42/2.41 at 141k–143k; seed 3: 2.18/2.17/2.17 around 100k) and the batch-1 re-evaluation reproduces the
  seed-4 loss to all printed digits. The 14M/31M late rises do not drive the residual width: also excluding the two
  worst late risers at 14M (seeds 4, 7) and 31M (seeds 5, 7) leaves W₁ at 0.058 (n = 1,031). The residual 0.051 is
  driven mostly by the 31M seed (43% of residual variance), and specifically by seed 0, the original Pythia-31m,
  whose forecasts are low (median 1.752) because it is the one 31M run with no late rise.
- **To add.** (a) At 14M and 31M the original seed 0 is monotone while 8/9 and 7/9 of the new seeds rise late by up
  to 0.43 nats (`late_rise_final_minus_min`), so "known saturation" (line 73) is a hypothesis; the seed-0 exception
  should be stated. (b) The PolyPythias paper's abstract says the extra seeds let the authors identify outlier
  training runs; the report should cross-reference its two 410M runs to the paper's outliers rather than present them
  as a new observation. (c) Replace "Most of that comes from just two training runs" with the measured share (73%).

### 7. MINOR — post hoc exclusion presented as a lesson

- **Evidence.** The 0.051 is legitimately computed (`posthoc.py:26–30`; a 1,578-ladder subset of the preregistered
  draws, reproduced). But `report.md:44` ("The practical lesson is to ... drop or rerun unstable ones, rather than
  trusting averaging") is a prescription drawn from a selection on the outcome, and `overclaim_check.md` row 34 labels
  it Supported. The body (line 115) hedges correctly; the plain-terms section and title do not say the exclusion is
  post hoc.
- **Fix.** In plain terms: "In this data, dropping the two runs ... would have cut the spread to about 0.05; whether
  inspecting curves beats averaging in general was not tested." Re-label row 34 Exploratory-labelled. Note that
  median-across-seeds aggregation, the obvious robust alternative, was not run (already stated at line 116; keep).

### 8. MINOR — gates

- **G5** passes mechanically but is not fully honest: rows 22, 34 and 35 are labelled Supported on backing that
  does not establish the causal or prescriptive content (Findings 2 and 7). Re-label and rewrite after the re-fit.
- **G6** passes (`attribution.py check . --show`: 6 claims; Q1–Q4 resolve by arXiv id to matching titles). Spot
  checks: Q1 matches the abstract; Q6 (1.4B − 2.8B gap 0.090) recomputed as 0.0900; Q5 is correctly marked an
  absence claim from the lead's search.
- **G1 (missing).** No leakage audit. The Pile validation split is held out by construction, but train/validation
  near-duplicates in the Pile are documented in the literature, and larger models memorise more, so contamination
  would lower the 2.8B target relative to the ladder and contribute to an apparent overshoot. State it as a
  limitation; it cannot be quantified without the training set.
- **G2** passes: no fit is dropped (2,000 rows), none fails (Finding 4), no silent fallback.
- **G3** fails as stated: the overshoot's plausibility rests on N (Findings 1–2).

### 9. MINOR (process) — deviation recorded after the results it affected

- D2's batch-size change happened at 16:40 on 2026-10-24 (`evaluate.py` mtime; OOM in `evaluate_fp32.log`) and
  was recorded at 01:36 on 10-25, after the fits, contrary to `plan.md` §6. Harmless: batch size does not change the
  loss (Finding 6). Order of the rest is verified: plan 02:08 → corpus 02:11 → fit code 03:33 → D1 07:55 → fp32
  evaluation to 18:02 → fits 18:05–00:52 → `spike_check.py` 00:56, `posthoc.json` 01:06, `spike_check.csv` 01:34
  (mtimes; all post hoc files sit in the same commit as `primary.json`, so git alone cannot show the order).

### 10. NITS

- `figures.py:80` / `F2_extrapolation.txt`: "values above 2.3 are clipped" — the largest forecast is 1.88; nothing is
  clipped. Remove.
- `report.md:39` "7 times larger": 7.5× on the table's N, 8.3× non-embedding, 6.8× total. Pick one and say which.
- `deviations.md` D1 table values (200 sequences) sit about 0.33 above the full-corpus values; say the subset is the
  first 200 sequences, or quote the full-corpus numbers (70M seed 0 final: bf16 4.12, fp32 2.63).

## What was not done

- The seed bootstrap and the procedure decomposition were not re-run under the corrected N (about 7 core-hours
  each); the verdict expectations in Finding 5 are inferred from the point estimates. The 3-seed corrected fit used
  the first 1,000 of the 2,000 draws, and the total-N fit the first 500.
- The PolyPythias full text was not read; the cross-reference in Finding 6(b) rests on its abstract.

---

# Confirmation pass — 2026-10-28 (commit 0e3b0ab)

## Verdict: PUBLISH WITH EDITS (three small edits, none changes a number in the headline or verdict block)

### Checked against each finding

1. **N (major) — fixed and verified.** `code/fix_n.py` recomputes N from the HF configs as L(12d²+13d)+2d and asserts
   the old N equals this plus one 50,304×d head before overwriting; `n_params.csv` matches my `check_params.py` for
   all eight sizes. `evaluate.py:69` now excludes `embed*` and `lm_head`. Only the N columns changed in `losses.csv`
   (405 rows; losses and D identical to the committed v1; `N_with_head` equals the old N). The re-run
   `ladders_single.csv` matches my corrected-N refit (`refit_n1_preds.csv`, `pred_nonemb`) to 0.0 on all 2,000
   ladders; W₁ 0.1025, W₃ 0.0925 (my 1,000-draw estimate 0.092), total-N sensitivity 0.160 / +0.017 / 67% (my
   500-ladder 0.155 / +0.017 / 67%). Bootstrap and procedure decomposition were re-run (mtimes 06:39–17:04); v1
   tables kept in `results/tables/v1_pre_review/`; D3 recorded.
2. **Overshoot attribution (moderate) — fixed.** "Reflects the fitting form" and "the formula itself was biased" are
   gone (report lines 23–29, 49–51, 143–150). Both conventions are stated, E's 5th percentile 0.16 is stated, and the
   three candidate causes are listed. G5 rows 19, 23, 36 rewritten.
3. **Evaluation noise (minor) — fixed in the report, one bug in the script.** Report lines 127–132 quote the paired
   SDs. But `code/posthoc_review.py:37–38` loads `pythia-2.8b_step143000.npy`, which is the pre-D1 **bf16**
   per-sequence file (mean 1.7097), not `pythia-2.8b_step143000_float16.npy` (mean 1.7038, the target used
   everywhere else). Evidence: the stored `mean_difference` values −0.2704 and −0.0842 equal 1.7097 − 1.9800 and
   1.7097 − 1.7939; with the fp16 file they are −0.276 and −0.090. The SDs are unaffected (my fp16-based values:
   0.0076 and 0.0026, `table_checks.json`), so no report number changes beyond possibly 0.0027 → 0.0026. **Edit A:**
   point the script at the `_float16` file, re-run it, and refresh `posthoc_review.json`.
4. **16-start grid (minor) — fixed** (report lines 117–125; now framed as a sparse grid stopping in worse optima).
5. **No change needed — confirmed.** Corrected-N verdicts are both Inconclusive, as predicted: W₁ CI 0.041–0.119
   straddles 0.05; shrinkage CI −0.13 to 0.81 straddles 0.5.
6. **Two unstable runs (minor) — fixed and corroborated.** (a) Seed-0 exception stated (lines 82–87); the late-rise
   figures match `posthoc_review.json` (14M: all nine new seeds, up to 0.431; 31M: seven of nine, up to 0.282).
   (b) I fetched the paper's HTML: §3 identifies 410M seeds 3 and 4 as the only two runs outside its outlier
   threshold (a downstream-accuracy criterion on final checkpoints; the authors note a formal test would need more
   tasks), and §5 characterises them by loss spikes and forks in their training maps. Q7 is therefore supported.
   The paper itself attributes the small models' mid-training downstream drops to saturation, citing Godey et al.,
   which supports the report's hypothesis framing. (c) Variance share 77% recomputed under the corrected N; the
   per-seed medians in the report match `posthoc_review.json`.
7. **Post hoc exclusion (minor) — fixed.** Plain terms now say "In this data ... was not tested"; G5 row 32 is
   Exploratory-labelled, as are rows 13 and 21.
8. **Gates.** G5: `overclaim_check.py --verify` passes (36 rows); labels are now honest. **Edit B:** two backing
   cells still quote first-run numbers — row 17 ("W3 0.103 vs W1 0.123") and row 34 ("shrinkage 0.16 (−0.10 to
   0.81)"); update to 0.093 / 0.103 and 0.10 (−0.13 to 0.81). G6: `attribution.py check` passes, 8 claims; Q7 and Q8
   resolve to the right titles, and Q7's content is corroborated above. G1: limitation stated (lines 148–150). G3:
   `results/plausibility.md` present and consistent with the tables.
9. **D2 timing — noted** in `deviations.md` (lines 34–35).
10. **Nits — fixed:** clipping sentence removed from `figures.py` and the F2 caption; "about 8 times the parameters"
    (8.33× non-embedding); D1 table note added.

### Every number in the revised report checked against the tables

Title/verdict: W₁ 0.103 (0.041–0.119); 77%; medians 1.844/1.831 vs 1.757–1.765; 1,578 and 0.050; shrinkage 0.10
(−0.13 to 0.81); W₃ 0.093; W₅ 0.077; overshoot 100%, +0.061; total-N +0.017, 67%; E p5 0.16; decomposition 85/4/11.
Table: 0.091/+0.060; 0.093 (0.016–0.102)/+0.059; 0.077/+0.066; 0.050/+0.058; 0.084/+0.119; 0.021/+0.121;
0.160/+0.017. Secondaries: 1B +0.055 (0.070), 1.4B +0.066 (0.081); α 0.086/0.104/0.138, β 0.786/0.881/1.059;
total-N α 0.20/0.25/0.30; procedure widths 0.101/0.106/0.104/0.106/0.114; final-only 0.607/−0.029; paired SDs
0.0076/0.0027; seed SDs and 0.010 unchanged. All match `primary.json`, `posthoc.json`, `posthoc_review.json`,
`sensitivity_total_n.json`, `n_params.csv`.

### Edits before publishing

- **A.** `code/posthoc_review.py:37–38`: use `pythia-2.8b_step143000_float16.npy`; re-run; refresh the JSON (and
  the report's 0.0027 if it becomes 0.0026).
- **B.** `review/overclaim_check.md` rows 17 and 34: replace the first-run backing numbers.
- **C.** `report.md:168–169`: replace "confirmation pass to follow" with the confirmation outcome.
- Optional: the post hoc 64k-cut 3-seed width of 0.021 (shrinkage 0.75, `posthoc.json`) sits in the table without
  comment; one sentence noting it is post hoc and untested would help, and the Q7 sentence could add that the
  paper's outlier criterion is downstream accuracy at the final checkpoint.

### Not independently verified

- The paper's appendix (loss-spike steps) was beyond the fetched text; §3 and §5 were read.
