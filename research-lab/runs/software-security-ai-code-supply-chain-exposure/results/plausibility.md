# Plausibility gate (G3) — added in D2 (the study predates METHODS.md)

## 1. Headline numbers against expectation

| quantity | value | expected range and source | plausible? | notes |
|---|---|---|---|---|
| AI-signed share of non-bot commits, Sept 2026 | 10.8% (npm), 13.3% (PyPI) | repository-level census reports widespread agent traces across 180M repositories, single signals biased low (ledger S5, S11) | yes | a lower bound; concentrated (top 50 repositories hold 44%) |
| repositories with any AI-signed commit, Sept 2026 | 28% / 33% of active repositories | same | yes | |
| tree multiplier, download-weighted | 1.61 / 1.58 | trees of the most-downloaded packages are small (deps.dev graphs: few nodes per root) | yes | far below the plan's fivefold |
| H2 latency ratio | 1.01 (per package), 1.12 (per repository) | AI-signed commits go through the same release process | yes | 80% of per-package pairs share a release |

## 2. Three units traced end to end

| unit | raw input | intermediate values | output | matches the pipeline? |
|---|---|---|---|---|
| npm `readable-stream` 4.8.0 (single-package repository) | registry release list; tag range in nodejs/readable-stream | tag method; 4 commits in the range, 1 AI-signed (Copilot) | latest release flagged; counts in p | yes |
| PyPI `pydantic` (latest release unflagged) | deps.dev graph of its latest version, 5 nodes | one flagged node, `annotated-types` (its latest in-window release has an AI-signed commit) | root exposed through its tree; enters P_w with its downloads | yes |
| stratified audit item | an `identity` match re-derived with `git cat-file` (local objects only) | the matched account is an AI agent's bot identity | both blind labellers: ai_signature | yes |

## 3. Invariants

| invariant | where | holds? |
|---|---|---|
| every analysed release is ok, a date-window fallback, or an empty range | coverage.json `release_ranges` | yes (287,595 + 112,839 + 22,747 = 423,181) |
| every cloned package's latest release is in the window or counted as unflagged by construction | coverage.json `packages_in_p` | yes (13,754 + 4,937 = 18,691) |
| PyPI tree-node versions match in canonical form; none remains unmatched for padding | coverage.json `tree_nodes_pypi` | yes (0 "version in no registry release" after D2) |
| the reviewer's independent re-implementation reproduces p, P_w, R and the H2 ratio | review/review.md | yes |
