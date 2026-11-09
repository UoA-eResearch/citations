# Review: software-security-advisory-range-overapproximation

Reviewer: Fable 5.1 (fresh independent reviewer), 2026-11-09.

## Verdict: **fix first**

The headline verdicts (H1 Inconclusive, H2 Inconclusive) follow from the preregistered G4 rule, and they survive
everything I checked. The pipeline numbers reproduce exactly from the stored release walks. The plan and the
deciding code were committed before any data or presence result.

The post hoc layer the report leans on is not sound:
- The "strict" H1 share (58%) and the strict H2 factor (1.35) use incompatible denominators. The H2 factor and the
  "audit-calibrated" 25–55% range come from code that is not committed.
- The audit's "a third" counts packet-construction artefacts as failures.
- The strict reading's apparent audit support is an artefact of how the packets were built.
- The title states a post hoc range, without its sampling uncertainty, as "the defensible share".
- G7 is missing, and G1 and G4 are partly hollow.

All of this is fixable without new data collection, and none of it changes the headline verdicts. Fix it before
publication.

Check scripts and outputs are in `reviewer_checks/` (each `cN_*.py` writes `cN_*.txt`; run as
`venv/bin/python -I reviewer_checks/cN_*.py RUN_DIR`).

## What I verified and found sound

- **Headline numbers reproduce exactly** (`c1_rederive.txt`). Re-classifying all 800 stored walks independently
  gives 0 mismatches with `classes.csv`. The following all match `primary.json`:
  - H1 308/411 = 0.749 (Wilson 0.705–0.789); 38.5% of 800;
  - H2 35,590/16,353 = 2.176 (1.931–2.497);
  - by ecosystem 177/220 and 131/191; `introduced: 0` 280/338 against explicit 28/73;
  - 81.4% of the sample is `introduced: 0`;
  - gap median 42.5 releases and 3.06 years; upper bound 35/693; cap hit 41 (all 41 undetermined).
- **Order of work.**
  - Plan commit 0d6dda5 at 18:48:09; `data/raw` written at 18:49:34.
  - eligible.py and the sample at 18:51; fetch.py and presence.py at 18:54; classify.py at 18:55.
  - First presence file at 19:30 on 11-07.
  - None of these code files has changed since its commit (`git diff` clean; no later commit touches them).
- **Short signatures are not driving the result** (`c9_sigsize.txt`). The over-approximated share is flat in
  signature size: 0.74 for 1 line, 0.75 for 2, 0.70 for 3–5, 0.76 for 6–10 and 0.80 for more than 10.
- **The publish-order walk is not mis-ordering branches** (`c7_order.txt`). No PyPI over-approximated case has an
  "absent" release that precedes the first present one in publish order but carries a higher version (0/177).
- **The lower-bound choice is safe in this sample** (`c8_eligibility.txt`). The string sort in presence.py is
  latent: it never picks a different lower bound here (0 cases).
- **G5 and G6 pass mechanically** (`g5_verify.txt`, `g6_check.txt`). Three spot checks against OpenAlex abstracts
  hold (`g6_spotcheck.txt`):
  - Chen et al. 2025: "no tool exceeds 45.0% accuracy", C/C++;
  - VERJava: Sun et al. 2022, Java;
  - Mandl et al. 2026: an OSV-derived ground truth.

## Findings

**1. Major: the strict reading uses two incompatible conventions, and two of its numbers come from uncommitted code.**
- **The conventions differ.**
  - Strict H1 = 142/(142+103) = 58%. This drops the 161 non-strict over-approximations and the 5 unknowns from
    the denominator.
  - Strict H2 = 1.345 (1.266–1.45) is reproduced only by keeping all 411 and treating non-strict cases as tight
    (`c3_strict_h2.txt`, V1).
- **Either convention applied consistently gives a different picture.**
  - Under the H2 convention, strict H1 is 142/411 = **34.5% (30.1–39.3%)**.
  - Under the H1 convention, strict H2 is **1.81 (1.58–2.12)**, which would clear the 1.5 bar.
  - The report pairs the convention that gives the higher H1 with the one that gives the lower H2.
- **Two numbers have no committed code.** `code/posthoc_strict.py` does not compute `H2_strict_factor`,
  `H2_strict_ci` or `H1_audit_calibrated_range`, yet all three appear in `results/tables/posthoc_strict.json`
  (grep finds them in no code file). The JSON was either hand-edited or written by code that was never committed.
- **Fix.**
  - Commit the code that produces every number in `posthoc_strict.json`.
  - Pick one convention and report both quantities under it. Treating non-strict as "not over-approximated" is the
    natural reading: 34.5% and 1.35.
  - Show the other convention as a sensitivity.

**2. Major: "right only a third of the time" counts packet artefacts as pipeline failures (G4 hollow).**
- **Most undecidable cases are packet gaps.** Of the 12 "cannot tell" over-approximations, 11 cite a file "not
  provided" or "unprovided", and in 10 the packet gave release A no file at all (`c4_audit.txt`).
- **Why.** `audit_packets.files_for` copies only files that suffix-match the diff paths. The pipeline, in contrast,
  searched the whole release when no path matched (the "any source file" fallback). The auditor therefore often did
  not see what the pipeline judged.
- **What G4 requires.** METHODS G4 requires classing each error as artefact, label noise or genuine, and reporting
  the metric on the judgeable denominator. That was not done.
- **Judgeable agreement.**
  - Over-approximated: **10/18 = 56% (Wilson 34–75%)**.
  - Tight: **24/25 = 96%**.
- The bar still fails, so H1 stays "unreliable" and Inconclusive. But "a third" overstates the error rate.
- **Fix.**
  - Report 10/30 as measured and 10/18 on judgeable items, with the 11 artefacts named.
  - Rebuild the packets for the 12 undecidable cases with the files the pipeline actually searched, and re-label
    them in two fresh blind sessions (see finding 5).

**3. Major: the strict reading's audit support is an artefact of how the packets were built.**
- **By construction the auditor sees nothing in A.** "Strict" means release A has no file with the same name as a
  fix file, and packets include only same-name files. So every audited strict case shows the auditor an empty A:
  all 14 had zero matched files.
- **The outcome is therefore predetermined.** The auditor either inferred "absent" from the file list (4) or could
  not tell (10).
- **The reasons show module moves, the very case "strict" is meant to exclude.**
  - a22: "A single flask_cors.py not provided". The code lived in a single module that was later split.
  - a47: "proxy header path in unprovided proxy/server.py".
- "No audited strict case was contradicted" (D3, report) is therefore not evidence for the strict reading.
- **Fix.**
  - Drop the claim.
  - Describe the strict reading as unvalidated, since it cannot detect renamed or merged modules.
  - Or audit it with packets that include the files where the deleted lines' identifiers occur.

**4. Major: the "audit-calibrated" 25–55% ignores n=30 and is put in the title as "the defensible share".**
- **The arithmetic reproduces:** 308×10/30/411 = 0.250 and 308×22/30/411 = 0.550.
- **It treats the 30-case fractions as exact.** With Wilson limits on 10/30 and 22/30, the range is **14% to 64%**.
- **On judgeable items alone** it is 42% (25–57%) (`c3_strict_h2.txt`).
- **Two further gaps.**
  - It ignores errors on the tight side (1 of 30 tight cases was judged absent in A).
  - It assumes the undetermined half of the sample behaves like the classified half.
- **The title breaks the G5 rule.** "The defensible share is a quarter to a half" states a post hoc number as
  settled and does not label it post hoc, which G5 requires for headlines.
- **Fix.**
  - Retitle, for example: "…a code-presence test flags three in four, but a blind audit could confirm only about
    half of its judgeable calls; the true share is not pinned down".
  - Report the calibrated range with its uncertainty and label it post hoc.

**5. Major: the G4 audit's blindness was not enforced, the G1 leakage audit is missing, and G7 is missing and not
declared.**
- **The key was not secret.**
  - The "secret" key can be rebuilt from committed `classes.csv` and the seed in `audit_packets.py`. My rebuild
    matches all 26 disagreement IDs in `g4_audit.json`.
  - `results/tables/classes.csv` and `data/presence/` (per-release labels) sat in the same run directory as the
    packets.
  - Nothing shows the labelling session lacked file access. "The pipeline's labels stayed outside its view" cannot
    be verified.
- **The packet structure leaks the class.**
  - B is the first present release for over-approximated cases but a mid-range release for tight ones.
  - The median A→B gap is 2.48 years against 0.39.
  - A has fewer matched files than B in 16/30 against 1/30.
  - A two-feature rule predicts the pipeline class with **80%** accuracy, and the A–B gap alone with 75%
    (`c4_audit.txt`).
- **Missing gates.**
  - plan.md has no G1 "Leakage audit" section: no list of label-correlated fields, no shuffling, no order-swap probe.
  - G7 (two independent blind labellers, kappa, adjudication) was not run, and the report's gate list silently
    omits it.
  - The 60 labels were written within about 14 minutes of the packets (10:28 to 10:42).
- **The leak cuts towards agreement.** So the failure to reach 80% is, if anything, conservative, and the
  Inconclusive verdict survives.
- **Fix.**
  - Declare G1 and G7 as missing in the report.
  - Re-run the audit with two fresh labellers in a sandbox without the run directory.
  - Choose B the same way for both strata, for example a fixed-quantile in-range release.
  - Report kappa.

**6. Moderate: "What holds regardless of the audit" does not hold regardless of it.**
- **Every number in that block rests on pipeline classes:**
  - the `introduced: 0` contrast (83% against 38%);
  - the gap (42 releases, 3.1 years);
  - the 5% upper-bound result.
- **The `introduced: 0` contrast is confounded with walk length.**
  - Those walks start at a package's first releases: 58 of the 308 release A versions are 0.0.0 or 0.0.1, and 28
    are pre-releases (`c7_order.txt`).
  - Long histories accumulate exactly the "same flaw, different code" drift that the audit found the matcher
    mistakes for absence.
- **The upper-bound check is unaudited.** "Present at the fixed version" can arise when a deleted line still occurs
  elsewhere in the file, or through the any-file fallback.
- **Fix.**
  - Retitle the block "Pipeline-only patterns (not audited)".
  - Drop "drive the pattern".
  - Audit a sample of the 35 upper-bound cases before citing 5%.

**7. Moderate: the pipeline H2 factor counts unexamined releases as unaffected.**
- **The cut sits at the first release that is at least 80% present.** That removes every release before it,
  including releases never shown absent: 4,630 of 19,237 removed releases (24%) were undetermined.
- **There is earlier partial evidence.** 141/308 walks show partial presence (0.2 < s < 0.8) before the cut
  (`c2_walk_structure.txt`).
- **Moving the cut changes the factor** (`c10_h2_partial.txt`):

| corrected range starts at | factor (95% CI) |
|---|---|
| first ≥80% present release (as reported) | 2.18 |
| first release with s > 0.2 | **1.67 (1.53–1.84)** |
| just after the last absent release | **1.73 (1.60–1.91)** |

- **Fix.** Report this sensitivity beside 2.18, and call 2.18 the upper end even under the pipeline's own calls.

**8. Moderate: two fallbacks in the presence step change values silently (G2).**
- **(a) The "any source file" fallback is never counted.** `coverage.json` reports 0 fallbacks, and the presence
  JSON does not record per release whether the path matched or the fallback was used. The plan names the fallback,
  but G2 still requires it to be counted.
- **(b) An empty artefact counts as absent.** An artefact with zero source files yields s = 0, so "absent". The plan
  requires absent to mean "source extracted successfully".
  - Packet a56: release A is 0.0.0, its source listing is empty, and the case is counted over-approximated.
- **Fix.**
  - Record the match type and the source-file count per release.
  - Treat empty extractions as undetermined, recompute, and add both counts to `coverage.json`.

**9. Moderate: the figure titles state the claim the verdict withdraws.**
- F1: "Most advisory lower bounds start before the vulnerable code existed".
- F2: "Over-approximated lower bounds sit a median 3.1 years before the code appeared".
- Both are embedded in report.md.
- **Fix.** Retitle both as unaudited pipeline output, for example "Pipeline flags (audit could not confirm)".

**10. Minor: "rests on a minority" is wrong, and the classified subset is selected.**
- 411/800 = 51% were classified, which is a majority. The 40% warning applies; the wording does not.
- **Who gets classified is not random.** npm fixes that touch only TypeScript are 64% of undetermined npm cases but
  34% of over-approximated ones (`c5_paths.txt`): transpiled packages fall out of the classified set.
- **Fix.** Correct the wording, and state that the classified half is selected by packaging.

**11. Minor: an undisclosed restart of the presence run.**
- 170 presence files were written between 19:30 on 11-07 and midnight.
- `logs/presence.log` starts at about 00:00 and completes the first 100 advisories in 15 s (99/100 already existed;
  `c7_order.txt`).
- The first segment's log was overwritten.
- The code is unchanged in git, so the restart is probably benign.
- **Fix.** Disclose the restart in D2 and keep both logs in future.

**12. Minor: fetch.py silently queries the host's credential store.**
- `fetch.py` runs `git credential fill` for github.com and would send any token it finds to api.github.com.
- This sits awkwardly with D2's "this host has no GitHub token".
- Study code should not query credential stores implicitly.
- **Fix.** Remove the call or make it an explicit opt-in, and state in D2 which route the 790 diffs came by.

**13. Minor: the G3 traces are hand-picked and not independent of the path matching.**
- The three units are fixed IDs. METHODS asks for random units.
- `handtrace.py` reuses `audit_packets.files_for` and `presence.match_file`, so it is not independent of the path
  matching.
- The invariants are stated in plausibility.md, but no code asserts them. I confirmed 800 = 411 + 300 + 79 + 10,
  and corrected pairs ≤ declared pairs holds by construction.
- **Fix.** Trace three seeded-random units, with path matching done by hand.

**14. Minor: the G5 table is hollow.**
- All 44 sentences are labelled "Supported", including the post hoc title and "regardless of the audit".
- See the re-labels below.

**15. Minor: deviation records and wording.**
- **D1 timestamp.** D1's timestamp (19:00 NZDT) is later than its commit (0be72b1, 18:51).
- **D2 timing claim.** D2 says it was written "before any presence result", but it first appears in the report
  commit (0efa9c8). Its substance (public diff URLs, the walk and the cap) is in code committed at 18:54, so this is
  a provenance-wording issue only.
- **"Renamed, rewritten or moved."** The report says the contradicted cases are "renamed, rewritten or moved", but
  the auditor's reasons describe the flaw being present ("both default download base http://", "both use unbounded
  ambiguous digit regexes"). They do not show renames or moves.
- **Construct shift.** The audit also judged a different construct: whether the flaw is present, against whether the
  fix's lines are present. Say so.

## Answers to the brief's specific questions

1. **Eligibility and sampling.**
   - GHSA-only and withdrawn-exclusion are implemented as planned (coverage drops 414 npm and 251 PyPI withdrawn).
   - SEMVER/ECOSYSTEM is handled correctly (D1).
   - The fix commit is the package-repo match, else the first listed. The picked commit is from another repository
     in 10% of over-approximated, 16% of tight and 6% of undetermined cases, and multi-commit fixes are 7–15%
     (`c8_eligibility.txt`).
   - `pull/N/commits/sha` URLs can be partial fixes; this is acknowledged in the limits.
   - The lower bound is chosen by string sort: latent, no effect.
2. **Signatures and normalisation.**
   - Deleted lines capture the removed code; the add-only rule uses 3 context lines.
   - The test-file exclusion is a substring filter (`test`, `doc`, …), so a path like `docker/` or `latest.py` is
     dropped too. This is minor.
   - Signature size does not drive the result (c9).
   - The real failure is semantic drift of the vulnerable code over long histories, which the audit exposes.
3. **Presence and path matching.**
   - The longest-suffix match is sound. The any-file fallback and empty-artefact absences are silent (finding 8).
   - Transpiled npm packages mostly end up undetermined, not falsely over-approximated: TypeScript-only fixes have a
     73% over-approximated rate among classified, against 67% for JS.
   - A packaging change (starting to ship `src/*.ts`) could still create false absences. Record the match type to
     test this.
4. **Classification and walk.**
   - Publish order is implemented as stated, and it causes no branch interleaving (c7).
   - Pre-releases are included. 28 over-approximated cases have a pre-release as release A, and 58 have 0.0.0 or
     0.0.1 as release A.
   - All 41 cap hits are undetermined, consistent with D2.
   - The corrected start ignores partial evidence (finding 7).
5. **The G4 audit.**
   - Packet position leaks the class: B is chosen differently per stratum (80% predictable).
   - The key is reconstructible.
   - Scoring is as coded. "Cannot tell" is mostly a packet artefact; judgeable agreement is 56%.
   - "Inconclusive" does follow: even 56% (upper limit 75%) fails 80%.
   - The 25–55% range is not a fair use of 30 cases without its uncertainty (14–64%).
6. **Strict reading and H2 1.35.**
   - 1.35 is computed correctly only under "non-strict = tight", which contradicts the 58% denominator.
   - The code that computes it is uncommitted.
   - It is labelled post hoc in D3 and in the table, but not in the title.
   - Its audit support is an artefact (findings 1 and 3).
7. **Report.**
   - All pipeline numbers match the tables.
   - The issues are the title (finding 4), the "minority" wording, the "regardless of the audit" block, the figure
     titles and "a third" (findings 2, 6, 9 and 10).

## Gate checks (G1–G7)

| gate | status |
|---|---|
| G1 | **Missing.** No leakage-audit section; the audit leaks (finding 5). |
| G2 | Present, but the fallbacks are uncounted (finding 8). |
| G3 | Present, with weaknesses (finding 13). |
| G4 | Run and honestly reported as failed, but the error classification and judgeable denominator are missing (finding 2). |
| G5 | Passes mechanically but is hollow (finding 14; re-labels below). |
| G6 | Passes; spot checks hold. The novelty claim ("no measurement … was found") has no ledger row: add one with the searches made. |
| G7 | **Missing** and undeclared (finding 5). |

## G5 re-labels (row numbers from review/overclaim_check.md)

| row | sentence | re-label | reason |
|---|---|---|---|
| 1 | title | **Overstated** | Post hoc range, no uncertainty, not labelled (finding 4). |
| 7 | "right only a third of the time" | **Partially supported** | 56% on judgeable items (finding 2). |
| 10 | "38.5% of all 800" | **Partially supported** | Presented as a robust lower bound but uses pipeline classes. |
| 11 | "without the labels" | **Partially supported** | Blindness not enforced; packet leak (finding 5). |
| 15–16 | "renamed, rewritten or moved" | **Partially supported** | Finding 15. |
| 17 | audit-calibrated 25–55% | **Overstated** | Finding 4. |
| 18 | "the bar is the bottom of that range" | **Overstated** | It sits inside the uncertainty-aware range. |
| 20 | strict 58% | **Overstated** | Denominator inconsistent with H2 strict (finding 1). |
| 21 | "contradicted none of the 14 strict" | **Overstated** | Artefact by construction (finding 3). |
| 23 | "rests on a minority" | **Overstated** | Wrong: 51% (finding 10). |
| 26 | strict H2 1.35 "below the bar" | **Partially supported** | Convention-dependent; 1.81 under the H1 convention. |
| 29–33 | "What holds regardless of the audit" block | **Overstated** | Pipeline-only (finding 6). |
| 40 | plain terms, "only a third" | **Partially supported** | Finding 2. |
| 42 | "true share is roughly a quarter to a half" | **Overstated** | Finding 4. |
| 43 | "those are the ones most often too broad" | **Partially supported** | Pipeline-only, confounded (finding 6). |

## What to do

1. Commit code that produces every number in `posthoc_strict.json`. Use one convention for the strict H1 and H2;
   report 34.5% and 1.35, or state both conventions.
2. Report G4 properly: 10/30 as measured, 10/18 judgeable with the artefacts listed, tight 24/25, and the strict
   cases' audit as uninformative.
3. Retitle the report and rewrite "In plain terms" without "a quarter to a half". Give the calibrated range with its
   uncertainty (about 14–64%) and label it post hoc.
4. Declare G1 and G7 missing. Ideally, re-audit with rebuilt packets (all searched files, B chosen identically
   across strata) and two blind labellers without run-directory access.
5. Move the `introduced: 0`, gap and upper-bound results under "pipeline-only, unaudited". Retitle F1 and F2.
6. Add the H2 corrected-start sensitivity (1.67–1.73).
7. Record the match type and source-file count per release. Treat empty extractions as undetermined, and count both
   in `coverage.json`.
8. Fix the small items:
   - "minority";
   - disclose the presence-run restart;
   - the D1 and D2 provenance wording;
   - remove `git credential fill` or make it opt-in;
   - make the G3 traces random;
   - add a G6 row for the novelty claim;
   - redo the G5 table with the re-labels above.

## In plain terms

The study asked whether npm and PyPI security advisories claim that older versions are affected when the flawed
code was not yet there. Its automatic check said this is true for three in four advisories, but a blind spot check
could not confirm most of those calls. So the study rightly concludes it cannot say whether the true share is above
the 25% target.

The numbers it offers instead need fixing:
- **The audit packets.** Many cases the auditor "could not decide" were left out of the packets by mistake, which
  makes the check look worse than it was: about half of the judgeable cases were confirmed, not a third.
- **The "strict" figures.** They mix two ways of counting, and part of them was computed by code that was never
  saved.
- **The headline.** "A quarter to a half" leaves out how little 30 audited cases can tell you; the honest range is
  wider, roughly 15% to 65%.
- **The "regardless of the audit" patterns.** Several patterns presented as holding "regardless of the audit" rest
  on the same unreliable check.

The core conclusion, that this method cannot settle the question, stands. The write-up needs correcting before it
is published.

## Confirmation pass

Reviewer: Fable 5.1, 2026-11-10.

Scope: the nine items of `review/confirmation_prompt.md` against findings 1–15, D4 (commit 86b244f), the new and
changed code, the tables, report.md/report.html, the G5 table and the ledger. Everything was recomputed from the
committed tables and the stored walks (`data/presence`, `data/recheck`, `data/audit`), not taken from D4. Check scripts
and outputs are in `reviewer_checks/confirm_*` (run as `venv/bin/python -I confirm_N_*.py RUN_DIR`):

| check | what it recomputes |
|---|---|
| `confirm_1_strict` | strict H1/H2 under both conventions from `classes.csv` + `classes_strict.csv`; fields of `posthoc_strict.json` |
| `confirm_2_audit_v1` | first audit re-scored from the seed-rebuilt key, artefact classing, 10/18, 24/25, 14/14 |
| `confirm_3_audit_d4` | rebuilt audit: draw and order, A/B choice via `classify.in_range_sorted`, final labels, kappa, 19/30, 19/28, 29/30, the 6/3/14/8/13 counts, calibrated shares, extra leak probes |
| `confirm_4_h2_start` | 2.18 / 1.67 / 1.73 with CIs from the stored walks |
| `confirm_5_recheck` | `release_recheck.csv` vs `coverage.json`, 217 = 169 + 48, 307/410, 106/193, 25 recheck JSONs vs the stored walks |
| `confirm_6_small` | fetch.py text, wording, figure titles, html/md consistency, D1/D2, ledger S6–S7, G5 rows, plausibility |
| `confirm_7_reasons` | L1/L2/adjudicator reasons for 14 packets; quoted fragments found in the fix diffs |
| `confirm_8_spotfetch` | six registry fetches (b38 A, b30 A, b03 A and B, b43 A, b41 A; saved in `scratch/releases/`) checked against the reasons |
| `confirm_9_rule` | the two-part scoring rule against "A absent" alone; the three A-absent/B-absent packets |

Limit: the packet directory and key under `/home/ubuntu/.claude/jobs/09561ec0/tmp/` are not readable by this account
(`/home/ubuntu` is 0750, owner ubuntu). I did not try to get round that. So "the packets carry no pipeline measurement"
and "a first build was rebuilt before labelling" are checked only at code level (`make_d4` writes `how[f].split("|")[0]`
to `packet.json`, the counts go to the key; the key published in `g4_audit_d4_labels.json` has no
`file_selection_detail` or count fields) and from the labellers' reasons, which cite file names, line numbers and code,
never counts. The labellers' claims about the released code were instead checked against six fresh registry fetches.

### Final verdict: publish with edits

The headline verdicts (H1 and H2 Inconclusive) hold under every reading I tried. All fifteen findings are fixed or
fixed in substance. Two things need editing before publication: the description of the three "missing from release B"
cases is wrong (B already contains the fix), and the write-up contradicts itself on the hand-traced advisory.

### Findings 1–15

**Item 1 (finding 1): fixed.** `posthoc_d4.py` computes every strict number. Recomputed independently: convention A
(non-strict counted as not over-approximated, all 411 in the denominator) gives H1 142/411 = 34.5% (30.1–39.3) and
H2 1.345 (1.266–1.45); convention B (non-strict and unknown dropped) gives 142/245 = 58.0% (51.7–64.0) and 1.812
(1.583–2.119). All eight numbers match `posthoc_d4.json` to the last digit. `posthoc_strict.json` now holds only the
eight fields `posthoc_strict.py` writes; the hand-added fields are gone. report.md pairs 34.5% with 1.35 and gives
58% / 1.81 as the sensitivity (`confirm_1_strict.txt`).

**Item 2 (finding 2): fixed.** From the seed-rebuilt key and `data/audit`: 10/30 agree, 12 cannot tell, 11 artefacts
(the same 11 packet ids as `posthoc_d4.json`; 10 with an empty A, a37 by its "unprovided token.py" reason), judgeable
10/18 (33.7–75.4%), tight 24/25, 1 tight judged absent. The one non-artefact cannot-tell (a23) is a genuine "cannot
judge" (`confirm_2_audit_v1.txt`). The report states 10/30, 11 of 12, 10/18 and 24/25.

**Item 3 (finding 3): fixed.** All 14 audited strict cases had an empty release A in the first packets (14/14
recomputed). "No audited strict case was contradicted" is gone; the report calls the strict reading unvalidated.

**Item 4 (finding 4): fixed.** The title carries no number. The calibrated shares recompute: 308/411 × 19/30 = 47.5%
(34.1–58.5) and × 13/30 = 32.5% (20.5–45.6), reported as 47% (34–59) and 33% (20–46), labelled post hoc, with the two
assumptions stated. See new finding N1 for a third figure that should sit beside them.

**Item 5 (finding 5, G1, G7): fixed in substance; one edit (N1).**
- Draw and order: the 60 ids are the first audit's seed-20261107 draw, shuffled with seed 20261110; the key's classes
  match `classes.csv`.
- B chosen identically: for all 60 packets A is the first and B the last in-range release by `in_range_sorted`. B
  coincides with the old first-present release in only 1 of the 30 over-approximated packets, so the B choice no
  longer encodes the class.
- Leak probe: the study's two features reproduce (A has no same-name file 68%, A has fewer packet files than B 62%). I
  added what a labeller can see: A's major version is 0 (57%), A is 0.0.x (50%), B's major is two or more above A's
  (63%), A has no files at all (53%), A has at most five source files by the recheck's count (60%). Nothing beats the
  68%, which is legitimate evidence of absence. The medians the labeller cannot see (49 against 14 in-range releases)
  differ, but version strings carry that weakly. The probe is fair, and the report says blindness was enforced by
  instruction only.
- Reasons against labels: I read L1, L2 and the adjudicator for 14 packets (b03, b30, b38, b41, b57, b26, b43, b34,
  b02, b25, b39, b46, b18, b21). The reasons are specific (file paths, line numbers, the code), the quoted fragments
  are in the fix diffs, and they support the labels. Six fetches confirm them against the released code: synapse
  0.33.5 has `self.http_client = hs.get_simple_http_client()` at handlers/federation.py:121,
  federation_server.py:823 and push/httppusher.py:90 and no blacklisting client (b38, A present); picklescan 0.0.1 has
  the `"aiohttp.client"` entry and no `InvalidMagicError`, `RelaxedZipFile` or `scan_err=True` (b30, A absent);
  swift 1.0.2 has no gatekeeper and swift 2.36.4's gatekeeper.py already holds the post-fix
  `'x-account-(host|device|partition)$'` list (b03); hermes 0.8.1 wraps `load_settings` in `try/except Exception`
  already (b43, the one tight error); toml 0.0.0 has no source files (b41). The three adjudications read as independent
  judgements and side once with each labeller and once on B only.
- Kappa and scoring: raw agreement on A_code 59/60, Cohen's kappa 0.966 (A_code), 0.92 (A_flaw); over the 30
  over-approximated packets alone 0.915; B_code kappa 0.818 (two disagreements, b03 and b38), which the report does
  not give. The final labels recompute exactly from L1, L2 and the three adjudications. Rule: confirmed = A absent and
  B present (or no B); judgeable = neither A nor B "cannot tell". 19/30 (45.5–78.1%), 19/28 (49.3–82.1%), tight 29/30;
  6 A present, 3 A and B absent, 2 cannot tell (b26: B's dist bundle truncated at 200 KB; b57: A lists build/index.js
  but the packet carried no A file, so one packet gap remains in the rebuilt audit, correctly excluded), 14 flaw
  present, 8 code absent with the flaw present, 13 flaw absent, 1 flaw "disagree" (b46) counted as neither
  (`confirm_3_audit_d4.txt`).
- The reading of G4: the plan's packet is "the earliest in-range and first-present releases", so agreeing with
  "over-approximated" means A absent and B present. That is the right reading of the plan. But D4 replaced the
  first-present release by the last in-range release, and with that B "B present" tests the upper bound, not whether
  some release has the code. See N1.

**Item 6 (findings 6 and 9): fixed.** "Pipeline-only patterns (not audited)"; "drive the pattern", "regardless of the
audit", "minority", "defensible", "quarter to a half" and "renamed, rewritten or moved" no longer occur in report.md.
Figure titles in `figures.py` are "Pipeline flags: ..." and "Pipeline flags (unaudited): ..."; alt texts "Pipeline
flags" and "Gap". The rendered PNGs clip the titles (N3).

**Item 7 (finding 7): fixed.** From the stored walks: 2.176 (1.931–2.497), 1.670 (1.533–1.843), 1.732 (1.596–1.909),
identical to `posthoc_d4.json` and the report's 1.67 / 1.73. 141 walks have an s > 0.2 before the cut (140 with
0.2 < s < 0.8). "Never shown absent" is 4,602 by D4's definition and 4,630 by classify's state (my earlier figure); the
difference is 28 releases with s ≥ 0.8 but a patch share ≥ 0.5, immaterial (`confirm_4_h2_start.txt`).

**Item 8 (finding 8): fixed.** `release_recheck.csv`: over-approximated deciding release path 106, fallback 153,
mixed 48, none 1; tight path 87, fallback 16; so 193 path, 169 fallback, 48 mixed, 1 dropped, exactly the new
`deciding_release_match` stage. Stored s reproduces 307/307 and 411/411; 25 seeded recheck JSONs match the stored walks
on version and s. Five over-approximations had an empty absent release; GHSA-hvfh-5mj3-5f3j, whose only absent release
(2.7.1) has no source files, is reclassified; 307/410 = 74.9% (70.5–78.8) and 106/193 = 54.9% (47.9–61.8) recompute.
In 11 of 308 the deciding absent release is not release A (A undetermined or an empty extraction), which the audit's
"A absent" construct handles correctly (`confirm_5_recheck.txt`). The reclassification contradicts the hand-trace
text (N2).

**Item 9 (findings 10–15): fixed, with one wording note.**
- 10: "51% ... a majority", "selected by packaging", TypeScript sentence present.
- 11: the restart is in D4 item 8 and in the report's process section.
- 12: `fetch.py` has no `subprocess` and no `git credential` call; `token()` is
  `os.environ.get("GITHUB_TOKEN") or None`; the only other D4 change is the docstring. D4 states all 790 diffs came by
  the public URL. The file was otherwise unchanged since ab54a45.
- 13: `handtrace.py` picks one seeded-random advisory per class, downloads with plain urllib, matches paths by its
  own suffix routine, imports neither `presence.py` nor `audit_packets.py` (only `classify.in_range_sorted` for the
  release order). Hand shares track the pipeline (32/32 vs 1.0; 0.405 vs 0.315; 0.648 vs 0.613). The invariants are
  asserted in `posthoc_d4.py`. The first, chosen traces are kept. But see N2.
- 14: the G5 table has 57 rows, all "Supported"; the sentences were rewritten, and the ones I checked are backed
  (the title, 51–56). It is no longer hollow, though "all Supported" after a rewrite should still be read with that in
  mind.
- 15: D1 says committed 18:51, first draft stamped 19:00; D2 says code at 18:54 on 11-07, written up on 11-08. The
  construct shift is stated in D4 item 7 and the report ("Code versus vulnerability"). "Renamed, rewritten or moved" is
  gone; the plain-terms "written slightly differently" fits five of the six A-present cases (b38 has the removed line
  verbatim; the fix touched 43 files, most not yet existing).
- G6: ledger rows S6 (OpenAlex queries, 2026-11-10) and S7 (Zenodo 10.5281/zenodo.23597710) exist and the report
  cites S6.

**Title, verdict block, "In plain terms".** The title ("blind audits confirm only part of its flags, so the true share is
not pinned down") is fair. The verdict block's numbers all reproduce. "Two in three" (19/30), "about half of the rest"
(6 of 11), "almost every time" (59/60), "about a third of the confirmed cases" (6 of 19 flaw present) are right. "A
third to a half" is the span of the two calibrated point estimates (33%, 47%) and is fair under the two-part rule; under
the lower-bound-only reading (N1) it is "a third to three fifths".

### New findings

**N1. Moderate: the three "missing from release B too" cases are releases that already contain the fix, and the report
describes them wrongly; the lower-bound-only reading should be shown beside the two-part rule.**
- report.md: "in 3 it is missing from release B too, so the packaged releases never show the code the fix changes",
  and "a further sixth could not be confirmed (the fixed code missing from release B too, or undecidable)".
- What the labellers wrote (b03, b25, b39): "B's gatekeeper.py already holds the post-fix inbound_exclusions", "B's
  auth_helper.py already contains the fixed user_login", "B already escapes limit and offset". Checked for b03: swift
  2.36.4 has the post-fix list at gatekeeper.py:58 while the advisory's `fixed` is 2.37.2. In all three the pipeline's
  first-present release exists and shows the code (2.20.0 s = 1.0; 3.8.0 s = 0.867; 2.0.6 s = 1.0), so the packaged
  releases do show it; the last in-range release is already fixed because the declared upper bound is late.
- With B switched from the first-present to the last in-range release, "B present" no longer tests "some release has
  the code" (the plan's second half) but the advisory's upper bound. Counting those three against the pipeline's
  lower-bound call is therefore a scoring choice, not evidence against the call. On A alone: 23/30 = 76.7%
  (59.1–88.2), 23/29 judgeable = 79.3% (61.6–90.2); calibrated 57.5% (44–66%). Both are still below the plan's 80%
  point rule, so H1 stays unreliable and Inconclusive under either reading (`confirm_9_rule.txt`).
- Fix: correct the two sentences ("in 3 the last in-range release already carries the fix, so the declared upper bound
  is late; the pipeline's lower-bound call is not contradicted"); give the lower-bound-only figures beside 19/30 and the
  57% beside 47% and 33%; say that the 80% bar fails under both; adjust "a third to a half" accordingly.

**N2. Minor: the hand-trace write-up says the class of GHSA-hvfh-5mj3-5f3j stands, but it is the one advisory the
recheck reclassified.** D4 item 10 and `results/plausibility.md` say "A later absent release has files, so the class
stands (`release_recheck.csv`)". The stored walk has exactly one absent release before the first present one, 2.7.1,
with zero source files; `release_recheck.csv` gives this id `cls_d4 = undetermined (only empty extractions absent)`,
and it is the "one" of D4 item 4 and the report's 307 of 410. Fix: correct D4 item 10 and plausibility.md, and say in
the report that the reclassified advisory is the random hand-trace case.

**N3. Minor: the rendered figure titles are clipped.** F1_share.png ends at "(not confirmed by the" and F2_gap.png at
"before the tes"; F2's x-axis label is cut at both ends. The "Pipeline flags" qualifier survives, but the audit
qualifier in F1 does not. Fix: wrap or shorten the suptitles and the F2 x-label.

**N4. Minor: one of the 19 confirmations rests on an empty release.** b41 (toml 0.0.0) has no source files at all; both
labellers scored "code absent, flaw absent" from the empty listing. By the plan's "absent means source extracted
successfully", that is unjudgeable; without it 18/27 = 66.7% (the pipeline's class stands via 0.1.0, which has files and
s = 0.009). Say so, or exclude it; nothing changes.

**N5. Minor: unadjudicated flaw disagreement and an unreported kappa.** The adjudicator was called only for code
disagreements, so b46's A_flaw disagreement (L1 "cannot tell", L2 "no") is left as "disagree" and counted as neither
in the 13/30. B_code kappa is 0.818 (two disagreements) and is not reported. State both.

### Remaining issues

- N1: correct the description of the three A-absent/B-absent cases and report the lower-bound-only figures (23/30,
  23/29; calibrated 57%, 44–66%) beside the two-part rule; both fail the 80% bar.
- N2: D4 item 10 and plausibility.md contradict release_recheck.csv on GHSA-hvfh-5mj3-5f3j.
- N3: clipped figure titles and the F2 x-label.
- N4, N5: one-line disclosures (empty-release confirmation b41; b46 flaw disagreement unadjudicated; B_code kappa).
- Unverifiable by me: the packet contents themselves (directory unreadable to this account); checked at code level
  and by six fetches only.
