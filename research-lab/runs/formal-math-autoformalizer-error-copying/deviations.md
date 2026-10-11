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
