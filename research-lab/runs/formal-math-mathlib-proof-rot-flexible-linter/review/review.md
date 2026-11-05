# Review: formal-math-mathlib-proof-rot-flexible-linter

Reviewer: independent adversarial review (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.py`–`checks4.py` with `.txt` outputs). All checks used `venv/bin/python -I` with `code/` on `sys.path`
and read the work parquet files, snapshots and rewritten files; no Lean compile was run by the reviewer.

## Verdict: fix first (the primary verdict is robust; the error-class table, the pooled analysis and two sentences are not)

What holds: the GEE reproduces exactly (OR 1.4805), the substitution is correct (rewritten bodies identical to O
in 7/7 checked declarations, diff hunks equal to the number of changed bodies), error attribution by span works
(0 declarations lost in rewriting, 3 parse-error cascades out of 704 failures), v1 and v2 give the same H1
statistic, and four hand-traced failures are genuine rot (a renamed `le_or_lt`, the new `by_cases!`, a changed
`simp` normal form needing `dsimp`, a heartbeat timeout). "Inconclusive" is the right call under the
preregistered rule. What does not hold: the preregistered error classes "simp made no progress" and "rewrite
failed" are never detected because newer Lean wraps tactic names in backticks, so the two classes that would
evidence the linter's mechanism sit inside "other"; the pooled analysis treats 2,425 declarations present in both
pairs as independent; 9.7% of the population are terminal multi-line `simp` calls misread as non-terminal; and
the report presents a tautology ("none whose text mathlib left alone fail") as a finding while omitting the fact
that 99% of flagged proofs were rewritten during the year.

## Findings

### 1. (Moderate) Flagged proofs were almost all rewritten by mathlib; the "unchanged bodies never fail" sentence is a construction, not a result

Evidence: `checks1.txt` §A. Body changed between O and N: 109 of 110 flagged proofs (99.1%) against 1,310 of
2,613 unflagged (50.1%). A replayed body identical to N's cannot fail (the file is N's own), so
`same_body_fail_rate = 0.0` (`analyse.py:52`) is true by construction and the verdict bullet "none whose text
mathlib left alone do" says nothing about rot. The 99% figure is the real context: the flexible linter was
adopted in mathlib's `Init` between O and O₂, so flagged proofs were systematically edited to silence it. This does
not bias H1 (fail depends only on O's body and N's library, not on the edit), but it changes how the secondary
pair reads: O₂'s 115 flagged proofs (2.9%) are the residue after that clean-up, so the second pair's null (OR
0.99) is not a replication of the first. For the record, conditioning on changed bodies (a post-treatment
variable, not recommended as an estimate) gives OR 0.65 (0.42–1.02): flagged proofs that were edited were more
often edited for style than because they broke.

Fix: replace the tautology with the 99%/50% rewrite rates and what they imply; say in the second-pair bullet that
O₂'s flagged set is post-clean-up.

### 2. (Moderate) The preregistered error classes "simp made no progress" and "rewrite failed" are never detected

Evidence: `checks1.txt` §B, `rot.py:186-196`. Newer Lean writes "`simp` made no progress" and "Tactic `rewrite`
failed: Did not find an occurrence of the pattern"; the patterns `simp made no progress` and `did not find
instance of the pattern|rewrite failed` match neither (backticks; "occurrence" vs "instance"). Among the 122
"other" first messages, at least 12 are simp-no-progress and 15 are rewrite failures, i.e. the two classes the
flexible-linter hypothesis predicts; the table reports both as absent. D2 claimed to have made class matching
robust; it fixed case only. Also, `eclass` returns the highest-priority class among all of a declaration's
errors, not the first error (row 164 in `checks4.txt`: an "Invalid argument" error classed "timeout" because a
later message mentions heartbeats), so the gate's "most common first error" wording is itself inaccurate.

Fix: patterns tolerant of backticks and the new wording (`\bsimp\b.*made no progress`,
`(did not find|Did not find an occurrence|motive is not type correct|rewrite.*failed)`); report the class of the
first error by line, or say "highest-priority class"; re-run `analyse.py` and re-fill the error-class bullet and
the "What this shows" paragraph (which currently says style-related failures are absent).

### 3. (Moderate) The pooled analysis double-counts declarations

Evidence: `checks1.txt` §E. 2,425 of the 3,936 second-pair declarations are the same (file, name) as primary-pair
declarations (1,429 with identical O bodies). `analyse.py:65` prefixes file names with "A:" and "B:", so the same
proof enters the GEE twice in different clusters. The pooled interval 0.89–1.88 is therefore too narrow and the
pooled n (6,653) overstated.

Fix: drop the pooled row, or pool with declaration-level clustering (cluster = file without the prefix) and say
the two pairs overlap.

### 4. (Moderate) 264 population proofs (9.7%) are terminal `simp` calls with a multi-line argument list

Evidence: `checks1.txt` §C, `rot.py:87-93`. The non-terminal test treats any more-indented next line as a
following tactic, so `simp [a, b,` / `  c, d]` as the last tactic counts as non-terminal. 264 declarations qualify
only through such a continuation line; 1 is flagged and their fail rate is 18.9% (population 25.9%). Excluding
them: OR 1.52 (0.95–2.45), p = 0.08 (`checks4.txt`); the verdict is unchanged but the population definition in
the report is not what was measured.

Fix: treat a more-indented line as a continuation when the previous line has an unclosed bracket or ends with a
comma; re-run `decls` (no recompile needed for the replay results, which can be filtered by name).

### 5. (Minor) Parser and feature details

- `rot.py:69`: the offset correction for comments before `:= by` is a no-op (both branches equal `block[pos.end():]`);
  4 population declarations have such comments. Spot-check of 20 random declarations found the right line, name,
  statement and body in all 20.
- `features`: `<;>` is counted twice (once by `count(";")`); harmless for log(tactics).
- Labelling coverage was not independently compiled; the flagged examples I read are plausible
  (`checks2.txt`), the FlexTest file emits the warning, and the linter's rigid/stopper lists match the plan's
  description. A syntactic "simp then rw on the goal" heuristic flags only 14 of 396 such sequences, but most of
  those sequences are terminal `simp` closing a bullet or a `have`, so this is not evidence against the labels.
- Timeouts (4) are per-declaration heartbeat errors, not whole-file timeouts; no file hit the 30-minute limit, so
  G2's "silently treated" case does not arise. One declaration had an O-side error and was excluded (99.96%).

### 6. (Minor) Report wording and numbers

- Results table row 2 still says "failures caused only by unknown identifiers"; the gate changed the equivalent
  verdict wording to "whose only error is".
- All numbers match `primary.json` (2,723 / 1,294 / 110; 43.6% / 25.1%; 1.48 (0.92–2.39), p 0.11; 1.62; 1.67;
  0.99; 1.29; class counts 258/179/122/83/31/27/4 of 704). The independence working correlation gives OR 1.60
  (0.97–2.65) and the unadjusted OR is 2.31, so the adjustment for length and simp count halves the effect; worth
  one sentence.
- Timeline verified: plan 07:41, pipeline 07:43, D1 08:08 before `pop_*` (08:08:47–08:09:03), labels 08:27/08:43,
  `analyse.py` committed 08:45 before the replay results (09:30–09:54), draft 09:56.

## Gate checks

- **G1:** no leak through the population filter; the flag does not enter the outcome. The 99% rewrite rate
  (finding 1) is context the report must state.
- **G2:** no silent drops; the one O-side error and the 4 heartbeat timeouts are counted.
- **G3:** four replayed failures traced by hand to concrete library changes (`checks3.txt`).
- **G5:** `review/overclaim_check.md` present and honest for the primary rows; rows 17–19 and the "What this
  shows" paragraph need revision after findings 1 and 2.
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (5 claims)".
