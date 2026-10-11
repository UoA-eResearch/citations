# Deviations and implementation details

The plan (plan.md) was committed in 6bfdc63 at 2026-10-07 09:32 NZDT. Entries are timestamped with `date`.

## D1. Certification safeguards, defined before certification runs at scale (2026-10-07 09:42 NZDT)

A test on 16 retrieved pairs (benchmark × DeepSeek-Prover-V1) showed that the plan's tier logic can certify an
implication without using the hypothesis at all. If the conclusion side is provable by the portfolio on its own, then
"train ⇒ test" (or "test ⇒ train") holds for any training statement. Several "test ⇒ train" certifications for one
AM-GM item came from training statements that `aesop` proves alone. Three safeguards are therefore added
(`code/certify.py`):

1. **Self-provability.** Whenever an implication a ⇒ b is certified, b is also tried on its own with the portfolio
   (`simp_all`, `aesop`, `norm_num`, `linarith`, `nlinarith`; 20 s).
   - If b is provable alone, the implication is uninformative and does not count.
   - **L1** requires both directions to be informative.
   - **L2** requires train ⇒ test to be informative.
   - Benchmark items provable alone are reported as "automation-provable". They can be leaked only through L0.
2. **autoImplicit off.** Otherwise an undeclared variable in either statement would be auto-bound once at the outer
   level and shared between the two sides. Statements that need it are "unchecked".
3. **`π` read as `Real.pi`.** Under all of Mathlib with `open Real Nat`, a bare `π` is ambiguous. The vacuity study
   found this made 2.6% of rows fail.

Each side is first checked to elaborate on its own, so any error in the combined theorem is a failed proof.

**In the test.** Of the 16 pairs, 10 high-similarity pairs certified as non-trivial L1 equivalences; 2 were unchecked
(undeclared variables); and 3 "test ⇒ train" certifications were trivial.

## D2. Cap on numeral-only candidates, before certification (2026-10-08 12:03 NZDT)

Retrieval over the seven corpora gave 110,226 unique candidate pairs for the 488 miniF2F items. 85% of them are
numeral matches: statements with the same multiset of numerals that share half the item's identifiers. For simple
items the rule matches thousands of statements; one item matched 3,192 STP statements. Certifying them all would
take about 21 CPU-hours for miniF2F alone, almost all on unrelated pairs.

**The cap.** Numeral-only candidates are capped at 20 per benchmark item and corpus. They are ranked by the Jaccard
similarity of the identifier sets, then by corpus id, which is deterministic. L0 and MinHash candidates are not
capped.

**How many items it affects** (more than 20 numeral matches):

| Corpus | Items |
|---|---|
| Goedel-Pset | 79 |
| STP | 75 |
| SFT v2 | 73 |
| NuminaMath-LEAN | 29 |
| Lean-Workbook | 26 |
| Goedel's Lean-workbook-proofs | 8 |
| DeepSeek-Prover-V1 | 2 |

**What this may miss.** A certified equivalent that shares an item's numerals but has low character overlap and
falls outside the top 20. Such misses would understate the leak rate.

**Retrieval results seen so far:** counts only (`results/tables/retrieval_counts.csv`). STP has 174 miniF2F items
at L0, Goedel-Pset 10, NuminaMath-LEAN 5 and Goedel's Lean-workbook-proofs 1. No certification has been run except the
16-pair test in D1.

## D3. The D1 informativeness guard replaced, before any prover sampling (2026-10-08 14:36 NZDT)

**What was found.** A spot-check of certified L2 pairs (miniF2F × Goedel-Pset and × NuminaMath-LEAN) found
implications that cannot reflect the same problem. Examples:

- a training statement that 8^2012 % 10 = 2 "implies" the test statement (k² + 2^k) % 10 = 6 with k = 2008² + 2^2008;
- one closed fraction computation "implies" another.

The D1 guard missed these for two reasons:

1. It tried a *smaller* portfolio on the conclusion alone than the implication check uses, so a conclusion provable by
   `simp_all` with an extra hypothesis present looked non-trivial.
2. It failed open: a timeout counted as "not provable alone". Timeouts were frequent for about 20 minutes while two
   certification runs (44 workers) competed for 24 cores, after an interrupted restart.

The spot-checked L1 pairs were genuine: the same problem with renamed hypotheses or a reworded conclusion.

**New guard** (`code/recheck.py`). For every certified implication a ⇒ b, the *identical* command is rerun with a
replaced by `True`, with the same portfolio and a 60 s limit, on uncontended cores.

- If it succeeds, or times out, the certificate does not depend on a. The implication is not informative and does
  not count (fail-closed).
- **L1** requires both directions informative. **L2** requires train ⇒ test informative.
- The D1 flags are kept in the data but no longer used.

**Status.** No prover output has been generated beyond the D-pilot (truncation only; next entry), and no proof has
been verified. The secondary-benchmark certification is paused and will resume after the recheck.

## D3a. The D3 recheck also failed open; replaced by a hypothesis-free portfolio (2026-10-08 14:41 NZDT)

The D3 recheck (14:37-14:40) still counted closed arithmetic facts as L2 leaks. For example, the training statement
1 + 1/(1 + 1/(1 + 1/(1 + 1/2))) = 8/5 "implied" the test statement 1 + 1/(1 + 1/(1 + 1)) = 5/3.

**The cause.** With the hypothesis replaced by `True`, `simp_all` clears `h : True` from the context, so the
portfolio's `nlinarith [h]` branch fails on an unknown identifier. A conclusion that `simp_all` plus `nlinarith`
proves on its own therefore looked informative.

**The fix.** The counterfactual is now the conclusion on its own, with no hypothesis, under every hypothesis-free
branch of the certification portfolio plus `norm_num`, `linarith`, `nlinarith` and `decide` (60 s;
fail-closed). This is at least as strong as anything the certification portfolio could do without the training
statement. The D3 outputs are kept in `data/certify/recheck_D3_true_variant/`.

No prover sampling or verification has taken place.

## D3b. Explosion guard: implications from refutable training statements do not count (2026-10-08 14:45 NZDT)

After D3a, a spot-check of Goedel-Pset L2 pairs still found unrelated statements. Each training statement was false,
for example "∀ a : ℝ, a = 0" and "n = 20 → n − 2 = 18 → 18 + 1 = 19 → n − 18 = 1". `simp_all` or `aesop` derives
a contradiction from the false hypothesis and then proves the benchmark statement by explosion. This was checked
branch by branch in Lean on three pairs. Goedel-Pset contains false formalisations, as other autoformalised corpora
do.

**The extra condition.** An implication a ⇒ b counts only if a is not refutable: `(∀ a) → False` must not be provable
by the certification portfolio within 60 s. A refutation or a timeout makes the implication uninformative
(fail-closed). For L1 the same applies in the other direction.

The D3a outputs are kept in `data/certify/recheck_D3a/`. No prover sampling or verification has taken place.

## D4. Leak tiers final; sampling plan and minimum detectable effect, before main sampling (2026-10-08 14:52 NZDT)

**Leak tiers for the 488 miniF2F items** (D1-D3b; `results/tables/leak_rates.csv`, `leak_pairs_bench_minif2f.csv`):

| Corpus | Items leaked (L0/L1/L2) | Share |
|---|---|---|
| STP_Lean_0320 | 179 (174 / 3 / 2; 173 of the 174 L0 items are validation items) | 36.7% |
| Goedel-Pset-v1 | 67 (10 / 36 / 21) | 13.7% |
| SFT_dataset_v2 | 61 (0 / 31 / 30) | 12.5% |
| NuminaMath-LEAN | 55 (5 / 37 / 13; the 5 L0 items are all test items) | 11.3% |
| DeepSeek-Prover-V1 | 16 (0 / 15 / 1) | 3.3% |
| Goedel's Lean-workbook-proofs | 10 | 2.0% |
| Lean Workbook | 0 | 0% |
| Any corpus | 252 | 51.6% |

69 items are automation-provable.

**Leaked (item, prover) pairs against each prover's own corpora:** Goedel-Prover-V2 99, Kimina 55, DeepSeek-Prover-V2
16; 170 in all. Every one has at least one certified reformulation in its prover's environment.

**The pilot** (13:06-13:39 NZDT, 8 October). 20 items, 8 samples per version, at the plan's 4,096-token cap. **No
pilot output was verified or scored.** Only finish reasons and lengths were read. Truncated outputs:

| Prover | Truncated |
|---|---|
| DeepSeek-Prover-V2 | 24% |
| Goedel-Prover-V2 | 44% |
| Kimina | 36% |

The model cards recommend 8,192 (DeepSeek), 8,096 (Kimina) and 32,768 (Goedel) tokens. Throughput implies that the
plan's full design (488 items × about 2.7 versions × 32 samples × 3 provers) would take about 35 GPU-hours at 4,096
tokens and 45 or more at 8,192. That is a long outage of the lab owner's shared vLLM service.

**Sampling plan.**

1. **Token cap: 8,192** for all three provers, close to the DeepSeek and Kimina model cards. Goedel's documented
   32,768 is not affordable, so some of its outputs will still be truncated. Truncation is treated identically
   across versions, so the DiD is not biased by it.
2. **Items per prover:**
   - every own-leaked item;
   - **150 clean items** drawn at random (seed 20261008) from that prover's clean items with a certified
     reformulation.

   The leaked arm dominates the DiD's variance, so dropping clean items costs little precision. **pass@32 is kept.**
3. **Secondary, pre-specified now: the STP prover** (kfdong/STP_model_Lean_0320, revision ae7751cc).
   - Its own corpus, STP_Lean_0320, holds 179 leaked items, nearly all miniF2F-valid statements verbatim.
   - All 488 items, 32 samples per version, completion-style prompt as in STP's corpus.
   - Temperature 1.0, top-p 0.95, at most 2,048 tokens.
   - Analysed separately and not pooled into H1.
4. **Verification** uses all of Mathlib, with bare `π` read as `Real.pi` in both statement and proof (as in D1).
   Lean 4.9 serves DeepSeek, Goedel and STP; Lean 4.15 serves Kimina.

**Minimum detectable effect (plan section 5), recorded before sampling.** With n_leaked = 170 and n_clean = 450:

  MDE = 2.49 × 0.30 × sqrt(1/170 + 1/450) = **6.7 pp**

That is at most 10 pp, so all three verdicts remain reachable.

## D5. STP tokenizer configuration fixed; the first STP outputs discarded unverified (2026-10-08 14:59 NZDT)

**The problem.** STP's released `tokenizer_config.json` declares `LlamaTokenizer`, a SentencePiece class, but its
`tokenizer.json` is DeepSeek's byte-level BPE. Loaded that way:

- prompts were encoded to the wrong token ids;
- outputs were decoded as raw byte-level symbols ("Ġ", "Ċ").

The first 21 STP requests returned English prose instead of Lean tactics. They are kept as
`data/samples/stp_broken_tokenizer.jsonl` and are **not verified or scored**. The run was stopped after 90 seconds.

**The fix.** The local copy's `tokenizer_class` is set to `PreTrainedTokenizerFast`, which uses `tokenizer.json` as
released. The original is kept as `tokenizer_config.orig.json`.

- Checked on CPU: a prompt round-trips exactly, and the BOS token (100000) is added by the post-processor.
- STP is resampled in full after the three main provers (`code/run_gpu_stp.sh`), with the same restart guarantee for
  the owner's vLLM.

**Also.** The CPU chain (`run_cpu_main.sh`) was stopped and restarted from the edited script. bash had kept the old
copy open after the in-place edit. Every step resumes from its output file.

## D6. Memory safety net during verification (2026-10-10 01:28 NZDT)

Some proof checks make one Lean REPL grow to 11-16 GB. Together with the other workers this twice pushed the machine
to critically low memory. Claude Code then stopped background monitors, though no verification work was lost.

**Mitigations.**

- **Fewer, fresher REPLs.** Verification was restarted on 9 October with 10 workers instead of 22, and with REPL
  restarts every 40 commands (`VERIFY_MAX_CMDS`).
- **A watchdog** (`code/repl_watchdog.sh`, from 01:28 NZDT on 10 October). It kills any single REPL above 20 GB. The
  output being checked is then recorded as a failure, as a timeout would be.

**Which outputs it could affect.** DeepSeek-Prover-V2, Goedel-Prover-V2 and Kimina were fully verified before the
watchdog started. Only the STP verification (secondary) can be affected. Kills are logged in
`logs/repl_watchdog.log` and will be reported.

## D7. DeepSeek-Prover-V2 outputs invalid (tokenizer); resampled. The pooled result was seen first (2026-10-10 01:31 NZDT)

**What happened.** The first pooled analysis (01:30 NZDT, 10 October; `code/analysis.py --no-stp`) showed
DeepSeek-Prover-V2 at 0% pass@32 on every item and version. 14,407 of its 14,688 outputs had no extractable code.

**The cause** is the same class of bug as D5. Under the transformers version in the vLLM image, DeepSeek-Prover-V2's
`tokenizer_config.json` (`LlamaTokenizerFast`, `legacy`) loads a tokenizer that drops spaces and non-ASCII
characters. Prompts were therefore encoded wrongly: the model saw `theoremt(bhv:)(h:0<b0<h)…`. Outputs were decoded
lossily. The fix is the one used in D5 (`tokenizer_class: PreTrainedTokenizerFast`). With it the tokenizer
round-trips exactly, and the chat template yields BOS followed by the intact statement.

Goedel-Prover-V2 and Kimina (Qwen2 tokenizer) were checked the same way and are unaffected. The pilot did not catch
the problem because it read only lengths and finish reasons. `sample.py` now aborts when early outputs contain
byte-level artefacts.

**The invalid run** is archived in `data/invalid_D7/`, not scored, and DeepSeek-Prover-V2 is resampled in full
(`code/run_gpu_dsp.sh`).

**Disclosure.** The pooled analysis with the invalid DeepSeek-Prover-V2 rows was printed:

| | Value |
|---|---|
| DiD | +1.0 pp |
| One-sided 95% bounds | −0.9 to +3.0 pp |
| Goedel-Prover-V2 alone | +1.0 pp |
| Kimina alone | +1.2 pp |

The secondary analyses were printed too, and the STP rows were excluded as incomplete. Nothing in the design changes
because of it: the resampled DeepSeek-Prover-V2 outputs go through the committed `analysis.py` unchanged.

## D8. Results; a correction to D6 (2026-10-11 12:29 NZDT)

**Runs.**

- The resampled DeepSeek-Prover-V2 run finished at 20:01 NZDT on 10 October, and the owner's vLLM was restarted
  automatically at 20:01:52.
- DeepSeek-Prover-V2 verification finished at 22:57.
- The committed `analysis.py` ran unchanged apart from the `--no-stp` switch, which this final run did not use.

**Primary result.** DiD = +1.33 pp, one-sided 95% bounds −0.75 to +3.50 pp; 170 leaked and 450 clean pairs.
**Refuted** under plan section 5. The STP secondary gives +3.5 pp (+1.0 to +6.2).

**Correction to D6.** D6 said only STP's verification could be affected by the 20 GB watchdog. The DeepSeek-Prover-V2
re-verification (D7) also ran under it.

| Verification | Watchdog kills (`logs/repl_watchdog.log`) |
|---|---|
| STP (1-5 a.m., 10 October) | 18 |
| DeepSeek-Prover-V2 (20:59-21:01, 10 October) | 4 |

Each killed check counts as a failed output. That is 4 of 14,688 DeepSeek-Prover-V2 outputs and at most 18 of 43,424
STP outputs.

**Rejection reasons, for the record.** All 869 of Kimina's "banned" outputs use `native_decide` in proof code, which
the plan bans. None was a commented `sorry`.

## D9. Fixes after the independent review (2026-10-11 13:29 NZDT)

The independent review of the draft (`review/review.md`, commit a1797f1) recommended "fix first". It found two bugs in
the leak certification and several problems with the analysis and the prose. Its recomputations already show many of
the numbers below (per-sample DiDs by prover, test-only and valid-only DiDs, the DiD with identical R1 dropped), so
none of the changes in this entry is blind to outcomes. The decision rule is unchanged. Every change is listed here,
and the analyses as first run (D8) stay in `results/tables_D8/`.

**1. Lean Workbook was never certified (bug).**

- `extract.py` appended `:= by` to Lean Workbook statements that already end in `:=  by sorry`. Every statement
  therefore kept `sorry`, all 1,915 miniF2F candidate pairs were "unchecked", and the reported "0 leaks" was an
  artefact.
- **Fix:** strip the suffix, then rerun retrieval, certification and the recheck for Lean Workbook on all four
  benchmarks.
- The buggy certification files are kept in `data/certify/lean_workbook_buggy/`.

**2. The explosion guard (D3b) let false training statements through (bug).**

- D3b claimed the guard caught the motivating example "∀ a : ℝ, a = 0". It did not. `(∀ a : ℝ, a = 0) → False` is
  not provable by the portfolio, because nothing instantiates the quantifier. In the implication, the benchmark's own
  binders supply the term. The reviewer found such pairs in the final leak list, for example `n = 320`, `a = 4` and
  `0 < n → Nat.Prime n → False`.
- **Two extra conditions.** An implication a ⇒ b now also requires:
  1. **Witness refutation fails.** a must not be refuted by instantiating it at small numerals (0, 1, 2, 3 and
     pairs), each closed by `norm_num`.
  2. **The negation is not certified.** a ⇒ (∀ binders of b, ¬ conclusion of b) must not be certified by the same
     portfolio. If both a ⇒ b and a ⇒ ¬b certify, a is inconsistent with b's binders.
- Timeouts count against the leak (fail-closed), as before.
- **Checked in Lean (Lean 4.9) on the reviewer's cases:**
  - "a = 0" and "n = 320" are refuted by witnesses;
  - "0 < n → Nat.Prime n → False" is refuted by a witness, and its negation implication also certifies;
  - a genuine leak (the same linear system with renamed hypotheses) is unaffected.
- The recheck is rerun for every benchmark and corpus. The D3b outputs are kept in `data/certify/recheck_D3b/`.

**3. Benchmark items.**

- **Automation-provable count.** It is now computed with the operative FREE portfolio on all 488 miniF2F items
  (`code/benchcheck.py`, 60 s each). The draft's "69" was D1's narrower flag.
- **Vacuous items are dropped from the DiD units.** These are items whose hypotheses are contradictory, certified by
  `exfalso` plus automation as in the vacuity study's v2 certificate. Example: `valid/mathd_numbertheory_35`, with
  `h₀ : ∀ n, n ∣ Nat.sqrt 196`. Any statement sharing such a hypothesis is "equivalent" to them, and every prover
  solves them.

**4. Reformulations.**

- **Identical R1 versions are dropped.** For 83 items without binders, R1 is textually identical to the original, so
  "R1" was the same prompt sampled twice.
- **Units without a genuine reformulation are dropped.** These are units whose only certified reformulation is an
  identical R1.

**5. Whitespace-only rejections.**

- **Re-checked.** Outputs rejected as "changed statement" are re-checked with a comparison that ignores spaces next to
  brackets, colons and commas (`code/reverify_ws.py`). Example: `v₁ )` in R2 against `v₁)` in the output.
- **Recompiled.** Those that then match are compiled exactly as in `verify.py`, and the new status replaces the old.

**6. Documented training on miniF2F-valid.**

- **The plan's mapping omits it.** The plan gave DeepSeek-Prover-V2 only its public lineage, DeepSeek-Prover-V1, as
  "own corpora". Both its papers document training on miniF2F-valid:
  - V1.5 (arXiv 2408.08152): SFT data;
  - V2 (arXiv 2504.21801): curriculum learning.
- **STP's paper (arXiv 2502.00212)** documents the same, consistent with its 173 verbatim valid statements.
- **The primary analysis keeps the preregistered mapping** with fixes 1 to 5.
- **Two analyses are reported alongside it, with equal prominence:**
  - **(a) Documented training:** every miniF2F-valid item counts as leaked for DeepSeek-Prover-V2 and STP.
  - **(b) Test items only:** every prover, since the valid split is probably trained on more widely. Goedel's
    clean-valid items are solved more often than its clean-test items.
- Analysis (a) changes which pairs are "clean", so it is not the preregistered contrast.

**7. Analyses added.**

- **Per-sample DiD by prover.** This secondary was preregistered pooled.
- **Solve-rate DiD by version.** R1 and R2 separately; descriptive.
- **The preregistered mixed logistic model.** It was missing from the draft:
  - specification: `success ~ reformulated × leaked + (1|item) + (1|prover)`;
  - fitted as a Bayesian binomial mixed GLM by variational Bayes (statsmodels `BinomialBayesMixedGLM`), because no
    Laplace or adaptive-quadrature GLMM is available in the environment.
- **Interval labels.** The 5th and 95th bootstrap percentiles are a 90% two-sided interval. The verdict uses only the
  one-sided bound.
- **The two MDE figures.** `mde.json` records 6.09 pp, computed from the 1,294 clean pairs before the 150-item
  subsample. D4 and the verdict use 6.72 pp.

**8. Prose.**

- **Scope of the verdict.** The pass@32 metric sits at a 100% ceiling for the leaked arms of DeepSeek-Prover-V2 and
  STP, so it cannot register degradation there. The verdict is scoped to "surface rewording, pass@32".
- **Sentences removed.** Those that claimed more than pass@32 can show are removed.
- **The L2 composition is stated.**
- **The selection of leaked items is stated.** Proof corpora contain only items their pipeline solved.
- **The prompt description is corrected.** It is the DeepSeek-Prover-V1.5 miniF2F header with each model's documented
  instruction, and it uses `maxHeartbeats 400000` where the cards use 0.
- **Retrieval recall and the unchecked share are quantified.**

**Timeline note.** `analysis.py` was committed (7657ea0) before the pooled analysis was first run. Some per-prover
verification files existed by then, so "before any verification result is read" is changed to "before the pooled
analysis was first run".

**The reviewer's sample.** One of the reviewer's re-check stages started while the fixed Lean Workbook certification
was being written. Its random sample of rejected pairs may therefore include some newly certified Lean Workbook pairs.
That affects only the reviewer's reproducibility check, not any study number.

### D9 addendum: guard audit and the vacuity portfolio (2026-10-11 16:00 NZDT)

**The fix chain finished at 15:55 NZDT on 11 October.** The new guards removed 27 pair-directions on miniF2F that the
D3b recheck had accepted:

| Corpus | Directions removed |
|---|---|
| Goedel-Pset | 16 |
| Goedel SFT v2 | 6 |
| STP_Lean_0320 | 3 |
| NuminaMath-LEAN | 2 |

None was gained. The reviewer had confirmed 11 spurious pairs, so each of the 27 was re-run with a per-condition
record (`code/d9_diagnose_flips.py`, `results/d9_checks/`). The negation test was also retried with a 300 s
timeout.

| Outcome | Directions |
|---|---|
| A kernel-checked proof rejects the direction | 27 |
| A timeout rejects the direction | 0 |
| The 300 s negation retry changes the result | 0 |

**What the rejecting proofs are.**

- **Witness refutation:** 20 directions. The training statement, or for the reverse direction the benchmark-side
  premise, is refuted outright by a numeral instance.
- **Negation proof:** 11 directions. The premise implies the negation of the conclusion for every value of its
  binders.
- These overlap, because some directions have both proofs.

**Where they come from.** The reviewer's 11 spurious pairs are among the 27. The rest are the same kind of pair: the
reviewer's prose named several of them. A few are new false Goedel-Pset statements, for example the pairs behind
`test/imo_1960_p2` and `test/induction_1pxpownlt1pnx`.

**The vacuity portfolio, as first written, found no vacuous item.** It missed `valid/mathd_numbertheory_35`. Two
reasons:

- the portfolio cannot instantiate a ∀-hypothesis;
- its branches did not have to close the goal, so `first` committed to a branch that made progress without closing
  the goal.

**The fix.**

- Every branch must now close the goal.
- Each hypothesis is also instantiated at 0 to 3, as in the explosion guard.

The portfolio now finds exactly one vacuous item, `valid/mathd_numbertheory_35`, and 82 automation-provable items
(80 + 2 timeouts in the reviewer's run). The first output is kept in
`results/d9_checks/bench_items_first_portfolio.csv`.

The pooled analysis has not yet been run on the D9 tiers.
