# Plausibility gate (G3) — added in D2 (the study predates METHODS.md)

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| post-overruling decline D(+5), preregistered | 0.29 (-0.05 to 0.51) | a sharp fall after overruling (Broughman & Widiss 2017, ledger P4) | weak | the anchor implied a clear decline; the shortfall prompted the co-citation exclusion and the coverage-break checks |
| D(+5) excluding co-citing opinions | 0.66 | as above | yes, as an upper bound | partly mechanical: later discussion of a precedent tends to cite its overruling decision |
| lower-court citation pairs to Supreme Court clusters | 10.6 million (2026-09-30 snapshot) | the CourtListener citation map has hundreds of millions of citations in all | yes | |
| district-court pairs per year | 59,504 (2018) to 319,779 (2020) | a coverage change, not citing behaviour: appellate and state counts flat | flagged | D1, D2 |
| share of SCDB alterations on the list | 58% (101 of 174) | Wikipedia's list is self-tagged incomplete | yes | |
| matching balance | mean SMD 0.25, median 0.12; 30 of 73 stacks above 0.5 | famous precedents sit at the top of the citation distribution, so near neighbours are less cited | partly | treated pre-trends within the matching window are not steeper (review check) |

## 2. Three units traced end to end

The independent review recomputed these from the raw tables (`review/reviewer_checks/`):

| unit | raw input | intermediate values | output | matches the pipeline? |
|---|---|---|---|---|
| Gideon v. Wainwright (372 U.S. 335) | citation map rows for both CourtListener clusters (106545 and CAP twin 8954562) | citations split about 50/50 and stably across periods | the most-cited-cluster rule loses no time pattern | yes (check4_dups) |
| Chevron (467 U.S. 837) | yearly citations by court type for Chevron and its 10 controls | district-court citations to its controls jump 2018-2020 while Chevron's stay at 137-173 | the 2019 step is the coverage break | yes (check7_chevron; posthoc_d2 chevron_by_court) |
| the pre-2019 pooled D(-1) | the stacked panel | cluster-robust intervals against the stack bootstrap | -1.01 to -0.20 against -0.96 to -0.21 (first version) | yes (review finding 10) |

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| every list row is parsed or dropped with a reason | `coverage.json` wiki_rows | yes: 142 of 146; 4 dropped |
| citing-cited pairs are unique | counts.py dedup | yes: 10,620,418 unique pairs (review) |
| no Supreme Court decision counts as a lower-court citer | counts.py | yes: 0 citing clusters with an SCDB id (review) |
| controls are never-listed, SCDB-identified, same issue area | event.py match (D2) | yes |
| every bootstrap fit succeeds or is counted | event.py (boot_ok) | yes: 1000 of 1,000 |
