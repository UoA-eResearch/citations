# Confirmation pass — fixes at `a0aaff1`

Reviewer: same independent adversarial pass (Fable 5.1), 2026-10-14, against `a0aaff1` (D11).
Checked against draft `04c7f25` and the 19 issues in `review/review.md`.

## Recommendation: **publish with edits** — 5 items remaining, all small

**17 of 19 issues are properly fixed.** One (12) is not fixed although D11 says it is. One (7) was *done* — the
preregistered check was actually run, which I could not do — but the conclusion drawn from it is wrong in a way
that matters, and fixing it makes the sampling arm's argument stronger rather than weaker. I also found two
surviving traces of withdrawn claims (the thing I checked for in D10 and should have checked harder here), one
stale table, and one presentational over-correction. None of this touches the verdict.

**And one correction to my own review:** on (d) you are right and I was wrong. See §D.

| | |
| --- | --- |
| Fixed and verified | 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19 |
| Done but the conclusion drawn is wrong | **7** (`repro.csv`) → R1 |
| Not fixed, though D11 says it is | **12** (B1 per-axis variant switch) → R5 |
| New residual items | R2 (two withdrawn-claim traces), R3 (multiplicity), R4 (stale table) |

---

## A. Answers to your four questions

### (a) Is the new mechanism framing correct, or merely different? — **Correct.**

I re-derived it independently and it holds. The mechanism is exactly as the report now states it: the model and B1
are tied on telling the ceiling block from real binders, that subtask carries ~27 % of P1's weight, and every
statistic that avoids it separates them. The report's sentence "Exactly two rows fail to exclude zero, and they are
the same fact twice" is the right reading.

Your numbers and mine reconcile **exactly** once the aggregator is accounted for — and the cause is not tie
handling, as you guessed. It is mean vs median:

| statistic | my median (review) | my mean | report |
| --- | --- | --- | --- |
| concordance (uncensored) | 0.6688 | **0.6532** | 0.653 |
| AUC ceiling vs binders | 0.7332 | **0.7240** | 0.724 |
| NDCG | 0.8813 | **0.8638** | 0.864 |
| NDCG@3 | 0.7224 | **0.6927** | 0.693 |
| NDCG@5 | 0.7444 | **0.7088** | 0.709 |
| B1 concordance | 0.6055 | **0.6036** | 0.604 |
| B1 AUC | 0.7331 | **0.7113** | 0.711 |

I reported medians; `paired_vector_difference` uses `np.nanmean`, so your point estimates and intervals are
internally consistent (both means) and your implementation is correct. Worth knowing that on the median the AUC
comparison is an even more perfect dead heat (0.7332 vs 0.7331) than on the mean (+0.013), so "a dead heat" is
well supported either way. Minor presentational note: the "model" column of the rank-statistics table is a median
for P1/P2 and a mean for the other seven rows — worth a footnote so a reader recomputing it lands on your numbers.

**One wording caution.** "P1 understates the model" and "the preregistered primary was the wrong instrument" are
slightly tilted. P1 is a legitimate statistic: for a triage user, separating binders from non-binders genuinely is
part of the job, and P1 measures the composite job honestly. What is true is that **the model's advantage over
these baselines is concentrated in one of P1's two components**, and P1 averages it away. I would say that rather
than "wrong instrument" — it is the difference between "the statistic was badly chosen" and "the statistic is a
composite, and here is which part carries the difference". The latter is both more accurate and less vulnerable.
The report's own guard ("a lesson about the preregistration, not a licence to pick the flattering number") is
exactly right and should stay.

### (b) Does the withdrawn floor recommendation leave traces? — **Two traces survive.**

The correction itself (l. 236–248) is exemplary — the P2 columns, "It is not", and the explicit admission that an
earlier draft built a recommendation the data would not support. But:

1. **l. 393** still reads "its advantage is concentrated at the top of the ranking **and in its floor** rather
   than spread across the profile." That directly contradicts l. 246–247 ("The floor gap is another consequence of
   the ceiling block, not a separate property"). This is the same class of leftover D10 was written about.
2. The whole paragraph at l. 390–397 reads like the pre-D11 draft: it gives the P1 null and the floor as the two
   findings and never mentions that seven other statistics separate the model from B1 with intervals excluding
   zero. So the summary section now **under**-states the results section — see (c).

Also: **issue 4's wording survives in the plain-language summary.** l. 45 still says the model flattens "between
any two kinases ... whether they are near-twins or unrelated proteins". Both halves are the claim D11 agreed to
retire: "any two kinases" (6 of 496 pairs are expanded, ratios to 1.32) and the assertion of uniformity ("whether
they are near-twins or unrelated"), which is now only "no dependence detectable". The abstract (l. 11, "a typical
pair") and the geometry section (l. 286, 309) are both correctly fixed; the plain-terms section was missed — and
it is the part most people read.

### (c) Has the pendulum swung too far? — **In presentation, slightly; in conclusion, no.**

The conclusion is sound. It rests on three comparisons that are large and robust — P2 +0.171 (+0.065, +0.292),
NDCG@3 +0.196 (+0.096, +0.296) and top-1 +0.375 (+0.188, +0.562), all against B1 — and any one of them carries
the argument alone. I would not soften that.

But the presentation implies more independent confirmation than exists. `primary.json` now holds **16 post-hoc
comparisons** (7 statistics × the baselines where defined), bolded where they exclude zero, with no multiplicity
statement anywhere in the report. Of those 16:

- three do not exclude zero: concordance vs B2 +0.037 (−0.010, +0.082), AUC vs B1 +0.013 (−0.061, +0.090), AUC vs
  B2 +0.038 (−0.030, +0.115);
- **five are marginal** — lower bound under +0.025 — and would not survive a correction over 16 tests: NDCG vs B2
  (+0.012), concordance vs B1 (+0.014), P2 vs B2 (+0.017), NDCG@3 vs B2 (+0.019), NDCG vs B1 (+0.021).

So about a third of the "wins" are bolded on a lower bound that a Bonferroni step would erase. The honest fix is
one sentence, not a reanalysis: say these are 16 post-hoc comparisons on one panel with no multiplicity
correction, that the conclusion rests on the three largest (all against B1), and bold only those. The abstract
should also note the seven statistics were chosen after seeing P1 — the body says so at l. 233, the abstract's
"it wins on every statistic tried" does not, and "tried" is carrying a lot of weight.

Pulling the other way, l. 393 (above) over-corrects *conservatively*. Fix both and the report is balanced.

### (d) The 6-vs-1 expanded-pairs discrepancy — **you are right, I was wrong.**

6 of 496 pairs have a predicted/measured ratio above 1: **1.3187, 1.1655, 1.1278, 1.1035, 1.0018, 1.0012.** My
review's "One pair is expanded, not compressed" was sloppy — I read off the maximum (1.3187) from my ratio-range
output and asserted a count I had never computed. The report's "6 of 496 pairs are predicted *further* apart than
they measure" is correct and my review's §A.4(c) should be read as wrong on that number. The substantive point it
was attached to (ratios run 0.25–1.32, so "halves any two" is false) is unaffected.

---

## B. The one item that needs real attention

### R1 — `repro.csv` does not show what the report says, and the sampling-arm argument should be rebuilt on a better number

You ran the check I could not, and that is a genuine improvement. But nobody compared the result against the
**stored panel value for the same pair**, and it does not match:

| | `affinity_pred_value` for `O00238__10113978`, seed 20261013 |
| --- | --- |
| `repro.csv` run a (1-complex directory) | 0.9130484461784364 |
| `repro.csv` run b (1-complex directory) | 0.9130484461784364 |
| **stored panel value (`pairs_panel.csv`, 1024-complex run)** | **0.8504559397697449** |
| difference | **0.0626 log units** |

Same pair, same seed, same flags, same weights, same MSA, byte-identical YAML. The only difference is the run
context. I ruled out the obvious confounders: this pair's structure pass wrote at 11:47 and its affinity JSON at
19:42 on 13 Oct, both inside the *first* panel run, so this is not the crash, the resume, or the vLLM-constrained
memory. The cause is either the position of the complex in the arm's RNG stream or non-deterministic GPU kernel
reductions under different batching — and for this purpose it does not matter which.

Three consequences:

1. **"Re-running one complex at the same seed reproduces the affinity value bit for bit, so the pipeline is fully
   deterministic" (l. 348–350) is false as stated.** It is bit-identical across two identical *single-complex*
   runs. It is not reproducible from `(arm, pair, seed)`, which is what a reader of the released
   `predictions.jsonl` will assume.
2. **D4 and D6 are falsified on this point** — D4's "makes each prediction reproducible from the pair alone" and
   D6's "a prediction is still reproducible from its arm and pair alone". Those sentences were the stated
   justification for deleting the 22 sharded decoy complexes, so the justification was weaker than believed (the
   decision itself was still right, for the simpler reason that two provenances in one arm is bad hygiene).
   This matters for the released artefact: someone spot-checking one released pair will be off by ~0.06 and
   conclude something is broken.
3. **The "0.128 against 0.156" comparison is not apples-to-apples.** 0.156 is a seed change within a 1-complex
   run; 0.128 is the mean absolute change between two 96-complex runs differing in *both* setting and run context.

**But the same data give you a better argument, and it points the same way.** The 0.0626 figure is a direct
estimate of run-to-run spread with **no seed change at all** — identical seed, identical settings, different run
context. That is the cleanest available noise floor, and the sampling arm's mean absolute change is 0.128, only
about twice it. So a large share of the movement between the two sampling settings is run context rather than the
setting, which supports "not a sampling artefact" more directly than the seed comparison does.

**Fix:** state that the value is reproducible given the same input set and seed but not from the pair alone, give
the 0.063 figure as the no-seed-change noise floor, correct D4/D6 in D11, and rebuild the sampling paragraph on
0.128-against-0.063. Add a line to the reproduction section warning that a single-pair re-prediction will not
reproduce a released value exactly. Dropping the "fully deterministic" phrasing is the essential part.

## C. The other four remaining items

**R2 — two surviving traces of withdrawn claims.** l. 393 ("and in its floor"), and l. 45 in the plain-language
summary ("any two kinases ... whether they are near-twins or unrelated"). Both are one-line edits. Worth also
bringing l. 390–397 into line with the results section, since it currently reports only the P1 null.

**R3 — multiplicity.** One sentence, and bold only the three load-bearing rows. See (c).

**R4 — the sensitivity intervals in the report table are stale.** You re-ran them at 2,000 draws and `primary.json`
now says kinase **0.3675–0.5782** and dyadic **0.3291–0.6237**; D11 quotes those correctly. But report.md l. 162–163
still shows the old 500-draw values **0.368–0.569** and **0.331–0.619**. The verdict is unaffected (both still
clear 0.25, and "the lower end of every interval sits above 0.25" remains true), but the table disagrees with the
stored results and with D11.

**R5 — issue 12 is not fixed.** D11 states "B1 LOO-vs-full switch disclosed with both numbers". It is not in
report.md, and not in D11 either. `assemble.py:132` still carries it only as a code comment. Specifically missing:
that B1's within-kinase cell is read off the *non*-leave-one-out variant (the LOO variant gives exactly −1.000000
there, a pure artefact of subtracting the ranked ligand from its own kinase mean, which is why that cell reads
"0.000 by construction"); and that B1 **without** the adjustment scores **0.4256** on P1 against **0.3856** with
it, so the choice shrinks the quoted margin from +0.018 to +0.058 and mildly flatters the model on the central
comparison. The choice is legitimate and predates the panel run (`bdd795d`, 10:04, panel started 10:33) — it just
needs saying. Two sentences.

Issue 6 (labelling B1 as using the measured panel) *is* fixed, and well — l. 199–203 carrying plan §7's caveat
is the single best addition in this revision.

## D. Verified fixed

Spot-checked each against the results files rather than taking D11's word for it.

| # | fix | verified |
| --- | --- | --- |
| 1 | P2 columns in both baseline tables; central claim names its statistic; censoring sentence corrected to "not propping the model up ... emphatically doing work in the comparison" | ✓ matches my +0.1712 / +0.1701 |
| 2 | Rank statistics implemented in `analysis.py` with the same paired bootstrap; mechanism restated | ✓ all seven reconcile exactly (§A.a) |
| 3 | Floor qualified to all cells, P2 floors tabulated, recommendation withdrawn, F1 annotated "uncensored cells it closes" | ✓ (but see R2) |
| 4 | Compression table one estimator (0.52 / 0.57); "no dependence detectable ... interval admits a large effect either way"; "typical pair" | ✓ (but see R2) |
| 5 | Crop gradient quantified with both directions; confidence filter reframed as "not an artefact of the worst-folded complexes, and no further" | ✓ ρ = 0.389 p = 0.028, 0.524 vs 0.389, 6 of 32 kinases retain no cells, 31.6 % vs 22.7 % |
| 6 | B1/B2 relabelled "(uses the measured panel)"; plan §7 caveat carried in | ✓ l. 199–203 |
| 8 | Budget 1,597 against ≈1,624; shortfall and the two `postcutoff.py` filters logged | ✓ |
| 9 | "plus the shard index" deleted | ✓ gone |
| 10 | "stopped twice" → once | ✓ |
| 11 | B0/B3 hit rates undefined; `hit_vectors` returns nan for a constant predictor; new column-order test | ✓ `primary.json` B0/B3 `top1 = nan`; **18/18** tests pass |
| 13 | Promiscuity "only 16 of the 32 ligands have a defined correlation"; union P3 = 0.379 flagged as crossing H2's floor | ✓ |
| 14 | HSP90 answered | ✓ |
| 15 | chance 0.096 | ✓ both tables |
| 16 | Sensitivity bootstraps re-run at 2,000 draws | ✓ in `primary.json` — but see R4 |
| 17 | Post-cutoff censoring 8.6 % counting both bounds | ✓ |
| 18 | Centring described as "cosmetic: a per-ligand constant cancels in the difference between two kinases" | ✓ exactly right |
| 19 | plan §2 literature carried in; Koch cited and reconciled; H4 restatement disclosed; Nesso-1 added | ✓ 4 Koch mentions, Nesso-1 in the table |
| — | Boltz doc scoping `affinity_pred_value` away from inactives, stated where the read-out is defined | ✓ l. 116–122, and it is the best-handled addition in the revision |

I re-verified that nothing broke: the panel still re-derives identically, P1 = 0.4435 (0.4182, 0.5324), the verdict
branch still fires Refuted, "protein-blind" is still correctly withheld, P3 = 0.4529 still clears H2's floor, and
`figures.py` regenerates its captions consistently with the committed files.

## E. Summary

The revision is thorough and, on the three substantive reversals, correct — including the parts that required
implementing statistics rather than quoting mine, and including the check I was unable to run. The remaining work
is five small edits: drop "fully deterministic" and rebuild the sampling paragraph on the 0.063 noise floor (R1),
two one-line trace removals (R2), one sentence on multiplicity plus de-bolding the marginal rows (R3), refresh two
stale interval cells (R4), and two sentences actually disclosing the B1 variant switch (R5).

The verdict — **Refuted** — is unchanged and remains well supported on every interval, and the central
contribution is now stated more accurately than in either previous draft.
