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
