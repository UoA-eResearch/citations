# Review: do Supreme Court precedents die before they are overruled?

Reviewer: independent (Fable), 2026-10-26. Scripts and outputs: `review/reviewer_checks/` (check1_data, check2_robust,
check3_controls, check4_dups, check5_scdbonly, check6_recent, check7_chevron, each with a `.out`).

## Verdict: fix first

The pipeline is sound and every reported number reproduces. The preregistered verdict (H1 not testable) is correctly
applied. The post hoc "cited more before overruling" result is real in the data and survives every alternative I
tried: equal weighting, dropping the most-cited cases, other matching, SCDB-only controls, federal/state/appellate/
district citers, and a placebo. But two things the report does not show change what it may conclude:

1. **The pattern belongs to 1960–1989.** For overrulings in 1990–2013 the year-before gap is −0.09 (−0.38 to +0.14),
   and for the 14 recent stacks without district-court citations it is +0.03. The plain-terms claim "in the years
   before an overruling, the doomed decisions were cited more" is a statement about Warren/Burger-era overrulings, not
   about the last 35 years (finding 1).
2. **The post hoc "fix" is mis-described and not the best one.** Cutting calendar years at 2018 changes nothing
   (D(−1) −0.56 → −0.55); the whole sign flip comes from dropping the 14 recent, heavily cited stacks. The direct fix,
   excluding district-court (FD) citations where the break lives and keeping all 71 stacks, gives D(−1) −0.31 and
   D(+5) +0.08, and should be the headline robustness analysis (finding 2).

Add those two analyses, correct the coverage figures and the Chevron reading, and soften the three overclaims. No
re-run of the data pipeline is needed. With that, publish.

## Findings

### 1. Major: the pre-overruling citation rise is confined to 1960–1989 overrulings
- Evidence (check2_robust.out, A2): T0 1960–1989 (40 stacks) D(−1) −1.04 (−1.59 to −0.61); T0 1990–2013 (17 stacks)
  D(−1) −0.09 (−0.38 to +0.14), D(+5) +0.38 (+0.11 to +0.57). check6_recent.out: T0 ≥ 2015 (14 stacks) without FD
  citations D(−1) +0.03, D(+5) +0.47. So for every overruling since 1990, citations neither rose nor fell before
  overruling and fell clearly after. In that era H1's precondition holds (D(+5) excludes 0) and the pre-share is about
  −0.2: erosion refuted, not "not testable".
- The report's post1990 subset (report.md:93, D(−1) 0.44) is contaminated by the break and cannot be read.
- Fix: add the era split to the results table and the plain-terms section; rewrite "In the years before an overruling,
  the doomed decisions were cited more" (report.md:38–39) as "For overrulings of the 1960s–80s ... ; since 1990 they
  were cited about as often as comparable decisions until the overruling, and less afterwards." Title: keep "cited
  more, not less" only with the era qualifier, or change to "were not cited less".

### 2. Major: the pre-2019 restriction is a sample restriction, not a window restriction; the cleaner fix is omitted
- Evidence (check6_recent.out): T0 ≤ 2013 with years to 2025: D(−1) −0.56, D(+5) −0.01; with years ≤ 2018: −0.55,
  −0.01. The `d.year <= 2018` cut (event.py:173–174) does nothing; the result comes from dropping stacks 57–70.
  Those 14 stacks alone give D(−1) +0.56 with all citations and +0.03 without FD citations.
- The break is in district courts only (check1_data.out: FD 59,504 → 171,701 → 319,779 in 2018–2020; F appellate
  flat at 54–60k; state S and SA fall by about 20% after 2018, so "state citations stay near 45,000" (report.md:22) is
  loose). deviations.md:19 attributes the bias to "a case's mix of federal and state citers"; it is the mix of
  district-court citers against everyone else.
- All 71 stacks without FD citations: D(−1) −0.31, D(0) −0.42, D(+5) +0.08 (check6). This keeps the recent
  overrulings in and removes the break at its source.
- Fix: report the FD-excluded 71-stack analysis beside the 57-stack one; say plainly that the 57-stack result differs
  from the primary because it drops 14 stacks, not because of the year cut; correct the mechanism in deviations.md.

### 3. Major: the pooled estimate is count-weighted and the report does not say so
- Stacked PPML weights each stack by its citation volume. The five most-cited treated cases carry 43% of the
  pre-2019 weight (check2, per-stack table); the single largest stack, Fay v. Noia (2,595 pre-citations), shows
  erosion (D(−1) +0.42), the opposite of the pooled sign.
- The pattern is nonetheless robust: 72% of the 57 stacks have D(−1) < 0, median −0.42; dropping the 1/3/5/10
  most-cited gives −0.67/−0.69/−0.51/−0.54; the less-cited half −0.45 (−1.19 to +0.04); counts rescaled per stack
  −0.60.
- Fix: state the weighting in Methods; add the per-stack share and median to Results; name Fay v. Noia as the
  textbook erosion case that the pooled estimate hides.

### 4. Moderate: the Chevron reading is half right
- Evidence (check7_chevron.out): Chevron's controls are district-court staples (Matsushita 59,396 citations, Harlow
  21,717). Their FD citations go 1,276 → 3,315 → 5,556 in 2018–2020 while Chevron's stay at 137–173, so the 2019
  step is the coverage break, as the report says. But in federal appellate courts Chevron falls from 251 (2018) to 90
  (2023) against controls at 504 → 300: D +0.42 in 2023, +0.53 in 2025; "all except FD" rises from +0.11 (2018) to
  +0.35 (2023). A real relative decline of about a third begins in 2021–2023, before Loper Bright.
- The report (report.md:23, 104–106) uses Chevron only as an artefact illustration. It is also the one in-sample case
  with visible pre-overruling erosion once the artefact is removed, and its matching is the worst in the study
  (SMD 1.54, secondary.json; the report gives Humphrey's 1.05 but not Chevron's).
- Fix: add the appellate-only Chevron path and the SMD; reword "Chevron's path shows it" to "the step in Chevron's
  path shows it; without district courts a gradual decline of about a third remains from 2021".

### 5. Moderate: coverage of the overruling list is misreported and the parse loses rows silently
- SCDB's `usCite` is blank for the 2016–2021 terms. 13 of the 88 "alterations not on the list" are on the list
  (Janus, Wayfair, Knick, Hyatt, Ramos, Dobbs, Kennedy, Loper Bright, ...; check in the transcript, overruled.py:90).
  Correct figures: 75 of 174 not listed, coverage 57%, not "about half" (report.md:70, 126; overruled_coverage.json).
- overruled.py:23 `CITE` does not match old-reporter cites ("80 U.S. (13 Wall.) 29"), and overruled.py:49–50 skips
  them without a count. 13 of 146 table rows are dropped (check1_data.out), five of them with overrulings in
  1960–2024: Low v. Austin (93 lower-court citations, eligible), Minturn v. Maynard (61, eligible), Pace v. Alabama
  (40), Kentucky v. Dennison and The Schooner Catherine (not found by name). Two eligible treated cases are missing.
- The CRS/Constitution Annotated table was attempted (data/raw/conan_overruled.html is a Cloudflare challenge page)
  and the fallback to Wikipedia, whose page is self-tagged `{{Incomplete list}}`, is not recorded in plan.md or
  deviations.md. Wikipedia's selection favours famous overrulings, which is the population most likely to be
  "fought over".
- Fix: recount with name matching for blank-usCite terms; fix the regex and add the two cases or record them as
  dropped; log the CRS attempt; add the selection caveat to "Not shown".

### 6. Moderate: the control pool contains orders-list clusters and CAP duplicates
- event.py:82–85 admits pool members with no SCDB issue area; 81 of 672 distinct controls have no `scdb_id`
  (check3_controls.out): cert denials and summary dispositions cited through "cert. denied" parentheticals (e.g.
  Joslyn v. Joslyn 257, Schanbarger v. Kellogg 284, Jordan v. Arizona 744) and Harvard CAP twins of real decisions
  (Gideon 8954562 with 6,672 citations; Grayned, Griffin v. California, Marks). plan.md says "same SCDB issue area",
  which these cannot satisfy.
- Effect is nil: with SCDB-id controls only, pre-2019 D(−1) −0.52 (−0.96 to −0.18), primary D(+5) +0.29, pre-share
  0.72 (check5_scdbonly.out), and balance improves (SMD 0.21 → 0.14).
- Fix: restrict the pool to clusters with an SCDB id (one line) and re-run, or disclose.

### 7. Minor: overclaims (G5 re-labels)
| row | sentence | my label | why / fix |
|---|---|---|---|
| 1 (title) | "Not in lower-court citations: ... cited more, not less, in the years before" | Partially supported | True for 1960–89; not for 1990–2013 or the recent stacks without FD (finding 1). Qualify. |
| 6 | "the evidence runs against erosion" | Overstated | Counts cannot separate reliance from criticism; the rise before overruling is compatible with Feldman's erosion (negative treatment). Write "against a decline in citation counts". |
| 20 | "they peak at 74% more in the year of overruling" | Overstated | posthoc_pre2019.json: D(0) −0.743, D(+1) −0.785. The peak is +79% the year after. |
| 22 | "citations rise as a precedent heads for the Court" | Partially supported | Era-dependent (finding 1). |
| 28 | "The best evidence we have says no" | Overstated | "No" answers "do lower courts stop relying"; counts show no decline, not continued reliance. |
| 29 | "presumably because they were being fought over" | Exploratory-labelled, add | Part of the rise is mechanical: the overruling case's own lower-court history and parallel litigation cite the precedent. Say so. |
| 114 (body) | "No support for lower-court reliance eroding" | Overstated | Same as row 6. |
Also report.md:17 "the post-overruling decline is clear: 65%": removing opinions that cite the overruling decision
removes post-overruling citations partly by construction (any later discussion of the precedent cites the overruling
case); call 0.65 an upper bound.

### 8. Minor: balance is reported as one mean
- Mean SMD 0.28 (0.21 pre-2019) hides 16 of 57 stacks with |SMD| > 0.5 and 2 with > 1 (check2). The mean is positive
  in every variant: the treated are more cited than their nearest controls, a ceiling for famous precedents. Within
  the matching window treated slopes are not steeper (mean difference 0.009 log points a year; 61% steeper), so
  pre-trends in −20..−11 are matched. Report the distribution.

### 9. Minor: process and plan deviations not in deviations.md
- The committed event.py (18acfb2) could not run: `d.stack` is the DataFrame method, so `long_panel` and `_boot`
  fail; the fixes landed in the results commit (e09bf03) together with the `pre2019` variant. Mechanical, but the
  "code before counts" claim should say the committed code was patched for attribute access.
- The lead's own `lit_against` names "CourtListener coverage shifts (CAP to 2018, scrapers after)". The break was
  foreseeable and could have been preregistered as a court-type restriction; the plan's limit (section 6) only says
  coverage "changes over time". D1 is correctly stamped post-result (21:03, after primary.json 20:56 and
  secondary.json 21:02, before posthoc_pre2019.json 21:05), but it was not a discovery.
- Partial overrulings: 4 of 71 treated are "(in part)" (Pollock, Yates, Ahrens, Teague); plan.md covers only
  decisions overruled twice. Disclose.
- Plan says controls share the SCDB issue area; code lets missing issue areas through (finding 6).

### 10. Checks that passed (no action)
- Mapping: 10,620,418 pairs, all unique; year = citing cluster date_filed, none missing; 3 citing clusters without a
  court; no Supreme Court decision counted as a lower-court citer (0 citing clusters with an scdb_id). Non-federal,
  non-state citers (OLC, AG reports, TTAB, military, tribal) are 0.85% of pairs: immaterial.
- Duplicates: splits are small. Of citations in same-name same-year twin groups, 3.3% sit outside the most-cited
  cluster; the treated twins with real counts are distinct decisions (Pollock II, Sinclair II, Yates II) and the rest
  carry 1–33 citations; Gideon's twin splits about 50/50 and stably over time. (check2's final Chevron block crashed
  on a lookup; check7_chevron.py replaces it.) The "most-cited cluster" rule loses nothing
  material (check4_dups.out).
- Dates: 9 co-citing opinions dated before their overruling year across all stacks.
- Treatment rules: first listed overruling, age ≥ 20 and ≥ 50 citations are implemented as planned (event.py:46–70).
- Model and bootstrap: event dummies −10..+10 against pooled −20..−11, case×stack and year×stack FE, all-zero cases
  dropped, separation warnings are all whole all-zero year×stack cells (multiples of 11). Stack resampling with
  relabelling is correct; 1,000 of 1,000 fits succeeded; my cluster-robust intervals match the bootstrap
  (D(−1) −0.55: −1.01 to −0.20 vs −0.96 to −0.21).
- "Not testable" is applied as preregistered. The pre-share is meaningless when D(+5) ≈ 0 (bootstrap −14.6 to 7.7),
  which is why the precondition exists. Design note for follow-ups: a ratio makes H1 untestable exactly when the
  answer ("no decline at all") is most informative; test D(−1) directly.
- Placebo: random never-overruled pool members treated as if overruled give D(−1) +0.07 (10 draws, −0.20 to +0.32):
  the matching does not manufacture the result.
- Citer type, pre-2019: federal-only −0.46, appellate (F) −0.67, district (FD) −0.37, state −0.60; alternative
  matching (5/20 controls, ±5 years, same year, no issue area): −0.39 to −0.58; T0 ≤ 2008: −0.58.
- All numbers in report.md match the tables except the peak (row 20) and the coverage counts (finding 5).

## Gates
- **G5:** `overclaim_check.py --verify` passes (34 rows). Re-labels in finding 7; rows 1, 6, 20, 28 and the body
  sentence at report.md:114 need edits.
- **G6:** `attribution.py check` passes (10 claims). Spot-checked P1–P4 against the sources: Feldman (SCOTUSblog,
  16 June 2026) argues Supreme Court-driven erosion, says lower courts kept applying Abood and still had to reckon with Lemon [essay wording paraphrased by the lab before commit], and reports citation and negative-treatment counts (Bivens 38,000/1.7%, Smith 13.4%, Abood
  825/7%); the corrected framing and P2/P3 "refutes" roles are right. Broughman & Widiss (10.1086/689835) abstract:
  differences-in-differences, overrides vs overrulings, no pre-window stated; P4 and the removal of P5 are right.
- **G1:** no leakage audit in plan.md. I looked: matching is on −20..−11 counts, before the outcome window; the ≥ 50
  filter uses citations up to T0−1 (inside the outcome window) for treated and controls alike, and binds on only 4
  treated cases. Contamination of controls by SCDB-flagged, unlisted alterations is possible and small. No leak found.
- **G2:** no coverage.json; parse drops (13 rows) and the CRS fallback are unrecorded (finding 5).
- **G3:** no plausibility.md. The anchor exists in the ledger (Broughman & Widiss' sharp post-overruling fall) and the
  primary's weak D(+5) of 0.27 against it should have prompted the co-citation and break checks before the write-up;
  it did, informally.
- **G4, G7:** not applicable (no classifier or labelled sample).

---

# Confirmation pass (D2, commit 4770314) — 2026-10-26

Reviewer: independent (Fable). Script: `review/reviewer_checks/check8_confirm.py` (+ `.out`). I read the D2 diff
(event.py, overruled.py, secondary.py, posthoc_d2.py, deviations.md, report.md, overclaim_check.md, plausibility.md,
coverage.json), checked every number in report.md against primary.json, posthoc_pre2019.json, posthoc_d2.json,
posthoc_d2_yearcut.json, posthoc_d2_per_stack.csv, secondary.json and matching_balance.json, and recomputed the four
new headline estimates with the revised event.py.

## Verdict: publish with edits

Every finding is resolved and nothing new is wrong with the numbers. The edits below are three wording corrections
and two hedges; none changes a table.

## Status by finding

1. **Era — resolved.** Era splits are in the title, verdict, results table and plain terms. Recomputed with the
   revised matching: 1960–89 D(−1) −1.014 (42 stacks), 1990–2013 −0.055 with D(+5) +0.410 (17), 2014–2024 without
   district courts +0.100 with D(+5) +0.515 (13); all match posthoc_d2.json to three decimals. The "Refuted" reading
   for 1990–2013 is narrow on the pre-2019 counts (pre-share upper bound 0.31 against the 0.33 bar) and clearer
   without district courts (0.10); say "narrowly" in report.md:34 or lead with the district-court-free version.
2. **Coverage-break fix — resolved.** D1 is now described as a sample restriction (yearcut −0.522 vs −0.521, same as
   my check6 on the old matching), the mechanism is district courts, and the direct fix is reported: 68 stacks,
   D(−1) −0.274 recomputed exactly. Note the bootstrap interval (−0.74 to −0.01) barely excludes zero and my
   cluster-robust interval (−0.69 to +0.04) does not; the report's "if anything, slightly higher" (report.md:27–28)
   is the right register. "Courts of appeals and state courts stay flat" (report.md:24): state pairs fall 13% from
   2018 to 2020; "roughly flat" is safer.
3. **Weighting — resolved.** Disclosed in Methods and the verdict; per-stack file, top-five share (49%), leave-out
   range and Fay v. Noia all match the tables.
4. **Chevron — resolved.** Paths by court type and the three SMDs (1.28; 1.64; 2.15) are reported, and the reading
   now separates the 2019 step (coverage) from the gradual appellate decline before Loper Bright. The variants
   re-match Chevron's controls on the restricted counts rather than holding them fixed; both routes give the same
   picture (my check7 held controls fixed: 36% vs 35% in 2023 without district courts).
5. **Coverage and parse — resolved, two wording errors.** The regex now accepts old-reporter cites; coverage.json
   counts 142 of 146 rows parsed and 4 dropped with reasons, all correct (Humphrey's and FEC v. Colorado have
   "___" pages, Wales v. Whitney has no cite, Brown is written "347 US 483"). Kentucky v. Dennison and The Schooner
   Catherine enter the treated set; Low v. Austin and Pace v. Alabama fail the 50-citation bar. SCDB coverage: 91
   matched by cite plus 10 of the 13 blank-usCite terms matched by name = 101 (58%), as reported; Rucho and Shinn are
   correctly not on the list; Trump v. Hawaii is on the list (it overruled Korematsu) but the SCDB name
   "TRUMP, PRESIDENT OF U.S. v. HAWAII" defeats the first-party match, so the true figure is 102 (59%). Minor.
   - **Fix (deviations.md D2, report.md:93–94):** the decision with no link is Minturn v. Maynard (58 U.S. 476),
     not The Schooner Catherine (58 U.S. 170, which is linked and in the sample, overruled 1975). And Minturn does
     have a CourtListener cluster (86949, 61 lower-court citations): the link failed because CourtListener records
     its U.S. cite as 58 U.S. 477. Say "one whose U.S. cite differs by a page in CourtListener", or add it by hand.
6. **Controls — resolved and verified.** All 730 control slots in stacks.json have an SCDB id and the treated case's
   issue area. The pipeline after counting was re-run (file times: event.py 09:15, primary.json 09:28, secondary.json
   09:41, posthoc_d2_variants.json 09:59, posthoc_d2.json 10:00; no stale cache). Primary D(+5) +0.29 (−0.05 to
   +0.51), still not testable; the pre-2019 D(−1) −0.52 matches my SCDB-only re-run from the first review (−0.52).
7. **G5 re-labels — resolved.** The seven sentences are rewritten; the regenerated check (48 rows) passes and its
   labels are fair. The verdict sentence now claims no decline in citation counts, and the plain terms say counts
   cannot show continued reliance.
8. **Balance — resolved.** Mean 0.25, median 0.12, 30 of 73 above 0.5, 9 above 1, matching matching_balance.json.
9. **Process — resolved.** D2 records the patched event.py, the foreseeable break, the four partial overrulings, the
   plan/code mismatch (now fixed), the Constitution Annotated attempt and the incomplete-list tag.

## Gates
- **G5** passes (48 rows) and is honest. **G6** passes (10 claims); the ledger is unchanged and my earlier spot
  checks stand (the lab paraphrased the two essay phrases in my first-pass paragraph; nothing in substance changed).
- **G1** audit is in D2 and is complete for this design. **G2** coverage.json covers the list parse; the other
  per-unit stages (cluster linking: 1 unlinked, 7 multi-cluster) remain in overruled_coverage.json, which is
  adequate. **G3** plausibility.md traces three units and states invariants that hold (I verified the control
  invariant directly). **G4, G7** not applicable.

## New issues found
None affecting a number. The two wording errors in finding 5 and the two hedges in findings 1 and 2 are the edits.
