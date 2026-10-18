## Confirmation (revision 39c875b, D6)

Checked 2026-10-18 against the committed revision. Nothing outside `review/` was modified; no requests to
localhost:8000 or the PBS API.

**Final verdict: PUBLISH WITH EDITS.** The three hypothesis verdicts stand. All new numbers in the report match
`results/tables/post_review.json`, and every value in that file matches the reviewer's independent computations
(`reviewer_checks/03_retrieval.out`, `04_misc.out`, `07_screen_compare.out`, `08_key_readjudication.out`). Two stale
sentences and the HTML status label remain; none affects a number or a verdict.

### Findings addressed

| Finding | Status | Where |
|---|---|---|
| 1 Irreproducible (d) sample | Addressed by snapshot. `results/snapshot/{items,passages,runs}.jsonl` are byte-identical to `data/` (SHA-256 verified, `sha256sum -c` OK) and committed; the report and D6 say the snapshot defines the benchmark and that `generate.py` cannot regenerate (d). Leaving the generator unfixed is acceptable given the disclosure; sorting the set-derived pools before sampling is still advisable for any future run. | report.md:121-123, 315-316; deviations.md D6.1 |
| 2 AU retrieval misses misattributed | Addressed. Own-passage hit rates (NZ b 100%, AU b 89.5%, a 96%, d 70%/60%), accuracy conditional on the hit (100% for (a) and (b) in both countries), "all 19 AU errors among the 21 misses", "the retrieval column describes the retriever", conditional gap 0; F2 caption updated. | report.md:35-40, 166-173, 188-189; F2_gap.txt |
| 3 False BM25 claim; (d) retrieval = source attribution | Addressed. Claim removed; target 39%/26% vs source 90%/58% hit rates stated; "affirmed 26% (NZ) / 23% (AU) given target hit" verified (10/39, 6/26); F3 caption updated. | report.md:43-47, 216-219, 259-261; F3_fabrication.txt |
| 4 AU fabrication upper bound | Addressed. 28% (19.5-38%) reported beside 35% in the summary, the H3 table and the discussion; plain terms say "roughly 1 time in 4 to 1 in 3". | report.md:22-23, 71-72, 203-204, 214-215 |
| 5 Key-check description and rates | Addressed in the methods: AU half checks the generator's parsing; (d)-negative near-duplicate rate about one in six; AU (a) negatives at least 5/47 (10.6%); 272 "containing" presentations. One stale sentence remains (edit 1 below). | report.md:49-54, 124-129 |
| 6 Wording asymmetry | Addressed. | report.md:262-264 |
| 7 Counts, cap, oncology mix, null-content errors | Addressed (totals NZ 555 / AU 494; cap per family x answer, up to 6; two-thirds chemotherapeutic agents; "empty content from the server"). The optional footnote on the 59 duplicated sentences was not added; not required. | report.md:24-25, 62, 119-120, 164-165, 270 |
| 8 Provenance | Addressed. figures.py committed (a3019c2) with the stated note that the 43c9877 PNGs were drawn with it; PNGs and captions regenerated 19:58; D2 counts note; vacuous inheritance branches noted. | deviations.md D6.5; report.md:292-293, 308 |

Also verified: `report.html` was rebuilt after the final `report.md` (19:58:08 vs 19:57:57) and contains the new
text; `code/retrieval_diagnostics.py` rebuilds the index with `get_scores` + stable argsort rather than `get_top_n`,
which gives the same top-3 sets as the reviewer's rebuild (all hit rates identical); Youden's J for (b) matches to
three decimals, pooled J differs from the reviewer's only in the bootstrap stream (+0.063, CI -0.082/+0.22 vs
-0.081/+0.213); the reviewer-screened fabrication rates (30/81, 24/86) match.

### Required edits (text only)

1. `report.md:255-258` ("The answer keys are the structured data" bullet) still contains the two sentences the
   revision corrected elsewhere: "The Schedule XML and the PBS API were checked against the PDF and the raw API
   records" (contradicts 127-129; the API was checked against itself) and "The AU counterfactuals were not screened"
   (contradicts 214-215). Replace with: "The NZ keys were checked against the Schedule PDF; the AU check verified the
   generator's parsing of the API records only. Family (a) failed that check. The NZ counterfactuals needed a full hand
   screen; the AU ones were not screened by us, and the reviewer's blind screen is reported alongside."
2. `report.md:219` "On NZ, all of those affirmations were overlapping items": the 10 are 9 "equivalent" and 1
   "overlapping" under D5's own tiers. Say "all 10 were among the 17 equivalent or overlapping items".
3. Rebuild `report.html` after edits 1-2. Note that `code/build_report_html.py:31` switches the status label from
   "pre-review draft" to "revised after independent review" only if `review/confirmation.md` exists; the confirmation
   lives in this file, so either add a one-line `review/confirmation.md` pointing here or change the builder's check,
   otherwise the published page will keep saying "pre-review draft".

### Not required

- Fixing `generate.py`'s set ordering (sorted pools) for future runs.
- A footnote that 59 criterion sentences are asked about more than one chemical within a jurisdiction.
