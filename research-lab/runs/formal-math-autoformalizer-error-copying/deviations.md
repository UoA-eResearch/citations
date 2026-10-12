# Deviations from the preregistration (plan.md, commit 9afb62b)

## D1 - 2026-10-12 10:50 NZDT - implementation of the Lean checks and the candidate build (before any filter result was seen)

Logged while the Lean filters (plan 2.2) were running, before any result had been read. Only the three smoke-test
pairs had been checked.

1. **How statements are elaborated** (`code/lean_check.py`). certify.py wraps both statements under one fixed header
   (`open BigOperators Real Nat Topology Rat`). That header breaks ProofNet statements, which rely on other namespaces
   (`Filter`, `Metric`, `Subgroup` and others). So:
   - each statement is elaborated as `def stmtX : Prop := ∀ binders, concl` in its own section, under its own `open`
     lines;
   - a snippet with no `open` lines (a model output, say) gets the item's default opens: the defective reference's
     header;
   - the implication test is `theorem chk : stmtA → stmtB := by unfold stmtA stmtB; intro h; intros; <portfolio>`.

   The portfolio, the 20 s limit, the axiom check, autoImplicit off and π as Real.pi are certify.py's.
2. **Universes.** `Type*`, `Type _` and `Type u` are read as `Type`, so that both sides of an implication quantify
   over the same universe. Otherwise `apply h` fails on a universe mismatch, whatever the statements say.
3. **The truth screen (plan 3.1, check 5)** is `¬ stmt`, tried by a negation portfolio:
   - `push_neg; simp_all; done`;
   - `push_neg; norm_num`;
   - `decide`;
   - `simp_all; done`;
   - `aesop`.

   "Truth certified" (plan 8) means that `stmt` is proved by `simp_all; done`, `norm_num; done`, `decide`,
   `linarith`, `nlinarith` or `aesop` after `intros`.
4. **Parsing.** The last `theorem`, `lemma` or `example` in a snippet is used. Its statement ends at the first
   top-level `:=` after the binder colon, so any proof is ignored.
5. **Candidates** (`code/candidates.py build`). The normalisation compares binders and conclusion as parsed, and maps
   `∑ x in` to `∑ x ∈`. This gives:
   - **miniF2F:** 228 changed of 488. The 253 in the pre-plan notes came from a cruder string normalisation.
   - **ProofNet:** 147 changed of the 369 matched pairs. Two of DeepSeek's 371 items have no ProofNet# match at
     difflib ratio ≥ 0.8.
   - **Controls:** the 8 audit items with `v2_miscorrection = true`.
6. **Python environment:** the contamination run's venv (`../formal-math-certified-contamination-did/venv`). It has the
   same pandas and the same Lean REPL client.

## D2 - 2026-10-12 10:56 NZDT - implementation of the twins, sampling and classification (before any tag was read)

Written while the 16 rater subagents were running. No tag file had been opened.

1. **Twins and paraphrases for the one-rater set.** They are built for the items in the one-rater set as well as the
   included ones, because the plan's one-rater sensitivity analysis (section 8) needs them.
2. **Controls.** The 8 negative-control items are sampled in condition O only. They have no twin and no paraphrase.
3. **Twin builder** (`code/prompts/twin.md`, `code/twins.py`).
   - Claude Opus 5.5 subagents, in batches of 20.
   - Check 3 compares token sequences (numerals, words and single symbols). Every changed token must be a numeral,
     except where the twin side contains the declared answer span.
   - Check 4 runs the builder's script (60 s limit) and compares its last line of output with the declared answer.
   - Check 5 uses the negation portfolio of D1.
   - A failed twin may be rebuilt once (plan 3.1).
4. **Paraphrases** (`code/prompts/paraphrase.md`, `para_judge.md`).
   - They are written by Claude Opus 5.5 subagents.
   - They are judged by Claude Fable 5.1 subagents. The original and the paraphrase are shown in a seeded random
     order, 40 per batch.
5. **Sampling** (`code/sample.py`). An OpenAI-compatible vLLM server is used, as in the contamination run.
   - Each item and condition gets one request for 16 samples (`n = 16`, temperature 0.8, top_p 0.95, seed 20261012)
     and one greedy request.
   - Up to 32 requests are in flight at a time.
   - Herald uses the completions endpoint with its repository's DeepSeek-format string.
   - Qwen's three examples go in a single user turn, under "Examples:".
   - The run aborts if early outputs show byte-level BPE artefacts (the contamination run's D7 safeguard).
6. **Tokenizer check before sampling.** Each model's tokenizer is checked inside the vLLM image to round-trip a Lean
   statement with Unicode, before it is sampled. This is the contamination run's D5/D7 failure mode, and Herald (a
   DeepSeek-Math base) is at risk. A failed tokenizer is fixed as in that run (`tokenizer_class:
   PreTrainedTokenizerFast`), and the fix is logged.
7. **Extraction and classification** (`code/classify.py`).
   - Any `<think>` section is dropped first.
   - If the last code block is unterminated (a truncated output), the text after the last fence is used.
   - The reverse direction (D → O, C → O) is tested only when the forward one holds.

## D3 - 2026-10-12 10:58 NZDT - Herald's tokenizer repaired before sampling (D2 item 6)

**The failure.** Under the transformers version in the vLLM image, Herald_translator's `tokenizer_config.json`
(`LlamaTokenizer`, `legacy`) does not round-trip a Lean statement. It drops the spaces and the non-ASCII symbols:

`theoremmy_favorite_theorem(x:)(h:0<x):kFinset.Icc112,x^k2*:=bysorry`

This is the contamination run's D5/D7 bug.

**The fix.** As there, `tokenizer_class` is set to `PreTrainedTokenizerFast` (the original is kept as
`tokenizer_config.orig.json`).

**Checks after the fix** (`code/tokcheck.py`, `code/tokcheck_bos.py`, run in the vLLM image):

- All five tokenizers round-trip the test statement exactly.
- Herald's encoder still prepends BOS (`<｜begin▁of▁sentence｜>`, id 100000).
- Its generation config ends on id 100001, while the tokenizer's eos is `<|im_end|>` (id 100002). Herald's requests
  therefore stop on either (`stop_token_ids`).

No model had been sampled.

## D4 - 2026-10-12 11:16 NZDT - format pilot (no catalogue item sampled)

The pilot (`code/run_gpu.sh pilot`) sampled each model on six miniF2F and ProofNet items that are *not* in the
catalogue: pairs whose v1 and corrected statements are identical. It checked extraction and finish reasons only; no
output was classified. The owner's `vllm` container was restarted when the pilot ended (11:16:32).

| Model | Statements extracted (of 102) | Truncated at the token limit |
|---|---:|---:|
| Kimina | 102 | 0 |
| Goedel | 102 | 0 |
| Herald | 102 | 0 |
| Qwen | 99 | 0 |
| DeepSeek-Prover-V2 | 88 | 16 |

DeepSeek-Prover-V2 writes a long explanation before the statement. Its limit is therefore raised from 2,048 to 4,096
new tokens; its server's context is 6,144. The other models keep the plan's limits.

## D5 - 2026-10-12 11:22 NZDT - check 3 tokenizer fixed (before any twin check was run)

The builder of twin batch 00 reported a defect in check 3's tokenizer (`twins.TOK`). Its pattern `\w+` reads a
digit that follows letters or an underscore as part of the word. A digit-only change inside LaTeX (`x\leq15` →
`x\leq20`, `\log_8` → `\log_4`) then counts as a non-numeral change. Plan 3.1 and the builders' instructions
allow such changes ("digits, including digits inside LaTeX").

The word pattern is now `[^\W\d]+`, so digits are always separate tokens. Subscripted hypothesis names such as
`h₀` are unaffected: subscript digits are not decimal digits. The fix was made before `twins.py diffcheck` or any
Lean check had run.

The builders reported 63 twins built and 72 items skipped, most for having no numerical parameter (the ProofNet
items, chiefly).

**D5, addendum (same session, after the Lean twin checks).** One twin (t164) failed check 3 for a second mechanical
reason. difflib aligned the repeated numeral 3 across positions (\`x % 3 = 2\` → \`x % 7 = 3\`) and reported a spurious
insertion and deletion of \`=\`. When the two token sequences have the same length, check 3 now compares them position
by position, and it falls back to difflib otherwise. The twin's edit is numerals-only (σ: 2→3, 3→7, 14→24). No model
had been sampled.

## D6 - 2026-10-12 13:21 NZDT - informativeness check on the defective references (before any outcome was computed)

Added after sampling and during the Lean classification, before `analysis.py` had been run or any classification
row had been tabulated by class. Only extraction rates, finish reasons and elaboration rates had been looked at.

**The problem.** The copy test certifies O → D and D → O with a tactic portfolio. If D is itself proved outright by the
portfolio (a weakened conclusion that has become easy, say), any output the portfolio can prove is certified
equivalent to D, and "equivalent to D" no longer means "copies D". If D is refuted, D → O can hold by explosion. The
contamination run met the same problem and added informativeness and explosion guards (its D3, D9). The plan has no
such guard.

**The check** (`code/refcheck.py`). Each primary item's D and C (and, for items with a twin, D′ and C′) is tested with
`lean_check.provable` and `lean_check.refuted`, the portfolios already used for the twins' truth screen (D1 item 3).
Results go to `results/catalogue/refcheck.jsonl`.

**Its use.** It is a sensitivity analysis only (`secondary.json`, `informative_refs`): the primary rate ratio
recomputed on the included items with a twin whose D and D′ are neither proved nor refuted (a reference whose check
errors counts as uninformative). The preregistered verdict is unchanged. The report gives both.

**D6, timeline (added after the independent review, issue 10).** "Before any outcome was computed" needs the facts
behind it:

- **When the data existed.** The classification files of the three primary models were complete well before D6:
  `data/classified/kimina.jsonl` at 11:44, `goedel.jsonl` at 11:58 and `herald.jsonl` at 12:05. D6 was written at
  13:21.
- **What had been read from them.** Before D6, only the `error`, `elab` and timing fields (13:18). Four randomly drawn
  non-elaborating Herald outputs were also printed, to check that their failures were genuine. No `copy` or `correct`
  field had been tabulated or displayed.
- **What prompted it.** While drafting the methods, I asked how the certifier could misclassify. That question, and the
  contamination run's informativeness and explosion guards (its D3, D9), led to the check.
- **Verifiability.** None of this can be verified from the logs. The session transcript is the only record.
- **Effect.** The check changes the primary rate ratio from 0.91 to 0.93.

## D7 - 2026-10-12 13:30 NZDT - exploratory analyses added after the outcomes were seen

Added after `analysis.py` had produced the preregistered results. None changes the verdict, and the report labels them
exploratory.

1. **All three conditions on the same items.** The plan's O vs P comparison (section 8, item 2) uses the 129 included
   items with a paraphrase. Only 59 of them have a twin, so O, T and P are also compared on those 59 items
   (`secondary.json`, `exploratory`): O vs P and P vs T.
2. **O vs P by model**, for the same reason: the O vs P excess turned out to come from two models.
3. **The classification figure** (`classes.png`) is drawn from a new table, `classes_twin_items.csv`, on those 59
   items. The preregistered table, `classes_by_model_condition.csv`, pools different item sets across conditions
   (originals of all 129 included items, twins of 59), so its condition shares are not comparable.
4. **The count of items with any defect output.**
5. **The three twins the builders flagged dropped** (`flagged_twins_dropped`). Two were flagged as borderline (t237,
   t262); in one, D′ became true while D was false (t284). All three passed the mechanical checks and are in the
   primary set.
   - **Where the flags came from** (added after the review, issue 12). The builders raised these flags in their
     replies before sampling. The replies are in the session record; the committed `defect_rule` fields describe the
     twins but do not flag them.
   - **When the analysis was decided.** Running this sensitivity was decided after the per-item results had been seen.
     So was the "clearer paraphrases" reading of the O vs P result.

**Released outputs** (plan 10). The raw model outputs and the per-output classifications are released gzipped in
`results/outputs/` and `results/classified/`, because `data/` is not tracked.

## D8 - 2026-10-12 15:46 NZDT - analyses requested by the independent review (after the outcomes)

The review (`review/review.md`, fix first, 17 issues) asked for the analyses below. All come after the outcomes, are
exploratory, and leave the preregistered verdict unchanged. Code: `code/review_analyses.py` and `code/recheck_near.py`.
Tables: `results/tables/review/`.

1. **Port-header fingerprint** (issues 1 and 6). This is the share of extracted outputs on ProofNet items whose `open`
   lines include every `open` line of the item's ProofNet Lean 4 port header. It is broken down by model, condition,
   item set (with or without a twin) and split. A companion table, `header_by_textbook.csv`, shows which textbook's
   header Kimina emits.
2. **Per-item O/T/P table on the 59 primary items** (issues 2 and 3), pooled and by model. It comes with O vs P by
   model on those items.
3. **D6 applied to the 129-item O vs P set** (issue 9). The analysis drops items whose D is portfolio-provable or
   refuted, and logs the outputs certified equivalent to both references. Plan 5 says such outputs are logged and
   counted as "other". All 97 are on Rudin 1.1a, whose D and C are both portfolio-provable, and none is in the primary
   set.
4. **Greedy and verbatim counts for P on the 59 items** (issue 11). The report quoted them, but `secondary.json` holds
   them only for the 129-item set.
5. **Missed equivalences** (issue 7).
   - **Near-identical "other" outputs:** "other" outputs whose normalised statement has a difflib ratio of at least 0.9
     to the defective reference, counted by model and condition.
   - **Lean re-check:** a re-check of every unique "other" statement on the 59 items with a ratio of at least 0.8
     (674 statements). It uses a portfolio that first normalises both sides (`ring_nf`, `field_simp`, `simp only` with
     `div_div` and commutativity) and allows 40 s per direction.
   - **Sensitivity:** the primary ratio with the newly certified outputs counted as copies.
   - **Validation:** before the run, this portfolio was checked on the review's example from
     induction_sum_1oktkp1, `1 / (k + 1) / (k + 2)` against `1 / ((k + 1) * (k + 2))`. It certifies both directions
     where the preregistered portfolio certifies neither.
   - **Restart:** the first run was stopped after about a minute and restarted, because its output file had been moved
     by mistake while it was being written. No row of it had been read.
6. **Plan section 1's premise** (issue 17). The plan says Lean Workbook was "synthesized from miniF2F and ProofNet".
   More precisely, the dataset's statements are translated from contest problems. Its first-round translation model,
   however, was trained on all miniF2F and ProofNet statement pairs, both splits, the ProofNet pairs taken from
   `rahul3613/ProofNet-lean4` (arXiv 2406.03847, section 4.1). The premise that these benchmarks' formal statements are
   in the training lineage of open formalizers stands.
7. **Timeline** (issue 13). The study ran from 10:46 to 13:34 on 12 October 2026. Rater, twin-builder, paraphrase and
   judge subagents ran in parallel batches. GPU sampling overlapped with the Lean classification, which ran per model
   as each finished sampling. The report's methods sections were drafted during classification; its results sections
   were written after `analysis.py` ran.

**D8, addendum (after the confirmation pass, publish with edits).** The normalising re-check tested equivalence to D
only. The 16 newly certified statements were then also tested against the corrected reference, C or C′
(`recheck_near.py ctest`, `results/tables/review/recheck_near_C.jsonl`). None is equivalent to it, so plan 5's rule
(an output equivalent to both references counts as "other") changes nothing. `review_analyses.py` applies the rule
from that file.
