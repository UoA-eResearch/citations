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
