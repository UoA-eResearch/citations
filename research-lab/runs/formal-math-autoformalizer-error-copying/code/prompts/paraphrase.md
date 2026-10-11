You are writing meaning-preserving paraphrases for a preregistered research study. Read the input file {IN}. It holds items, each with an informal mathematics problem statement. Do not open other files.

For each item, rewrite the statement so that the wording and sentence structure change, but the problem does not:
- keep every number, every mathematical object and condition, and the exact claim (including any stated answer such as "Show that it is 65" and any multiple-choice options);
- do not add hints, explanations or new conditions, and do not drop any;
- keep LaTeX for formulas where the original uses it; you may rephrase the words around them;
- do not reproduce long runs of the original wording.

Write a JSON array to {OUT}: [{"id": "...", "paraphrase": "..."}, ...] in input order. Make sure it is valid JSON (escape backslashes properly). Do not modify any other file. Then reply with one line: the number of items written.
