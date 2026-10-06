# Deviations and implementation details

The plan (plan.md) was committed in 22616bf at 2026-10-06 14:52 NZDT. Entries are timestamped with `date`.

## D1. Bug in group assignment, found before any estimate (2026-10-06 14:55 NZDT)

**The bug.** `code/groups.py` mapped agencies with no cabinet department, such as EPA and other independent agencies,
to the comparison group instead of excluding them. Their department value is NaN, and pandas treats NaN as true.

**Consequence.** The counts table committed with the plan, and the plan's disclosure of "1,973 other-cabinet
documents" in the post window, include independent agencies.

**Corrected counts** (non-templated documents):

| Group | Pre (2024-25) | Post (2026-02 to 09) |
|---|---|---|
| Comparison group (the other 14 cabinet departments) | 3,295 | 1,178 |
| DOT | 732 | 290 |
| Independent agencies (excluded) | 2,483 | 795 |

DOT counts are unchanged. The plan's definition, "the 14 other cabinet departments, pooled", was always the intended
one; only the code was wrong.

**Fix.** The assignment is fixed, and the paragraphs, pools and power-analysis group sizes are regenerated. No LLM text
had been generated and no estimate computed. The 2019-2021 reference pools are now restricted to cabinet departments,
as `code/pools.py` intended: 3,849 human, 1,283 generation and 1,283 validation documents.

## D2. Two closer-proxy generators added before any estimate (2026-10-06 22:27 NZDT)

**The change.** The plan's three generators have each produced 4,000 polish and draft pairs:

- Qwen2.5-32B-Instruct (revision 5ede1c97);
- OLMo-2-0325-32B-Instruct (revision b9602434);
- Nemotron-3-Nano-Omni, thinking disabled.

The lab owner asked whether a better generator was available. DOT reports using Google Gemini. The closest open
relative is **Gemma 4 31B-it** (google/gemma-4-31B-it, March 2026, Apache-2.0, ungated). The gated Gemma 3 was not
accessible. Other departments mostly use ChatGPT- or Copilot-style tools, and **gpt-oss-120b** (OpenAI, Apache-2.0)
represents that family.

**Why it matters.** If the LLM reference lacks the style that DOT's tool actually produces, DOT's α is underestimated
relative to the comparison group, which biases the DiD towards zero.

**Revised design.**

- **Primary LLM reference:** pooled over all five generators, with the same prompts and sampling.
- **New secondary:** a Gemma-4-only reference, as the Gemini proxy.
- **Leave-one-generator-out (plan section 6):** now covers five generators.
- **Fallback:** if gpt-oss-120b cannot be served on the A100, gpt-oss-20b is used, and that is logged.

**Timing.** This change is made before any LLM-fraction estimate, any validation run, and the unsealing of the outcome
issues.

## D3. Power check (V2) at the real group sizes, before validation is run (2026-10-06 23:32 NZDT)

**The problem.** Plan section 4 builds four synthetic groups from 2019-2021 validation-pool documents, "with the
sentence and document counts of DOT-pre, DOT-post, other-pre and other-post". Those are 732, 290, 3,295 and 1,178
documents (D1), 5,495 in total. After D1 the validation pool has only 1,283 documents. The first code capped every
group at 320 disjoint documents. That understates power for three of the four groups, and could make Refuted
unreachable for a reason unrelated to the data.

**The change.** Each group is now drawn independently, with replacement, at its real document count. The draws come
from the human documents of the generation and validation pools: 2,566 documents of 2019-2021 text that the
estimator's human reference never sees. The rest is unchanged:

- injection into DOT-post;
- the document bootstrap within each group;
- 40 replicates per effect size;
- power is the share of 95% CIs that exclude 0.

The capped design is kept as a sensitivity (`validate.py capped`, `validation_v2_capped.csv`).

**Timing.** Validation has not been run, no LLM-fraction estimate exists for any period, and the 2026 issues are
still sealed.

## D4. Unicode normalisation in the tokenizer, and a typographic-marker check, before validation (2026-10-06 23:57 NZDT)

**What was found.** gpt-oss-120b and Nemotron write compound words with a non-breaking hyphen (U+2011) and put a
narrow no-break space (U+202F) after § and before units. Qwen, OLMo and Gemma never do. In the 2019-2025 Federal
Register text, no document in any year contains either character (0.00% of documents per year).

**Tokenizer fix.** The estimator's tokenizer kept ASCII-hyphen compounds as one token ("well-known") but split
U+2011 compounds into two. Tokens are now formed after mapping U+2010 and U+2011 to "-" and the no-break spaces to a
space (`code/mle.py`, `NORM`). No estimate had been computed.

**New secondary check (model-free, outside the decision rule).** For each group and period, `analysis.py` now reports:

- the share of documents whose non-procedural text contains U+2011 or U+202F;
- em dashes per 1,000 words.

Output: `results/tables/typographic_markers.csv`. A nonzero 2026 share would be evidence of pasted machine text,
since the base rate is zero. A zero share is not evidence against LLM use: the Federal Register's own typesetting
might normalise these characters, and other tools do not produce them.

**Timing.** Validation has not been run and the 2026 issues are still sealed.

## D5. V1 failed; estimator fixed with 2019-2021 data only (plan section 4), before unsealing (2026-10-07 00:43 NZDT)

**V1 with the plan's estimator** (`logs/validate_estimator_v1.log`, `results/tables/validation_v1_estimator_v1.csv`):

| True α | Mean estimate | Bias | Coverage |
|---|---|---|---|
| 0 | 1.68% | +1.68 pp | 0% |
| 2% | 3.79% | +1.79 pp | 0% |
| 5% | 6.53% | +1.53 pp | 0% |
| 10% | 10.77% | +0.77 pp | 44% |
| 25% | 22.96% | −2.04 pp | 0% |

That fails both criteria: |bias| < 1 pp at α ≤ 10%, and coverage ≥ 90%. The V2 run with this estimator was stopped
unfinished.

**Diagnosis** (2019-2021 data only; raw α):

- **The human reference itself:** 0.9%. Within-sentence overdispersion: the variance of the count of vocabulary words
  per sentence is 3.79, against 2.32 under the model's independence assumption. The mixture absorbs it.
- **Validation pool:** 1.6%.
- **Generation pool's human documents: 11.1%.** These are the documents whose paragraphs were rewritten. The rewrites
  keep their sources' topical adjectives, so the LLM reference carried the topics of a few hundred documents rather
  than only the generators' style (topic leakage).
- **Held-out generated text:** 81%, so estimates are attenuated.

**Fix, defined before the full V1 rerun.**

1. **Paired LLM reference** (`mle.Estimator(paired=...)`). p_A(w) = p_H(w) × r(w), where r(w) is the ratio of w's
   sentence-occurrence rate in the generated outputs to its rate in the source paragraphs they came from. The
   reference keeps the shift the generators introduce and takes its topic mix from the human reference.
2. **Two-point linear calibration** from 2019-2021 data that V1 never uses:
   - a = raw α on the generation pool's human documents;
   - b = raw α on half C of the held-out generated sentences, minus a.
   - Calibrated α = (raw − a)/b, applied to point estimates and bootstrap draws alike.
   - Half C is chosen by the md5 parity of the paragraph key.
   - In a difference-in-differences a cancels, and b rescales the DiD to the true-fraction scale that V1 validates.
3. **V1 is rerun on the validation pool and the other held-out half (V)**, with two constructions, both reported:
   - **"Pseudo-documents"**, as first coded: sentences are shuffled into 290 equal chunks. This destroys document
     clustering, so its bootstrap CI ignores between-document variation.
   - **"Documents":** 290 real validation documents per replicate, each sentence replaced by a generated one with
     probability α. This is the structure the analysis's document bootstrap faces.
4. **V2 is rerun with the fixed estimator** (D3 design), on the calibrated scale. Power does not depend on a linear
   calibration.
5. **`analysis.py`** uses the same estimator through `validate.build_estimator`. Leave-one-generator-out and the
   Gemma-only reference each get their own paired reference and calibration.

**Disclosure of the quick checks that led here.** Raw α, 10 replicates per level, pseudo-document construction, on
the validation pool and all held-out generated sentences (`scratchpad` runs, not committed):

| Estimator | Human reference | Generation pool | Validation pool | Held-out generated | Mixtures at α = 0 / 0.05 / 0.10 / 0.25 |
|---|---|---|---|---|---|
| Unpaired | 0.94% | 11.1% | 1.62% | 81.2% | 1.72 / 6.63 / 10.66 / 23.02% |
| Paired | 0.50% | 0.54% | 0.75% | 78.6% | 0.74 / 5.05 / 8.91 / 20.44% |

No other estimator variant was tried.

**Timing.** No estimate exists for 2022 or later, and the 2026 issues are still sealed.

## D6. V1 with the D5 estimator: bias passes, coverage fails; calibration uncertainty propagated (2026-10-07 00:57 NZDT)

**V1 with the D5 estimator** (`logs/validate_D5.log`, `results/tables/validation_v1_D5.csv`). Calibration:
a = 0.54% and b = 0.769. Calibrated α on the validation pool is 0.28%, and on half V is 103%.

| True α | Pseudo-documents: bias | Pseudo-documents: coverage | Documents: bias | Documents: coverage |
|---|---|---|---|---|
| 0 | +0.32 pp | 80% | +0.26 pp | 96% |
| 2% | +0.61 pp | 46% | +0.82 pp | 98% |
| 5% | +0.90 pp | 24% | +0.79 pp | 82% |
| 10% | +0.95 pp | 32% | +0.98 pp | 86% |
| 25% | +1.00 pp | 58% | +1.02 pp | 82% |

- **Bias criterion:** passes in both constructions (|bias| < 1 pp at α ≤ 10%).
- **Coverage criterion:** fails. With real documents, coverage falls to 82-86% at α ≥ 5%. The pseudo-document
  construction undercovers badly because its bootstrap ignores document clustering.

**Cause.** The residual bias rises with α. It matches the slope error between the two held-out halves: V reads 79.8%
raw and C reads 77.5%, about 3% apart. The bootstrap CI ignored this uncertainty in the calibration (a, b).

**Fix (2019-2021 data only).** 2,000 calibration draws (a_i, b_i) are made by resampling the generation pool's documents
and half C's paragraph keys (`build_estimator`). Bootstrap draw i of every estimate is calibrated with (a_i, b_i),
using the same i in every group. So a still cancels in a DiD, and the uncertainty in b now enters every interval.
Point estimates still use (a, b).

The V2 run with D5 intervals was stopped unfinished. V1, V2 and the capped V2 are rerun with D6.

**Rule set now, whatever the outcome.** This is the last change to the estimator.

- If V1 still fails, the study proceeds and the V1 shortfall is reported as a primary caveat.
- The decision rule depends on V2 (the minimum detectable effect), not on V1.
- V2 at delta = 0 reports the DiD's false-positive rate directly.

**Timing.** The 2026 issues are still sealed.

## D7. Validation results with the final estimator, and the minimum detectable effect, before unsealing (2026-10-07 03:50 NZDT)

Estimator: paired reference (D5), calibration a = 0.54% and b = 0.769, with calibration uncertainty propagated (D6).
The 95% range of the b draws is 0.728-0.814. Files: `logs/validate.log`, `results/tables/validation_v1.csv`,
`validation_v2.csv`, `calibration.json`, `results/figures/validation.png`.

**V1** (50 replicates per level):

| True α | Documents: estimate | Documents: coverage | Pseudo-documents: estimate | Pseudo-documents: coverage |
|---|---|---|---|---|
| 0 | 0.26% | 100% | 0.32% | 98% |
| 2% | 2.82% | 100% | 2.61% | 86% |
| 5% | 5.79% | 88% | 5.90% | 58% |
| 10% | 10.98% | 90% | 10.95% | 66% |
| 25% | 26.02% | 96% | 26.00% | 94% |

- **Bias criterion:** met in both constructions. The worst case at α ≤ 10% is +0.98 pp.
- **Coverage criterion:** not met. The documents construction falls to 88% at α = 5%; the pseudo-document construction
  (no document clustering) falls to 58-66%.
- **Consequence:** by the rule fixed in D6, the study proceeds, and this shortfall is a primary caveat. The estimator
  slightly overstates large fractions (about +4% of the true value), because the two held-out halves differ in
  detectability.

**V2** (D3 design: real group sizes, 40 replicates per level):

| Injected DiD | Power (95% CI excludes 0) | Mean estimated DiD | Mean CI width |
|---|---|---|---|
| 0 | 12% | +0.22 pp | 3.96 pp |
| 1 pp | 20% | +1.39 pp | 4.55 pp |
| 2 pp | 70% | +2.47 pp | 4.16 pp |
| 3 pp | 82% | +3.28 pp | 4.34 pp |
| 5 pp | 100% | +5.58 pp | 4.60 pp |
| 7.5 pp | 100% | +8.15 pp | 4.66 pp |

- **Minimum detectable DiD at 80% power: 3 pp.** That is at most 5 pp, so all three verdicts remain reachable under
  plan section 5.
- **False-positive rate at DiD = 0: 12%** (about 5 of 40), above the nominal 5%. The DiD interval is somewhat too
  narrow, consistent with V1. This is reported as a caveat on any "CI excludes 0" statement. Supported also needs
  DiD ≥ 5 pp, a size that V2 never produced under the null.
- **Bias:** the estimated DiD exceeds the injected one by about 0.2-0.6 pp.

**Not yet run.** The capped-design V2 sensitivity is still running. It is deterministic, committed code that uses only
2019-2021 data, so the unsealing below cannot affect it.

**Next.** Verify the sealed files against `data/SEALED_MANIFEST.sha256`, then parse them (`parse.py sealed`).

## D8. Unsealed; crash in the near-duplicate filter fixed before any estimate (2026-10-07 04:28 NZDT)

**Unsealing.** The 188 sealed issues matched `SEALED_MANIFEST.sha256` file by file. The manifest digest recomputed
to b8a470f9…, as stated in the plan, and the manifest is unchanged since 22616bf. `parse.py sealed` (03:50 NZDT,
7 October) produced 245,721 paragraphs in 3,540 documents, before the templated-action filter.

**The crash.** The first analysis run crashed in `dedup` before computing any estimate: a pandas Index was indexed by
document number.

**The fix.**

- `q` is now a Series indexed by document.
- MinHash signatures are built with `update_batch`, which gives the same hash values (checked) and is faster.
- An empty group-period returns NaN instead of failing.

No estimate had been produced. The analysis is rerun unchanged otherwise.

## D9. Independent review (fix first); post-review analyses and corrections (2026-10-07 07:53 NZDT)

The review (`review/review.md`) reproduced the primary estimate, its interval and the verdict to every digit. It
found the sealing and timing sound, and asked for text corrections plus several secondary analyses. Everything below
was done after unsealing and after the review. **None of it can change the verdict**, which rests on `analysis.py`'s
primary DiD (B = 2,000, seed 20261007, fixed before unsealing).

**Code.**

- **`groups.py`** took `agencies[0]`, which is the parent department, as the sub-agency. It now takes the first
  listed agency that is not a cabinet department, falling back to `raw_name` where the API gives no name (DOT's
  Office of the Secretary). It also flags FERC. The group, department and templated columns are unchanged (checked:
  38,833 of 38,833 identical).
- **`code/post_review.py`** produces the analyses below. Nemotron's revision (e5e99324, from the local download
  metadata) is now in `generator_revisions.json`.

**Results** (files in `results/tables/`).

1. **Bootstrap-seed sensitivity** (`seed_sensitivity.csv`). The point DiD is +0.56 pp under every seed. Over 12
   seeds at B = 2,000, the upper bound ranges from 4.84 to 5.11 pp and falls below 5 pp in 6 of them, so the formal
   rule would return Refuted under those seeds. A B = 10,000 run gives −4.23 to +5.01 pp. The verdict therefore sits
   within Monte Carlo error of the threshold. The preregistered seed's Inconclusive stands.
2. **Variance by cell** (`variance_by_cell.csv`, raw scale). Shares of the DiD's bootstrap variance:

   | Cell | Bootstrap sd | Share of variance |
   |---|---|---|
   | DOT 2026 | 1.58 pp | 74% |
   | Other departments 2026 | 0.81 pp | 19% |
   | Other departments 2024-25 | 0.35 pp | 4% |
   | DOT 2024-25 | 0.31 pp | 3% |

   21.5% of the DOT 2024-25 bootstrap draws sit at the lower boundary, raw α = 0. In all four primary cells the score
   of the log-likelihood at α = 0 is positive, so the full-sample estimates are interior.
3. **Monitoring series (plan section 6, not produced before).**
   - `monitoring_by_department.csv` gives α by department and quarter.
   - `department_pre_post.csv` gives each department's 2024-25 and 2026 values. 11 of the 14 comparison departments
     rose and 3 fell (Justice, Education, HUD). Commerce, the largest, moved from 0.9% to 1.3%.
   - Reweighting the comparison group's 2026 department estimates to its 2024-25 document mix gives 5.06%, against
     4.98% actual.
4. **DOT administrations** (`dot_subagency_pre_post.csv`).
   - The FAA's share of DOT documents fell from 48% to 32%, and PHMSA's rose from 11% to 26%.
   - PHMSA read 12.9% in 2024-25 and 2.2% in 2026. The Office of the Secretary read 23.3% in 2026 (11 documents).
     NHTSA read 9.2%.
   - At the 2024-25 mix, DOT's 2026 value would be 2.47%. At the 2026 mix, its 2024-25 value would be 3.34%. So the
     composition shift accounts for 1.1-3.7 of DOT's 4.0 pp change.
5. **Sensitivities** (`sensitivities.csv`; DiD and 95% CI, B = 2,000, seed 20261007):

   | Sensitivity | DiD (95% CI) |
   |---|---|
   | Clean baseline (2024-01 to 2025-06) | +0.3 (−4.1 to +4.6) |
   | Routine FAA-type titles excluded (38% of DOT's 2024-25 documents, 25% of 2026) | +1.1 (−4.0 to +5.7) |
   | FERC excluded | +0.1 (−4.5 to +4.6) |
   | Broader procedural filter (regulatory impact analysis, severability, good cause and similar) | +0.4 (−4.3 to +4.7) |
   | Prompt words ("every", "only", "supplementary") removed from the vocabulary; chat preambles and Markdown stripped | +1.5 (−5.0 to +7.3) |

**Corrections to earlier entries.**

- **D5 point 3 and D6 "Cause".** The pseudo-document construction does not hide document clustering: its sentences
  are drawn i.i.d., so its bootstrap is valid for that design. It undercovers because the estimator's bias, +0.6 to
  +1.0 pp at α ≥ 2% (about +4% relative, from the slope difference between halves C and V), is as large as its narrow
  intervals' half-width. The documents construction covers better only because real document heterogeneity makes its
  intervals wider.
- **D8 timing.** `parse.py sealed` started at 03:50:45 NZDT, which is the `date` printed immediately before it in the
  same shell command. That is 29 s after the D7 commit (03:50:16). Its output was written at 03:50:53.
- **Scope of the seal.** Only the 2026 issues were sealed. The 2022-2025 text, which includes the pre-period and both
  placebo windows, was on disk unsealed while D2-D6 were decided. No LLM-fraction estimate was computed on it before
  D8, but nothing beyond the commit history attests that.
- **Deregulatory filter.** The regex in `analysis.py` (committed at D2, before unsealing) is
  `rescind|rescission|remov|withdraw|deregulat|eliminat`. The report now states it in full.
