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

## Pre-review gate (G5, G6) — 2026-10-25 22:51 NZDT, after all results (wording, attribution, one descriptive table)

The lab's METHODS.md gates were run before this draft's review. No preregistered result changed.
- **G5 overclaim check** (`review/overclaim_check.md`, passes):
  - "a third of new releases" (title and plain terms) counted monorepo siblings, whose releases inherit each
    other's commits. New `code/monthly_nomono.py` (`results/tables/monthly_no_monorepos.json`) gives 21% (npm) and
    25% (PyPI) for September 2026 without them, so the text now says "a fifth to a third";
  - "read every change" now says the nine in ten packages traced to a repository.
- **G6 attribution ledger** (`results/attribution_ledger.csv`, 10 claims, passes):
  - the report's four prior-work citations had no identifiers; all are now verified (AIDev arXiv 2602.09185;
    Ghaleb 2601.17406; Robbes et al. 2601.18341; Takerngsaksiri et al. 2609.26847);
  - "reverts and follow-up fixes (MSR 2026)" was corrected to that paper's topic, follow-up fixes;
  - unverified venue claims were removed;
  - the lead's closest prior art, the 180M-repository census (arXiv 2606.24429), is now cited;
  - the lead's Nesbitt blog post could not be found and is not cited.
- **G7 not applied.** The 100-commit precision audit had a single auditor (left for the reviewer to judge).
