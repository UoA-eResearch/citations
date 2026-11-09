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

## Confirmation pass

Reviewer: Fable 5.1, 2026-11-09.

**What I checked.** Every number was recomputed from the stored parquet files under `data/work/`. The fixes were
checked against `deviations.md` D3, the code (`code/rot.py`, `code/analyse.py`, `code/figures.py`), `report.md`,
`report.html`, `results/figures/F1_rot.png` and `review/overclaim_check.md`. Python that read `data/` or `results/`
ran with `-I`, from a working directory outside `data/`. No Lean, lake or git command was run inside `data/`; the
snapshot evidence comes from `grep` only. The check files are in `review/reviewer_checks/` (staged as `confirm_*`):

- `confirm_1_numbers.{py,txt}`: an independent merge and GEE for the primary, independence, unadjusted,
  unknown-identifier, six-month, second-pair and pooled analyses. It also checks the body-change rates, the
  removed declarations (v1 backup against the D3 population) and the validation share.
- `confirm_2_error_classes.{py,txt}`: the stored messages classified with my own patterns, as first error and as
  highest-priority class, split by flag. It also lists what is left in "other".
- `confirm_3_multiline_simp.{py,txt}`: an independent reimplementation of the non-terminal-simp rule with multi-line
  continuation, run on all three pairs. It compares the result with the 231 removals and with the first review's
  264, and checks the `<;>` count and `comment_before_by`.
- `confirm_4_report_gates.{py,txt}`: checks that each D3 edit is in `report.md` and `report.html`, that report
  numbers match `primary.json`, that the figure's data source matches its label, and that the G5 table is current
  (built from the lab's `overclaim_check.py` `extract`/`table_rows`, read-only).
- `confirm_5_induction_prime.{py,txt}` (new): the largest residual "other" first error, "unknown tactic", and post hoc
  sensitivities that remove it.
- `confirm_6_gates_g5_g6.txt`: `overclaim_check.py --verify` and `attribution.py check --show`.
- `confirm_7_snapshot_grep.txt`: where `induction'` is defined and imported in each snapshot (grep only).

**What reproduces.** All stored numbers reproduce exactly (`confirm_1`):
- primary OR 1.5745 (0.9712–2.5524), p 0.066, n 2,488 in 1,203 files, 110 flagged, H1 Inconclusive by the
  preregistered rule;
- independence working correlation 1.7004 (1.0128–2.8547), unadjusted OR 2.20 (48/110 against 619/2,378 failing);
- excluding unknown-identifier-only failures 1.7261 (1.0748–2.7723);
- six months 1.7983 (1.1166–2.8962);
- second pair 1.029 (0.5723–1.8501);
- pooled 1.4508 (1.003–2.0985), with 2,209 shared declarations; the result does not depend on row order;
- body changed: 109/110 flagged against 1,195/2,378 unflagged.

The report's numbers, error-class lines and table rows match `primary.json`, and `report.html` carries the same
text (`confirm_4` §A–D).

### Final verdict: fix first

The six original findings are fixed, and finding 2 has small residues. Checking the corrected error classes,
though, shows a new moderate problem. The largest residual "other" error is a single removed import, not tactic
style, and it carries every secondary comparison that clears 1.0 (N1 below). The report's main reading, that the
style rule "points the right way in the first year", rests on it. H1 stays Inconclusive whatever is done about it.
The fix is narrow: one post hoc sensitivity in `analyse.py`, a D4 entry, a rewrite of three or four sentences, the
figure's right panel, and G5 re-run. A further pass can be limited to those.

**Original findings**

- **1 (tautology; body-change rates): fixed.**
  - The withdrawn sentence and the 109/110 against 1,195/2,378 rates are in the verdict block, and the second-pair
    bullet says O₂'s flagged set is post-clean-up (`confirm_4` §A).
  - The rates reproduce (`confirm_1` §1). Unchanged bodies still fail at 0.0, which is why the claim was withdrawn.
  - Supporting the "post-clean-up" description: O₂ has 3.2% flagged.
- **2 (error classes): fixed, with small residues.**
  - The patterns now match backticks and the newer wording. `eclass_first` is the class of the first stored error,
    and stored messages are in compiler order.
  - My independent patterns give the same counts for every class except `simp_no_progress`: 23 first errors against
    the stored 16 (`confirm_2`). The 7 extra are "`dsimp` made no progress" and "`field_simp` made no progress",
    which `\bsimp` does not match. One of them is flagged.
  - With those counted, the predicted classes are the first error for 3/48 flagged failures (6%) against 53/619
    unflagged (9%). Anywhere in the stored messages, the figures are 4/48 (8%) against 88/619 (14%). The report's
    conclusion that these classes are rare among flagged failures holds either way.
  - Residue a: the report says "highest-priority class among all of a proof's errors". Only the first three messages
    are stored, and 80 failing proofs have more than three errors. The next sentence of the report does disclose the
    three-message limit.
  - Residue b: the figure's right panel is wrong. See remaining issue 2.
- **3 (pooling): fixed.**
  - The pooled GEE clusters by file across both pairs: 1,104 file clusters contain rows from both pairs, and the
    2,209 shared declarations are noted in the report. The row is labelled descriptive only.
  - For the record, keeping one copy of each shared declaration gives OR 1.42 (0.95–2.12), p 0.09 (`confirm_1` §4).
    The pooled lower bound of 1.003 is therefore fragile. The report does not lean on it.
- **4 (multi-line simp): fixed.**
  - My reimplementation agrees with D3 on all 2,724 primary v1 declarations: exactly 231 are removed, none
    flagged, with fail rate 15.6%. It also agrees on all 3,936 second-pair declarations, and on all but 1 of 3,117 in
    the six-month population (`confirm_3`).
  - The difference from my earlier 264 is explained, slightly differently from the brief. 215 declarations are in
    both sets. 49 of my 264 are kept because the continued call is followed by a further tactic; 28 of those 49 are
    a term-mode `by simp` inside a multi-line term, a limit of syntactic detection that existed before. 16 removals
    were outside my 264. The one flagged declaration in my 264 is kept.
  - D3's claim that the corrected population is a subset of the first is not quite true. One primary declaration
    (`Affine.Simplex.scalene_reindex_iff`) and two six-month declarations are new under the corrected rule. They have
    no label or replay, and the inner merge drops them silently (`confirm_1` §1 bookkeeping, `confirm_3`). The effect
    on numbers is nil, but the statement is wrong. See remaining issue 4.
- **5 (parser details): fixed.**
  - The 4 `comment_before_by` declarations are the same 4 the first review found, and they are dropped. Five more
    are dropped in the second pair and six in the six-month population. The report's "Four" refers to the primary
    pair.
  - `<;>` is now counted once (`confirm_3` §5).
  - 309 primary declarations changed tactic count. `n_simp` is unchanged.
- **6 (wording and numbers): fixed.**
  - "whose only error is" is in the table, and "caused only by" is gone.
  - The unadjusted OR (2.20) and the independence OR (1.70, 1.01–2.85) are stated and reproduce.

**New finding**

- **N1 (moderate): the first-year excess is largely one removed import, `induction'`, and the report's reading
  depends on it** (`confirm_5`, `confirm_7`).
  - 118 of 667 primary failures (18%) have "unknown tactic" as their first error. That is 18 of 48 flagged failures
    (38%) against 100 of 619 unflagged (16%).
  - 116 of the 118 are proofs using `induction'`, and every one of the 116 `induction'` proofs in the population
    fails.
  - The cause is not a removed tactic: `induction'` is still defined in N (`Mathlib/Tactic/Cases.lean:118`).
    `Mathlib/Tactic/Common.lean` stopped importing `Mathlib.Tactic.Cases` between O and O₂, after mathlib migrated
    away from `induction'` (405 files use it at line start in O, 1 in O₂). In most N files the tactic is no longer
    in scope.
  - Flagged proofs use `induction'` four times as often: 18/110 (16.4%) against 98/2,378 (4.1%).
  - Excluding `induction'` proofs (post hoc):
    - primary OR 1.41 (0.83–2.40), p 0.20, with 32.6% against 22.9% failing;
    - six months 1.54 (0.87–2.72), p 0.14;
    - the second pair has no `induction'` proofs, so its OR is unchanged at 1.03.
  - Counting "unknown tactic" first errors as non-failures gives 1.08 (0.62–1.86). Also setting aside
    unknown-identifier-only failures gives 1.18 (0.69–2.01).
  - An `induction'` covariate separates failures perfectly, so exclusion is the usable form.
  - Every comparison in the report that clears 1.0 depends on these 116 proofs. Without them (post hoc):
    - the six-month OR 1.80 becomes 1.54 (0.87–2.72);
    - the unknown-identifier exclusion OR 1.73 becomes 1.54 (0.91–2.59);
    - the independence OR 1.70 becomes 1.44 (0.85–2.46);
    - the pooled OR 1.45 becomes 1.27 (0.82–1.94).
  - The first-year/second-pair contrast that the report attributes to "post-clean-up" is at least partly this as
    well: O₂ contains no `induction'` proofs.
  - The H1 verdict does not change, and failing because an import changed is legitimate rot under the preregistered
    definition (plan §6 lists context changes). But it is not the simp-fragility mechanism the linter targets.
    Leaving it as "other messages (37%)" makes "the style rule points the right way in the first year",
    "the direction is consistent in the first year" and the plain-terms "points the right way" overstated.

  Fix:
  - Add the `induction'` exclusion to `analyse.py` as a labelled post hoc sensitivity (D4), for the primary pair,
    six months and the pooled row.
  - State in the error-class bullet that 118 failures (18%; 18 of 48 flagged) are "unknown tactic", that 116 of them
    are `induction'` proofs which lost their import, and that 47 of "other" are "Invalid field … environment does
    not contain", i.e. renamed names reached by dot notation.
  - Rewrite the "direction is consistent" and "points the right way" sentences, in the verdict block, "What this
    does and does not show" and "In plain terms": without `induction'` proofs no comparison clears 1.0, and the
    flagged excess is partly a correlated import change.
  - Re-run G5 and re-label those rows.

**Gates.**
- G5: `overclaim_check.py --verify` passes (41 rows), and the 41 rows are exactly the 41 sentences of the current
  `report.md` (`confirm_4` §F, `confirm_6`). It is not fully honest:
  - rows 38–40 still give first-draft backing ("OR 1.48", "CI 0.92-2.39; second pair 0.99", "unknown identifier 37%");
  - rows 13, 37 and 40 should be Partially supported under N1.
- G6: `attribution.py check --show` passes (5 claims). F2–F4 resolve to the named works (Isabelle compatibility
  study, Lean Refactor, Growing Mathlib).

**Remaining issues**

1. (Moderate, N1) The `induction'` import confound. It needs a post hoc sensitivity in `analyse.py` (D4) and
   rewording of the "consistent direction" and "points the right way" sentences, as set out above.
2. (Minor) The right panel of `F1_rot.png` plots `error_classes`, the highest-priority classes (unknown identifier
   236, unsolved goals 165, other 80). Its axis label and caption say "first error class", which the report gives as
   other 246, unknown identifier 216, unsolved goals 40. `figures.py` was not updated in D3. Plot
   `error_classes_first`, or relabel the panel.
3. (Minor) G5 rows 38–40 carry first-draft backings and need current numbers. "What this does and does not show"
   says "the most common identifiable cause", the causal wording the pre-review gate removed; it should read "first
   error".
4. (Minor) D3 says the corrected population is a subset of the first. It is not: 1 primary and 2 six-month
   declarations are new, have no label or replay, and are dropped silently by the inner merge. Say so in D3, or
   label and replay them; the numbers do not move.
5. (Minor) "dsimp" and "field_simp made no progress" (7 first errors, 1 flagged) fall into "other". Fold them into
   simp-made-no-progress or say they are excluded. The conclusion is unchanged (3/48 against 53/619).

## Second confirmation pass

Reviewer: Fable 5.1, 2026-11-09.

**Scope.** As the brief asked, this pass covers only N1 and minor items 2–5 from the confirmation pass, which D4
(commit e2bac85) addresses.

**What I checked.**
- I recomputed every D4 number independently from the stored parquet files under `data/work/`.
- I checked the D4 diff to `code/analyse.py`, `code/figures.py` and `code/rot.py`, plus `results/tables/primary.json`,
  `results/figures/F1_rot.png`, `report.md`, `report.html` and `review/overclaim_check.md`.
- Every Python run that read `data/` or `results/` used `-I -B`, with the working directory in staging `scratch/`.
- No Lean, lake or build tool was run, and no git write was made.

The check files are in `review/reviewer_checks/` (staged as `confirm2_*`):
- `confirm2_1_induction.{py,txt}`:
  - the 119-against-116 reconciliation, for all three pairs;
  - every `excluding_induction_prime` GEE, refit and compared with `primary.json`;
  - the "unknown tactic" and "invalid field … environment does not contain" first-error counts;
  - the first-error classes recomputed with the D4 `rot.ERR`, including the dsimp/field_simp folding and the 3/48
    against 53/619 split;
  - a decomposition of how much of the flagged excess the `induction'` proofs carry.
- `confirm2_2_report_subset.{py,txt}`:
  - the D4 item 4 subset check (corrected populations against the `*_v1.parquet.bak` backups, and against labels and
    replays);
  - D4 phrases present in `report.md` and `report.html`;
  - the Results paragraph's class counts against `primary.json`;
  - which comparisons clear 1.0, with and without `induction'` proofs.
- `confirm2_3_gates_g5_g6.txt`: G5 (`overclaim_check.py RUN --verify`) and G6 (`attribution.py check RUN`), run from
  `research-lab/`.
- I also reused the first confirmation pass's `confirm_5_induction_prime` (the token-match exclusion) and
  `confirm_7_snapshot_grep` (the import change).

**What reproduces.** Every new `primary.json` number reproduces exactly from my own merge and GEE (`confirm2_1` §2–3).
- Excluding the 119 substring matches gives:
  - primary 1.4291 (0.8406–2.4297), n 2,369 with 92 flagged;
  - six months 1.5669 (0.884–2.7772);
  - without unknown-identifier-only failures 1.5541 (0.9214–2.6212);
  - independence correlation 1.4515 (0.8506–2.4769);
  - pooled 1.2721 (0.8282–1.9538).
- Of the 667 failures, 118 have "unknown tactic" as their first error, 18 of them flagged; 116 of the 118 are
  `induction'` proofs.
- 47 failures have "environment does not contain" as their first error, and all 47 are "invalid field" messages.
- The first-error classes match `error_classes_first` exactly: other 239, simp_no_progress 23.

No comparison clears 1.0 once these proofs are excluded. With them included, four do: independence, six months, the
unknown-identifier exclusion and pooled. G5 passes (47 rows) and G6 passes (5 claims).

### Final verdict: publish with edits

D4 resolves the substance of N1. The confound is in `analyse.py` as a labelled post hoc sensitivity, every number
reproduces, the verdict block states it, and H1 stays Inconclusive. The remaining problems are wording and stale text,
with no reanalysis needed:
- **The rewrite overcorrects.** The title, "What this does and does not show" and "In plain terms" now say the flagged
  excess is "mostly" the import change, and that without it "the difference is small". The numbers support "partly":
  - excluding the proofs removes about 21% of the primary adjusted log-odds ratio (1.57 to 1.43) and 44% of the raw gap
    (17.6 to 9.9 points);
  - what the proofs carry is the lower bounds clearing 1.0, not most of the effect.
- **Three of the 119 proofs do not use the `induction'` tactic.** They cite the lemma `LieSubmodule.iSup_induction'`.
- **The Results paragraph's error-class counts predate D4.**

**Items**

- **N1 (the `induction'` confound): partly fixed.**
  - Fixed: the sensitivity is in `analyse.py` (D4.1) and its numbers reproduce (`confirm2_1` §2). The verdict block
    has a dedicated bullet. The "direction is consistent" and "points the right way" sentences are gone, and "Excluding
    them, no comparison clears 1.0" is true (`confirm2_2` §4).
  - Not right, a: **119 against 116.** The brief's plain substring match also hits three proofs that only name the lemma
    `LieSubmodule.iSup_induction'` (`induction hy using LieSubmodule.iSup_induction' with`). All three are unflagged
    (`confirm2_1` §1).
    - They fail with "Invalid alternative name `hN`", not "unknown tactic", so "All 119 population proofs that use
      `induction'` fail, because Mathlib.Tactic.Common stopped importing it" is false for them.
    - The correct figures are 116 proofs, and 18 of 110 flagged against 98 of 2,378 unflagged. That is still about four
      times as often.
    - My token match, which skips comments, gives primary 1.41 (0.83–2.40) and six months 1.54 (0.87–2.72).
    - The same three proofs are the second pair's three substring matches, so the pooled exclusion drops second-pair
      rows that have no `induction'` tactic (substring 3, token 0).
    - No conclusion changes. Either use a token match, or keep the 119-proof exclusion and describe it as "119 proofs
      matching `induction'`, 116 of which use the tactic".
  - Not right, b: **"mostly" overcorrects** (`confirm2_1` §4).
    - The title says flagged proofs fail more often "mostly because a tactic many of them used lost its default
      import".
    - Plain terms says the extra breakage "mostly comes from one change", and that without those proofs "the difference
      is small and uncertain".
    - "What this does and does not show" opens with "The first-year excess is mostly one import change".
    - Against that, excluding the proofs moves the primary adjusted OR only from 1.57 to 1.43. The share of the
      log-odds ratio removed is 21% for the primary, 23% for six months, 19% for the unknown-identifier exclusion, 30%
      for independence and 35% for pooled. The raw gap falls from 17.6 to 9.9 points (44%).
    - What the 116 proofs do carry is every lower bound above 1.0. That is what the first confirmation pass asked to be
      said ("the flagged excess is partly a correlated import change").
    - Suggested wording: "partly because …" in the title and in plain terms; in plain terms, "the difference shrinks
      (odds ratio 1.43) and is no longer distinguishable from none"; and "The first-year comparisons clear 1.0 only
      because of one import change".
  - Not right, c: **"Two first-year comparisons clear 1.0"** (verdict block). Four comparisons in the report clear
    1.0: six months, the unknown-identifier exclusion, independence 1.70 (1.01–2.85) and pooled 1.45 (1.003–2.10).
    All four drop below 1.0 without the proofs. In the same way, "What this does and does not show" names only two of
    them, and attributes the six-month result to "the 119 `induction'` proofs". The six-month population has 141
    substring matches, 138 by token match.
- **2 (figure right panel): fixed.** `figures.py` plots `error_classes_first`, and the PNG shows other 239, unknown
  identifier 216, type mismatch 73, unsolved goals 40, rewrite failed 33, function expected 30, simp no progress 23, no
  goals 9 and timeout 4. That matches `primary.json` and the axis label. The caption's "first matching error class" is
  slightly loose: the class is that of the first error, which may be "other". This is not material.
- **3 (G5 rows and "the most common first error"): partly fixed.**
  - The table is rebuilt (47 rows, `--verify` passes), the stale first-draft backings are gone, and new rows cite D4,
    `induction_prime` and `excluding_induction_prime`.
  - "The most common first error" is in `report.md` and `report.html`, and "identifiable cause" is gone (`confirm2_2`
    §2).
  - The labels are not honest for these rows, all marked Supported:
    - row 1 (title) and rows 46–47 (plain terms, "mostly" and "small"): Overstated;
    - row 13: should name all four comparisons;
    - rows 17–18: "All 119 … use", "101 of 2,378"; should be Partially supported until corrected.
  - The new rows are not marked as new in the table itself, but rows 16–19 and 32–33 cite D4 or N1 in their backing,
    which is enough.
- **4 (D3's subset statement): partly fixed.** D4.4 correctly says that one primary and two six-month declarations are
  new under the corrected rule and are dropped by the inner merge. It misses one second-pair declaration,
  `Affine.Simplex.scalene_reindex_iff` in O₂ → N₂, which also has no label or replay (`confirm2_2` §1). The numbers do
  not move. Add "and one second-pair".
- **5 (dsimp and field_simp folded into simp_no_progress): fixed in code and verdict block, stale in Results.**
  - `rot.ERR` now matches dsimp, field_simp, simp_all and simp. Seven dsimp/field_simp first errors moved into the
    class (23 in all). The predicted classes are the first error for 3/48 flagged against 53/619 unflagged, and my own
    regex gives 3/48 against 54/619 (`confirm2_1` §3).
  - Only one "made no progress" first error remains in "other": "`repeat1'` made no progress", unflagged, which is
    correct.
  - The verdict block's "simp, dsimp or field_simp made no progress (3%)" and "other messages (36%)" match the data.
  - But the Results section's "Error classes of failing primary-pair proofs" paragraph was not regenerated
    (`confirm2_2` §3):
    - by first error it still says other 246 and simp made no progress 16; `primary.json` has 239 and 23;
    - by highest-priority class it says unsolved goals 165, other 80 and simp made no progress 23; `primary.json`
      has 164, 75 and 29.
    - The paragraph therefore contradicts the verdict block and the figure. The same text is in `report.html`.

**Also noted (outside the five items, minor).** "Process and deviations" in `report.md` and `report.html` ends at D3.
Its last line reads "Independent review: fix first … the fixes are in D3". There is no mention of the confirmation
pass or D4.

**Remaining issues**

1. (Minor–moderate, wording) The title, "What this does and does not show" and "In plain terms" say the flagged excess
   is "mostly" the `induction'` import change, and that the remaining difference is "small". The exclusion removes
   about a fifth of the adjusted log-OR (1.57 to 1.43) and 44% of the raw gap. Say "partly", and that the change is
   what lifts the lower bounds above 1.0. Relabel G5 rows 1, 46 and 47.
2. (Minor) 3 of the "119 `induction'` proofs" are `LieSubmodule.iSup_induction'` lemma uses that fail for another
   reason. Use 116 (18/110 against 98/2,378), or describe the 119 as substring matches. Fix G5 rows 17–18.
3. (Minor) "Two first-year comparisons clear 1.0" should be four (adding independence and pooled), with the same fix in
   "What this does and does not show". The six-month count there is 141 (138 tactic uses), not 119. Fix G5 row 13.
4. (Minor) The Results section's error-class paragraph is stale, in `report.md` and `report.html`: other 246 → 239,
   simp 16 → 23; highest-priority unsolved goals 165 → 164, other 80 → 75, simp 23 → 29.
5. (Minor) D4.4 omits the one new second-pair declaration. "Process and deviations" does not list the confirmation
   pass or D4.
