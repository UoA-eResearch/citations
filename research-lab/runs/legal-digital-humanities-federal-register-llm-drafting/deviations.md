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
