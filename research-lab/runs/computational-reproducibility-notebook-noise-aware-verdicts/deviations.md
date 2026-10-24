# Deviations from plan.md

## D1 — 2026-10-25 04:10 NZDT — selection fields and comparator scope, before any notebook is executed

1. **Eligibility** (plan §1) in the dataset's `db.sqlite`: `executions.reason IS NULL` (ran to completion) and
   `executions.diff_count > 0` (at least one cell differed), joined to `notebooks.language = 'python'`. That
   gives 340 executions. The sample is drawn from the distinct notebooks.
2. **Stored outputs and the AS-OF commit.** The repository is checked out at its last commit before the article's
   `published_date`, and the notebook's stored outputs are read from that checkout. If the notebook does not exist
   at that commit, the dataset's own `commit` is used and flagged.
3. **Comparator scope.** stdout streams and `execute_result`/`display_data` outputs are compared. stderr streams
   (warnings) and error outputs are not results and are not compared. This is fixed before any execution.
4. **H2 base.** Because the plan's sample is notebooks the dataset already found irreproducible, H2's exact and
   noise-aware fail rates are computed within that sample. The report says so.

## D2 — 2026-10-25 06:12 NZDT — failed AS-OF builds retried in full Python images, before any output comparison

In the first pass, 88 of 149 AS-OF builds failed, mostly because old pinned packages without wheels need a C compiler
and the `-slim` images have none (for example `kiwisolver==1.0.1` for `matplotlib==3.0.2`). Those 88 are
retried in the full `python:{version}` image, which has build tools, and their AS-OF executions run in the same
image. LATEST environments stay `-slim`. No output comparison had been computed. The first-pass status is kept in
`data/interim/run_status_pass1.csv`, and both passes are reported in the selection flow.
