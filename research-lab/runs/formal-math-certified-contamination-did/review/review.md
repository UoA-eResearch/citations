# Independent review: certified training-test leakage and the reformulation DiD on miniF2F

Reviewer: independent adversarial review (Claude, 11 October 2026), of the draft committed in a1797f1. Everything below was
re-derived from the run directory; the Lean re-checks were run with the study's own `certify.py` / `recheck.py` in the
study's Lean 4.9 and 4.15 environments (4 REPL workers, cores 0-3). Reviewer scripts and outputs are in
`review/reviewer_checks/` (`review_lean.py`, `reverify_ws.py`, `tally.py`, `neg_*.jsonl`, `free_v49.jsonl`,
`rejected_*.jsonl`, `ws_*.jsonl`, `tally_output.txt`).

## Recommendation: **fix first**
> **Reviewer's Lean jobs (complete, 13:31 NZDT 11 Oct).** `run_chain.sh` ran the negation/witness test on all 649 L1/L2
> pairs (Lean 4.9 then 4.15), the FREE check on all 488 items, and a re-certification of 120 rejected pairs;
> `run_ws.sh` re-verified the 56 whitespace-rejected outputs. All counts below are final (`reviewer_checks/tally_output.txt`).
> One interaction with the study's D9 reruns: the rejected-pair sample was drawn at about 13:03 while D9 was rewriting
> `data/certify/bench_minif2f__lean_workbook.jsonl`, so it contains 2 Lean-Workbook pairs certified under the *fixed*
> extraction (`lw34298`, `lw1195`; rejected both before and in my rerun) and 58 pre-D9 pairs; this changes nothing.


The preregistered decision rule was applied exactly as written, the primary number reproduces to the digit, and the
timeline in git shows the design changes (D1-D5) landed before the outcomes they could have been tuned on. The
"Refuted" verdict for H1 as preregistered (a >= 10 pp extra pass@32 drop) is therefore defensible. But the report
cannot be published as it stands:

1. one of the seven corpora (Lean Workbook) was never actually checked: an extraction bug left `:= by sorry` on every
   one of its 105,068 statements, so all 1,915 candidate pairs are "unchecked" and the reported "0 leaks" is an artefact;
2. the explosion guard (D3b) does not catch the case it was written for: `(a : ℝ) : a = 0` and other false
   single-binder statements are still certified as L2 "leaks" in `leak_pairs_bench_minif2f.csv`;
3. the plan's "documented training corpus" for DeepSeek-Prover-V2 omits a documented one: both the DeepSeek-Prover-V1.5
   and the V2 papers say miniF2F-valid was used in training, so half of DeepSeek's "clean" arm is documented-leaked;
4. the headline interpretation ("whatever the models learned survives simple rewording", "even there the effect is
   small") is contradicted by the study's own per-sample data for the two provers with near-verbatim leaks
   (DeepSeek: +6.8 pp, STP: +13.6 pp extra drop in solve rate, both with one-sided lower bounds above 0). pass@32 sits
   at a 100% ceiling for those arms, which is why the primary metric cannot see it.

None of these changes the pass@32 verdict (I recomputed it under every alternative below and it stays well under
10 pp), but 1-2 change the leak map, 3 changes what the primary contrast measures, and 4 changes what the report is
allowed to conclude. Concrete fixes are given per issue.

## Numbered issues

### A. Leak certification (brief item 1)

**1. Lean Workbook was never certified (blocking; leak map wrong).** `code/extract.py` line 90 appends `" := by"` to
each Lean-Workbook `formal_statement`, but those statements already end in `:=  by sorry` (two spaces). `statement()`
looks for the single-spaced `":= by"` first, finds the appended one, and keeps `:=  by sorry` inside the statement.
Result: 100% of `data/statements/lean_workbook.parquet` rows contain `sorry`; `certify.prop()` produces
`(∀ ..., ... :=  by sorry)`, nothing elaborates, and `data/certify/bench_minif2f__lean_workbook.jsonl` is 1,915 x
`"unchecked"` (likewise for the three secondary benchmarks). The L0 test also cannot fire because `norm` carries the
suffix. After stripping the suffix I find 2 L0 miniF2F items in Lean Workbook (`test/algebra_absapbon1pabsapbleqsumabsaon1pabsa`
= `lw9150`, a *test* item, and `valid/amc12_2001_p2` = `lw133722`) and 89 MinHash candidates with Jaccard >= 0.5 that
were never certified. Lean Workbook is a documented training source for STP (model card), DeepSeek-Prover-V1.5 (SFT
data), Goedel-V1 (Goedel-Pset-v1 includes 140K Lean Workbook statements) and Kimina, so the row matters even though the
plan's own-corpus mapping does not use it. *Fix:* strip `:=\s*by\s*sorry$` in `extract.py` (or stop appending `:= by`),
re-run `retrieve.py` and `certify.py`/`recheck.py` for `lean_workbook` on all four benchmarks (about 1 CPU-hour), regenerate
`leak_rates.csv`, the "any corpus" counts, Figure 1 and the leak map in the report. Also report the unchecked rate:
3,448 of 27,370 miniF2F candidate pairs (12.6%) were unchecked; 1,915 are this bug, the rest are statements with
undeclared variables (autoImplicit) that are silently dropped as potential leaks.

**2. The explosion guard (D3b) is insufficient; the published L2 list contains false training statements (blocking
for the leak list).** D3b says implications from refutable training statements were excluded and cites
`∀ a : ℝ, a = 0` as the motivating example. That exact statement is still in the final leak list:
`test/algebra_sqineq_at2malt1` is L2-leaked from Goedel-Pset-1222881 (`(a : ℝ) : a = 0`), -982374 (`a = 4`),
-722447 (`a ≠ 3`), -1618977 (`a = 6`) and sft400869 (`a = 50`); `recheck_bench_minif2f__goedel_pset.jsonl` has
`ab_inf: true` for all of them (both in the D3a and the final D3b files, so D3b changed nothing for them). Other
survivors of the same kind: `valid/mathd_numbertheory_136` <= `(n : ℕ) : n = 320` (sft55303),
`valid/induction_divisibility_3divnto3m2n` <= `(n : ℕ) : 2 * n = 2`, `valid/numbertheory_2dvd4expn` <= `0 < k → k ≤ 4 → k = 2`,
`valid/numbertheory_prmdvsneqnsqmodpeq0` <= `0 < n → 2 * n ≤ n`, `test/numbertheory_2pownm1prime_nprime` <=
`0 < n → Nat.Prime n → False` (Goedel-Pset-1640931), `test/mathd_numbertheory_100` <= a statement concluding `n = 356`,
`test/amc12b_2002_p4` <= `(1/2)^n = 1/64 → n = 6`, `test/induction_sumkexp3eqsumksq` <= `¬∃ k, n = k^2 + k^3`.
The mechanism: `(∀ a) → False` is not provable by the portfolio because `simp_all`/`aesop` cannot instantiate a
universally quantified false equation with no term in scope, but in the implication the test's own binders supply the
term and `simp_all` rewrites the goal with `h a : a = 0`. In Lean I confirmed for `n = 320` that the study's
`recheck.refutable` returns False while `exact absurd (h 1) (by norm_num)` refutes it, and for `Prime n → False` that
the same portfolio proves train ⇒ ¬test (explosion). A related case is a *benchmark* statement with a contradictory
hypothesis: `valid/mathd_numbertheory_35` has `h₀ : ∀ n : ℕ, n ∣ Nat.sqrt 196` (false at n = 3), so it is vacuously
true, any statement sharing the hypothesis is "L1-equivalent" to it (sft75023 is), and every prover scores 100% on every
version of it. The vacuity study next door catalogued such items; cross-reference it and drop vacuous items from the
units. Across all 649 L1/L2 pairs (433 L1, 216 L2; both Lean environments) the re-check found 11 spurious pairs: 8 of
43 Goedel-Pset L2 pairs, 2 of 65 SFT-v2 L2 pairs and 1 of 69 SFT-v2 L1 pairs; 0 of the 29+3 DeepSeek-V1, 20+2
Lean-workbook-proofs, 83 Pset-L1, 55+20 NuminaMath-LEAN and 177+83 STP pairs. 7 are explosions (train ⇒ ¬test also
certifies), 6 have witness-refutable training statements (3 both); the study's own `refutable` returned False for all
649. Removing them drops Goedel-V2's own-corpus leaked items from 99 to 95 (`test/amc12a_2002_p6`,
`test/mathd_numbertheory_435`, `valid/mathd_numbertheory_136`, `valid/mathd_numbertheory_35`), Goedel-Pset from 67 to
63 items, SFT v2 from 61 to 58, and "any corpus" from 252 to 250; Kimina's, DeepSeek's and STP's leak sets are
unchanged. So the published L2 tier is about 5% spurious, concentrated in the autoformalised Goedel corpora, and the
primary contrast loses 4 of 170 leaked units (see the table; the negation test
`train ⇒ (∀ B_test, ¬C_test)` and a small-witness refutation were run on every pair). *Fix:*
add to `recheck.py` (i) the negation test: an implication counts only if `a ⇒ ¬b` is *not* provable by the same
portfolio (if both `a ⇒ b` and `a ⇒ ¬b` certify, `a` is inconsistent with the test's binders), and (ii) a witness
refutation (`exact absurd (h 0/1/2/...) (by norm_num|decide)`), then rebuild tiers. Correct the D3b entry, which
currently claims the guard was verified on this example. Expect the L2 column to shrink (Goedel-Pset and SFT v2 most),
and re-run `analysis.py` since 38 of Goedel-V2's 99 leaked units and 13 of Kimina's 55 rest on L2 only.

**3. L2 semantics should be stated.** Of the 216 L2 pairs, 119 are "test conclusion ∧ extra conjuncts" (STP
conjectures and Goedel scaffolded variants of the form `original ∧ junk`), 21 have the same conclusion with fewer
hypotheses, 20 are iff versions, 17 are genuinely more general, and 39 are "other" (most of the spurious pairs above are
here). "The training statement is at least as strong" is literally true for the conjunction pairs, but a reader
imagining "a stronger theorem" will be misled; say that most L2 are the benchmark statement with extra conjuncts.

**4. Guards are portfolio-relative and the "69 automation-provable items" number is mislabelled.** The 69 comes from
D1's `b_trivial` flag (smaller SELF portfolio, 20 s, only computed for items that had a certified implication), not from
the operative D3a FREE check. The FREE check on all 488 items gives 80 provable, 406 not, 2 timeouts (60 s each, Lean 4.9); 68 of the D1's 69 are
among them, 12 FREE-provable items carry no D1 flag, and 1 D1-flagged item is not FREE-provable. The design property
holds: every leaked unit whose item is FREE-provable (Kimina 3, STP 35) is leaked through L0 only.
Report that number instead, and make clear that "not provable alone" means "not by this portfolio in 60 s", so a
training statement can still be counted as a leak when the implication only encodes a shared trivial step.

**5. False negatives are large and the report under-states them.** Using the study's own certified reformulations as
known equivalents: the retrieval rule (MinHash >= 0.3 or identical numerals + half the identifiers) would retrieve only
58% of R1 variants (renamed variables, reordered hypotheses) and 44% of R2 variants, before the top-10 cut
(median MinHash Jaccard of R1 against its original is 0.34). Add the 12.6% unchecked pairs, 20 s certification timeouts
under contention (D3) and the numeral cap (D2). "Leaks are a lower bound" is right but should quantify: a renamed copy
of a miniF2F item in a corpus has roughly a coin-flip chance of being found. This also means the "clean" arm contains
undetected equivalents, which attenuates the DiD toward zero.

**6. Reproducibility of the certification itself is good.** Re-running `certify.check` on every L1/L2 pair reproduced
all 649 (649/649 train ⇒ test, 433/433 test ⇒ train for L1), with 0 timeouts and 0 errors on uncontended cores. A
random sample of rejected pairs (60 certification-rejected and 30 recheck-rejected in Lean 4.9; 20 and 10 in 4.15)
reproduced too: 0 of the 80 certification-rejected pairs certify on rerun, and all 40 recheck-rejected pairs still
certify as implications but are correctly uninformative (39 of 40 test statements are FREE-provable; the remaining one,
`valid/mathd_algebra_267` × Goedel-Pset-1645673, has a refutable training statement). No evidence of false negatives
from timeouts in the sample. The informativeness check's fail-closed timeouts are a source of missed leaks but not of
false leaks.

### B. Reformulations (brief item 2)

**7. For 83 of 488 items, R1 is textually identical to the original.** Items without binders (e.g.
`theorem mathd_numbertheory_101 : 17 * 18 % 4 = 2`) have nothing to rename or reorder, so "R1" is the same prompt
sampled a second time; it is certified "equivalent" trivially. The report describes R1 as "fresh names for every
variable and hypothesis, with hypotheses reordered", which is false for 17% of items, and `pass32_ref` averages this
non-reformulation with R2. By arm: DeepSeek 0/16 leaked and 25/150 clean; Goedel 7/99 and 27/150; Kimina 5/55 and
27/150; STP 37/179 and 46/305. Dropping these R1 versions moves the pooled DiD from +1.33 to +1.36 pp (n 167/431), so
the verdict is unaffected, but the design description must be corrected and the versions excluded (units whose only
reformulation is an identical R1 should be dropped).

**8. The equivalence certification of R1/R2 is sound as far as it goes** (both directions, same portfolio with `symm`
branches; 869/976 in 4.9 and 863/976 in 4.15; 484 and 483 items with at least one). Two R2 rows show the transformer
can produce odd spacing (`(hyp4 : 13 / 2 = v₁ )`) and duplicated hypothesis names (`valid/aime_1994_p4` has two `h₀`,
which R1 maps to two `hyp1`); both are legal Lean but cause issue 10.

### C. Sampling and verification (brief item 3)

**9. Prompts are close to, but not, the model cards.** All three cards (`data/models/cards/*/README.md`) use
`set_option maxHeartbeats 0`; `sample.py` uses `400000` (DeepSeek-Prover-V1.5's benchmark header). Kimina's card has no
blank lines in the header and ends at `:= by`; the study adds blank lines. STP's corpus prompts use `maxHeartbeats 0`;
`STP_HEADER` uses 400000. The chat templates, the CoT instruction, the system prompt for Kimina, temperatures (1.0/0.95;
Kimina 0.6/0.95) and token caps (8,192; card: 8,192 / 8,096 / 32,768) match. None of this biases the DiD (identical
across versions), but "each model's documented prompt" should be "the DeepSeek-Prover-V1.5 miniF2F header with each
model's documented instruction".

**10. "Changed statement" rejections include valid proofs rejected for whitespace, and they fall on reformulations.**
`verify.py` compares whitespace-collapsed text, so a model that writes `v₁)` where R2 has `v₁ )` is rejected. Of
Goedel's 121 rejections 42 are whitespace-only (all R2: 22 clean, 20 leaked); of DeepSeek's 43, 14 (R1/R2 only); of
Kimina's 13, 0, but 9 of them are the `hyp1 hyp1` item (`valid/aime_1994_p4`) where the model renamed the shadowed
hypothesis. Re-verifying the
56 whitespace-only outputs in Lean: 37 are valid proofs (Goedel 31 of 42, DeepSeek 6 of 14; all R2) that were
scored as failures. No pass@32 unit flips (every affected item-version already had another passing sample), so the
verdict is unaffected, but the R2 per-sample rates are biased down by about 0.5 pp. The effect on pass@32 is at most one unit
(`test/amc12b_2020_p6|R1` for DeepSeek has pass@32 = 0 and a whitespace-rejected output), so the verdict is safe, but
the per-sample rates for R2 are biased down by up to 0.5 pp and the fix is trivial: strip spaces before `)`/`]`, or
compare the parsed binders and conclusion.

**11. Tokenizer issues (D5, D7) are resolved for the runs used.** I scanned every decoded output of the four final
sample files: 0 `Ġ`/`Ċ` artefacts in 117M (DeepSeek), 187M (Goedel), 170M (Kimina) and 9.8M (STP) characters, 2 U+FFFD
in DeepSeek. Outputs are well-formed CoT + ```lean4 blocks (Kimina: `<think>` then one block). The invalid D7 run is
indeed garbage (14,407 "no code" of 14,688). Every item-version has exactly 32 verified outputs, no duplicates.

**12. Other verification checks are correct**: last ```lean4 block; `sorry`/`admit`/`native_decide`/`axiom` banned by
regex (all 869 Kimina "banned" are `native_decide`, as D8 says); axioms restricted; truncated = failure; STP's statement
is prepended so it cannot restate; no helper-lemma-after-main false rejections (0 rejected blocks contain two theorems).
Environments match the provers' papers (Lean 4.9.0 for DeepSeek/Goedel/STP, 4.15 for Kimina). Verification uses the
model's own `set_option maxHeartbeats 400000`. The watchdog affected at most 22 outputs (log checked).

### D. Decision rule, timeline, bias (brief item 4)

**13. The rule was applied correctly and the number reproduces.** Independent recomputation from
`data/verified/*.jsonl` + `leak_status_by_prover.csv`: DiD = +1.33 pp, one-sided 95% bounds −0.79 / +3.50 (study:
−0.75 / +3.50; bootstrap seed differs), n = 170/450, mean d +0.88 / −0.44, SD(d) 0.135; MDE(design) 6.72 pp,
MDE(observed SD) 3.02 pp. Per-prover and all secondary rows reproduce to two decimals. `verdict()` implements the plan's
table in order. Two presentation points: (a) `mde.json` records 6.09 pp (n_clean = 1,294, before the 150-clean
subsample) while D4 and the verdict use 6.72; say so; (b) reporting the 5th and 95th percentiles together is a 90%
two-sided interval; call it that, or report only the one-sided bound the rule uses.

**14. Timeline is clean.** Commits: D1 09:42 (7 Oct), D2 12:03, scripts 12:30, D3 14:36, D3a/D3b/D4 14:53:08 (8 Oct);
`gpu_main.log` shows the first (broken-tokenizer) STP request at 14:56:09 and DeepSeek at 14:59:35, so the cap, guards,
clean subsample, token cap and STP addition precede all scored sampling. `analysis.py` was committed 23:50 on 9 Oct;
Goedel's and the invalid DeepSeek's verification files existed by then (16:36 and 01:28 on 9 Oct) but Kimina's did not
(01:04 on 10 Oct), so "before any verification result is read" is plausible but unverifiable; say "before the pooled
analysis was first run". After D7 the only code changes are the `--no-stp` switch and the artefact abort (diff
7657ea0..a1797f1 checked). D3-D3b were run in 15 minutes (14:36-14:51) and the recheck files have the right key sets.

**15. The clean arm is contaminated by documented training data (DeepSeek), and the primary contrast is driven by
validation items.** DeepSeek-Prover-V1.5 (arXiv 2408.08152): the SFT data includes "validation sets from the miniF2F
and ProofNet benchmarks"; DeepSeek-Prover-V2 (2504.21801): "the miniF2F-valid problems are incorporated into
curriculum learning". The plan calls DeepSeek-Prover-V1 "its documented public lineage", but miniF2F-valid is equally
documented, and 74 of DeepSeek's 150 "clean" items are valid items (clean-valid pass@32 77% vs clean-test 68%). STP's
base model (DeepSeek-Prover-V1.5-SFT) and STP itself trained on miniF2F-valid (arXiv 2502.00212: "we combine
LeanWorkbook, miniF2F-valid, and ProofNet-valid as the training dataset"), consistent with the 173 L0 items. Goedel's
clean-valid vs clean-test gap (89% vs 86%, per-sample 77% vs 62%) suggests the same, undocumented. Recomputed:
test items only, DiD = +0.03 pp (−2.0, +2.0; n 79/227); valid items only, +2.42 pp (−1.0, +6.0; n 91/223); DeepSeek with
valid counted as leaked, pooled +0.47 pp (−1.4, +2.4), DeepSeek alone −0.45 pp (−4.8, +3.8). *Fix:* add miniF2F-valid to
DeepSeek's own corpora (it is documented), report the test-only DiD as the cleaner contrast, and say in the caveats
that for every prover the valid split is probably trained on.

**16. "Leaked" is confounded with "already solved by the model family".** Four corpora consist of verified proofs
(SFT v2, Lean-workbook-proofs, DeepSeek-Prover-V1, STP_Lean_0320), so an item is "leaked" only if the pipeline that
built the corpus proved it. The STP arm shows this starkly: miniF2F-valid items with an STP proof in the corpus are
solved 100%; the 68 valid items *without* one are solved 1.5% (they are the ones STP failed on during training). The
report's "leaked problems may simply be easier" is too weak; it is a selection on the outcome, and it also explains why
Goedel's Pset-based leaks (statements, not proofs) are solved *less* often than clean items.

### E. Numbers in report.md (brief item 5)

**17. Every number I checked matches the tables**: leak map (all 32 cells), 252/51.6%, 20%/11%/3%, 484/483, +0.9/−0.4,
+1.3 (−0.7, +3.5), 6.7 and 3.0 pp, the per-prover and robustness rows, the solve-rate table, 2.1% max changed statement,
truncation 13-18% / 15-22%, 22 watchdog kills, 869 `native_decide`, corpus sizes, benchmark sizes (488/488/371/672), the
19 revised items, 5 L0 Numina test items, 22 PutnamBench. Two numbers are wrong for other reasons: "Lean Workbook 0"
(issue 1) and "69 automation-provable" (issue 4). One preregistered secondary is missing: the sample-level mixed logistic
model (plan section 5) is neither reported nor in `analysis.py`; add it or say why not.

### F. Interpretation (brief item 6)

**18. The per-sample results contradict the prose, and the pass@32 ceiling is why.** Leaked arms for DeepSeek and STP
are at 100% pass@32 on *every* version, so d is identically 0 there and the primary metric cannot register any
degradation short of all 32 samples failing. On the preregistered per-sample secondary (which the report lists but does
not discuss), by prover: DeepSeek +6.8 pp (one-sided bounds +0.3, +15.5), Goedel +0.9 (−1.0, +2.9), Kimina +1.7
(−0.9, +4.4), STP +13.6 (+10.8, +16.5); the pooled +1.5 (−0.1, +3.1) is dominated by Goedel's 99 units. Per version
(genuine reformulations only), the leaked-arm solve rate for DeepSeek goes 95.5% → 90.0% (R1) → 79.7% (R2) against
53-62% → 52-54% for clean; for STP 92% → 80% → 68% against 28-36% → 27-33%; the rate DiD for R2 is +8.2 pp (DeepSeek)
and +22.0 pp (STP). So the two provers whose leaks are near-verbatim do lose markedly more on rewording, with a
dose-response (R2 > R1), exactly the memorisation signature H1 posits, while the two whose leaks are autoformalised
equivalents (Goedel, Kimina) do not. The sentences "Whatever the models learned from them survives simple rewording"
(plain terms), "Rewording barely moves either group" and "even there the effect is small" (STP) must go. The honest
statement is: *at the preregistered pass@32 threshold of 10 pp, refuted; at the sample level the leaked items of the
near-verbatim provers lose 7-14 pp more, so surface memorisation is present but does not change which problems are
solvable at 32 samples.*

**19. Scope of "Refuted".** The verdict should carry its scope in the tag and the title: it refutes a >= 10 pp
pass@32 effect of *surface* rewording (renaming, reordering, flipping equalities), for leaks *defined against the
public lineage*, with a clean arm that is partly trained on. It does not answer the title's question "Does training-set
leakage explain how AI provers score on miniF2F?"; the design cannot, because (a) memorised proofs survive renaming, (b)
the clean arm is not clean (15), (c) leaked items are selected for solvability (16). Suggested tag: "Refuted (surface
rewording, pass@32)". The related work should be used: MiniF2F-ALF (arXiv 2606.12594) reports that every prover loses
accuracy on mutated statements, and "Right symmetries" (2605.22257) that LLM provers show large variation across
equivalent formulations; both use deeper rewrites than R1/R2, which is the natural reading of the null here.

**20. Smaller interpretation points.** (a) Kimina's own corpus is indirect: NuminaMath-LEAN trained Kimina-Prover-72B,
and the 8B is distilled from 72B rollouts; say "lineage" as for DeepSeek. (b) The 5 miniF2F *test* statements verbatim
in NuminaMath-LEAN (two human-authored `math_test`, two autoformalised `olympiads`, one `unknown`) despite the Kimina
paper's documented 13-gram decontamination is one of the most useful findings here and deserves a sentence. (c) "L1 and
L2 leaks ... which text-level decontamination can miss" is fair, but many L1 pairs differ only in a hypothesis name and
a 13-gram filter on the formal text would catch them; the miss is because decontamination is run on informal text.
(d) The leaked-vs-clean level differences are appropriately hedged except for the selection point (16).

**21. What the provers' own papers say (for the caveats).** DeepSeek-Prover-V2 reserves ProofNet-test "exclusively
for evaluation" because ProofNet-valid variants are in its public data, and puts miniF2F-valid into curriculum
learning; DeepSeek-Prover-V1.5 lists miniF2F-valid and ProofNet-valid in its SFT sources; STP trains on LeanWorkbook +
miniF2F-valid + ProofNet-valid and reports 57.2% vs 61.2% pass@128 with/without the validation sets; Goedel-Prover-V2's
paper contains no decontamination statement and calls Goedel-Pset-v1 low quality; Kimina decontaminates the *informal*
Numina Math 1.5 problems by 13-gram overlap and by removing AMC12/AIME/IMO problems whose sources overlap miniF2F-test,
which is consistent with formal copies of two MATH-sourced and two olympiad-sourced test items surviving in
NuminaMath-LEAN. The report should say that miniF2F-valid is a training set for at least two of the four provers by
their own documentation, and treat the valid half of "miniF2F" accordingly.

**22. Checks that came out clean on the certification mechanics.** `set_option autoImplicit false` is in every
certification header, so undeclared names cannot be shared across the two sides (they become "unchecked"); bare `π` is
rewritten to `Real.pi` on both sides and in verification; coercion-differing pairs I inspected (`x : NNReal` vs
`x : ℝ, 0 ≤ x`; `Nat.gcd` vs `Int.gcd`/`Nat.Coprime`; `↑j` vs `j`) are genuine implications; the `∀`-prop encoding
elaborates the binders as the theorem would. The portfolio's `apply h <;> ...` discharges the training statement's
hypotheses from the test's, which is the right direction for L2.

## Recomputed numbers

| Quantity | Report / tables | Reviewer |
|---|---|---|
| Primary DiD, pass@32, pooled | +1.33 pp (−0.75, +3.50); 170/450 | +1.33 pp (−0.79, +3.50); 170/450 |
| mean d leaked / clean; SD(d) | +0.88 / −0.44; 0.135 | same |
| MDE design / observed-SD / mde.json | 6.72 / 3.02 / 6.09 pp | 6.72 / 3.02 / 6.09 (n_clean 1,294) |
| Per prover pass@32: DSP / Goedel / Kimina / STP | +1.0 (−1.3,+3.3) / +1.0 (−1.0,+3.4) / +1.2 (−3.6,+6.1) / +3.5 (+1.0,+6.2) | +1.00 (−1.30,+3.29) / +1.01 (−0.96,+3.31) / +1.24 (−3.60,+6.09) / +3.53 (+1.04,+6.19) |
| Per-sample DiD pooled | +1.5 (−0.0, +3.1) | +1.50 (−0.08, +3.07) |
| Per-sample DiD per prover | not reported | DSP +6.84 (+0.31,+15.52); Goedel +0.94 (−1.00,+2.85); Kimina +1.73 (−0.85,+4.39); STP +13.59 (+10.82,+16.49) |
| Rate DiD by version (genuine reforms) R1 / R2 | not reported | DSP +3.8 / +8.2; Goedel +0.4 / +0.5; Kimina +0.3 / +4.5; STP +10.7 / +22.0 |
| Pooled DiD excluding identical-R1 versions | – | +1.36 pp (−0.76, +3.56); 167/431 |
| Pooled DiD, test items only / valid only | – | +0.03 (−2.01, +2.04); 79/227 / +2.42 (−0.97, +5.97); 91/223 |
| Pooled DiD, DSP valid counted leaked | – | +0.47 (−1.40, +2.38); 244/376 (DSP alone −0.45 (−4.75, +3.75)) |
| L0/L1 only; any corpus; excl. 19 revised | +2.2 (−0.0,+4.7); −0.1 (−2.1,+1.8); +1.0 (−1.1,+3.1) | reproduced |
| Items with R1 == original | not reported | 83 / 488 |
| Reforms certified (4.9 / 4.15) | 484 / 483 items | 869 and 863 pairs; 484 / 483 items |
| Leaked items, any corpus, by best tier | 252 | L0 185, L1 47, L2 20 (= 252) |
| L2 pair types (216) | – | 119 "test ∧ extras", 21 same concl., 20 iff, 17 more general, 39 other |
| Spurious L1/L2 pairs (explosion or witness-refutable train) | 0 assumed | 11 of 649 (8/43 Pset L2, 2/65 SFT L2, 1/69 SFT L1, 0/472 others); Goedel-V2 leaked 99 → 95; any corpus 252 → 250 |
| Certifications reproduced (train ⇒ test; test ⇒ train on L1) | – | 649/649; 433/433; rejected sample 0/80 certify, 40/40 recheck rejections justified |
| Test statements provable alone by FREE (Lean 4.9) | 69 (D1 flag) | 80 proved, 406 not, 2 timeouts; D1 overlap 68 |
| Lean Workbook pairs checked | 0 of 1,915 ("0 leaks") | 0 checked; 2 L0 after the fix; 89 strong MinHash candidates uncertified |
| Candidate pairs unchecked | not reported | 3,448 / 27,370 (12.6%) |
| Retrieval recall on R1 / R2 variants | – | 58% / 44% (threshold only, before top-10) |
| Changed-statement rejections whitespace-only | – | Goedel 42/121, DSP 14/43, Kimina 0/13; re-verified valid: 31 + 6 = 37 of 56 (all R2); 0 pass@32 flips |
| Clean-arm pass@32, valid vs test (orig) | – | DSP 77 vs 68; Goedel 89 vs 86; Kimina 72 vs 72; STP 1.5 (68 items) vs 55 |
| Decoded-output artefacts (Ġ/Ċ) | fixed (D5, D7) | 0 in all four final sample files |
| Watchdog kills; Kimina banned = native_decide | 22; 869 | 22; 869 |

## What is sound

The preregistration, the deviation log with timestamps, the fail-closed guards, the Lean-kernel certification idea,
the item-cluster bootstrap, the disclosure of the D7 preliminary result, the statement-match check, the archived invalid
runs and the published pair list are all good practice and reproduce. The primary verdict under the preregistered rule
stands. The problems are in (i) one corpus's extraction, (ii) the L2 guard, (iii) which corpora count as "own", and
(iv) the prose, which claims more than the pass@32 metric can support and less than the per-sample data show.

## Minimal path to publishable

1. Fix `extract.py` for Lean Workbook; re-run retrieval + certification + recheck for that corpus (all benchmarks).
2. Add the negation test and witness refutation to `recheck.py`; rebuild tiers; re-run `analysis.py`; correct D3b.
3. Add miniF2F-valid to DeepSeek's own corpora (documented); report test-only DiD alongside the pooled one.
4. Drop identical-R1 versions; fix the whitespace comparison in `verify.py` (re-verify the 56 outputs or re-run).
5. Report per-prover per-sample DiDs and the ceiling; rewrite the three sentences in issue 18; scope the verdict tag;
   add the missing mixed model (or a note); replace "69" with the FREE count; state L2 composition; correct the prompt
   description; note mde.json vs D4.
