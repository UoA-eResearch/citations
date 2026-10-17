# Confirmation pass: future-health-nz-medicine-access-lag (origin/main 3f97809)

Reviewer: the same independent review agent, 2026-10-18. Checked against report.md / report.html, deviations.md
D8a–D8d, the code diff c0386fc..3f97809, results/tables/*.json, data/cohort.csv and data/linked.csv as rerun, the
Purple Book file, and the Medsafe crawl log. Recomputation script: `review/reviewer_checks/confirm_checks.py` (the only
file added in this pass; nothing outside review/ was modified, nothing committed).

## Recommendation: **publish**, after the six small text edits in "Remaining edits" below. None of them changes a
number that bears on a verdict.

What I verified independently from the rerun data: cohort 694 (FDA-first 550, EMA-first 144), 28 excluded as old (8
by the refined HML rule), 666 analysed; H1 612 / 84 / 77; H1a 0.4014 [0.333, 0.480]; provisional bound 0.3957 (2
substances); H1b 1,668 [1,329, 2,134], 1,483 for all 84; stage table n = 71 with 22 early filers, medians
262/269/780/1,610, shares 0.251/0.166/0.583; the one remaining "consent before T0" is olodaterol; the frozen forecast
file is byte-identical to 4577be4 (sha256 70b7aec5…), the match-names file (sha256 6cc3392c…, pushed in 2b8f05f) lists
exactly the 125 forecast substances with the match names from the c0386fc release; every CBER date in cohort.csv comes
from the Purple Book file and agrees with my own expected dates to within a day for 26 of 30 and within 23 days for
the rest (immaterial, none funded); report.md and report.html carry the same numbers.

## Per-issue status

| # | issue | status | evidence |
| --- | --- | --- | --- |
| 1 | H3 framed against the source's definition | **resolved** | Report H3 section states the HealthiNZ definition (29 decided applications, application→decision, mean 7.7 / median 6.5), reports decided-only app→approval 3.4/2.2 y (n = 75), 4.1/3.6 (2022–23, n = 10), 6.4/5.6 (2024–26, n = 18), KM median 8.7 y, RMST by horizon 4.0/5.6/7.0/8.0; "not survivor-weighted, the reverse" and "7.7 is a reasonable summary" withdrawn explicitly; Figure 3 redrawn around the source definition. All numbers match primary.json H3_context. One citation error (page 16, not 26) — see edits. |
| 2 | "7–10 years" and "1,050 days" as their sources define them | **resolved** | 9 of 80 funded waited ≥ 7 y (4 in 7–10, 5 > 10); 60% of consented unfunded at 7 y; funded-only mean 1,156 d against 1,050; the "What was already known" table now quotes the BMS and IQVIA wording. |
| 3 | Stage table dropped early filers | **resolved** | analysis.py clips T1 at T0 instead of filtering; n = 71, 22 early filers (31%) stated in text and F1 caption; medians 262/269/780/1,610 and shares 25/17/58 with bootstrap CIs; the pre-review 494/2,200 figures are labelled as corrected. Recomputed identically. |
| 4 | T1 ignored Section 23 applications; T2 is the later full consent | **resolved** (T1), **partly by design** (T2) | NEW_APPL includes `^Provisional Consent \(Section 23\)`; 9 T1s moved (review_response.json R5_t1_changed, matching my list); t_prov column added; H1a lower bound 0.396 reported; D6.4 corrected in D8d; limitation names the 5 converted products. T2 cannot be recovered from this source, which the report says. |
| 5 | Cohort T0: CBER, duplicates, old substances, diagnostics | **resolved** | Purple Book CBER rows (sha256 recorded) give 45 earlier first-licensure dates (28 among pre-existing entries, 3 brought into the window, 14 CBER-only); the 8 duplicate pairs and the multi-component products are merged in ALIAS; the old substances and the two diagnostics (xenon Xe-129, C-11) plus the lutetium precursor are in EXCLUDE with reasons; the report states 62 of 705 (8.8%) wrong plus 17 missing, replacing "about 2%". One count inconsistency in deviations.md (D8b.1 says "40 substances get an earlier T0"; the correct figures are 28 pre-existing / 31 with an EMA date / 45 including CBER-only) — see edits. |
| 6 | "dimethyl" false HML match | **resolved** | `norm` keeps "dimethylfumarate" whole; the Medsafe crawl was repeated under the new name and the old "dimethyl" rows are pooled (LEGACY); linked.csv now has T2 2014-07-24, T3 2016-02-01, and the substance is in the H1 population. |
| 7 | TGA comparison on current ARTG entries | **resolved** | Paired median dropped from the report and the plain-language summary; KM by 2 / 5 y stated as a lower bound for Australia, with the cancelled-registration examples; F2 caption and legend updated. (The 427-day value remains in primary.json as a table field, unreported — acceptable.) |
| 8 | Scoring rule ≠ linking rule for 22 forecast substances | **resolved** | `results/forecast_2026_match_names.csv` + sha256 committed and pushed in 2b8f05f (before any 2027 data); content equals the c0386fc match names for all 125; score_forecast.py asserts both hashes and uses the frozen names; report notes 24 lapsed consents and the alpha1-proteinase inhibitor case. |
| 9 | H1a headline conflated sponsor delay with the regulator | **resolved** | Verdict line "Refuted as preregistered, with one claim holding for the regulator alone"; Medsafe-only share 17% [14, 20] given beside the preregistered 40%. |
| 10 | "Correctly absent" under-verified (tenofovir alafenamide) | **partly** | Brand-name matching against the register snapshot for multi-word names whose first word is an old token: 8 matched, T2 set for tenofovir alafenamide (2016-11-10, Genvoya). Its T1 is still missing because the Application rows are not brand-matched; the report says so. Adequate for publication; a brand match on the Application table would close it. |
| 11 | Validation speed / reproducibility | **resolved** | The four substances I identified are re-scored (m073, m116 in v1; r018, r059 in v2) with notes; both as-scored and re-scored precisions are reported beside my 0.89 / 0.94 / 1.00 with the enrichment caveat. Wording slip: the re-scoring touched six cells in four substances, not "four cells" — see edits. |
| 12 | First HML edition is not a funding event | **resolved** | Left-censoring applied only when the first HML edition would be the earliest listing (8 substances: artesunate, ciclosporin, defibrotide, glycopyrronium, iomeprol, methylthioninium, picosulfate, terlipressin — all plausibly pre-2013 hospital medicines); D8c.1 discloses that the first, over-broad version briefly flipped H1b to Supported. D2.1 corrected in D8d. |
| 13 | "Independent" cross-check | **resolved** | Renamed "crawl completeness check (the same register, the same name matcher)"; 663 of 664, exception explained. |
| 14 | Mixed populations in the decomposition | **resolved** | One population (n = 71) for sponsor / Medsafe / funding / T0→T2 with CIs; the n = 77 headline is labelled as the preregistered test. |
| 15 | Items promised by the plan and missing | **resolved** | 2024 approvals (54 / 3 / 2) in Limitations; all-cohort RMST 9.2 y and unreached median in H3; cutoff change stated; the 40 non-cohort recall chemicals characterised (28 pre-2010, 12 vaccines/nutritional/old NZ names). |
| 16 | "before any later Schedule Update was read" | **resolved** | Now "before any Schedule edition after the origin was used", with the 16 Oct 2026 Update and its contents stated. |
| 17 | D4 gap fill changed nothing | **resolved** | Stated in Limitations; review_response R17_D4 = 16 gap rows, none setting T3. |
| 18 | MSW T3_AU column semantics | **resolved** | Final sentence of the report labels the released column. |
| 19 | H2 MSW coverage wording | **resolved** | "submissions considered from July 2019". |
| 20 | Forecast year-feature extrapolation / LOSO skill ≈ 0 | **resolved** | Stated under H4 caveats. |
| 21 | D6.2 mis-attributed cause | **resolved** | D8d corrects it (coverage gap, Velphoro the one naming case). |
| 22 | FDA ingredient strings split on ";" only | **not changed, acceptable** | D8d says no cohort name joins two separately approved substances. That is not quite right: "ombitasvir paritaprevir ritonavir" is aliased to ombitasvir alone, so paritaprevir keeps its EMA date (2015-01-14) rather than Viekira Pak's FDA date (2014-12-19). The difference is 26 days (< 31) for one funded substance; no number in the report moves. Leave as is, or add paritaprevir to the alias. |
| 23 | report.html / captions | **resolved** | Numeric tokens in report.md are all present in report.html; F1 caption carries the 22-of-71 note; F3 caption rewritten. The html status line still reads "pre-review draft" because build_report_html.py keys it on the existence of review/confirmation.md — rebuild once after this file lands. |
| 24 | D2.1 HML years; plan cutoff | **resolved** | Both corrected in D8d. |

## The D8c CBER-only addition

The rule ("CBER 351(a) licence first granted 2010–2024 to a concept no earlier product had; vaccines, allergen
extracts, diagnostics, antivenoms, cord blood, immune globulins and plasma products of established concepts are out")
is written out in cohort.py, dates are taken from the file, and the 14 named products are searched through
medsafe.py (log rows present; Prochymal/remestemcel-L returns 1 product and 2 applications, plasminogen 5 and 9).

I scanned every Purple Book CBER proper name with a first approval date in 2010–2024 that is not matched to the
cohort: 65 names. 64 fall under the stated exclusions (vaccines, immune globulins, allergen extracts, cord blood,
antivenoms/antitoxins, skin-test diagnostics, Tachosil, and plasma products of established concepts: Wilate,
Corifact, Octaplas, Kcentra, Balfaxar, Fibryga, Albuminex, Haegarda) or are already in the cohort under another
name (Tretten = catridecacog via EMA; Adynovate via the T0 override; Lenmeldy = the EMA "cells encoding arsa gene"
entry; Kovaltry is old octocog alfa). The one omission is **Ixinity (trenonacog alfa, CBER, 2015-04-29)**, a distinct
recombinant factor IX never approved by the EMA. The stem-based scan cannot see it because its Purple Book proper name
is the generic "Coagulation Factor IX (Recombinant)", identical to Rixubis's. It has no NZ record, so adding it moves
only the cohort denominator (694 → 695). Two notes on the rule as applied:

- The exclusions by the preregistered old-substance rule are right for Prochymal (NZ consent 2012, 12 years before
  US licensure; the report's limitation covers it). For plasminogen the trigger is a 1992 register entry whose
  ingredient text contains "plasminogen" (an anistreplase product), which is a different active. Immaterial here
  (no NZ Ryplazim record either way), but the rule can fire on an ingredient-text coincidence.
- The additions change only cohort-wide denominators, as D8c says; H1 and H3 populations are unaffected (verified:
  none of the 14 has a T2 or T3 that survives the old-substance rule).

## Remaining edits (none affects a verdict)

1. **Shawview citation (my error, copied into the report).** The second quotation ("for the 29 applications that
   achieved a funding decision did so on average 7.7 years (or median 6.5 years) following their submission to
   Pharmac") is on Shawview p. 16, not p. 26 (review.md issue 1 said 26; `cache/downloads/shawview_2023.pdf.txt`,
   page marker 16). Change "pp. 10 and 26" to "pp. 10 and 16" in report.md and in review.md's issue 1.
2. **deviations.md D8b.1:** "40 substances get an earlier T0" should read "28 pre-existing entries get an earlier T0
   (31 including the three brought into the window; 45 including the 14 CBER-only additions)".
3. **report.md, Validation:** "found four cells" → "found six cells in four substances".
4. **D8c / cohort.py:** add trenonacog alfa (Ixinity, 2015-04-29) to CBER_ONLY, or state that products whose Purple
   Book proper name is a generic class name were not scanned and name this one.
5. **report.md, H4 caveats:** tenofovir alafenamide is now consented (2016) and unfunded, so it is at risk at the
   origin but absent from the frozen forecast, the mirror image of the alpha1-proteinase inhibitor note. One clause.
6. **report.html:** rebuild after this file exists so the status line changes from "pre-review draft".

Optional: issue 22's justification in D8d could mention the paritaprevir 26-day case rather than claim none exists.

## Files

`review/confirmation.md` (this file); `review/reviewer_checks/confirm_checks.py` (recomputation and Purple Book scan;
output reproduced above). Earlier review artefacts unchanged.
