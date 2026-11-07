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

## D3 — 2026-10-25 06:38 NZDT — an execution bug found by the comparator validation; all executions re-run (post-result)

While drawing the plan's 100-cell validation sample, after a first comparison had been computed, many pairs showed a
stored figure against no output at all. The cause is in the runner: executions set `MPLBACKEND=Agg`, which overrides
the notebook's inline backend, so no figure was emitted as an output. Every plot cell became a spurious stable
mismatch.

The setting is removed, and every build and execution is redone with the same per-notebook image choice (D2). The first
comparison is kept for the record (`results/tables/primary_pass_agg_bug.json`: 57 completed, 41 exact mismatches,
5 all-intrinsic, H1 and H2 Refuted). The corrected run is primary. The validation sample is redrawn from the corrected
run.

## Pre-review gate (G5, G6) — 2026-10-25 23:00 NZDT, after all results (wording and attribution only)

The lab's METHODS.md gates were run before this draft's review. No number changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - the title's "too few to call exact-match verdicts badly inflated" now gives both estimates and says neither
    clears nor clearly misses its bar (both intervals reach it);
  - the plain-terms claim that unseeded analyses are a "real cause" was removed, since unseeded run-to-run
    variation is what the study counts as noise.
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 5 claims, passes): the unnamed "2026
  containerisation study" is now cited (Samuel, Mietchen et al., arXiv 2604.01072); Pimentel et al. 2019, Samuel
  & Mietchen 2024, SRI (arXiv 2509.23645) and the Zenodo dataset resolve.
- **G7 not applied.** The 100-pair comparator validation had one labeller (left for the reviewer to judge); its six
  disagreements were audited (G4).

## D4 — 2026-11-07 — fixes after the independent review (verdict: fix first)

Everything here follows the first review (`review/review.md`) and is post hoc. The first draft's tables are kept as
`results/tables/primary_v1.json` and `notebooks_v1.csv`. H1 and H2 follow the preregistered rules, and both remain
Inconclusive.

1. **Stream chunking (finding 1).** Consecutive stdout outputs are joined before comparison (`NO_COALESCE=1`
   reproduces the draft). nb16791 now matches exactly, and nb4750's stored value is compared as one item.
2. **Validation (finding 2).** The first check was not blind. The labeller saw the comparator's verdicts, and was
   the same agent that wrote the comparator.
   - New `code/validate_blind.py` draws a fresh stratified sample (seed 20261107; 30 text mismatches, 20 text
     matches, 30 figure mismatches, 15 figure matches). The comparator's verdicts go into a key file outside the run
     directory.
   - A separate agent session labelled every pair from the outputs alone, then all 17 remaining figure mismatches.
   - Agreement: text 49 of 50; figures 14 of 15 matches but 13 of 30 sampled flagged mismatches (20 of all 47).
   - `code/posthoc_figures.py` re-computes H1 and H2 with the human judgement for every flagged figure (19.2%,
     1.24).
   - The 6-bit image threshold is preregistered and stays primary. The 12-bit and human-judged readings are
     sensitivities.
   - The keys and labels are in `results/tables/validation_blind/`.
3. **Attribution (finding 3).** The three rungs (byte-exact 48, masked 30, noise-aware 25 of 57) are reported. New
   `code/posthoc_commit.py` finds that the 31 notebooks read at a commit other than the dataset's have identical
   notebook files at both commits.
4. **The disjunction (finding 4).** The varies/envelope split is reported (22 varies-only cells, 3 both, 0
   envelope-only), with the envelope-only reading as a sensitivity (0 of 30). The plain terms now say randomness is
   possible, not demonstrated.
5. **"Exact" (finding 5).** The title and verdict say "masked exact matching", the byte-exact factor (1.92) is given
   beside it, and the within-sample caveat is repeated in the verdict.
6. **Precision and masks (finding 6).** Numbers printed to 10 or more significant digits are compared with a
   relative tolerance of 1e-9 (`NO_FULLPREC_TOL=1` reproduces the draft). Bracketed durations and `ls -l` dates are
   masked. nb17727, nb19008 and nb19758 now match.
7. **Environments and coverage (findings 7 and 8).** No notebook with a requirements file completed, and the report
   now says so. The three drop reasons, the stdout/stderr rule for shell messages, and the late nb19053 run are
   stated.
