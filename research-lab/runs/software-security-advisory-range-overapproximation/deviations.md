# Deviations from plan.md

## D1 — 2026-11-07 18:51 NZDT — range type, before any commit or release was fetched

(Committed in 0be72b1 at 18:51; the first draft stamped it 19:00.)

OSV encodes npm ranges as type SEMVER and PyPI ranges as type ECOSYSTEM. Plan section 1 says "an ECOSYSTEM range";
eligibility accepts either type. Nothing else changes. Eligibility counts: 258,101 records, 6,409 eligible (npm
3,244, PyPI 3,165); 800 sampled (seed 20261107).

## D2 — 2026-11-08 — implementation details (items 1–2 set in code committed at 18:54 on 11-07, before any presence result; written up on 11-08 with the report; item 3 after the run)

1. **Fix diffs** come from the public `github.com/{owner}/{repo}/commit/{sha}.diff` URL. This host has no GitHub
   token, and the REST API allows 60 unauthenticated requests per hour. 790 of 800 were fetched; 10 were not found.
2. **Release walk.** Plan section 1 says every release the declared range covers is downloaded. The classification
   (section 3) depends only on releases up to the first present one, so `presence.py` walks in publish order and
   stops at the first present release. It also checks the first release at or after `fixed` (secondary 3). A cap of
   400 downloads per advisory marks the rest undetermined. All of this was set in code committed before the run.
   H2 counts in-range releases from the registry lists, so it does not need downloads past the first present
   release.
3. **The cap was hit by 41 advisories** (found after the run). Their remaining releases count as undetermined, so
   an advisory whose first present release lies beyond 400 downloads is undetermined, not over-approximated.

## D3 — 2026-11-08 — after the G4 audit (post hoc)

The preregistered G4 audit failed its bar. A separate session judged 60 packets from the code alone, and agreed with
"over-approximated" in 10 of 30 cases (33%, against the 80% bar): 8 contradicted, 12 undecidable from the packet.
Agreement on "tight" was 24 of 30. By the plan's rule, H1 is reported as unreliable. The pipeline's verdicts
(H1 75%, H2 2.18) stay in the report beside the audit, and the headline verdicts are Inconclusive. Two post hoc
readings are added (`code/posthoc_strict.py`, `results/tables/posthoc_strict.json`):
1. **Strict over-approximation.** Release A has no file with the same name as any file the fix touches: 142 of
   308. That is 58% (52–64%) of strict plus tight. No audited strict case was contradicted, but 10 of 14 were
   undecidable. Under this reading H2's factor is 1.35 (1.27–1.45).
2. **Audit-calibrated range for H1.** The audited fractions (10 confirmed, 8 contradicted, 12 undecidable of 30)
   are applied to all 308 pipeline over-approximations: 25% to 55% of classified advisories.

## D4 — 2026-11-10 — fixes after the independent review (verdict: fix first; post hoc)

1. **One convention for the strict reading** (finding 1). The first draft paired strict H1 = 142/245 (non-strict and
   unknown dropped) with strict H2 = 1.35 (non-strict counted as not over-approximated), and wrote the H2 factor and
   the calibrated range into `posthoc_strict.json` by hand, from no committed code. Those hand-added fields are
   removed. `code/posthoc_d4.py` computes every number: with non-strict counted as not over-approximated, strict H1 is
   34.5% (30.1–39.3%, 142/411) and strict H2 1.35 (1.27–1.45); with them dropped, 58% and 1.81 (1.58–2.12), a
   sensitivity.
2. **The first audit, reported properly** (finding 2). 10/30 agree as measured. Of the 12 "cannot tell", 11 are packet
   artefacts (release A had no file in the packet in 10; the reason names an unprovided file); judgeable agreement is
   10/18 (56%, 34–75%). Tight: 24/25 judgeable. The 14 audited strict cases all had an empty release A in the packet,
   so "no audited strict case was contradicted" is withdrawn: the strict reading is unvalidated.
3. **The calibrated range with its uncertainty** (finding 4): 14–38% from the measured agreement, 25–57% on judgeable
   items, up to 64% at the most generous reading. Not in the title.
4. **G2 recheck** (finding 8; `code/recheck_d4.py`, `results/tables/release_recheck.csv`). The releases each
   classification rests on were re-downloaded (the absent releases before the first present one, until one has
   source files, and the first present release): stored s reproduces in 307/307 and 411/411. Match types are now
   counted: 153 of 307 over-approximations were judged absent by whole-release search (no file with the fix file's
   name), 48 mixed, 106 by path. Five had an empty-extraction absent release; one rested on empty extractions alone
   and is reclassified undetermined (H1 307/410, 74.9%). Restricted to path-matched deciding releases, the share is
   55% (48–62%, 106/193).
5. **H2 with an earlier corrected start** (finding 7): 1.67 (1.53–1.84) from the first release with s > 0.2 and 1.73
   (1.60–1.91) from just after the last absent release, against 2.18; 141 of 308 walks show partial presence before
   the cut, and 4,602 of the 19,237 removed releases were never shown absent. 2.18 is the upper end even under the
   pipeline's own calls.
6. **Pipeline-only results** (finding 6): the `introduced: 0` contrast, the gap and the upper-bound check rest on
   pipeline classes and are reported as unaudited; "drive the pattern" is dropped. The figure titles say "pipeline
   flags" (finding 9).
7. **Wording** (findings 10 and 15): 51% of the sample is classified (a majority); the classified half is selected by
   packaging (TypeScript-only npm fixes mostly end up undetermined). The audit judged whether the flaw is present,
   which is not the pipeline's construct (whether the fix's lines are present); D4's re-audit asks both.
8. **The presence run restarted** (finding 11): about 170 advisories were done between 19:30 and midnight on 11-07;
   the run was restarted around midnight and resumed from the existing files (the first segment's log was
   overwritten). The code did not change.
9. **fetch.py no longer queries git's credential store** (finding 12). A token is used only if passed in GITHUB_TOKEN.
   No GitHub token was present on this host, so all 790 diffs came from the public `.diff` URLs.
10. **G3 hand traces** (finding 13; `code/handtrace.py`): one seeded-random advisory per class, downloaded with plain
    urllib, path matching written by hand. Hand counts track the pipeline (tight: 32/32 against s 1.0; undetermined:
    0.65 against 0.61). The random over-approximated case (GHSA-hvfh-5mj3-5f3j) shows the empty-extraction problem:
    its first absent release (2.7.1) has no source files. A later absent release has files, so the class stands. The
    first, chosen traces are kept as `handtrace_v1_chosen.json`.
11. **G6** (G6 note): a ledger row records the novelty searches (OpenAlex keyword and semantic queries, 2026-11-10)
    and the closest work found, an unreleased MSR 2027 submission on affected-version inference.
12. **The audit rebuilt and rerun with two labellers** (findings 2, 3 and 5; G1 and G7; `code/audit_packets.py
    make_d4`/`score_d4`, `results/tables/g4_audit_d4.json`, `g4_audit_d4_labels.json`). The same 60 advisories in a
    new order (seed 20261110). Release B is the last in-range release for both groups, so its choice no longer encodes
    the class. Where no release file shares a fix file's name, the packet carries the release files containing the most
    signature lines (else the most shared identifiers), so the labeller sees what the pipeline searched. Packets carry
    no publish dates and no pipeline measurement (a first build said "N of M signature lines" and was rebuilt before
    any labelling). Two labellers in separate sessions, told to read only the packet directory, answered for A and B
    whether the code the fix changes is present, and for A whether the vulnerability is present in any form; an
    adjudicator in a third session settled the 3 packets they labelled differently. Results: kappa 0.97 (code) and
    0.92 (vulnerability); over-approximated confirmed 19/30 (63%, 46–78%), 19/28 judgeable (68%, 49–82%); tight
    29/30. Below the 80% bar, so H1 stays unreliable by the plan's rule. In 6 of the 30 the fixed code is present in
    A; in 14 the vulnerability is present in A in some form (8 with the fixed code absent). Audit-calibrated share
    (post hoc): 47% (34–59%) for the fixed code, 33% (20–46%) for the vulnerability. Leak probe: whether A has a
    same-name file still predicts the class 68% of the time (legitimate evidence of absence); A having fewer packet
    files than B, 62%. Blindness was enforced by instruction, not by the file system.
13. **posthoc_strict.json** was regenerated by `code/posthoc_strict.py` without the hand-added fields; the hand-edited
    version is not kept in the repository.

