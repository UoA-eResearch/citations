# Plausibility gate (G3)

Fill in before writing report.md. See METHODS.md G3.

## 1. Headline numbers against expectation

| quantity | value | expected range and source (pilot, known case, literature, control) | plausible? | if not: what was found |
|---|---|---|---|---|
|  |  |  |  |  |

## 2. Three units traced end to end

Pick units at random (state the seed), and record the actual values at each step.

| unit | raw input | intermediate values | output used in the analysis | matches the pipeline? |
|---|---|---|---|---|
|  |  |  |  |  |

## 3. Invariants asserted in code

| invariant | where asserted (file:line) | holds? |
|---|---|---|
| counts reconcile between stages (n in → n out + dropped) |  |  |
| the setting / version / subset used is the one plan.md names |  |  |
| no NaN reaches a primary statistic |  |  |
| joins neither duplicate nor drop units |  |  |
