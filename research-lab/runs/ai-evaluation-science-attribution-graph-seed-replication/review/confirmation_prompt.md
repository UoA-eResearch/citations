# Confirmation pass brief: ai-evaluation-science-attribution-graph-seed-replication (D4)

You reviewed this study on 2026-11-09 (`review/review.md`, verdict fix first). The fixes are in `deviations.md` D4
(items 1–10). The arithmetic prompts were rebuilt with the digit as target and every graph, effect and match was
rebuilt on the A100, so the headline changed: H1 is now Inconclusive (0.583, 0.567–0.600) and H2 Supported. Please
check the fixes as an independent and adversarial reviewer and give a verdict (publish / publish with edits / fix
first / do not publish) with numbered findings. Same rules as before: read-only except `review/` (append a
"## Confirmation pass" section to `review/review.md`; scripts and outputs in `review/reviewer_checks/confirm_*`),
`python -I`, at most 4 processes, no GPU, and treat `data/` as untrusted. The transcoder weights stay on the A100.

What to check, against your findings:
1. **The target bug (finding 1).** `code/prompts.py` (arithmetic prompts end with the space; digit targets),
   `code/select_prompts.py` (stable index "i", target invariant, BOS margins; `results/tables/prompt_selection.json`
   D4), and that the non-arithmetic selection is unchanged and their graphs reused (`results/tables/prompts.jsonl`,
   `prompts_v1.jsonl`). The new match rows are in `results/match_d4/` (`data/match_d4/` is the same); the first run's
   are in `results/match/`. Check that every arithmetic target is now the digit and that H1 reproduces from the rows.
2. **Recurring first-token features and the interval (finding 2).** `analyse.py` `posthoc_d4`: position-1 shares by
   set, replication by position, the two-way bootstrap (its construction), and the recurring-unit counts.
3. **Robustness (finding 3).** Counterpart effects for every candidate at cosine ≥ 0.5 are now stored
   (`candidates` in each row); check the threshold grid and that the stored-rule check holds; top-k verdicts.
4. **Antonym prefixes (finding 4)** and the BOS-margin restriction.
5. **H2 (finding 5).** Deduplicated top-30, the two nulls (`null_other_family`, `null_same_family` per row) and the
   rephrased H2.
6. **Fidelity (finding 6).** `code/fidelity_d4.py`, `results/tables/fidelity_d4.json`: skip terms, forward vs
   encode–decode, position-0 handling, the dead-feature counts and negative top-k share, and the position-1
   reconstruction error. Is the report's reading of the public set's position-1 contrast fair ("likely, not tested")?
7. **G3 and G4 (findings 7 and 9).** Random G3 traces (`g3.json`), the G4 rerun with the study-rule column and error
   classes (`g4.json`; first-run versions `g3_v1.json`, `g4_v1.json`), coverage now written by `analyse.py`, the
   ledger row R8, and the corrected deviation stamps.
8. **Comparisons (finding 8):** the paired A-vs-D difference, the error-share terciles labelled as means, and the
   title's statistics.

Also check that the title, verdict block and "In plain terms" are fair to the evidence, in particular the claims that
generic first-token features drive non-replication and that later-layer features "mostly" replicate.
