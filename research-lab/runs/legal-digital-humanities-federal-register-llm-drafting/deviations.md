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
