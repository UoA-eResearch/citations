# Plan (preregistration): do mathlib proofs the flexible linter flags break more often a year later?

Lead: `formal-math-mathlib-proof-rot-flexible-linter`. Written before any snapshot is compiled or any proof is
replayed.

**Seen before this plan:**
- the FlexibleLinter source and docstring;
- the commit hashes of four master snapshots.

## 0. Hypothesis

The docstring of mathlib's FlexibleLinter claims that a rigid tactic acting on the output of a flexible one (for
example `simp; rw`) is "more likely to break".

- **H1.** Consider theorem and lemma proofs in a 2025 snapshot O that contain at least one non-terminal
  unrestricted `simp`, and whose statement text is unchanged in the snapshot N twelve months later. Replayed verbatim
  in N, proofs the flexible linter flags in O fail with odds at least 1.5 times those of unflagged proofs, adjusting
  for tactic count and simp-call count, with clustering by file.
  - **Supported** if the odds ratio is at least 1.5 and its 95% lower bound exceeds 1.0.
  - **Refuted** if the upper bound is below 1.5.
  - **Inconclusive** otherwise.

## 1. Snapshots

- **Primary pair:** O = `9bed6a56` (master on 2025-03-31) and N = `08fd1302` (2026-03-31).
- **Secondary pair, pooled as a sensitivity:** O₂ = `bb6ed240` (2025-09-30) and N₂ = `2a885768` (2026-09-30).
  O₂ also serves as O + 6 months for the primary O's decay curve.
- Each snapshot is a depth-1 checkout, built with its own `lean-toolchain` via elan, and uses mathlib's prebuilt
  olean cache (`lake exe cache get`). If a cache is missing, that snapshot is built from source and logged.

## 2. Declarations and features (from O's source)

- **Declarations.** `theorem` and `lemma` commands with a tactic proof (`:= by`), parsed with a line-based Lean
  parser.
  - The qualified name is formed from `namespace … end` blocks plus the declared name.
  - The **statement** is the text from the name to `:=`. The **proof body** runs from after `by` to the next
    top-level command.
- **Features** (syntactic, on the body with comments removed):
  - **tactic count:** non-empty tactic lines, plus `;` and `<;>` separators;
  - **simp calls:** occurrences of `simp`, `simp_all`, `simpa`, `dsimp` and `field_simp`;
  - **non-terminal unrestricted simp:** a `simp` or `simp_all` without `only`, not `simp?`, that is not the last
    tactic of its block.
- **Flag.** The O file is compiled against O's cache with `-Dlinter.flexible=true`. A declaration is flagged if any
  flexible-linter warning falls inside its source span.

## 3. Matching and replay

- **Population.** O declarations with at least one non-terminal unrestricted simp, whose file exists at the same path
  in N, and which have a declaration of the same qualified name in that file with identical statement text (after
  collapsing whitespace).
- **Replay.**
  - In N's file, each matched declaration's proof body is replaced by O's, one rewritten file per source file.
  - The file is compiled against N's cache (`lake env lean`, with a 30-minute limit per file).
  - Errors are attributed to declarations by source span in the rewritten file.
- **Fail:** at least one error inside the declaration's span, or the file timing out (classed "timeout").
- **Validation.** Compiling the unchanged O files against O's cache must leave more than 99% of population
  declarations error-free. Otherwise the pipeline is fixed before any replay.

## 4. Model

- **Specification:** logistic GEE, fail ~ flagged + log(tactic count) + simp calls, clustered by file with
  exchangeable correlation. This is the population-averaged counterpart of the lead's mixed model, chosen for
  robustness.
- **Statistic:** the odds ratio for `flagged`, with a 95% robust interval.

## 5. Secondary (labelled as such)

1. **Error classes.** Unknown identifier or constant (removed or renamed lemmas), simp made no progress, rewrite
   failed (pattern not found or motive), type mismatch, unsolved goals, timeout, and other.
2. **H1 without failures whose only errors are unknown identifiers,** since deprecations dominate.
3. **The decay curve:** failure rate at O + 6 (N = O₂) and O + 12, by flag.
4. **The secondary pair** (O₂ → N₂), alone and pooled.

## 6. Limits stated in advance

- **Syntactic parsing.** Lean syntax is parsed approximately: line-based declaration spans and token-based features.
- **Context changes.** File-level context (variables, opens, imports) changes between snapshots and can break proofs
  regardless of style. Clustering by file absorbs some of this. Moved files are not followed.
- **Linter coverage.** Flexible-linter coverage depends on the linter's version in O.
