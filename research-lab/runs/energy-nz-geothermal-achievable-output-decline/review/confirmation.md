# Confirmation pass on the review response

Reviewer: Claude (Fable 5.1). Date: 2026-10-17. Reviewed at commit 7a904a6 (response code committed unrun at
2f8c705, D4 and the revised report at c371b0f, the `[sic]` fix at 7a904a6). Nothing outside `review/` was changed by
me; one new script, `review/reviewer_checks/confirm_v1c.py`.

## Recommendation: publish with edits

One edit is required and is cosmetic: the regenerated **F2 clips its two long y-axis labels** at the left edge of
the figure (the Ohaaki row reads "haaki 2008-13 (post hoc, / w chosen from the series)" and the fleet label starts
at the frame). `figures.py` kept `left=0.20` while the label grew; widen the margin (about 0.30) or shorten the
label to "Ohaaki 2008-13\n(post hoc window)" and re-run `figures.py`. The HTML references the PNG, so no other
rebuild is needed. Everything else in the response is either resolved or honestly disclosed, every new number
matches `results/tables/review_response.json`, and the plain-language summary is now supported by the results.
Three optional wording points are listed at the end.

## Process

- `review_response.py` written 08:02:51, committed 08:02:59 (2f8c705), `review_response.json` written 08:03:06; the
  script is byte-identical between 2f8c705 and HEAD. "Committed before it runs" holds.
- `analysis.py`, `build_series.py`, `supplementary.py`, `test_analysis.py`, `plan.md`, `primary.json` and
  `supplementary.json` are unchanged since 2b39db6. Only `figures.py` (labels and captions), `report.md/html`,
  `deviations.md` and the new files changed. The preregistered numbers are untouched.
- `review_response.py` imports `analysis.py` read-only and restores `RAMP`/`EVENTS` after the rule-based variant.
  Its segment-combination standard error reduces to the inverse-variance formula when weights are inverse
  variances and is the correct weighted-combination SE for capacity weights. V2's membership test
  (`plants == "KAW1101:kawerau_new"`) selects exactly the KGL-only segment (2009-06..2016-12 with a 12-month ramp).

## Issue by issue

| issue | status | where, and what I checked |
| --- | --- | --- |
| A1 "flat" not robust | **Resolved** | Abstract now gives the preregistered +0.02, "after review: between about 0 and −0.2", "last decade −0.4 (−1.0, +0.1)". Sensitivity table has V1a/b/c, V2, V3, V4, V5 rows; Results text names the two start-up artefacts and Poihipi; "It shows" gives "+0.1 to −0.2%/yr". All against the preregistered verdict number, correctly labelled post hoc. |
| A2 upkeep mechanism | **Resolved** | "Upkeep", "offset has worked", "only one field" gone from md and html. Replaced by "Whether make-up drilling has kept pace cannot be read from metering" and "Our data can show what the stations delivered, not why." Wairakei since 2015 and Ohaaki since 2019 named as slow decliners. |
| A3 data coverage | **Resolved / disclosed** | New "Data and its gaps" subsection lists TAOM (not identifiable before 2025-09), GDL, TOPP1, Kawerau binary, OEC4 absent to 2024-01, and the Kawerau composition; Kawerau row relabelled; limitation 2 added; D4 corrects plan §3. The 28–37 MW series is called "a mill's net export" as fact; it is an inference from the SKOG/CHHE network codes (see wording 3). |
| A4 Ohaaki post hoc | **Resolved** | Section rewritten: two steps in late 2007, plateau ~2 years, back by 2013, cause undocumented, Kortright/Contact "40–45 MW net since 1999", metering change not excluded, slope endpoint-determined with −12.1/−5.1/−1.7 alternatives, "three times" deleted. F2 label and caption say the window was chosen from the series. Abstract and plain terms no longer attribute it to drilling. |
| B1 interval coverage | **Disclosed** | "Intervals are approximate ... nearer 87–90% than 95%" at the four high-ρ segments (matches my simulation: 0.867–0.897); AR(2) row +0.02 (−0.19, +0.23); F2 caption repeats it. The Kawerau 2008–16 residual structure (Ljung–Box p<0.001) is not mentioned; covered implicitly by the AR(2) sensitivity. Acceptable. |
| B2 segment combination | **Disclosed** | V3 capacity-weighted segments +0.10 (−0.15, +0.36) in the table; F1 caption and the Kawerau row say the first segment is a 5.5 MW plant. Primary method unchanged, which is the right call post hoc. |
| B3 KGL 117 / TAOM window | **Resolved** | "to 107 MW per FGGS Table 2 (its text says 117; no step is visible in the metering)"; "Te Ahi O Maui (2018; not in the data then)". `analysis.py`'s EVENTS string still says 117, disclosed in D4; leaving the preregistered file untouched is preferable. |
| B4 P95 and long outages | **Resolved** | "outages shorter than about a month"; "P95 does register multi-month outages of a single unit, and commissioning ramps, as lost capability"; V5 rolling filter −0.08 (−0.24, +0.08), 42 months dropped; limitation 4; the Ohaaki 2018–19 and Tauhara steps attributed to unit outages. |
| B5 EDGS / F2 label / [sic] | **Resolved** | "EDGS 2024 does not model any decline ... EDGS 2016 instead modelled consent expiries ... as retirements" with FGGS as the source; F2 line relabelled "H2 line (−3%/yr)" (checked in the PNG); FGGS quotation now verbatim with "outrages [sic]" in md and html (7a904a6). "MBIE's 3%" survives only in the lead's quoted claim and in "not a run-down rate to set against MBIE's 3%", both correct in context. |
| B6 Mokai | **Resolved** | H2 section: FGGS "maintaining close to full output" contradiction, direct-use steam (greenhouses, milk plant from 2011), 2024 consent expiry; "What was already known" row; Scope and care updated; plain terms mention the steam offtake. |
| B7 novelty | **Resolved** | "Field trends are noticed in annual generation statistics. What is new here is a capability measure ... separated from outages, and segmented at capacity changes." NZGA/Kortright added to the known-work table. |
| C1 numbers/facts | **Resolved** except one | "about 110%"; reproduce note explains `data/processed/`; `review_response.py` added to the recipe. Not added: that Ohaaki's original/installed capacity differs by source (104/105/108/116 MW); the FGGS figures remain correctly attributed, so this is optional. |
| C2 code/data checks | n/a | Nothing to change; reproduce note added. |
| C3 wording | **Resolved** | Ngāwhā's reporting artefact is in the gaps section; Scope and care now concrete. |

## Numbers in the revised report against the results files

| report statement | results file | match |
| --- | --- | --- |
| Wairakei 2014– from 2015-01: −0.09 (−0.27 to +0.09) | V1a −0.0892 (−0.2695, +0.0914) | yes |
| …plus Ngā Tamariki from 2014-10: −0.13 (−0.29 to +0.02) | V1b −0.1332 (−0.2906, +0.0244) | yes |
| …plus Wairakei 2006–13 dropped: −0.19 (−0.34 to −0.03) | V1c −0.1865 (−0.3401, −0.0327) | yes |
| rule-based: −0.04 (−0.22 to +0.14) | V2 −0.0390 (−0.2190, +0.1413) | yes |
| capacity-weighted segments: +0.10 (−0.15 to +0.36) | V3 +0.1044 (−0.1463, +0.3558) | yes |
| AR(2): +0.02 (−0.19 to +0.23) | V4 +0.0195 (−0.1865, +0.2260) | yes |
| rolling filter: −0.08 (−0.24 to +0.08); 42 months (D4) | V5 −0.0827 (−0.2435, +0.0784); months_dropped 42 | yes |
| Ohaaki −10.4 / −12.1 / −5.1 / −1.7 | V6 −10.40 / −12.10 / −5.10 / −1.71 | yes |
| "between about +0.1 and −0.2%/yr" (It shows) | V3 +0.10 … V1c −0.19 | yes |
| "between about 0 and −0.2" (abstract, plain terms) | V2 −0.04 … V1c −0.19 | yes |
| last decade −0.4 (−1.0 to +0.1) | primary last_10_years −0.438 (−0.992, +0.118) | yes |
| Ngā Tamariki +0.05 from 2014-10 | V1b fields 0.047 | yes |
| Ohaaki since 2019 −1.3 (−1.9 to −0.7) | supplementary −1.256 (−1.853, −0.655) | yes |
| KGL "about 97 to 105–108 MW over 2009–14" | plant_monthly annual medians 97.4 (2010) → 105.2 (2014), 107.9 (2018) | yes (108 is reached by 2018) |
| Mokai "about 110% to about 85%" | annual medians 110–112% (2008–11), 84% (2026) | yes |
| V2 segments (Wairakei 2014-10–, Ngā Tamariki 2014-03–, Kawerau 2009-06–2016-12, Rotokawa 2011-01–, Tauhara 2011-05–) | review_response.json V2 segments | yes; consistent with 12-month ramps and the Poihipi window |
| preregistered table and other sensitivities | primary.json | unchanged, still match |
| report.html vs report.md | all shared numbers identical; html-only numbers are the embedded figure captions | yes; both new captions present |

**Reconciling −0.17 (review) with −0.19 (response).** `confirm_v1c.py`: with the review's shortcut of keeping each
field's original mean-P95 weight after trimming, the cumulative V1 is −0.1737 (−0.330, −0.017); recomputing the
weight from the trimmed months, as `review_response.py` does, gives −0.1865 (−0.340, −0.033) because Wairakei's
weight rises from 0.355 to 0.392. The response's method is the more consistent one; the report's −0.19 is right.

## Plain-language summary

Supported as now written. Each sentence maps to a result: "barely changed: somewhere between flat and a fall of
about 0.2% a year, depending on how the start-up months of new plant are handled" (V1/V2); "No field is falling
anywhere near 3%" (H2, all specifications); "Mokai shows the clearest decline, about 1.5% a year since 2008; that
field also supplies steam to greenhouses and a milk-processing plant" (segment −1.54; FGGS); "at Ohaaki output rose
sharply in 2007–08 and then fell back over five years" (annual medians); "Our data can show what the stations
delivered, not why" (the mechanism claim withdrawn); "Across the fleet, output has fallen much more slowly than 3%
a year" (every specification). No claim about drilling or upkeep remains.

## Optional wording edits

1. Plain terms: "Over the last ten years it is about 0.4% a year" leaves the sign to context; "a fall of about 0.4%
   a year, with an uncertainty that spans flat" is explicit.
2. "Process and deviations" lists commits up to 2f8c705; add c371b0f (D4 results and report) and 7a904a6.
3. "the latter a mill's net export" states an inference as fact; "probably the Tasman mill's net export (network
   codes SKOG, then CHHE)" is what the data support.
4. The abstract's "between about 0 and −0.2" and the "It shows" paragraph's "+0.1 and −0.2" are both correct
   (the +0.1 is V3, which is not a ramp adjustment); saying "0 to −0.2 for the segmentation variants, +0.1 if
   segments are combined by capacity" in one place would remove the apparent inconsistency.
