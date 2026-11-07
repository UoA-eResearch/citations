# Deviations from plan.md

## D1 — 2026-10-25 08:08 NZDT — linter activation and parser fixes, before any population or replay

1. **The linter option.** `-Dlinter.flexible=true` is rejected for a library-defined option, so
   `-Dweak.linter.flexible=true` is used. It was verified on a test file to emit the expected warning.
2. **Linter availability.** In O = 2025-03-31, `Mathlib/Init.lean` does not import the FlexibleLinter, so most files
   never load it. For snapshots whose Init lacks it, labelling compiles a temporary copy of the file with
   `import Mathlib.Tactic.Linter.FlexibleLinter` prepended, and warning lines are shifted back by one. That module
   imports only Lean core and adds no lemmas. By 2025-09-30 (O₂), Init imports it, and files are compiled as they are.
3. **Parser.** `public section`, `noncomputable section` and `@[expose] public section` count as sections, so
   their `end` does not pop a namespace. A unit test was added.

## D2 — 2026-10-25 09:20 NZDT — error classification fixed after the first results (secondary analyses only)

The first results (`results/tables/primary_v1.json`) showed no "unknown identifier" errors and 354 "other". Newer Lean
writes "Unknown identifier", and the class patterns were case-sensitive. Class matching is now case-insensitive, two
frequent classes are added ("function expected", a changed lemma signature; and "no goals"), and error messages are
stored. The replays are re-run to recover the messages.

**H1 is unaffected,** because failure means any error in the declaration's span. **Affected:** the error-class
composition and the preregistered "excluding unknown-identifier-only failures" sensitivity, which in v1 equalled the
primary analysis.

## Pre-review gate (G5, G6) — 2026-10-25 23:28 NZDT, after all results (wording and attribution only)

The lab's METHODS.md gates were run before this draft's review. No number changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes): error classes are first errors, not causes.
  - "Removed or renamed lemmas" became "names (usually lemmas)".
  - "Changed lemma signatures" became "'function expected' errors, typically a changed signature".
  - "The largest single cause" became "the most common first error".
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 5 claims, passes):
  - the Isabelle/AFP study (TOSEM 2025) and Lean Refactor (arXiv 2605.20244) resolve with matching titles;
  - the latter's "brittle across library versions" is a motivating statement in its abstract, not a measured
    result, and is recorded as such.

## D3 — 2026-11-07 — fixes after the independent review (verdict: fix first)

Everything here follows the first review (`review/review.md`) and is post hoc. The table the review saw is kept as
`results/tables/primary_v2_pre_d3.json`, and the first populations as `data/work/pop_*_v1.parquet.bak`. No Lean
file was recompiled. The corrected population is a subset of the first, so the existing labels and replay results
are reused.

1. **Multi-line `simp` (finding 4).** A more-indented line after `simp [...,`, with an unclosed bracket or a trailing
   comma, is now treated as a continuation of the same call. 231 primary-pair declarations leave the population;
   none is flagged, and their fail rate is 15.6%. Primary OR 1.57 (0.97–2.55), p = 0.07; H1 stays Inconclusive.
2. **Comment offset (finding 5).** The body offset was computed on comment-stripped text, so the "correction" was a
   no-op. Four declarations with a comment before `:= by` are flagged and dropped. The `<;>` double count in the
   tactic covariate is fixed.
3. **Error classes (finding 2).** The patterns now accept backticks and newer wording. Classes are recomputed from
   the stored messages (the first three errors per proof, 200 characters each), both for the first reported error
   and for the highest-priority class.
4. **Pooling (finding 3).** The two pairs share 2,209 declarations, so the pooled GEE clusters by file across pairs.
5. **Body changes (finding 1).** The "unchanged bodies never fail" sentence, true by construction, is replaced by the
   body-change rates: 109 of 110 flagged and 1,195 of 2,378 unflagged. The second pair's flagged set is described as
   post-clean-up.
6. **Wording (finding 6).** The unadjusted and independence-correlation odds ratios are reported, and the table row
   now reads "whose only error is".
