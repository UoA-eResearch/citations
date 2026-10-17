# Confirmation pass: `future-health-nma-rank-temporal-fragility` at 090577c (D4)

Reviewer: the same independent reviewer as `review/review.md`, 2026-10-18. I re-ran my own scripts against the
merged `data/fits.jsonl`, the regenerated `data/jobs.json` / `data/holdouts.csv` and the new tables, and read
report.md, report.html, deviations.md (D4) and the code diffs 9340e97..090577c. Nothing outside `review/` was
modified; nothing committed; at most 8 cores used.

## Final recommendation: **publish**

Every number in the rewritten report reproduces from the merged fits with independent code (table below); the two
code defects are fixed as recommended; the framing changes requested in issues 8–12 are made. Five trivial loose ends
remain (A–E at the end); none touches a number or a verdict and all can go into the publication commit.

## Per-issue status

| # | issue (review.md) | status | evidence |
| --- | --- | --- | --- |
| 1 | largest-component rule never ran | **resolved** | `nma.R` now builds components from `netconnection()$D.matrix` (the fix I proposed); 44 networks refitted from the committed code (637023d 06:36:01 → refit 06:36:05–08:18:00). 41 records changed; the 3 unchanged are genuine failures (479664 full fit; 479807 S1; 481856 S3). Remaining errors: 208 = 201 in 479664 (excluded, "full fit failed") + 7 elsewhere (479807 S1, 479993 R×2 singular, 480492 S1/S3, 481695 S3, 481856 S3 — all one-treatment components or singular systems; none is the old error). 501229 is back in the primary set (n = 177); 35,398 of 35,400 random fits used (one network at 198). Report states the rule, the failure and the refit; inclusion row reads "the full-network fit succeeds: 177 / 29". |
| 2 | 501220 and 501274 inverted | **resolved** | `direction.py` / `direction.csv` corrected to `bad` with D4 notes; both refitted (jobs for exactly these two plus the three changed-data networks differ from `jobs_v1.json`; all other jobs byte-identical). iv sensitivity 39/206 = 18.9%, high-confidence 38/199 = 19.1% — reproduced. The two guards I suggested (name-then-code treatment tables in `treatments()`, a control-on-top check) were not added; my own check of every contrast-level full fit finds no control/placebo in the top half and plausible tops throughout (FOLFIRINOX, FIB, CAF+CTG, fingolimod, zoledronate …), so nothing is currently wrong. Recommend the guards for future runs only. |
| 3 | arm-level adjudication undocumented | **resolved, one caveat** | `results/tables/direction_arm_record.csv` released (178 rows; 60 hand-checked; 66 with a named control; 63 consistent; the 3 "no" are safety outcomes). Its `hand_checked` flag comes from `data/validation/d2_handchecked_lists.txt`, written today at 06:49 — a reconstruction of the D2 set, not a contemporaneous log. It is credible: the 60 are exactly the 30 binary/rate networks whose sheet label disagrees with or is absent from the catalogue plus all 30 continuous networks, which is identical to my independent selection, and the 116 calls I re-adjudicated all match the record. The record or D4 should say the list was reconstructed (see D). |
| 4 | iv `withheld_share` wrong | **resolved** | `analysis.py` counts original study ids; released values now 0.10–0.40 for the 29 contrast-level networks. |
| 5 | empty "studies" counted and withheld | **partly** | Arms with n ≤ 0 or no n, and one-arm studies, are dropped (`standardise.py`); exactly 479585 (49→48), 479808 (31→27) and 501307 (17→16) change, their tranches and fits updated, no other std file changed, the inclusion cascade is unchanged (277/236/208/207). Still open: arms with n > 0 but no mean (482475, Chou 2007 and Hazenberg 2000, sd = 0) are counted (k = 28) and silently dropped in the fit (k = 26). One network, no reported number affected beyond its own k and tranche target. Fix when convenient: also drop arms missing the outcome values at standardisation, or say so. |
| 6 | sheet years unvalidated | **resolved** | Limitation added with the 479888 example (MPACT dated 2002; a 2005 trial dated 2013). The Europe PMC spot-check I suggested was not done; the limitation suffices. |
| 7 | V1 combined-label note | **resolved** | v1_parse_validation.csv: "combined labels take the last year written in the label (D1 rule)". |
| 8 | negative-control framing | **resolved** | "We could not distinguish …"; 28% relative excess and "up to about 60%" stated; participant asymmetry quantified (temporal mean 24% vs random 18%; I reproduce 0.236 / 0.177 from the new `random_withheld_share`). Plain terms: "not clearly more disruptive". |
| 9 | calibration excludes new entrants | **resolved** | "Among treatments already compared" in the verdict line, H2, Figure 2 caption and plain terms; retention counting new entrants 71% (T10) and 46% (S3) reported with the S3 overstatement of about 13 points (I reproduce 70.6% / 46.0%). |
| 10 | "safe, perhaps too safe" | **resolved** | Replaced with the suggested wording plus "not a forecast of the next analysis's winner once new treatments can enter". |
| 11 | Daly et al. wording | **resolved** | "studies removed one at a time, in five data sets (quadratic-weighted kappa down to 0.40)"; "one-at-a-time, not temporal". |
| 12 | ISPOR citation | **resolved** | Dropped from the table. |
| 13 | run-time comment | **resolved** | "about 5 h on 24 cores". |
| 14 | D2 confidence labels | **resolved** | Limitations state what "high confidence" meant and that the two errors were misreadings, not uncertain calls. The labels stay "high" for the corrected calls, which is defensible given the explanation. |
| 15 | iv set as sensitivity set; primary N | **acceptable** | Pre-fit, logged, results both ways. The inclusion table shows 178 / 29 and D2 is cited; the report does not say in words that the plan implied 207 primary networks. Optional one-line addition. |

## Recomputed numbers (merged fits.jsonl, independent code: `reviewer_checks/recompute_verdicts.py`, `holdout_checks.py`)

| quantity | report (090577c) | my recomputation |
| --- | --- | --- |
| primary networks; excluded | 177; 1 (479664 full fit) | 177; 1 |
| H1 | 35/177 = 19.8% (14.6–26.3) Refuted | 35/177 = 19.77% (14.58–26.26) Refuted |
| flip or new-entrant top; new entrants | 52/177 = 29%; 19 | 52/177 = 29.4%; 19 (overlap 2) |
| H2 mean P(best) / retention / gap | 0.61 / 80% / −20 (−26 to −13) Refuted | 0.6066 / 0.8023 / −0.1957 (−0.256 to −0.136) Refuted |
| retention counting new entrants | 71% (T10), 46% (S3) | 70.6%, 46.0% |
| H3 R² / AUC | 0.11 (0.04–0.24) / 0.69 Supported | 0.1149 (0.042–0.241) / 0.686 Supported |
| flip rate gap < 0.05 / ≥ 0.2 | 24% / 7% | 24.4% (41) / 7.3% (55) |
| random control; difference | 15.4%; 4.4 (−0.8 to 9.7) | 15.39%; 4.39 (−0.8 to 10.0) |
| participants withheld, temporal / random | 24% / 18% | 23.6% / 17.7% |
| S1 / S2 / S3 flips | 34% (27–41) / 15% (10–21) / 33% (26–40) | 59/175 = 33.7% / 26/177 = 14.7% / 57/174 = 32.8% |
| with new entrants S2 / S1 / S3 | 18% / 50% / 54% | 18.1% / 49.7% / 54.0% |
| S3 P(best) vs retention | 0.59 vs 67%, −8 (−15 to −1) | 0.592 vs 0.672, −0.080 |
| Kendall median; top-2 changed | 0.90; 43 (24%) | 0.905; 43 |
| common effect; SUCRA | 19.2%; 21.5% | 34/177; 38/177 |
| + contrast-level; high-confidence only | 18.9%; 19.1% | 39/206; 38/199 |
| calibration bins | 71%, 63%, 88%, 31/32 | 0.714 (28), 0.633 (49), 0.875 (64), 0.969 (32) |
| median tranche share / participants | 15% / 20% | 0.154 / 0.198 |
| D3 split networks | 13 | 13 |
| holdouts | — | T10 sets match in all 207; undated never withheld; random holdouts T10-sized and dated-only in all 207 |
| report.md vs report.html | — | every number above appears identically in both; "Souring" and "random, not temporal" gone |

## Loose ends (trivial; none affects a number or verdict)

- **A. Stale meta description.** `report.html` line 102 (`code/build_report_html.py`) still says "across 176 published
  network meta-analyses"; the body says 177. The lab-wide fix (368e59e, 06:37) predates the refit. Update the string
  and rebuild.
- **B. Figure 2 caption file.** `results/figures/F2_calibration.txt` lacks the "among the treatments already compared"
  qualifier that report.md's Figure 2 caption now carries (figures.py was not changed). Harmless; align if the caption
  file is used anywhere.
- **C. Code-before-output.** The verdict-bearing refit followed the committed D4 code (637023d), as required. Two
  smaller steps did not: the standardised data were regenerated at 06:34:38–06:34:52, about a minute before that
  commit, and `analysis.py`'s D4 additions (retention with new entrants, random withheld share; modified 08:20:40) and
  `direction_record.py` (06:49) were committed in 090577c together with the outputs they produced. Descriptive
  additions only; a sentence in D4 would close it.
- **D. D2 count wording and the reconstructed list.** deviations.md D2 still says "Each of the 60 binary or rate
  networks where they disagree or the sheet has none, and all 30 continuous networks"; the hand-checked set is 30
  binary/rate + 30 continuous = 60. Correct the count, and note in D4 or the record that
  `d2_handchecked_lists.txt` was written during D4 to document the D2 set.
- **E. "The independent review re-parsed 32 networks and found them exact."** 31 were exact; the 32nd (480666) could
  not be compared by my parser (its label column), not a fault found. "31 of 32 exact, one not comparable" is accurate.

With A–E made (or left as they are), the study is ready to publish: Refuted (H1, H2), Supported (H3).
