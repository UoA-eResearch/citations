# Confirmation pass on the revised draft (commit f4672e5)

Reviewer: the same independent reviewer as `review/review.md` (Claude, 11 October 2026, 16:30 NZDT). Same stance: every
number was re-derived from the run directory, and the new guards and the new Lean Workbook leaks were re-checked in Lean
with the reviewer's own scripts (`review_lean2.py`; outputs `conf_lw_neg.jsonl`, `conf_lw_rej.jsonl` in the reviewer's
scratchpad, to be copied to `review/reviewer_checks/` by the study). At most 6 REPL workers were used.

## Verdict: **publish with edits** (small, listed under "New issues"; none changes a number in the verdict)

The two bugs are fixed and the fixes are verified; the 27 new rejections are all kernel proofs; the new Lean Workbook
leaks are genuine (0 of 63 L1/L2 pairs spurious under my negation and witness tests); the primary recomputes to the
digit under the D9 rules; every number in `report.md` that I checked matches the tables; the prose now says what the
data support, and the plain-terms section is honest. Remaining edits are wording and disclosure items.

## Issue-by-issue status (numbers refer to `review/review.md`)

| # | Issue | Status | Evidence (reviewer) |
|---|---|---|---|
| 1 | Lean Workbook never certified | **Resolved** | `extract.py` strips `:=\s*by\s*sorry$`; `lean_workbook.parquet` has 0 rows with `sorry`; 3,075 miniF2F candidate pairs, 163 unchecked (5.3%, in line with the other corpora); 30 leaked items (2 L0, 18 L1, 10 L2 at best tier). All 63 L1/L2 pair-directions reproduce in Lean 4.9; 0 are spurious (negation test, witness refutation, FREE on the test side all negative). Pairs I inspected are near-verbatim copies (`aime_1990_p15`, `imo_1983_p6`, `imo_1974_p3`, `aime_1983_p9`, ...). |
| 2 | Explosion guard missed false training statements | **Resolved** | `recheck.one_way` adds `witness_refutable` and `negation_certified`, fail-closed. 27 directions flipped (21 pairs removed, 1 L1→L2). `flipped_pairs_diagnosis.jsonl`: 20 witness proofs, 12 negation proofs (5 both), 0 timeouts, 300 s retry identical. All 11 pairs I had found are among them; the other 10 removed pairs are false training statements too (`(1/2)^n = 1/64 → n = 6` in ℕ, `x + 1 > x * 1 → x = 1`, `y = x² − 6x + 1 → x = 3 ∧ y = −8`, the ℕ-division `2/3·n(n+1)(2n+1)` Numina item, the `x ≠ 0` iff for `imo_1960_p2`, ...). Goedel-V2 own leaks 99 → 89, Kimina 55 → 54, DeepSeek 16, STP 179. D3b's false claim is corrected in D9. Residual, under-rejection only: the witness tactic (`have := h 0 ...`) cannot instantiate implicit binders (`{x : ℝ}`) or statements whose first binder is a hypothesis, which is why `valid/aime_1988_p3` × Numina `algebra_280685` (the same false formalisation, implicit binder) survives as L2 while its reverse direction is rejected. Not a correctness problem; note it as a limitation. |
| 3 | L2 semantics | **Resolved** | Table of 211 L2 pairs (114 / 24 / 10 / 63) matches `diagnostics.json`. |
| 4 | "69 automation-provable" mislabelled | **Resolved** | `benchcheck.py` FREE on all 488: 82 (my run: 80 + 2 timeouts; 68 of D1's 69 overlap). Design property holds (every FREE-provable leaked unit is L0-only). `mde.json` still carries the D1 figure 69 in `automation_provable_items` and `tiers.py` still writes the D1 flag to `leak_status_by_prover.csv`: stale but unused by the report. |
| 5 | False negatives under-stated | **Resolved** | Retrieval recall 58% / 44% and median Jaccard 0.34 (`diagnostics.json`, reproduces my numbers); unchecked share 5.9% (1,696 / 28,530) now that the Lean Workbook pairs elaborate. |
| 6 | Certification reproducibility | n/a (was sound) | Confirmed again on the 63 Lean Workbook pairs. |
| 7 | 83 items with R1 == original | **Resolved** | Identical R1 versions dropped (83 items); units whose only reformulation was an identical R1 dropped (DeepSeek 7, Goedel 6 + the vacuous item, Kimina 9), which gives the 143 / 154 / 144 clean units. One wording fix: "70 of those 83 items keep a genuine R2" counts R2 texts; 69 certify in Lean 4.9 and 65 in Lean 4.15. |
| 8 | R2 spacing / duplicate hypothesis names | Resolved via 10 | The `hyp1 hyp1` case (`valid/aime_1994_p4`, 9 Kimina outputs) remains a "changed statement" because the model renamed a hypothesis; that is a real change, so leaving it rejected is defensible. |
| 9 | Prompts not the model cards | **Resolved** | Report now says "DeepSeek-Prover-V1.5's miniF2F header ... `maxHeartbeats 400000`, where the model cards use 0". |
| 10 | Whitespace false rejections | **Resolved** | `reverify_ws.py` + overrides in `analysis.py`: DeepSeek 6 ok / 6 error / 31 still changed; Goedel 31 / 11 / 79; Kimina 0; STP 0; 37 restored, matching my re-verification exactly. The override logic (`np.where(k.isin(o.index), ...)`) applies only to re-checked (key, idx) rows; verified by recomputation. |
| 11, 12 | Tokenizer and verification mechanics | n/a (were sound) | Unchanged. |
| 13 | Interval labels, mde.json | **Resolved** | "90% intervals (the 5th and 95th bootstrap percentiles)" and the one-sided bound used by the rule; mde.json 6.3 vs design 7.0 explained. |
| 14 | Timeline wording | **Resolved** | "before the pooled analysis was first run". See new issue C on the D9 ordering. |
| 15 | DeepSeek's documented miniF2F-valid training | **Resolved** | Primary keeps the preregistered mapping (correct: the mapping was preregistered, and D9 is not blind to outcomes); documented-training, test-only and valid-only contrasts reported with equal prominence (+0.1, 0.0, +1.8 pp). |
| 16 | Leaked ⇔ solved-by-pipeline selection | **Resolved** | Stated under "Levels and selection" with the STP 2%-of-63 illustration. |
| 17 | Numbers; missing mixed model | **Resolved, one disclosure missing** | Every number in `report.md` re-checked against the tables (list below). Mixed model added; but `logs/analysis_D9.log` records `ConvergenceWarning: VB fitting did not converge`, which the report does not say. I refit with `minim_opts={"maxiter": 5000}`: converges, and the estimate is unchanged to four decimals (interaction log-odds −0.0354, SD 0.0349, OR 0.965, 95% 0.901–1.033). Fix: pass the larger budget and state that it converged. |
| 18 | Per-sample results contradicted the prose | **Resolved** | Per-prover per-sample DiDs, the ceiling, the by-version table and both figure rows are in the report; the three sentences are gone; the verdict line states the per-sample finding. |
| 19 | Scope of "Refuted" | **Resolved** | Title and verdict scoped: "Refuted (surface rewording, pass@32)"; "What the design cannot answer" bullet. |
| 20 | Kimina lineage; 5 Numina test items; 13-gram on informal text | **Resolved** | All three stated. |
| 21 | What the papers say | **Resolved** | In the plain-terms section and the documented-training block. |
| 22 | Certification mechanics | n/a | Unchanged. |

## The four questions asked

**Do the new guards over-reject?** No evidence of it. (i) Both new conditions reject only on a kernel-checked proof
that the premise is false (witness) or inconsistent with the conclusion's binders (negation), which is sound by
construction; a timeout would also reject, but none of the 27 flips was a timeout (0/27 at 60 s and at 300 s). (ii) The
witness tactic cannot refute a true statement (I ran it on true benchmark items: it fails with `this : True`). (iii) For
Lean Workbook, whose certified implications were never audited before, I re-ran all four conditions with explicit
timeout/proved/failed status on the 318 certified Lean Workbook directions the recheck rejected: all 318 are justified by a kernel-checked proof (301
because the benchmark side is provable alone by FREE, 6 FREE + negation, 4 FREE + witness, 4 D3b + negation, 2 witness,
1 witness + negation); 0 were rejected by a timeout alone; 0 would be accepted on rerun. (iv) The 10
removed pairs beyond my 11 are false statements on inspection (listed above). The one asymmetry (implicit binders)
goes the other way.

**Is keeping the 10 formerly-leaked items in the clean arm acceptable?** Yes, with the number stated. They were
sampled because of spurious matches to false Goedel-Pset / SFT / Numina statements, not because of anything about the
items, and their d values are nine 0.0 and one 0.5. Primary without them: +1.11 pp (90% −1.08 / +3.35; n 156/431) against
+0.98 (−1.17 / +3.30; n 156/441) with them; per-sample pooled +1.18 (−0.47 / +2.89) against +1.06 (−0.64 / +2.76). Put
the without-them number in the caveat bullet.

**Does every number in report.md match the tables?** Yes for everything I checked: the leak map (all 32 cells and the
four "any corpus" totals), 250 / 51.2%, 18% / 11% / 3%, 173 + 1 STP verbatim, 5 Numina test items, 2 Lean Workbook
verbatim, best-tier 185 / 47 / 18, the L2 table, 82 / 1 / 2 benchmark items, 156 / 441, +0.6 / −0.3 / +1.0 (−1.2, +3.3),
MDE 7.0 / 3.2, the per-prover pass@32 and per-sample rows (16/143, 88/154, 52/144, 173/296 and all intervals), the
ceiling table (95.5 → 90.0 → 79.7; 92 → 80 → 68; clean ranges), the R2 extra drops (+8.3; +22.1), 69 of 143, 77% vs 70%,
89% vs 86%, 2% of 63, all seven robustness rows, 51,232 samples, OR 0.97 (0.90, 1.03) and 0.67, 100% vs 73% / 44%,
58% / 44% / 0.34, 5.9%, 10 items (9 + 1), truncation 19% / 25%, 22 kills, mde.json 6.3 vs 7.0, 27 directions, 99 → 89,
30 Lean Workbook items, 37 restored proofs, 82 not 69. The only textual miscount is "70 of those 83 keep a genuine R2"
(see issue 7).

**Is the plain-terms section honest?** Yes. It states the refuted preregistered test, the blind spot of pass@32, the
per-sample 7 and 14 points for the two near-verbatim provers, the absence of the effect for Goedel and Kimina, the
documented validation-split training, and the three defective items. One hedge: "That is the signature of memorised
wording" should read "That is consistent with memorised wording" (the design does not rule out that near-verbatim
leaked items are, for other reasons, the ones most sensitive to equality flips).

## New issues (all minor)

**A. Mixed-model convergence not disclosed** (issue 17 above). Refit with a larger budget converges to the same
estimate; say so and pass `minim_opts` in `analysis.py`.

**B. "70 of those 83 items keep a genuine R2"**: 70 have a distinct R2 text; 69 certify in Lean 4.9 and 65 in 4.15.

**C. D9 says the fixes were "committed before the reruns"; the first rerun preceded the commit.** `lean_workbook.parquet`
and its candidate file were rewritten at 13:03, the D9 entry is timestamped 13:29 and committed at 13:32 (d4f24fb), the
certification started 13:46 and the rechecks 14:43–15:12. The extraction fix is mechanical and the review had specified
it, so nothing turns on this, but the sentence should say the extraction and retrieval step started before the entry was
committed. Likewise the vacuity portfolio was changed after its first result (0 vacuous) was seen; the addendum logs
this, and the choice is outcome-neutral for the DiD (vacuous and refuted items contribute d = 0 in both arms), which the
report should say in one clause.

**D. Stale D1 fields.** `mde.json` (`automation_provable_items: 69`) and the `automation_provable` column of
`leak_status_by_prover.csv` still come from the D1 flag; the report uses `bench_items.csv`. Either regenerate or label.

**E. The witness guard's implicit-binder blind spot** (issue 2): a false training statement written with `{x : ℝ}` or
with hypotheses before its first explicit binder is not witness-refutable, so a false ⇒ false pair can still count (the
`aime_1988_p3` × `algebra_280685` L2 is one; it is the same false formalisation, so it is a leak of the defective item in
any case). Say so under "Certification is bounded".

**F. The Lean Workbook finding deserves one more sentence.** Of its 30 leaked items, 18 are miniF2F *test*
items, 11 of them at L0/L1 (verbatim or near-verbatim copies with renamed hypotheses: `aime_1990_p15`, `aime_1994_p3`,
`imo_1963_p5`, `imo_1974_p3`, `imo_1983_p6`, `amc12a_2021_p8`, `algebra_amgm_sumasqdivbgeqsuma`, ...), in a corpus that
DeepSeek-Prover-V1.5, STP and Goedel-V1 document using. Four test items are leaked *only* through Lean Workbook
(`algebra_abpbcpcageq3_sumaonsqrtapbgeq3onsqrt2`, `algebra_apbon2pownleqapownpbpowon2`, `amc12a_2021_p25`,
`induction_pord1p1on2powklt5on2`).
The report currently says only "Lean Workbook contains 2 verbatim, one of them a test item".

**G. "That is the signature of memorised wording"** → "consistent with" (plain terms).

## Recomputed numbers (confirmation)

| Quantity | Report / tables | Reviewer |
|---|---|---|
| Primary DiD (pass@32, D9 rules) | +0.98 pp (−1.17, +3.30); 156/441 | +0.98 pp (−1.24, +3.24); 156/441 (seed differs) |
| Units from `units.csv` vs independent rebuild | 597 | 597, identical d values |
| Per prover pass@32: DSP / Goedel / Kimina / STP | +1.0 / +1.1 / 0.0 / +3.9 | +1.05 / +1.14 / +0.00 / +3.90, intervals within 0.1 pp |
| Per prover per-sample | +6.8 / +0.5 / +0.8 / +14.4 | +6.75 / +0.53 / +0.76 / +14.38 |
| Primary without the 10 formerly-leaked items | – | +1.11 pp (−1.08, +3.35); 156/431; per-sample +1.18 (−0.47, +2.89) |
| Mixed-model interaction | OR 0.97 (0.90, 1.03), VB not converged | identical at maxiter 5000, converged |
| Flipped directions: witness / negation / timeout | 20 / 12 / 0 | 20 / 12 / 0 (re-read; 300 s identical) |
| Lean Workbook L1/L2 pairs spurious (negation/witness/FREE) | – | 0 of 63; all 63 certifications reproduce |
| Lean Workbook rejected directions (318): proof / timeout-only / would-accept | – | 318 / 0 / 0 |
| Benchmark items: automation-provable / vacuous / refuted | 82 / 1 / 2 | 80 + 2 timeouts / 1 / 2 (both refutations and the vacuity reproduce with the study's portfolios; the witness tactic does not refute true items) |
| Identical-R1 items with certified R2 | "70" | 70 texts; 69 (4.9) / 65 (4.15) certified |
| Whitespace re-verification restored | 37 (6 + 31) | 37 |
| Clean units dropped for lacking a genuine reformulation | – | DSP 7, Goedel 6 (+1 vacuous), Kimina 9 |

## Bottom line

The revision does what the review asked, and the reruns did not introduce an error I could find. After the edits A–G
(none touches a verdict number) the report can be published.
