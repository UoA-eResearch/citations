You are one of two independent raters in a preregistered research study. Your task is blind annotation: deciding
whether Lean 4 (Mathlib) formal statements faithfully formalize a natural-language mathematics problem.

Read exactly one file: {BATCH}. Do not open, list or search any other file or directory, and do not use the web.
Work only from the text in that file and your own knowledge of mathematics and Lean 4/Mathlib.

The file holds items. Each item has an informal statement and two formal statements, A and B. Theorem names are
replaced by X, and proofs are omitted. A and B are in random order. Judge each one on its own against the informal
statement: both may be faithful, both unfaithful, or one of each.

For EACH of A and B, decide:

- **faithful: true** if the formal statement's objects, hypotheses and claim match the informal problem. Benign Lean
  conventions count as faithful, for example:
  - stating "show that the answer is 65" as an equation;
  - encoding a "find all" answer as a set equality or an iff;
  - a reasonable number type where the problem's domain allows it;
  - an extra hypothesis that the informal statement states or clearly implies (for example the positivity of a
    quantity the problem calls positive).

  Multiple-choice problems: a statement that proves the correct choice's value is faithful.
- **faithful: false** if any part of the formal statement changes the mathematical content. Then give exactly one
  category, the most important:
  1. wrong constant or answer
  2. missing hypothesis or condition (one the informal statement imposes)
  3. extra or stronger hypothesis (not stated or implied by the informal statement)
  4. wrong domain or type (for example ℕ where the problem needs ℝ or ℤ, or truncating ℕ division or subtraction
     that changes the meaning)
  5. wrong quantifier, scope or binding
  6. wrong relation, operator or formula
  7. weakened or trivial conclusion (for example only existence where uniqueness is asked, or only part of the answer)
  8. vacuous or contradictory hypotheses
  9. other
- **reason:** one short line (at most 25 words).

Write your answer as a JSON array to {OUT}, with one object per item in file order:

[{"id": "t012", "A": {"faithful": true, "category": null, "reason": "..."}, "B": {"faithful": false, "category": 4, "reason": "..."}}, ...]

Make sure the file is valid JSON and covers every item in the batch. Then reply with one line: the number of items
written.
