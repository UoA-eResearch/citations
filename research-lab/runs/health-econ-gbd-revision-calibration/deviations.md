# Deviations log

Timestamped record of every change after the plan was committed. Departures from the lead decided before the plan are
in plan.md section 2.

Plan committed 2026-10-12 00:07 NZDT)

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
