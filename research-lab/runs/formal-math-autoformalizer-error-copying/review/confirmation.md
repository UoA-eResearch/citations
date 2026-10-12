# Confirmation pass on the revised report (commit bb741cb)

Reviewer: the same independent Claude agent as `review/review.md`. Read-only, as before; the recomputations below
reuse `review/reviewer_checks/outputs_df.pkl` and the new files in `results/tables/review/`.

## Recommendation: **publish with edits**

All 17 issues are resolved or resolved by correction; the two points the author contested were checked against the
saved sources and the author is right on both. The revision introduces no error I could find. The new numbers in the
report all reproduce. The edits below are small wording and completeness items that do not need another pass.

## The two contested points

**(a) Issue 5, the size of the miniF2F-v2 drop. The author is right; my figure came from the wrong table.** In the
saved paper (`scratchpad/v2paper.html`), the sentence "This finding suggests that current autoformalizers may suffer
from data contamination" follows the discussion of Table 3 (Herald, Kimina and o4-mini at @1, human-verified), where
the v1→v2s changes are Kimina 88.1→79.5 (test) and 82.0→78.7 (valid), Herald 55.3→51.6 and 59.4→48.0, o4-mini
46.3→51.6 and 47.1→52.5. The report's table reproduces these exactly. The −0.8 pp I cited is Herald's automated-judge
row of Table 2 (@128). One optional addition: Table 2's *human* rows at @128 show no decline for either model (Herald
62.7→66.0 test, 69.7→68.9 valid; Kimina 90.6→91.0, 88.1→88.1), so the paper's contamination suggestion rests on its @1
table alone. A clause saying so would make the paragraph complete; it does not change the report's reading.

**(b) Issue 17, the Lean Workbook premise. The author is right.** `scratchpad/lw.html`, section 4.1: "We first collect
Lean 4 formal statements with their corresponding natural language questions from MiniF2F [lean-dojo-mew] and ProofNet
[rahul3613/ProofNet-lean4] ... Since we do not test autoformalization on MiniF2F and ProofNet, we use all samples from
these two datasets ... organized from two directions into the training data." The first-round translator was trained
on all pairs from both benchmarks. "Synthesized from" was loose wording, not a false premise; D8 item 6 states it
precisely. Resolved.

## Issue-by-issue

| # | Issue (short) | Status | Where resolved / note |
|---|---|---|---|
| 1 | Headline and plain terms overreach; template memorisation in the data | **Resolved** | Verdict box lines 11-16; plain terms 18-39; new section "Kimina reproduces the ProofNet port's templates" (245-301); "What this means" (452-468). Header-fingerprint table verified against `header_fingerprint.csv`: 547/1,022 = 54%, 121/304 = 40%, T 111/304 = 37%, P 524/1,023 = 51% and 115/304 = 38%; test 355/734 = 48%, valid 313/592 = 53%; other four models 0. 8.3.6a: 11/11/5 ✓. Sylow bodies 42/39 ✓. Kimina 80 of 86 and 74 of 81 on ProofNet ✓; Herald 93 of 111 on miniF2F ✓ |
| 2 | Category-1 row conceals 8.3.6a | **Resolved** | Row relabelled (227); paragraph 237-239 explains the degenerate interval |
| 3 | O-vs-P analysis incomplete | **Resolved** | 59-item by-model table (322-328; Kimina 1.99 (1.27-3.30) ✓); per-item drivers (332-346) with `per_item_OTP.csv`; 4.5.14 reading corrected; Herald `xy` artefact (10 of 16 vs 1 of 16 ✓); non-uniform items; judge weakness |
| 4 | Negative-control wording | **Resolved** | 364-368: "rare on these eight items: 1 of 640"; elaboration 85/128, 75/128 ✓ |
| 5 | miniF2F-v2 drop unquantified | **Resolved (reviewer corrected)** | Table 473-477 matches the paper's Table 3 exactly; see (a) |
| 6 | Direction of selection bias | **Resolved** | Limitations 500-507; 54% vs 40% ✓ |
| 7 | Certifier misses identical statements | **Resolved** | 429-446; D8 re-check of 674 near-D "other" statements, 16 re-certified (all Herald, induction_sum_1oktkp1 and aime_1983_p9), sensitivity row 378 and figure row. Recomputed: 211 vs 229, RR 0.9216 (0.7995-1.0489) ✓; O vs P 59: 211 vs 145, 1.4536 (1.0944-2.0467) ✓; near-D counts match `near_D_other.csv` ✓ |
| 8 | Twin answer-format quirk | **Resolved** | Limitations 517-518: 8 of 16 ✓ |
| 9 | 97 both-equivalent outputs unlogged; D6 not applied to O vs P | **Resolved** | 448-450 and `both_equivalent.csv` (97 outputs, 33 unique, all Rudin 1.1a ✓); O vs P without the three provable-D items: 319 vs 208 on 126 items, 1.5324 (1.2641-1.9562) recomputed ✓ (308-310) |
| 10 | D6 timeline | **Resolved** | `deviations.md` D6 timeline (11:44-12:05 vs 13:21; "cannot be verified from the logs" stated); report 385-386 |
| 11 | Report numbers absent from tables | **Resolved** | `review.json`: greedy 14/16/8 of 177 and verbatim 35/31/11 on the 59 items ✓ |
| 12 | Post-hoc status of the flagged-twin sensitivity and the "clearer" reading | **Resolved** | D7 item 5 amended; report 387-390 |
| 13 | Timeline plausibility | **Resolved** | D8 item 7 |
| 14 | "Verbatim" definition and inference | **Resolved** | 398-400: whitespace runs collapsed, `(x:ℝ)` vs `(x : ℝ)` differ; the "even verbatim reproduction on twins" inference removed |
| 15 | Plain-terms wording | **Resolved** | "certified which ones say the same thing as"; "59 such problems that contain numbers" |
| 16 | ProofNet lower bound 1.01 | **Resolved** | 241-243 caveated |
| 17 | Lean Workbook premise | **Resolved (reviewer corrected)** | D8 item 6; see (b) |

## Checks on the revision itself

- **Git.** Only the expected files changed (`git show --stat bb741cb`): report, deviations, two new scripts, three
  figure/builder lines, the review tables and the review directory. `results/tables/primary.json` and
  `secondary.json` are untouched, so the preregistered numbers are unchanged. The reviewer's scratch files are now
  committed under `review/reviewer_checks/`; `outputs_df.pkl` there is untracked (add to `.gitignore` or delete).
- **`review_analyses.py`.** The header test is "every `open` line of the item's port header is among the output's
  `open` lines" (superset), temperature samples only, ProofNet included items only; its counts equal my exact-match
  counts (668 of 1,326 on originals), so the superset criterion adds nothing spurious. Per-item O/T/P, both-equivalent,
  near-D and the 59-item greedy/verbatim counts all agree with my earlier computations.
- **`recheck_near.py`.** Sound as written: the normalising tactics are kernel-checked and axioms are verified against
  the same allowed set. All 674 rows have `copy_norm`; no errors. The 16 re-certified statements had `to_D = to_C =
  False` under the preregistered portfolio; the preregistered classification was conservative, as the review said.
- **`report.html`** was regenerated and carries the new section and the confirmation link.

## New points (minor; publish with these edits)

1. **The re-check tested O ↔ D only.** Plan section 5 counts an output equivalent to both references as "other". For
   the 16 re-certified statements this cannot bite (on induction_sum_1oktkp1 C carries the extra hypothesis `0 < n`,
   so C → O fails; on aime_1983_p9 C is an `IsLeast` form), but the report should say that C was not re-tested, or
   `recheck_near.py` should test it, for consistency with the plan's rule. *Location:* report 435-444; `recheck_near.py`
   `work()`.
2. **Statements versus outputs.** Line 391-392 reads "16 more statements are certified as copies ... 7 more copies on
   originals, 4 on twins and 16 on paraphrases". Say "16 unique statements, 27 temperature outputs (7 O, 4 T, 16 P)";
   two further greedy outputs were also re-certified (1 O, 1 P) and are correctly excluded from the counts.
3. **Test-split items in the Sylow evidence.** Line 296 notes that 8.3.6a is a validation-split item "which a model may
   legitimately train on". The Sylow-body reproduction (point 3 of the new section) includes the test-split items
   4.5.13, 4.5.15 and 4.5.17 (`per_item_OTP.csv`, `split`), so the caveat does not cover that evidence. One clause.
4. **miniF2F-v2 Table 2 at @128.** See (a): one clause that the paper's @128 human-verified table shows no decline.
5. **`outputs_df.pkl`** is untracked under `review/reviewer_checks/`; ignore or remove.

## Recomputed numbers for the revision

| Quantity | Recomputed | Report / table | Match |
|---|---|---|---|
| D8 re-check: statements re-checked; re-certified | 674; 16 (all Herald: aime_1983_p9 O 2, T 3 statements, P 4; induction_sum_1oktkp1 O 4, P 3) | 674; 16 | yes |
| Re-certified temperature outputs by condition (primary models, 59 items) | O 7, T 4, P 16 (plus 1 greedy O, 1 greedy P) | 7, 4, 16 | yes |
| Primary with re-check | 211 vs 229, 0.9216 (0.7995-1.0489) | 0.92 (0.80-1.05) | yes |
| O vs P, 59 items, with re-check | 211 vs 145, 1.4536 (1.0944-2.0467) | 1.45 (1.09-2.05) | yes |
| O vs P, D6 applied (126 items) | 319 vs 208, 1.5324 (1.2641-1.9562); excluded mathd_algebra_188, _314, Rudin 1.1a | 1.53 (1.26-1.96) | yes |
| Kimina O vs P, 59 items | 1.9885 (1.2680-3.2955), 86/43 | 1.99 (1.27-3.30) | yes |
| Header fingerprint (Kimina): no-twin O / P; twin O / T / P | 547/1,022, 524/1,023; 121/304, 111/304, 115/304 | 54%, 51%; 40%, 37%, 38% | yes |
| Header by split, originals | test 355/734 = 48.4%; valid 313/592 = 52.9% | 48%, 53% | yes |
| Header by textbook (Kimina, originals) | Rudin 167/224; Munkres 113/144; Shakarchi 32/32; Dummit-Foote items: DF header 175, Herstein 87 | same | yes |
| Both-equivalent outputs | 97 outputs, 33 unique, all Rudin 1.1a, 0 in primary set | same | yes |
| Near-D "other" (ratio ≥ 0.9), O / T | Herald 33/31, Kimina 30/25, Qwen 7/7, DSP 1/4, Goedel 0/0 | same | yes |
| 8.3.6a split; 4.5.13 / 4.5.14 / 4.5.15 / 4.5.17 | valid; test / valid / test / test | "validation split" (8.3.6a) | yes (see new point 3) |
| miniF2F-v2 paper, Table 3 (@1, human): Kimina test/valid, Herald, o4-mini | 88.1→79.5, 82.0→78.7; 55.3→51.6, 59.4→48.0; 46.3→51.6, 47.1→52.5 | same | yes |
