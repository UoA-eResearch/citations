# Deviations from plan.md

## D1 — 2026-10-24 23:13 NZDT — inactive repositories, before any release flag is computed

`git clone --shallow-since=2024-01-01` fails ("error processing shallow info") when a repository has no commits since
that date. About a fifth of the first 3,300 clone attempts failed this way.

The plan says failed clones are "excluded and counted". Applied to these repositories, that would drop packages
whose releases certainly contain no AI-attributed commit in the window, and so inflate p. Instead, each failed clone
is retried once with its error captured (`code/classify_failures.sh`) and classified:
- **inactive:** treated as cloned. Their releases in the window are unflagged, with method "inactive".
- **missing** (repository gone or private), **or other:** excluded and counted, as planned.

This is a change of handling, not of any planned choice, made before any flag, exposure or latency was computed.
