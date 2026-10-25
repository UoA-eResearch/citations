Confirmation pass. You reviewed this study earlier today (verdict: fix first; review/review.md). The fixes are in
deviations.md D2, and the first version's tables are in results/tables/v1_pre_review/. Check that each finding is
resolved, that nothing new is wrong, and give a verdict (publish / publish with edits / fix first). Be economical:
read the diffs and tables, re-run only what you need. Append your confirmation to review/review.md.

What changed, by your finding:
1. **Era.** posthoc_d2.py adds era splits (pre-2019 sample and without district-court citers), reported in the
   verdict, table and plain terms.
   - 1960–89: D(−1) −1.01.
   - 1990–2013: −0.05, with D(+5) +0.41 (+0.21 to +0.65); pre-share −0.13, "would read Refuted".
   - 2014–2024 without district courts: +0.10.
   - The title now carries the era.
2. **Coverage-break fix.**
   - All stacks without district-court citers: 68 stacks, D(−1) −0.27 (−0.74 to −0.01), D(+5) +0.09.
   - The year-cut check (posthoc_d2_yearcut.json, −0.522 against −0.521) shows D1 is a sample restriction.
   - D1's mechanism is corrected to district courts, and F2 now plots courts by type.
3. **Weighting.** Disclosed in methods and the verdict.
   - Per-stack fits in posthoc_d2_per_stack.csv: 68% negative, median −0.26. The top five carry 49%.
   - Leave-top-k-out: −0.39 to −0.47. Fay v. Noia is named.
4. **Chevron.** Paths by court are in posthoc_d2.json (chevron_by_court).
   - Without district courts the decline grows from 13% in 2019 to 36% in 2023. Appellate only, it is flat until
     −45% in 2023.
   - Its SMD is reported (1.28; 1.64; 2.15).
5. **Coverage and parse.**
   - The old-reporter regex is fixed: 141 pairs, and 4 of 146 rows dropped, counted in coverage.json.
   - SCDB blank-usCite terms are matched by name: 101 of 174 (58%).
   - The Constitution Annotated attempt and the incomplete-list tag are recorded. 73 treated (was 71).
6. **Controls.** They now require an SCDB id and the treated case's SCDB issue area (event.py match). The whole
   pipeline after counting was re-run.
   - Primary D(+5) +0.29 (−0.05 to +0.51): still not testable.
   - Excluding co-citing opinions: D(+5) 0.66 (0.41–0.83), pre-share 0.35, Inconclusive.
   - Pre-2019: D(−1) −0.52.
7. **G5 re-labels.** The title, "runs against erosion" (now "against a decline in citation counts"), the peak (now
   +71% the year after), "best evidence says no", the mechanical part of the rise, and "66% is an upper bound".
   review/overclaim_check.md is regenerated (48 rows, passes).
8. **Balance** is reported as a distribution: mean 0.25, median 0.12, 30 of 73 above 0.5, 9 above 1.
9. **Process.** D2 records the patched event.py, the foreseeable break, the 4 partial overrulings and the
   plan/code mismatch (now fixed).
- **Gates:** the G1 audit is in D2, G2 in coverage.json, and G3 in results/plausibility.md. G5 and G6 pass.

Note: posthoc_d2.py itself had the same `d.stack` attribute bug on first run (fixed; variants cached). Check the
new numbers in report.md against results/tables/primary.json, posthoc_pre2019.json, posthoc_d2.json and
secondary.json.
