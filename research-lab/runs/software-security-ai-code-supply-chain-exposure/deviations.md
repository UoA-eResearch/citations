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

## D2 — 2026-10-27 16:46 NZDT — after independent review ("fix first"); POST-RESULT

No preregistered verdict changes: H1 and H2 stay Refuted. v1 tables and figures are in `results/tables/v1_pre_review/`.

**Bug fix: PyPI version matching** (`code/analyse.py`, `vnorm`).
- deps.dev reports padded PyPI versions ("3.20.0" for the registry's "3.20"). So about 10% of in-set PyPI tree nodes
  could never match a release and were silently unflagged.
- Versions are now compared in canonical PEP 440 form (`packaging.utils.canonicalize_version`).
- PyPI P_w 35.5% → 36.1%, R 1.91 → 1.94 (1.67–2.24), unweighted exposure 48.4% → 48.8%; npm unchanged.
- `primary.json`'s mislabelled `latest_release_in_window` is now `releases_analysed`.

**Post hoc analyses** (`code/posthoc_review.py` → `results/tables/posthoc_review.json`, `coverage.json`):
- **R mixes weighting with tree inclusion.** P_w is download-weighted and p is not.
  - Like for like, P_w divided by the download-weighted own-release rate is 1.61 (1.51–1.73) for npm and 1.58
    (1.43–1.78) for PyPI.
  - Unweighted, the root → tree multiplier is 1.55 (npm) and 3.05 (PyPI).
  - R stays the preregistered statistic but is no longer read as the tree effect.
- **Denominators of p.**
  - npm p is 6.0% for packages whose repository hosts no other top package and 38.6% for the rest; 86% of flagged
    npm latest releases are in multi-package repositories.
  - Among cloned packages with a release since 2024-06-01, p is 30.9% (npm) and 24.0% (PyPI). 2,918 npm and 2,019
    PyPI cloned packages have no release in the window and are unflagged by construction.
  - Excluding the five repositories with most flagged latest releases gives 18.8% and 16.0%.
- **G2 coverage** (`coverage.json`):
  - 112,839 releases use the date window and 22,747 (5.4%) have an empty range and are unflagged;
  - tree nodes match a window release 57.9% (npm; most of the rest are pre-window versions) and 85.9% (PyPI).
- **Flag rate rises with range size,** from 5.8% (1–5 commits) to 76% (over 2,000).
- **H2 extras.**
  - The 296,806 per-package pairs contain 89,401 distinct agent commits, and 80% of pairs share their partner's
    release.
  - Matching as the plan worded it (per repository, one row per commit, first release containing it) gives 89,700
    pairs and a ratio of 1.12 (1.05–1.19).
  - Unmatched agent commits have shorter latencies (median 4.8 days against 6.8).
  - **Deviation recorded here:** the reported matching was within (repository, package), not the plan's "same
    repository".
- **Hubs.** Leaving out any one of the ten most-included flagged PyPI nodes lowers P_w by at most 1.7 points (numpy,
  cffi, annotated-types and others), so exposure is diffuse. "Largely through a few hubs" is withdrawn.
- **Trend at repository level.** In September 2026, 28% (npm) and 33% (PyPI) of active repositories had at least one
  AI-signed commit. The top 10 repositories hold 18% of AI-signed commits since June 2024, and the top 50 hold 44%.
  Several agents' series are dominated by their own repository: aider 91%, junie 89%, openhands 56%.

**Precision audit, stratified, two blind labellers (G4, G7).** `code/audit_strata.py`,
`results/tables/precision_audit_strata.json`.
- 120 commits in 7 strata, oversampling the risky rules:
  - claude trailers without an Anthropic address;
  - Copilot trailers that are not suggestion trailers;
  - other agents' trailers;
  - identities.
- The matched text was re-derived from the clones (`git cat-file`, local objects only).
- Two fresh labellers, blind to stratum and rule, each with their own shuffled order, labelled all 120 as AI
  signatures: 100% agreement, no adjudication needed.
- Per-stratum 95% lower bounds are 0.69 (strata of 10) to 0.86 (strata of 25).
- `extract.py`'s `matched_line` now returns the trailer that matched. The stored lines in this run's
  `ai_matches.parquet` predate the fix; the audit does not use them.
- **Note.** An earlier draft of the audit script used `git show`, which lazily fetched objects from GitHub for some
  commits of these partial clones. It was stopped and replaced by `git cat-file`. Commit sets are unaffected.

**Not changed (review findings acknowledged as limits):**
- **Tag candidates.** Generic tags are tried before name-specific tags: 2,207 ambiguous matches and 17,466 suspect
  ones in multi-package repositories, with flag rates no higher than name-tag matches (review check).
- **About 3% easy false negatives** ("Assisted-by:" trailers and similar; review scan).
- **Review bots.** Review-suggestion bots are counted for Copilot and gemini-code-assist but not for CodeRabbit or
  Greptile.
- **Monorepo definition.** The definition counts repositories across both ecosystems, which affects 52 packages.

**Wording.**
- "agent-signed" → "AI-signed" where the count includes committed review suggestions;
- "Claude Code signs 68%" → "Claude-model signatures, mostly Claude Code";
- provenance: the plan and attribution rules preceded all data, and the npm top list finished downloading one second
  after the pipeline-code commit.
