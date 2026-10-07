You are coding the causes of certified-vacuous statements in an AI prover's self-play training corpus (STP). Each row
of /mnt/citations/research-lab/runs/formal-math-selfplay-vacuity-drift/results/tables/vacuous_sample_100.csv is a Lean 4
theorem whose hypotheses were proved contradictory by the Lean kernel (a proof of False from exactly the hypotheses, as
the theorem elaborates). Columns: row_id, iteration, swap, auto, auto_bound, statement. auto_bound is True when the
statement uses a variable it never declares (Lean's autoImplicit binds it; if nothing fixes its type, it defaults to ℕ).

For each row, read the statement and decide, without running Lean:
- cause (one code):
  K1 natural-number subtraction or division (truncation makes the hypotheses inconsistent);
  K2 contradictory numeric constraints (equalities/inequalities that cannot hold together);
  K3 a single hypothesis false on its own (e.g. 2 < 1, a false identity);
  K4 cast or division-by-zero conventions (x/0 = 0, coercions);
  K5 unsatisfiable functional equation, domain or range confusion, or parsing slip (e.g. `x i+1` read as `(x i)+1`);
  K6 an undeclared variable defaulted to ℕ makes the hypotheses inconsistent (use only when auto_bound is True and the
     contradiction depends on that type; otherwise code the underlying cause).
- locality: "local" if one or two hypotheses suffice for the contradiction, else "global".
- real_claim: "yes" if the statement reads like a genuine competition-style claim, "no" if it is obviously malformed.
- explanation: one short sentence naming the contradiction.

Write /mnt/citations/research-lab/runs/formal-math-selfplay-vacuity-drift/results/tables/vacuous_causes.csv with columns
row_id, iteration, cause, locality, real_claim, explanation (one row per input row, same order). Do not modify any
other file. Reply with the counts per cause.
