# Do npm and PyPI security advisories declare affected ranges that start too early? A code-presence test flags three in four, but blind audits confirm only part of its flags, so the true share is not pinned down

*800 GitHub-reviewed npm and PyPI advisories with a fix commit (a seeded random sample of the 6,409 eligible) were
checked release by release. The test asked whether the code the fix removes or guards existed in each release inside
the declared affected range, from the earliest onward. The preregistered blind audit judged 60 of them from the code
alone; after the independent review, the audit was rebuilt and rerun with two blind labellers (D4, post hoc). The plan
was committed before any advisory, commit or package file was downloaded.*

**Verdict: H1 Inconclusive; H2 Inconclusive.** The pipeline's counts would give Supported for both. Neither audit
reaches the plan's 80% agreement on "over-approximated", so by the plan's rule the pipeline's share is reported as
unreliable.

- **H1 (at least 25% of advisories declare a lower bound that starts before the vulnerable code existed):
  Inconclusive.**
  - **Pipeline:** 308 of the 411 classified advisories are over-approximated (75%; Wilson 70.5% to 78.9%), and 103
    are tight. A recheck of the releases each call rests on reclassifies one, whose only absent releases had no
    source files (307 of 410). Counting every undetermined advisory as not over-approximated gives 38.5% of all 800.
  - **The preregistered audit** (one session, 30 over-approximated and 30 tight packets): it confirmed 10 of the 30
    over-approximations, contradicted 8 and could not decide 12. Eleven of those 12 were gaps in the packets, not in
    the pipeline: release A's relevant file had not been included. On the 18 judgeable cases it confirmed 10 (56%;
    34% to 75%). It confirmed 24 of 25 judgeable tight cases.
  - **The rebuilt audit** (post hoc, D4): the same 60 advisories, with packets that show what the pipeline searched
    and choose the second release the same way for both groups. Two labellers worked blind in separate sessions and
    agreed with each other on 59 of 60 releases A (kappa 0.97); an adjudicator settled 3 packets. They confirmed 19 of
    the 30 over-approximations (63%; 46% to 78%), or 19 of 28 judgeable (68%; 49% to 82%), and 29 of 30 tight cases.
    In 6 of the 30 the fixed code is already present in release A; in 3 it is missing from release B too, so the
    packaged releases never show the code the fix changes.
  - **Code versus vulnerability.** In 14 of the 30 over-approximations the labellers found the vulnerability itself
    in release A in some other form. In 8 of those the code the fix changes is absent, so the range is too early
    for the fixed code but not for the flaw.
  - **Audit-calibrated share** (post hoc): applying the rebuilt audit's agreement to all 308 gives 47% of classified
    advisories (34% to 59%) for the fixed code, and 33% (20% to 46%) if a range only counts as too early when the
    vulnerability itself was absent. Both assume that the 30 audited cases represent all 308 and that the undetermined
    half of the sample behaves like the classified half.
  - **Strict reading** (post hoc): the module the fix touches is missing altogether from release A (no file of the
    same name). That holds for 142 of the 411 (34.5%; 30.1% to 39.3%). It is unvalidated: it cannot see renamed or
    merged modules, and the first audit could not test it.
  - 49% of the sample is undetermined: no usable signature (79), no diff (10), or no release in which the signature
    matches (300). That is above the plan's 40% warning line. The classified half is a majority, but it is selected
    by packaging: npm fixes that touch only TypeScript mostly end up undetermined.
- **H2 (correcting the lower bounds removes at least a third of affected version pairs, a factor of 1.5):
  Inconclusive.**
  - **Pipeline:** 35,590 declared (version, advisory) pairs fall to 16,353, a factor of **2.18** (1.93 to 2.50).
    That is the upper end even under the pipeline's own calls. The corrected range starts at the first release that is
    at least 80% present, and 141 of the 308 walks show partial presence earlier. Starting it at the first partial
    presence gives 1.67 (1.53 to 1.84), and just after the last absent release 1.73 (1.60 to 1.91).
  - **Strict reading:** 1.35 (1.27 to 1.45), below the bar, on the same convention as the strict 34.5%. Dropping the
    non-strict cases from the denominator instead gives 1.81 (1.58 to 2.12).
  - **npm installs** (pipeline classes): 36% of current weekly downloads of versions inside declared ranges fall
    outside the corrected ranges.
- **Pipeline-only patterns (not audited).**
  - 81% of sampled advisories declare every release affected (`introduced: 0`). Of those classified, the pipeline
    flags 83% (280 of 338), against 38% (28 of 73) of explicit lower bounds. This is confounded with history length:
    those walks start at a package's first releases (58 of the 308 releases A are 0.0.0 or 0.0.1), where older forms
    of the code are most likely.
  - Where the pipeline flags a lower bound, the gap is a median of 42 releases, or 3.1 years.
  - **Upper bounds:** in 35 of 693 checked advisories (5%), the fix's deleted lines are still found in the first
    release at or after the declared fixed version. This was not audited.

## In plain terms

When a security flaw is found in an open-source package, an advisory records which versions are affected. Tools such
as Dependabot then warn everyone who uses those versions. If the advisory says "every version before the fix" when the
flaw only arrived recently, users of old, safe versions get warnings they do not need.

We took 800 advisories for JavaScript (npm) and Python (PyPI) packages and checked, release by release, whether the
code that the fix changed was actually there. A simple automatic check said three in four advisories start their
range too early.

We then had the check's calls judged blind, from the code alone. The first audit could confirm only a third of the
"too early" calls, largely because it had been shown the wrong files. A rebuilt audit, with two independent
reviewers who agreed with each other almost every time, confirmed about two in three. In about half of the rest the
code was already there in the earliest release, written slightly differently, and the check had missed it. That is
better, but short of the four in five the study required before trusting the check.

So a rough estimate made after the fact puts the share of advisories that start too early at around a third to a
half of those we could check, with wide uncertainty; the study cannot say more precisely. The answer also depends on what counts: in about a third of the confirmed cases
the flaw already existed in an older form even though the fixed code did not. A check that follows code through rewrites,
and a larger audit, are needed before the unnecessary warnings can be counted.

## What was asked

The lead (`software-security-advisory-range-overapproximation`) asked whether published advisory ranges for npm and
PyPI over-approximate the affected versions, and how many dependency alerts that inflates. It predicted at least 25%
over-approximated lower bounds and a 1.5-fold inflation.
- **Affected-version identification has been studied as a tool problem** for C/C++ (no tool above 45% accuracy; Chen
  et al. 2025) and Java (VERJava, Sun et al. 2022). A 2026 submission studies how the functions named in CVE
  descriptions differ from those a fix changes, and how that shifts inferred ranges; its data are not yet released.
- **An OSV-derived dataset for evaluating detection tools takes the published ranges as ground truth** (Mandl et al.
  2026).
- No measurement of the published npm and PyPI ranges against code presence was found (OpenAlex searches,
  2026-11-07 and 2026-11-10; ledger S6).

## How it was done

- **Advisories** (`code/eligible.py`): the OSV export for npm and PyPI (2026-11-07). GHSA records, not withdrawn, one
  affected package, a range with `introduced` and `fixed` events (OSV encodes npm ranges as SEMVER; D1), and a fix
  commit. 6,409 are eligible; 400 npm and 400 PyPI were sampled.
- **Fix diffs** from github.com's public diff URLs (790 of 800; D2) and **release lists** with publish dates from the
  npm registry and PyPI.
- **Signatures** (`code/presence.py`, unit-tested): the normalised lines the fix deletes in non-test source files.
  For fixes that only add a check, the signature is the context lines before the added code, and the added lines are
  a patch signature.
- **Presence:** the share of signature lines found in the release file with the same path, or anywhere in the release
  when no file shares the name (the plan's fallback). "Present" needs at least 80%, "absent" at most 20%, and
  anything between is undetermined. The recheck counts the fallback: 217 of the 411 deciding judgements used it,
  wholly (169) or for some fix files (48) (`results/tables/coverage.json`).
- **Classification:** releases inside the declared range are walked in publish order, stopping at the first present
  one.
  - **Tight:** the earliest in-range release is present.
  - **Over-approximated:** an absent release comes before the first present one.
  - **Undetermined:** otherwise.
  - A cap of 400 downloads per advisory was reached by 41 advisories (D2).
- **Preregistered G4 audit** (`code/audit_packets.py make`/`score`): a stratified sample of 30 over-approximated and
  30 tight advisories. Each packet held the fix diff and the same-name source files of two in-range releases (A, the
  earliest; B, the first present release or a mid-range one). One separate session labelled each release.
- **Rebuilt audit** (`make_d4`/`score_d4`, D4, post hoc): the same 60 advisories in a new order. Release B is the last
  in-range release for both groups. Where no release file shares a fix file's name, the packet carries the files the
  pipeline's search would hit. Packets carry no dates and nothing of the pipeline's measurement. Two labellers in
  separate sessions, with access only to the packets, answered for A and B whether the code the fix changes is
  present, and for A whether the vulnerability is present in any form; an adjudicator settled their 3 disagreements.

## Results (`results/figures/F1_share.png`, `F2_gap.png`)

![Pipeline flags](results/figures/F1_share.png)

| reading | over-approximated | classified | share (95%) | H2 factor (95%) |
|---|---|---|---|---|
| pipeline (preregistered) | 308 | 411 | 75% (70.5–78.9) | 2.18 (1.93–2.50) |
| pipeline, corrected start at first partial presence (post hoc) | | | | 1.67 (1.53–1.84) |
| pipeline, thresholds 0.6 / 0.4 | 360 | 487 | 74% (69.9–77.6) | |
| pipeline, path-matched deciding releases only (post hoc) | 106 | 193 | 55% (47.9–61.8) | |
| strict: module missing in release A (post hoc) | 142 | 411 | 34.5% (30.1–39.3) | 1.35 (1.27–1.45) |
| calibrated by the rebuilt audit, fixed code (post hoc) | | 411 | 47% (34–59) | |
| calibrated by the rebuilt audit, vulnerability (post hoc) | | 411 | 33% (20–46) | |

| audit | pipeline over-approximated: confirmed / judgeable / all | tight: confirmed / judgeable |
|---|---|---|
| preregistered (one labeller; packets with gaps) | 10 / 18 / 30 | 24 / 25 |
| rebuilt (two labellers, kappa 0.97, adjudicated; post hoc) | 19 / 28 / 30 | 29 / 30 |

By ecosystem (pipeline): PyPI 177 of 220 (80%), npm 131 of 191 (69%).

![Gap](results/figures/F2_gap.png)

## What this does and does not show

- **Line-signature presence is not reliable enough for "absent".** It recognises present code well (29 of 30 tight
  cases confirmed in the rebuilt audit). But in the rebuilt audit a fifth of its over-approximations had the fixed
  code already in release A, and a further sixth could not be confirmed (the fixed code missing from release B too,
  or undecidable). Measuring
  range accuracy at scale needs a matcher that follows code through rewrites and moves.
- **Two constructs give different answers.** "The code the fix changes was not there" and "the vulnerability was not
  there" disagree in about a quarter of the audited over-approximations. The plan's question is the first; an
  advisory reader cares about the second.
- **The alert inflation is not established.** Even under the pipeline's own calls the factor is 1.7 to 2.2 depending
  on where the corrected range starts, and the calls themselves are only partly confirmed.
- **The calibrated shares are rough.** They rest on 30 audited cases and assume the undetermined half behaves like
  the classified half, which packaging makes doubtful.
- **Not shown:**
  - **Exploitability.** Presence of the code is not proof that a release was exploitable.
  - **Dependency-graph alert counts** (deps.dev). Version pairs and npm downloads stand in for them.
  - **Advisories without a fix commit**, which are 2,850 of the 9,259 GHSA records with a range in these ecosystems.

## Process and deviations

- **Preregistration:** `plan.md`, committed before any data. Eligibility and the sample, then the fetch, presence and
  classification code, were committed before any presence result. The presence run was restarted once around
  midnight on 7 November and resumed from its existing files (D4).
- **Deviations** (`deviations.md`): D1, the SEMVER range type (before any commit or release was fetched); D2, public
  diff URLs, the release walk and the cap; D3, after the first audit, the strict reading (post hoc); D4, after the
  independent review: one convention for the strict reading with every number from committed code, the first audit's
  packet artefacts, the calibrated range's uncertainty, the G2 recheck, the H2 start sensitivity, the rebuilt
  two-labeller audit, random hand traces, and the removal of an implicit credential lookup from `fetch.py`.
- **Quality gates:**
  - G1: the plan had no leakage-audit section. The first audit's packets encoded the pipeline's class (second release
    chosen differently per group; about 80% predictable, per the review). The rebuilt packets choose it identically and carry no
    pipeline measurement. Whether release A has a same-name file still predicts the class 68% of the time, but that
    is evidence the labeller legitimately needs.
  - G2: `results/tables/coverage.json`, now with the fallback counts.
  - G3: `results/plausibility.md`.
  - G4: both audits are reported and both fail the 80% bar; the first audit's "cannot tell" cases are classed.
  - G5: `review/overclaim_check.md`.
  - G6: `results/attribution_ledger.csv`.
  - G7: the first audit had one labeller. The rebuilt audit has two blind labellers (kappa 0.97 for the fixed code,
    0.92 for the vulnerability) and an adjudicator. Blindness was enforced by instruction, not by the file system.
- **Independent review:** fix first; the fixes are in D4.

## Reproducing it

1. `code/eligible.py` (OSV export in `data/raw/`).
2. `code/fetch.py versions`, then `code/fetch.py commits`.
3. `code/presence.py run`.
4. `code/classify.py run`, `code/classify.py downloads`, `code/classify.py run`.
5. `code/audit_packets.py make` (key outside the run directory), labelling in a separate session, `code/audit_packets.py score`.
6. `code/posthoc_strict.py KEY`, `code/recheck_d4.py run`, `code/audit_packets.py make_d4` and `score_d4` (two
   labellers and an adjudicator in separate sessions), `code/posthoc_d4.py KEY`, `code/handtrace.py`, `code/figures.py`.
