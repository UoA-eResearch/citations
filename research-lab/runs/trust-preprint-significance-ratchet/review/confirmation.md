# Confirmation pass on the fixes (commit 9420dd6, deviations D5)

Reviewer: Claude (Fable 5.1), same reviewer as `review/review.md`. Date: 2026-10-17.
New checks are under `review/reviewer_checks/` (`s1_surviving_check.py`, `s1_star_check.py`, `census_gaps.py`;
outputs in `cache/`). No study file other than this one and `reviewer_checks/` was touched.

## Recommendation: **publish with edits**

The twenty issues of the first review are addressed adequately, every new number in report.md matches
`results/tables/review_response.json`, the coding table and Figure 2, and the verdict and its framing are now right.
One new thing is wrong and must be changed before publication: the post hoc S1 comparison (+9.6 points, "the
direction is what selective removal would produce") is an artefact of significance-star legends. Four smaller edits
follow. None touches the verdict.

## What was confirmed

- **Issues 1-2.** The verdict block states the mechanical Refuted and why it is not credited; the four fallback
  crossings are tabulated correctly (R1: 3 artefacts, 1 real correction, down; 8 of 13 all-version exact crossings
  with p = 0 or 1; 5,232 of 10,031 df-less); "4 trustworthy cases" is gone; the automated strict 0.516 is mentioned
  and not credited.
- **Issue 3.** `verified_coding.csv` codes all 54 ids; the dedup keeps the v2 id for the two cross-sample duplicates
  (w008 for v073, w095 for v022), so the 52-row set is 13 / 12 / 16 / 8 / 2 / 1 with 9 / 7 / 10 / 3 / 1 / 1 up, as
  the report's table says. I recounted the census of changed results by hand from the codes and the directions:
  33 (13 new data, 10 re-analysis, 10 unstated), 20 up, 28 papers. Sensitivities 20/31, 9/13, 16/27, 20/33, 23/37,
  31/52 and all exact intervals reproduce. The eight "correction or typo" codes each rest on a value that contradicts
  its own sentence, which is a defensible, direction-neutral criterion.
- **Issue 4.** 1.80 and 3.65 per 1,000 reproduce (64 x 42/64 / 23,271; 1,411 x 0.12 / 46,389).
- **Issues 5-7, 8-12, 15-17.** Disclosures present and accurate (blinding, batch passes and the 44 shared notes,
  glued text 20.8%, failure taxonomy, title rejections by server 1,234 / 789 / 469 / 172, version-1 timing,
  44% of pairs with no statistic). The pipeline was not re-run, and the report says so.
- **Issue 14.** S2 decomposition reproduces (1,361 evaluable; 153 verbatim; 52 one-tailed; 29 decision
  inconsistencies, 3 repaired).
- **Issue 17 (R17).** Independent re-fetch of Crossref dates for the 28 census papers: all 28 known, minimum gap
  51 days, none negative (`cache/census_gaps.jsonl`).
- **Issue 18.** Yin et al. 2026 verified in Europe PMC under 10.64898/2026.06.30.735556 (Yin H, Ahn W, Forster PM,
  Rust R; 72,644; 39.8 / 50.0 / 10.2%; 8.4% vs 4.2%). Sommer, Janda, Bero, Nelson, Brierley, Nuijten & Wicherts as
  corrected are right.
- **Issues 19-20.** report.md and report.html carry the same numbers (the HTML-only tokens are captions, table cells
  and a URL-encoded glyph). Figure 2's six rows match review_response.json and its caption.

## Remaining issues

**C1 (must fix). The post hoc S1 comparison is an artefact of star legends (report: verdict block "Selective removal
could not be tested well", "In plain terms", Results S1 third and fourth bullets; D5.3).**
Of the 7,752 statistics "added to a sentence that survived", 3,169 (41%) are significance-star definitions
(`*p < 0.05, **p < 0.01, ****p < 0.0001`), which are "significant" by construction (91.3%); of the 1,250 dropped,
344 (28%) are. Ten random short "added" items were ten star legends. The asymmetry comes from journal captions
carrying extra star levels and from caption text glued into results sections, not from results being removed.
Without star legends the difference is **+2.4 points (-6.1 to +10.7)**; without star legends and glued or over-long
sentences +4.8 (-0.8 to +11.0); text sections only +2.2 (-5.1 to +9.6); equalities (`p = x`) in text only -2.3
(-12.5 to +8.4). (`cache/s1_star_check.out`.) The sentence "The direction is what selective removal of
non-significant results would produce" is therefore unsupported, and the headline bullet "a sharper post hoc
comparison ... finds removed ones less often significant" and the plain-terms "a sharper one hints that removed
results are somewhat less often significant" must go.
*Fix:* either drop the post hoc comparison, or keep it in S1 only with the star-legend-free numbers and the sentence
"once significance-star legends are removed the difference is +2 points with an interval from -6 to +11; the
comparison is uninformative". Update D5.3 and review_response.json accordingly (add a `star` exclusion to R13).

**C2. "29 decision inconsistencies, 3 repaired" is an upper bound (verdict block; S2).**
Of the 29, 24 are verbatim-unchanged tuples, 3 are one-tailed-explicable (t(27) = 2.01, p = 0.024; t(27) = 1.99,
p = 0.028; F(1,439) = 3.7, p = 0.026), and several are `z` matches that are not z-tests (`z = 53.95, p = 0.14`,
`z = 6.0, p = 0.68`, `F(9,466) = 800.9, p = 0.054`). *Fix:* "at most 29", and say that the z-regex catches z-scores
that are not test statistics.

**C3. The pre-coding census should appear as a sensitivity (Results "Lead estimate" table; Figure 2).**
The coding was done after unblinding and moves the census from 24/42 (0.57, exact 0.41-0.72) to 20/33 (0.61). The
excluded 11 are 5 up and 6 down, so the move is small and in no reading consequential, but the blind-only number is
the one a sceptic will ask for. *Fix:* add the row "all 42 blind-verified strict crossings, before coding: 24/42,
0.57, 0.41-0.72".

**C4. Coding inconsistency (verified_coding.csv).** w053 is `changed_data` ("n 15 -> 13") and w057
`changed_analysis` for the same sentence pair; both carry "reviewer rejects positional identity". *Fix:* give both
the same code (changed_analysis, since the sentence structure, not the n, is what changed); "new data only" becomes
9/12 (0.75, 0.43-0.95). Either way the reading is unchanged.

**C5. Small wording.**
- Results, strict-rule limitation: "20.8% of strict-eligible pairs" is the reviewer's figure from
  `strict_leak_and_middot.py`, not reproduced in review_response.json; say so or add it to R8.
- "Pairs: Of the 2,664 rejected ... the reviewer's sample suggests most are true pairs": the sample was 14; say "a
  sample of 14".
- Plain terms: "internal arithmetic errors in preprints were almost always carried into the journal version
  unchanged" should read "reported p-values that disagree with their own test statistic were almost always carried
  over unchanged", since many are not errors (the report's own S2 says so).

## Numbers recomputed for the new material

| quantity | report / JSON | recomputed | note |
| --- | --- | --- | --- |
| codes n / up | 13/9, 12/7, 16/10, 8/3, 2/1, 1/1 | same | from verified_coding.csv and the blind directions |
| census of changed results | 20/33, 0.61, exact 0.42-0.77, boot 0.43-0.78, 28 papers | same | |
| minus reviewer rejections; new data only; without glued; gap > 30 d; pooled v1 changed; all 52 | 20/31; 9/13; 16/27; 20/33; 23/37; 31/52 | same | glued = 15 of 64 by D5's regex, 13 by mine |
| rates per 1,000 | 1.8 strict, 3.6 preregistered | 1.80, 3.65 | |
| census posting gaps | 28 known, none <= 30 d | 28 known, min 51 d | independent Crossref fetch |
| S2 decomposition | 1,361; 153; 52; 29; 3 | same | of the 29: 24 verbatim, 3 one-tailed-explicable |
| post hoc S1 | 70.8% of 1,250 vs 80.4% of 7,752; +9.6 (0.6-18.6); 1,899 papers | same | star legends: 41% of added, 28% of dropped; without them +2.4 (-6.1, +10.7) |
| Yin et al. 2026 | 72,644; 39.8/50.0/10.2; 8.4 vs 4.2 | same | Europe PMC record, first published 2026-07-01 |
| Figure 2 rows | 0.25 (0.006-0.81); 0.489; 0.516 (0.40-0.63); 0.61 (0.42-0.77); 0.65 (0.45-0.81); 0.60 (0.45-0.73) | same | image inspected |
