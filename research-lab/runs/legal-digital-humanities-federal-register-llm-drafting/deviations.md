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
