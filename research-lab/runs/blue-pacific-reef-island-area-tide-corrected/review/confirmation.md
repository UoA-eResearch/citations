# Confirmation pass: blue-pacific-reef-island-area-tide-corrected

Reviewer: Fable 5.1, 2026-10-24. Checked commit d7c2ace (D7 and the Theil-Sen addendum) against `review/review.md`.
Independent recomputation: `review/reviewer_checks/confirm_recompute.py` -> `confirm_recompute.out` (scipy
`theilslopes` on time-sorted input; the study's `theil_sen()` is not called for any rate). Nothing outside `review/`
was modified.

## Verdict: publish with edits

The Theil-Sen fix is correct and complete, every number in the revised report follows from it, and all nine review
findings are addressed. The edits below are wording and labelling; none changes a verdict.

## 1. The Theil-Sen fix

- **Standard estimator now.** `theil_sen()` (rates.py) takes the median of (y_j - y_i)/(t_j - t_i) over every pair
  with |dt| > 1e-6 (32 s; acquisitions are already de-duplicated to the minute). It equals `scipy.stats.theilslopes`
  to 1e-6 on shuffled and on reversed input, and all 150 E2 corrected and uncorrected rates in `islet_rates.csv`
  match my independent values to 1e-5.
- **Other time-order dependencies.** The only pairwise-slope code is `rates.theil_sen`; `h2_diag.py` (level trends,
  permutation floor) and `review_fixes.py` call it and were re-run after the fix (file times 15:00-15:02, after
  `h1_h2_D7_pre_theilsen_fix.json` at 14:59). `dep_compare.py` reads rates from the table and was re-run;
  `dep_audit.py` uses `np.polyfit`; `figures.py` reads tables. Nothing else sorts or assumes order.
- **The review's own numbers.** `checks_core.py` used the study's `theil_sen` before the fix, so the rate-based figures
  in `review.md` (the guard span scan, the H2 variants, per-islet level-trend scatter, the E1 step correlation 0.67)
  were computed with the bug; the per-atoll union-of-acquisitions level trends were on time-sorted input and were
  correct. The directional findings (Tarawa/Kiritimati tide response, E1 composition, imagery, STAC spans, FD/RQ
  seam, no baseline step) did not depend on the estimator. `review.md` is left as the record; this file supersedes
  its numbers.
- **Independent recomputation** (`confirm_recompute.out`): H2 0.878%/yr, bootstrap 0.735-1.05 (study 0.878,
  0.723-1.043; seeds differ); mean signed +0.593 (0.5925); pooled corrected +0.421 (0.264-0.577), median +0.226;
  uncorrected +1.013 (0.776-1.265); by-atoll corrected means equal to 3 decimals; guard 11 islets, -0.578 (-1.163 to
  +0.157) (study -0.578, -1.172 to +0.144), by atoll Kwajalein 4 islets +0.01, Majuro 6 -0.93, Penrhyn 1 -0.84; H1 33
  islets, D +0.383 (+0.04 to +0.741) (study +0.3835, +0.027 to +0.749); DEP r -0.111/-0.085 (report -0.11/-0.09).
  H2 variants: >= 5 ha only 0.420 (0.327-0.527); slopes used only when negative beyond 2 SE 0.816 (0.671-0.984),
  pooled +0.373 (study 0.816, 0.665-0.975); without the gross filter 0.894, pooled +0.387. By size [1,5) 1.29,
  [5,20) 0.42, >= 20 0.41 (report 1.26 on the (1,5] bin, "about 0.42"). All consistent.

## 2. Findings 1-8

1. **Mechanism withdrawn.** report.md:31-32, 109-118 and D7 item 5 withdraw the orbital-drift mechanism; panel b of
   F1 and its caption label the relation an identity; the table's last column is the union-of-acquisitions level
   trend with bootstrap CI from `review_fixes.json` (all six include zero; the values match). Done.
2. **Tarawa and Kiritimati.** report.md:28-30, 104-105, 121-125, 195 report the Otsu tide-response failure (pooled r
   +0.20 and -0.05 against -0.34 to -0.70 elsewhere, from `review_fixes.json`), give NDWI rates (Tarawa +0.30,
   Kiritimati -0.20, matching `e2_ndwi_rate_by_atoll`), and the Kiritimati Otsu number is no longer shown. Done.
3. **E1 composition.** report.md:21-23, 135-137: median 5 L7 / 20 L8 images, r = 0.66 with the L7->L8 step
   (`review_fixes.json` e1_composition), "not interpretable as a change in the islets", face-value claims removed;
   results kept "for the record only". Done.
4. **Spans.** report.md:3, 77-80, 197: 2017 start, late 2019 at Funafuti and Tarawa, 6.8 years; matches
   `review_fixes.json` s2_span. Done (two figure titles still say 2016, see new issue 3).
5. **Guard.** Tier preference (rates.py:46-49; LC08 rows now T2 29,675 / T1 23,163 / RT 38, was RT 313 of 580 guard
   acquisitions), Landsat restricted to each islet's Sentinel-2 window (rates.py:195-197), per-atoll reporting and
   the three-atoll caveat (report.md:19-20, 131-133). Done; see new issue 1 on wording.
6. **kwajalein_078.** report.md:162-163: unnamed 1.3 ha intertidal cay, tide-phase dependence, four pre-2019 images,
   "no change can be inferred". Done.
7. **Not-measured list.** `qa_d5.not_measured_by_s2_ge_1ha` lists kanton_000, kiritimati_000, tarawa_000;
   report.md:69-70. The one-sided possible-loss rule is stated (164-165). Done.
8. **Numbers and wording.** Funafuti positive (report.md:27, 100); DEP "closer" removed (172-173); bin edges stated
   (119, 150); "after the land screen" (73); Landsat image counts no longer quoted. Every number I checked in the
   report, the F1-F3 captions, `h1_h2.json`, `h2_diagnostics.json`, `review_fixes.json` and `dep_compare.json`
   agrees with the others and with my recomputation.
9. **Process.** D7 is logged with times (14:56, addendum 14:59) before the final run (15:00-15:02) and the commit
   (15:04); `h1_h2_before_D7.json` and `h1_h2_D7_pre_theilsen_fix.json` are kept and differ from the final as
   described. Done.

## 3. New issues (edits)

1. **"Disagree" is now overstated.** With the fixed estimator the guard interval is -1.17 to +0.14: it is not inside
   +/-0.2, so the guard is not passed, but it includes zero, so the sensors are not shown to disagree. My span scan
   with the correct estimator gives -0.51, -0.49, -0.64, -0.58 for spans 3.0-4.5 y, every interval including zero
   and none inside +/-0.2 (so the report's "the result does not depend on [D6]" holds, in the sense of not passing;
   it should cite `confirm_recompute.out`, not the pre-fix review). Edit report.md:18 ("It fails" -> "is not passed:
   the interval is too wide to establish agreement within +/-0.2%/yr"), report.md:187 ("disagree in the overlap" ->
   "cannot be shown to agree within +/-0.2%/yr in the overlap"), report.md:131 ("Two of the three atolls are clearly
   negative": Penrhyn is one islet), the F2 suptitle in figures.py:97 ("The two sensors disagree in the overlap")
   and the F2 caption ("The mean difference lies outside the band" -> "the interval is not within the band").
2. **D6's rationale is stale and the ignoring-guard label is unreported.** `h1_h2.json` now reads
   `verdict_ignoring_guard: "Supported"` (D = +0.38, lower bound +0.03 >= -0.2). D6 justified a post-result change by
   "H1 without the guard is already Inconclusive", which was true only under the bug. The verdict still cannot depend
   on the span, because no span from 3.0 to 4.5 y passes the guard (issue 1), but deviations.md D6/D7 and
   report.md:138-143 should say both things plainly: that the preregistered rule ignoring the guard would now read
   Supported, and why that label is not claimed.
3. **Figure titles not updated to the actual windows.** figures.py:47 F1 panel a "Sentinel-2 epoch, 2016-2026" should
   be 2017-2026; figures.py:87 and the F2 caption "2016-2021" describe a Landsat side now restricted to each islet's
   Sentinel-2 window (2017-2021). Regenerate F1 and F2.
4. **`h2_diagnostics.json` still carries the per-islet-median `level_trend_mm_yr` per atoll** (-25 Funafuti, -24
   Tarawa, -17 Majuro) and `corr_bias_vs_predicted` 0.92, which the report rightly no longer uses. Rename the key
   (e.g. `median_islet_level_trend_mm_yr`) or add a note in h2_diag.py so the table is not read as the atoll trend.
5. **"No usable Landsat 5 image survived the screens"** (report.md:75): the Collection 1 listings
   (`l1_scenes_log.json`, `data/scenes/*_l1.parquet`) contain no LT05 scene at all for these path/rows at <= 80%
   cloud; none was screened out. Say "the archive holds no Landsat 5 scene for these path/rows".
6. **Window-restriction effect, for transparency.** With tier preference but without the Sentinel-2-window
   restriction the guard is 13 islets, -0.29 (-0.85 to +0.30); with it, 11 islets, -0.58 (-1.17 to +0.14). D7 item 2
   could record both so the restriction is not read as having been chosen for its result (both fail the guard).

## In plain terms

The author found a real bug while fixing the review's points: the slope estimator was using only about half of the
image pairs, and in a lopsided way, so the earlier "2% a year" tide bias was really about 0.9% a year, and the
islands on average grew slightly rather than shrank slightly. I recomputed everything with a separate, standard
estimator and got the same numbers. The old-versus-new satellite check now fails because the comparison is too
uncertain to confirm agreement, not because the satellites demonstrably disagree, so a few sentences and two figure
titles still claim more than the data show. Otherwise the fixes are complete and the report can be published once
those lines are softened and the stale reasoning in deviation D6 is updated.
