You are building number-perturbed "twin" problems for a preregistered research study on autoformalization (plan.md
section 3.1 in /mnt/citations/research-lab/runs/formal-math-autoformalizer-error-copying). Read the input file {IN}.
It holds items, each with:
- an informal statement N;
- a defective formal statement D (Lean 4, Mathlib), with the raters' description of its defect;
- a corrected formal statement C.

For each item, build ONE twin as follows.

1. **The substitution.** Choose a substitution σ of the problem's numerical parameters (the given numbers, not
   structural constants such as exponent 2 in "square" unless they are parameters). Apply σ consistently to N, D and
   C: a number that appears in all three changes in all three. Choose values that keep the problem well-posed, of
   similar difficulty, and with the same kind of answer (an integer stays an integer, a unique solution stays unique,
   a divisibility condition still holds). Change at least one number in N.
2. **The answer.** Recompute any stated answer, including the value of the correct choice in a multiple-choice problem
   (recompute the other choices by the same σ where possible), so that the corrected twin C' is TRUE. Write a short
   self-contained Python script (standard library, fractions, math, or sympy) that computes the twin's answer and
   prints it, and run it with: /mnt/citations/research-lab/runs/formal-math-certified-contamination-did/venv/bin/python
   (sympy may or may not be installed there; prefer the standard library).
3. **The analogous defect.** D' must carry the SAME defect as D, transferred to the new numbers. If the defect involves
   a number with no counterpart in N (for example a wrong constant), carry it over by the same rule (the same offset,
   factor or relation) and state the rule.
4. **Numerals only.** Outside one declared "answer span", the twin texts N', D', C' may differ from N, D, C ONLY in
   numerals (digits, including digits inside LaTeX). Keep every word, symbol, variable and hypothesis name. If the
   answer changes form (for example from 65 to 13/2 or to a square root), declare the exact substring of C' (and of
   D' and N' if needed) that holds the answer as answer_span; otherwise answer_span is null.
5. **When to skip.** If the problem has no numerical parameter that can be changed while keeping it well-posed and
   true (for example a purely structural statement), or the defect cannot be carried over, skip the item and say why.

Write a JSON array to {OUT}, one object per item in input order:
[{"id": "...", "skip": null, "sigma": {"30": "42", "6.5": "7.5"}, "N_twin": "...", "D_twin": "...", "C_twin": "...",
  "answer_script": "...", "answer_value": "...", "answer_span": null, "defect_rule": "..."},
 {"id": "...", "skip": "reason", ...}]
D_twin and C_twin are the full formal statements in the same format as D and C (same theorem name, same proof stub).
Make sure the file is valid JSON. Then reply with one line: items written, items skipped.
