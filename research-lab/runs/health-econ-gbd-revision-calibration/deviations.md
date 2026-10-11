# Deviations log

Timestamped record of every change after the plan was committed. Departures from the lead decided before the plan are
in plan.md section 2.

Plan committed 2026-10-12 00:07 NZDT.

## D1 - 2026-10-12 00:08 NZDT - crash in the secondary analyses (code fix, no change to any rule)

The first full run computed and saved the primary results (results/tables/primary.json), then stopped in
`secondary()` with `TypeError: unhashable type: 'numpy.ndarray'`. The line merging the "all" entry with the quality
groups was written `{"all": None} | g.items()` instead of `({"all": None} | g).items()`. The synthetic test covered
only the primary analysis, so it did not catch this. Fixed that one line; the analysis is rerun unchanged otherwise.
The primary analysis uses a fixed seed, so its numbers are reproduced exactly by the rerun.

## D2 - 2026-10-12 00:12 NZDT - exploratory analyses added after the primary outcomes (labelled exploratory)

After seeing the by-cause table, "Other neoplasms" had the lowest per-cause C2 (8%). The GBD 2023 causes-of-death
appendix (p. 361) attributes GBD 2023's large increase for this cause to fixing a CoDCorrect error that excluded
"Other benign and in situ neoplasms" deaths in previous cycles, and to restoring brain-tumour codes dropped in earlier
rounds. To show how much single causes drive the result, `code/exploratory.py` adds X1-X6: excluding Other neoplasms;
excluding every residual "Other ..." cause (a name rule); the per-cause distribution of C2; calibration at several
nominal levels, with the widening factor needed to reach each level; the H4 contrast within each year; C2 with asymmetric half-widths. None of these changes a
preregistered verdict; the report labels them exploratory.

## D3 - 2026-10-12 00:41 NZDT - edits after the independent review (review/review.md: publish with edits)

All analyses below are in `code/review_checks.py` (results/tables/review_checks.csv, none_class_audit.csv) and are
labelled "review-requested, exploratory" in the report. No preregistered verdict changes.

- **R1, erratum to plan section 4.** The plan, quality.py and the draft report said the 85 countries absent from WHO
  Table 4.1 "have no vital-registration data in the WHO Mortality Database". That is wrong. Table 4.1 lists only
  countries in WHO's GHE scope (Section 3.1: Member States over 90,000 people plus Puerto Rico, Taiwan and Palestine).
  Of the 85, 9 have national WHO Mortality Database data since 2010, and 17 have registration data in GBD's own
  garbage-code table for 2010-2021, among them China, India and Taiwan. The class is now described as "not assessed in
  WHO Table 4.1". The H4 gap is reported under three alternative groupings.
- **R2.** Death-weighted C2, as an alternative formulation alongside the preregistered equal-cell one.
- **R3.** H4 gap with the country-only bootstrap, the upper bound across seeds 1-10, and B = 20,000.
- **R4.** A distribution-free check (do the two UIs overlap?), and expected C1, C2 and overlap under error correlations
  0, 0.5 and 0.8.
- **R5.** C2 by cell size; C2 excluding cells with fewer than 1 death; agreement between years.
- **R6.** Plain-language statements drawn from exploratory X4 are now labelled. The 2.2× factor is described as a
  log-scale factor.
- **S7-S12.** E1 is described as a floor. IHME's descriptions of its UIs are quoted. "Other intestinal infectious
  diseases" is discussed (its revision came with no substantive modelling change). The mechanism behind the H4 null is
  stated. The reply to "rounds are not comparable" concedes more. Prior work is cited (Dorrington & Bradshaw 2016;
  Byass 2013).
- **M13-M15.** The rows outside their own interval are recounted exactly: GBD 2021 has 21, of which 5 have a relative
  excess above 1e-6; GBD 2023 has 13, none above 1e-6. The plan's 6 and 5 came from the first per-file checks. The
  secondary analyses use B = 1,000, not 2,000. The stray ")" in this file is fixed.
- **review_checks.py** had the same dict-iteration slip as D1 in its last block; it was fixed before any output was
  used.
- **The `none`-class audit.** It first counted countries present in the GBD table at any year (27). It now uses
  countries with data in 2010-2021 (17), matching WHO's post-2010 window and the reviewer's count. Both counts are
  reported.
