# Independent review: "Do AI autoformalizers copy the known mistakes in miniF2F and ProofNet?"

Draft reviewed: `report.md` at commit db0689f (12 October 2026). Preregistration: `plan.md` at 9afb62b. Reviewer: an
independent Claude agent, working read-only on the study directory; scratch scripts and dumps are under
`review/reviewer_checks/` (`recompute.py`, `show_outputs.py`, `lean_rerun.py`, `catalogue_dump.md`, `outputs_df.pkl`).

## Recommendation: **fix first** (the preregistered verdict stands; the interpretation, the plain-language summary and several disclosures do not)

The arithmetic is right. Every number in `primary.json`, `secondary.json`, `tiles.json`, the figure captions and the
report's tables was recomputed independently from `data/classified/*.jsonl` and matches (table at the end). The
preregistered rule, applied to the preregistered estimand, gives **Refuted** (RR 0.91, 95% CI 0.76-1.06, 204 vs 225
defect copies on 2,832 samples each), and the catalogue, twins and paraphrases are of good quality.

The problem is what the report says the result means. The study's own data contain direct evidence that at least one
model (Kimina) has memorised the ProofNet Lean 4 port and reproduces it, including a wrong constant that has no
counterpart in the problem text, *on the twins as well as the originals*. The twin design classifies exactly this
behaviour as a "natural habit". So the sentence in the verdict box, "The defects they reproduce are habits they show
whatever the numbers, not recall of the benchmark's statement", and the plain-terms line "The mistakes the models
make are common habits", are not supported; the test refutes recall keyed to the item's *numbers*, nothing more. The
report half-acknowledges this in "What the test cannot rule out", but the headline, the plain-language summary, the
by-category table and the "What this means" section all say the stronger thing. That has to be corrected before
publication, and the evidence below has to be reported. Several smaller disclosure and consistency problems are
listed after it. None requires re-sampling; all can be fixed from the data on disk.

## Numbered issues

### A. Interpretation and scope

**1. The headline claim goes beyond what the design can show, and the data contradict it.**
*Location:* `report.md` lines 11-14 (verdict box), 32-33 (plain terms), 358-367 ("What this means"), 231-233.
*Evidence:*

- **Dummit-Foote 8.3.6a** (category 1, "wrong constant"; 11 copies on O, 11 on T, all Kimina). The ProofNet port
  writes the ideal generator of Z[i]/(1+i) as `span ({⟨0, 1⟩} : Set GaussianInt)`, i.e. the unit *i* instead of
  `⟨1, 1⟩`. The twin asks for Z[i]/(2+i), order 5. Kimina answers, in 11 of 16 samples,
  `(hR : R = (GaussianInt ⧸ span ({⟨0, 1⟩} : Set GaussianInt))) : IsField R ∧ ∃ finR : Fintype R, @card R finR = 5`
  with the port's exact header `open Fintype Subgroup Set Polynomial Ideal / open scoped BigOperators`. Nothing in
  "Z[i]/(2+i)" yields `⟨0, 1⟩`; the only place that token exists is the memorised port statement. Kimina recalled the
  template and filled the one slot the twin changed (the order). I confirmed in Lean that this output is certified
  equivalent to D′ and that a `⟨2, 1⟩` output is equivalent to C′ and not to D′ (`lean_rerun.py`), so the
  classification is right; it is the inference that is wrong. The twin builder itself had to invent an arbitrary
  "rule" ("set the generator's real part to 0") to carry this defect over, which is a sign the item is not of the
  natural-pitfall kind the design assumes.
- **The ProofNet-lean4 header fingerprint.** The port's per-textbook `open` lines (for example
  `open Fintype Subgroup Set Polynomial Ideal` for Dummit-Foote, `open Topology Filter Real Complex TopologicalSpace Finset`
  for Rudin) are not derivable from an informal statement. Kimina reproduces the item's own textbook header exactly in
  **668 of 1,326 (50.4%)** of its extracted outputs on the 129 included ProofNet originals, **638 of 1,327 (48.1%)** on
  the paraphrases and **111 of 304 (36.5%)** on the twins. Goedel, Herald, DeepSeek-Prover-V2 and Qwen: **0 of ~1,300
  each**. This is a memorisation signature independent of the defect test, and it fires on twins and paraphrases.
- The Dummit-Foote Sylow items (4.5.13/14/15/17; 42 of Kimina's 86 copies on O) reproduce the port's statement body and
  header on the twins too. The report presents these as "the original port's shapes for some algebra statements" under
  the heading "formalization habits".

*What follows:* the primary result rules out item-level recall *keyed to the numbers*. It does not rule out, and the
data positively show, template-level recall of the benchmark statements in at least one primary model. A model that
has memorised `statement(numbers)` as a template produces RR = 1 in this design by construction, so RR ≈ 1 is not
evidence against memorisation of the statement. *Fix:* rewrite the verdict sentence as "...not recall keyed to the
problem's numbers"; rewrite the plain-terms paragraph; add a subsection reporting 8.3.6a and the header fingerprint
(a table of header-match rates by model and condition is a one-line addition to `analysis.py`); move the "habits"
reading to a hypothesis the design cannot test against template memorisation.

**2. The by-category table hides the single most informative item.**
*Location:* `report.md` line 226, "Wrong constant (1) | 4 | 11 | 11 | 1.00 (1.00-1.00)".
Three of the four category-1 items have 0/0; the whole row is 8.3.6a, where a memorised wrong constant was reproduced
11 times on the twin. A reader sees "RR 1.00, no excess", the opposite of what the item shows. *Fix:* name the item in
the text and explain the degenerate interval (every category-1 bootstrap draw has x_O = x_T because each item has
identical counts).

**3. The O-vs-P discussion omits the analyses that bear on the two readings.**
*Location:* `report.md` lines 243-280.

- On the 59 primary items, Kimina's O-vs-P ratio is **1.99 (95% CI 1.27-3.30)** (86 vs 43), not the 1.69 shown from
  the 129-item set; on exactly the items where O ≈ T, the originals draw twice the defect copies of their paraphrases.
- The header fingerprint is the same on O and P (50% vs 48%): Kimina recognises the item as a ProofNet item either
  way; what the paraphrase changes is the *statement body*. For 4.5.14 and 4.5.15 (15→1 and 12→1 copies) the
  paraphrase keeps the condition "prime p dividing |G|" that the original also states, so reading 2 ("the paraphrases
  are clearer") has no content to point to; the original *wording* triggers the port's body. The report cites 4.5.14
  as evidence *for* reading 2.
- Part of the O−P gap is an elaboration artefact, not fewer defects: on amc12a_2021_p7 Herald writes `(xy - 1)` with
  juxtaposition in 10 of 16 paraphrase samples (no elaboration) and `x * y` on the original (15 copies).
- Items with P > O exist (mathd_algebra_410: 5→12; amc12b_2020_p22: 9→10).

*Fix:* add a per-item O/T/P table (27 items, `primary_by_item.csv` plus a P column) and the Kimina 59-item O-vs-P
estimate; replace the 4.5.14 example or state what actually differs; state that the header fingerprint is wording-
independent while the body defect is wording-dependent, which favours reading 1 for the Sylow items.

**4. The negative-control sentence overstates.**
*Location:* `report.md` lines 298-301, "The faithful v1 statement ... was produced once in 640 samples ... these
models do not reproduce v1 statements verbatim on demand."
The test was portfolio equivalence, not verbatim text; it is eight items; elaboration on them is low (Herald 85/128,
Qwen 75/128); and an output equivalent to the v1 statement would in several cases need the idiosyncratic
`σ : Equiv ℝ ℝ` form. One event in 640 shows that *on these eight items* the models rarely produce the v1 form; it does
not license a general statement about v1 statements. *Fix:* "On these eight items, outputs equivalent to the v1
statement were rare (1 of 640)."

**5. The miniF2F-v2 paragraph is fair but should quantify the "drop".**
*Location:* `report.md` lines 369-372. The paper (arXiv 2511.03108, Section 4) does say "This finding suggests that
current autoformalizers may suffer from data contamination" about Herald and Kimina declining from v1 to v2s while
o4-mini improves, so the paraphrase is accurate. The published differences are small and metric-dependent (Herald
−0.8 pp under the paper's LLM judge; the human-verified numbers move the other way). Say so, and note that this study
speaks to miniF2F-style items for Herald (equal copying on twins) but that for Kimina the ProofNet evidence in issue 1
is *consistent with* contamination of the kind the paper suspects.

**6. The direction of the selection bias is not stated.**
*Location:* `report.md` lines 381-383 (Limitations). Excluding items without numbers removes 64 of 83 ProofNet items,
the abstract statements where Kimina's memorisation signature is strongest, and keeps the miniF2F "find the value"
items whose defect (a one-sided bound) is the most natural pitfall of all. The restriction therefore biases the primary
set *towards* items where RR ≈ 1 is expected under both hypotheses. *Fix:* say this; report the header-fingerprint rate
on the 70 excluded items as a partial check (it is computable from the O and P samples already on disk).

### B. Classification

**7. The certifier misses mathematically identical reformulations, and the model's surface form co-varies with condition at item level.**
*Location:* `report.md` lines 329-354 ("Is the classifier biased between conditions?"), 391-395.
Re-run in Lean (`lean_rerun.py`): Herald's `∑ k in Finset.range n, (1 : ℝ) / (k + 1) / (k + 2) = n / (n + 1)` is
**not** certified equivalent to D (`1 / ((k + 1) * (k + 2))`) in either direction, although it is the same statement
(`div_div` under a binder is out of the portfolio's reach). On induction_sum_1oktkp1 Herald wrote the division chain in
most original samples ("other") and the product form in all 16 twin samples ("copy"); the item's 3 vs 16 is a
certifier artefact. The ZMOD-vs-MOD forms on Ireland-Rosen 3.10 are likewise "other". A textual scan of "other"
outputs within character ratio ≥ 0.9 of D finds comparable counts across conditions (Herald 26/32/30 on O/P/T, Kimina
22/18/21), so I found no aggregate bias, but the report's argument ("the 'other' shares are similar, so this should
not bias the ratio") is aggregate only. *Fix:* disclose the induction_sum_1oktkp1 case and the Lean re-run; add a
`ring_nf`/`field_simp` normalisation step to the portfolio in a sensitivity run, or at least report the near-D "other"
counts by condition.

**8. Twin texts can change the model's parsing in ways unrelated to the numbers.**
*Location:* twins for aime_1988_p3 and aime_1983_p9 (AIME three-digit answers). Herald read the twin's "016" as `0.16`
in 8 of 16 samples (the original's "027" was read as 27 in 15 of 16). The item's 7 vs 4 therefore reflects a
formatting quirk, not the numbers. Minor for the pooled estimate; worth a sentence under Limitations, and a note that
answer formats were kept as in the source.

**9. Ninety-seven outputs certified equivalent to both D and C are not logged.**
*Location:* `plan.md` section 5 ("If it happens it is logged and counted as other"); `report.md` has no mention.
All 97 (Kimina 32, Goedel 31, Herald 15, DSP 18, Qwen 1 unique statements; 73 temperature outputs from the primary
models) fall on **Rudin 1.1a**, whose D and C are both portfolio-provable (`refcheck.jsonl`). The item is outside the
59 but inside the 129-item O-vs-P set, where it contributes nothing to the copy counts only because "both" is counted
as "other". By the D6 logic (a provable D is uninformative) the item should be excluded from the O-vs-P analysis; D6
was applied to the primary set only. *Fix:* log the 97 in the report; apply the D6 exclusion to every analysis that
uses D as a reference (O-vs-P: 127 items).

### C. Timing and disclosure

**10. D6 is dated 76 minutes after the primary models' classifications were complete.**
*Location:* `deviations.md` D6 (13:21); `logs/classify_kimina.log` (done 11:44:28), `classify_goedel.log` (11:58:16),
`classify_herald.log` (12:05:19); `data/classified/{kimina,goedel,herald}.jsonl` mtimes 11:44-12:05.
D6 says it was written "before any outcome was computed" and that "only extraction rates, finish reasons and
elaboration rates had been looked at". That is unverifiable, and everything needed for the primary result had been
on disk for over an hour. The check happens to be the kind of thing one notices when looking at results
(mathd_algebra_314's "copies" are the ℕ-truncated form, trivially true). It changes nothing (0.91 → 0.93), but the
log should state the facts: when the classification files existed, that they had not been opened, and what prompted
the check. *Fix:* amend D6 with the timeline above.

**11. Numbers in the report that are not in any released table.**
*Location:* `report.md` lines 324-327 ("8 of 177 on paraphrases", "11 on paraphrases of the same items");
`results/tables/secondary.json` `greedy.P` = 19 of 387 and `verbatim.P` = 28, computed on the 129 items
(`analysis.py` lines 104, 106). The report's 59-item numbers are correct (recomputed: 8/177 and 11), but they were
computed outside the committed code. *Fix:* add `verbatim_twin_items` and `greedy_twin_items` to `secondary.json`
(or cite the 129-item figures) so that every number in the report has a table.

**12. Post-outcome code changes.**
*Location:* `git diff 3a7a245 db0689f -- code/analysis.py` (the D7 block, +14 lines) and `code/refcheck.py` (resume
logic). Both are disclosed in D7 and labelled exploratory in the report; fine. But the `flagged` set in
`analysis.py` line 155 and the "clearer paraphrases" reading were chosen after seeing per-item results. Say so in D7
item 5 (it currently reads as if the drop were a neutral robustness check).

**13. Timeline plausibility should be stated once.**
The whole study, from preregistration (10:46) to draft report (13:34), took 2 h 48 min; 63 twins, 135 paraphrases and
135 paraphrase judgements were produced and checked in 16 minutes (11:08-11:24) by parallel subagents, and the
report was written in the three minutes between the last `analysis.py` run (13:31:54) and the commit (13:34:30),
which means it was drafted while the classification ran. None of this is wrong, but a reader will ask; one sentence
in the report or deviations log on how the pipeline was parallelised would pre-empt it.

### D. Smaller points

**14. "Verbatim" is defined loosely.** `report.md` line 325 says "character for character, apart from whitespace and
the theorem name"; `classify.py` `verbatim_key` collapses whitespace runs to one space, so `(x:ℝ)` and `(x : ℝ)`
differ. Also, "even verbatim reproduction is as common for the twins, whose D′ no model has seen" (line 327) is
exactly what a template memoriser produces: D′ differs from D by one numeral. Drop the inference; keep the count.

**15. Plain-terms wording.** Line 29: "which ones say exactly what the flawed official statement says" → "which ones
are certified to say the same thing as". Lines 32-33: see issue 1. Line 23: "59 problems with a documented mistake"
→ add "that have numbers to change" (the selection is material).

**16. Degenerate bounds.** Several intervals have a bound of exactly 1.00 (Qwen by-model lower, ProofNet lower 1.01,
categories 1, 5, 6). The report explains this once (line 385); the ProofNet sentence (line 235) should not describe a
lower bound of 1.01 as sitting "above 1" without the same caveat, since it rests on 19 items with near-identical
per-item counts.

**17. Plan §1's premise.** "Lean Workbook and similar training sets were synthesized from miniF2F and ProofNet" is not
how Lean Workbook describes itself (it is synthesised from natural-language problem sets; miniF2F and ProofNet were
used for evaluation and as style references). The report does not repeat the sentence, but the lead's motivation
should be corrected.

## What I checked and found sound

- **Timing of commits.** Plan (10:46) → candidates and Lean filters committed (10:50-10:53) before tagging → tagging
  prompts, twin/paraphrase/sampling/classification code and `analysis.py` committed (10:53-10:59) before any tag was
  read (tags 11:07) → frozen catalogue committed 11:24:23, sampling began 11:26:39 (`gpu_main.log`). The pilot used
  non-catalogue items only. D1-D5 are dated before the outcomes they could affect. D6/D7: issues 10 and 12.
- **Catalogue.** I read all 59 primary pairs with their twins (`catalogue_dump.md`). D is unfaithful and C faithful in
  every pair I examined (10 in detail: mathd_numbertheory_277, _5, _156, _435, mathd_algebra_410, _28, aime_1988_p3,
  amc12_2000_p12, Dummit-Foote 4.5.14, Putnam 2010 A4). Twins are the same problem with new numbers, the answer is
  recomputed, and D′ carries a defect of the same kind in all 59, including the weakened-conclusion items (the twin
  states only the new one-sided bound). t237 (Ireland-Rosen 3.10, (n−2)!) is a true, well-posed twin; t262 (Rudin
  1.11a, |w| = 2) is fine; t284 (Shakarchi 1.19b) is as the builder warned: D′ is true while D was false, but both are
  unfaithful in the same way ("zn" read as z·n), so keeping it is defensible and the sensitivity without it is
  reported. The only twin I would not have accepted is 8.3.6a (issue 1): the "same rule" is not a numeral rule.
- **Tags.** κ(D) = 0.957 recomputed (283/289 agree); κ(C) = 0.966; 129 included, 6 one-rater; category agreement
  120/129. Both-unfaithful 38, both-faithful 100.
- **Denominators.** Every one of the 1,705 keys has exactly 16 temperature outputs and 1 greedy output; no request
  failed; no classification row has an error; 19,807 unique statements.
- **Bootstrap.** Item-cluster percentile bootstrap reproduced exactly with the seed; with seed 1 and 10,000 draws the
  interval is 0.76-1.06. Fixed denominators are correct since every item has the same n.
- **Classification spot checks** (`show_outputs.py`): about 40 "copy" and 40 "other" unique statements for Kimina and
  Herald across O and T (4.5.13/14/15, 8.3.6a, Shakarchi 1.19b, Putnam 2001 A5, mathd_algebra_314, Putnam 2010 A4,
  amc12_2000_p12, Ireland-Rosen 3.10, induction_sum_1oktkp1, mathd_numbertheory_156, aime_1988_p3, control
  mathd_algebra_393). Every "copy" I read is the same statement as D or D′. "Other" is conservative: most are
  genuinely different (dropped `n ≠ 4`, `0 < x`, ZMOD casts, `0.16`), a minority are missed equivalences (issue 7). No
  "copy" was wrong.
- **Condition asymmetry in the certifier.** Classification time per unique statement is the same in O and T (median
  1.6 s vs 1.5 s; ≥ 20 s: 3.1% vs 3.2%; ≥ 40 s: 0.37% vs 0.69%). Elaboration rates and "other" shares match the
  report. A reworded digit-sum form of amc12a_2021_p25 is certified equivalent in both O and T.
- **D6.** Correct as far as it goes: it finds the two portfolio-provable D (mathd_algebra_188, _314) and no refuted
  primary reference; the one refuted D (mathd_numbertheory_343) and the one provable C′ are in the one-rater set, as
  stated. The "easy to hit by accident" worry does not bite here because the certifier is weak, not strong: a weak but
  unprovable D (the Sylow items, Putnam 2010 A4) is only matched by outputs of the same shape. The real failure mode is
  the opposite one (issue 7).
- **Report claims verified against data:** 15/16 and 14/16 for Kimina on 4.5.14; Herald 16/16 on both Putnam 2010 A4
  and amc12_2000_p12; Herald 11 control copies, 8 on mathd_algebra_393; Lean-filter attrition table; 63 twins built,
  72 skipped, 59 + 4 valid; 135/135 paraphrases judged same (a judge that accepts everything provides no evidence of
  discrimination; say so); extraction 98.3%-99.9%; 204/19/4 truncations.
- **Web checks.** No prior error-copying or defect-copying test for autoformalizers was found; the nearest work is
  mutation/functional-variant benchmarks for provers (MiniF2F-ALF, Putnam-AXIOM) and the paraphrase-robustness papers
  the study cites. arXiv 2606.14867, 2606.29493 (ICML 2026, atp-checkers), 2511.12784 and 2604.23135 exist and are
  described correctly. Goedel-Formalizer-V2-8B: 20 July 2025; miniF2F-v2 paper: 5 November 2025. The Lean Workbook
  claim: issue 17.

## Recomputed numbers

All from `data/classified/*.jsonl` and `*_outputs.jsonl` with `review/reviewer_checks/recompute.py`, independent of
`analysis.py`. "Report" is the value in `report.md`/`results/tables`.

| Quantity | Recomputed | Report / tables | Match |
|---|---|---|---|
| Primary RR (95% CI), x_O, x_T, n | 0.9069 (0.7574-1.0595), 204, 225, 2,832 | 0.91 (0.76-1.06), 204, 225, 2,832 | yes |
| Verdict by rule | Refuted (upper < 3; x_O + x_T = 429 ≥ 20) | Refuted | yes |
| Primary, seed 1, 10,000 draws | 0.9069 (0.7625-1.0554) | — | — |
| By model: Kimina | 1.061 (0.956-1.183), 86/81 | 1.06 (0.96-1.18) | yes |
| Goedel | 1.000 (0.840-1.857), 7/7 | 1.00 (0.84-1.86) | yes |
| Herald | 0.811 (0.608-1.050), 111/137 | 0.81 (0.61-1.05) | yes |
| DeepSeek-Prover-V2 | 1.065 (0.630-3.000), 16/15 | 1.06 (0.63-3.00) | yes |
| Qwen | 1.262 (1.000-1.649), 38/30 | 1.26 (1.00-1.65) | yes |
| O vs P, 129 items | 1.571 (1.277-1.986), 327/208, n 6,192 | 1.57 (1.28-1.99) | yes |
| O vs P, 59 items | 1.579 (1.203-2.211), 204/129 | 1.58 (1.20-2.21) | yes |
| P vs T, 59 items | 0.574 (0.402-0.771), 129/225 | 0.57 (0.40-0.77) | yes |
| O vs P by model, 129: Kimina / Herald / Goedel / DSP / Qwen | 1.694 (1.315-2.274) / 1.410 (1.015-2.262) / 1.154 (0.684-1.615) / 0.569 (0.227-1.138) / 1.055 (0.037-2.928) | 1.69 / 1.41 / 1.15 / 0.57 / 1.05 | yes |
| **O vs P by model, 59 items: Kimina** | **1.99 (1.27-3.30), 86/43** | not reported | — |
| O vs P, 59: Herald / Goedel / DSP / Qwen | 1.39 (1.00-2.26) / 1.15 (0.68-1.62) / 0.94 (0.39-1.62) / 1.08 (0.04-3.40) | not reported | — |
| By source: miniF2F / ProofNet | 0.784 (0.584-1.026), 101/129 / 1.073 (1.012-1.165), 103/96 | 0.78 (0.58-1.03) / 1.07 (1.01-1.16) | yes |
| By category 1/2/4/5/6/7 | 1.00 (1.00-1.00) / 0.74 (0.36-1.15) / 0.88 (0.62-1.18) / 1.13 (1.00-1.24) / 1.27 (1.00-2.60) / 0.96 (0.80-1.14) | same | yes |
| One-rater set (63) | 0.907 (0.748-1.059), 204/225, n 3,024 | 0.91 (0.75-1.06) | yes |
| Informative refs (57) | 0.925 (0.770-1.084), 196/212 | 0.93 (0.77-1.08) | yes |
| Flagged twins dropped (56) | 0.884 (0.731-1.042), 183/207 | 0.88 (0.73-1.04) | yes |
| Verbatim O / T / P (59 items) | 35 / 31 / 11 (all 35, 31, 11 are also "copy") | 35 / 31 / 11 | yes (P not in tables) |
| Verbatim P (129 items) | 28 | `secondary.json` 28 | yes |
| Greedy copies O / T / P (59 items) | 14/177, 16/177, 8/177 | 14, 16, 8 of 177 | yes (P not in tables) |
| Greedy P (129 items) | 19/387 | `secondary.json` 19/387 | yes |
| Accuracy O / T: correct, copy | 13.52%, 7.20% / 13.38%, 7.94% | 13.5%, 7.2% / 13.4%, 7.9% | yes |
| Among elaborating O / T / P | 204/2,180 (9.36%), 225/2,179 (10.33%), 129/2,190 (5.89%) | same | yes |
| Controls: copy per model (n 128) | Herald 11 (8 on mathd_algebra_393, 2 imo_1959_p1, 1 numbertheory_notequiv…), DSP 1, others 0; correct: Herald 1 | same; "once in 640" | yes |
| Items with any defect output | 27 of 59 | 27 | yes |
| Elaboration O / T (Kimina, Goedel, Herald, DSP, Qwen) | 84/83, 79/80, 68/68, 64/62, 26/25 % | same | yes |
| "Other" share among elaborating O / T | 0.62/0.62, 0.82/0.82, 0.77/0.74, 0.84/0.83, 0.84/0.87 | same | yes |
| Cohen's κ on D; category agreement | 0.957; 120/129 | 0.957; 120/129 | yes |
| Outputs; unique statements; extraction; truncations | 28,985; 19,807; 98.3-99.9%; DSP 204, Herald 19, Goedel 4 | same | yes |
| Outputs ≡ both D and C | 97 unique statements, all on Rudin 1.1a; 0 in the primary set | not reported | — |
| **Kimina outputs with the item's ProofNet textbook header, O / P / T** | **50.4% / 48.1% / 36.5%**; other four models 0% | not reported | — |
| Classification seconds, median O / P / T; ≥ 20 s | 1.6 / 1.6 / 1.5; 3.1% / 2.9% / 3.2% | — | — |
| Lean re-run: Herald `1/(k+1)/(k+2)` vs D (induction_sum_1oktkp1) | not equivalent either direction; product form equivalent | classed "other" | classifier miss |
| Lean re-run: Kimina `⟨0, 1⟩` output vs D′ (8.3.6a twin) | equivalent both ways; `⟨2, 1⟩` ≡ C′, ≢ D′ | classed "copy" | correct |

## Suggested order of fixes

1. Issues 1-3 and 15: rewrite the verdict sentence, plain terms, "What this means" and the O-vs-P section; add the
   header-fingerprint table and the per-item O/T/P table; name 8.3.6a.
2. Issues 9, 11: log the 97 both-equivalent outputs, apply D6 to the 129-item set, add the 59-item verbatim/greedy
   figures to `secondary.json`.
3. Issues 7, 8, 10, 12-14, 16-17: disclosures and wording.

After these the verdict "Refuted" can be published with the scope "no excess of defect copying keyed to the problem's
numbers", together with the finding the study did not set out to make but did make: one open autoformalizer
reproduces the ProofNet Lean 4 port, header and wrong constant included, whatever the numbers.
