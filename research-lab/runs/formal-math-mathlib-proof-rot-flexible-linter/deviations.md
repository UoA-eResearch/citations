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
