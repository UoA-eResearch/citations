# Confirmation pass: legal-phantom-citations-judicial-opinions (D9; commits 933e085, 9f6b26b, 7a6e6b8)

Reviewer: the same independent reviewer as `review/review.md`, 2026-10-23. New files this pass:
`review/reviewer_checks/confirm_flag_db.py` (→ `confirm_flag_db.json`, `confirm_flag_db.log`) and this file. Document
pulls, the `assemble_verified.py` reproduction and the recall re-derivation were run from scratch space (`/tmp/confirm`)
and are quoted below; nothing else in the study was touched.

## Verdict: **fix first** (one item; everything else is confirmed)

Findings 1–4 and 6–11 are fixed as the brief describes, the numbers in `report.md` reproduce against `primary.json` and
the data, and the matcher fixes (New Mexico, same-day captions) introduce no false match I can find. The one defect is in
the fix for finding 5. The new `flag_vs_database()` name match is vacuous: `norm_name()` keeps only `[a-z0-9]`, so the
three Cyrillic captions that the `NON_US` regex lets into the "US in-window" set ("ООО «Точка опоры» v. ООО «ЦСС»",
Russian Federation; two Ukrainian "ОСОБА_1 v. …") normalise to `"v"` or `"1 v"`, and `party_score()` then falls through to
`token_set_ratio("v", name)`, which is 100 against every corpus caption with a standalone "v". `by_name` is therefore True
for 41 of the 43 clusters whatever the database holds (`flag_vs_database.csv` shows the Cyrillic caption as `best_case`
for 16 of them), and the two "found by hand" are simply the two cluster names without a "v" token (`…zaykariyav…`,
`in re … nwaubani`). Recomputed without degenerate captions, the caption match holds for 6 of the 17 non-cluster
clusters, not 15; a hand search of every field of the database settles 6 more and finds 5 of the 43 nowhere. So the
headline "All 43 are already in the public AI Hallucination Cases database, so the screen adds no unrecorded incidents"
(verdict bullet, "In plain terms", the F2 caption, "What this does and does not show") is wrong: **38 of 43** are in the
database and **5 court-flagged opinions are unrecorded**. The draft's error (19 unrecorded) has been replaced by one in
the opposite direction (0). The repair is a one-line code change, a re-run of `analysis.py score`, and rewording; the
hand checks are done below.

## Finding by finding

1. **Fixed.** `report.md` line 8 "Verdict: Inconclusive"; `primary.json` `H1.verdict = "Inconclusive"` with `rule`
   recording the sampled-sheet rule and `point_estimate_band = "Refuted"`; `screened_reliance.ci = [0.0, 40.2]`
   unchanged. Title and plain-terms section match.
2. **Fixed.** "Blind to the known pattern" and "Why so blind" report the three mechanisms (empty California name →
   consistent; fabricated caption at a real page → misattribution; one shared surname → consistent) with the
   Contreras/Shahid/Payne examples, and "the screen flags none of the fabricated citations" on the three in-corpus
   opinions that quote them (= 0 of 3). *Henry County Schools v. Grant* is rightly not among the three: I read it this
   pass (opinion 11340562, 2026-06-10): the trial court's order, "drafted by the plaintiffs' attorney … relies on at
   least one hallucinated case", which the Court of Appeals does not name.
3. **Fixed.** `primary.json` `recall_detection`: 879 rows → 869 distinct clusters, pre-filter 465 (53.5%; 50.2–56.8),
   post-filter 42 (4.8%; 3.6–6.5), with the note that "flagged" means any candidate;
   `recall_corrected_screened_reliance.upper_bound = 832`, report "roughly 830". My own scan
   (`reviewer_checks/scan_candidates.py` re-run unchanged against the new `charlotin_matched.csv`, output in scratch)
   reproduces both exactly: 465 and 42 distinct clusters of 869, and the same per-document candidate sets for the five
   judge incidents (Henry County flag+reliance pre-filter, CorMedix reliance pre-filter, the other three none; none
   post-filter). `match_charlotin.py` has the `(?<!New )Mexico` fix (the 16 New Mexico incidents are in; 10 matched)
   and the same-day token-containment rule (`contained`).
4. **Fixed, and it matches my reading.** `JUDGE_DOC` classifies CorMedix as the relying opinion and Shahid, Payne,
   Contreras and Henry County as reviewing-court opinions; `recall_reliance`: 1 relying opinion in the corpus, flagged
   as reliance 1 pre-filter, 0 post-filter. Henry County (above) is the Court of Appeals of Georgia vacating a
   trial-court order; the relying order is not in the corpus.
5. **Partly fixed; a new bug.** In code now, and the cluster intersection is right (26 of 43). The name match is
   broken as described in the verdict. Recomputed (`confirm_flag_db.py`, threshold 85, captions with at least one
   token): **by caption 6** — *Morgan* (second order), *Jackson v. Auto-Owners*, *Carter v. UZGlobal*, *Schoene*
   (second document), *Virgil v. Experian*, *U.S. Bank v. Richmond*. **By hand, in the database under another
   caption or date: 6** — *Zaykariya* and *In re Nwaubani* (the two `HAND_DB` entries; confirmed in `charlotin.csv`);
   *Puerto Rico Soccer League* (84.2, the same case, D.P.R. 2025-09-23 order); *Qamar v. Board of Trustees of
   Governors State University* (N.D. Ill., opinion 11014134, 2025-05-06 = database "X v. Board of Trustees of
   Governors State University", N.D. Illinois 2025-05-06); *Flowz Digital* (the document is *Flowz Digital LLC v.
   Caroline Dalal*, C.D. Cal. 2025-05-05; the corpus caption says "v. Flowz Staffing"; database "Flowz Digital v.
   Caroline Dalal", same day); *Brick* (the document is *Jennifer Brick v. Gallatin County*, D. Mont. 2025-05-27; the
   corpus caption says "Brick v. Breuner"; database "Brick v. Gallatin County", same day). **In no field of the
   database: 5** — *Freeland v. Selene Finance LP* (M.D.N.C., opinion 10794526, 2025-02-05: "unable to locate either
   case … It is not clear the cases exist"); *Carrington v. Detroit Buildings Safety Engineering & Environment Dept.*
   (E.D. Mich., 10813927, 2025-02-27: "this case does not exist", twice); *Simmons v. City of Hurricane* (S.D. W. Va.,
   11216112, 2025-12-08: "unable to locate any case titled State ex rel. Cline v. Mazzone"); *Tarani-Alike Johnson v.
   Wells Fargo Bank* (N.D. Cal., 11236093, 2026-01-05: "multiple cases that the Court could not locate"); *Piper v.
   State of Indiana* (S.D. Ind., 11429405, 2026-08-27: suspected generative AI, cases that do not exist). Total in
   the database 26 + 6 + 6 = **38 of 43**.
6. **Fixed.** Labels carry `phantom-flag` (58 rows) and `phantom-party-asserted` (screened_flag k=115 *Younker*,
   k=156 *Dept. of Rev.*); screened_reliance k=141 and placebo_reliance k=247 are `real` with the Schwarzer F.R.D.
   note; `score()` counts `phantom-flag` as a flag on any sheet. Re-running the `assemble_verified.py` logic from the
   sheets and labels reproduces `data/screen/verified.csv` and `verified_misattributions.csv` byte for byte (1,036
   rows, 117 labelled; the tracked copies in `results/verification/` are identical to the `data/screen` files and
   labels). Label commit 9f6b26b 20:18:29 precedes `primary.json` (mtime 20:36:17) and the scoring commit 7a6e6b8
   (20:38:02).
7. **Fixed, one number wrong.** 43 court-flagged opinions (58 citations, 43 clusters, re-counted from
   `verified.csv`) plus 2 party-asserted, no overlap. 2019–2022 is qualified in the results ("none among the 116
   flag-sheet opinions … the only court flags there are of litigants' miscited real cases") and in the F2 caption;
   the one-liner in "What this does and does not show" leans on that context. But "43 opinions … are 42 cases" is
   wrong: *Morgan* (clusters 9818300 of 2023-10-23 and 9818576 of 2024-01-19) and *Schoene* (10617263 of 2025-06-25
   and 10637166 of 2025-07-18) each contribute two documents, so **41 cases**; and Schoene's second is an "Amended
   Opinion and Order" 99.8% identical to the first, i.e. a re-issue rather than a second finding (the author may
   prefer to count 42 opinions, 41 cases).
8. **Fixed.** The reporter table matches `primary.json` `reporters` (WL 650,612/1; F.4th 9,252/0; F. Supp. 3d
   22,061/209; Cal.App.5th 8,438/28; So.3d 4,229/0; A.3d 4,076/6; N.E.3d 2,049/1; F.3d 10,359/2,335; U.S.
   2,168/1,065; F.2d 1,981/696); 51% = 4,096/8,071.
9. **Fixed.** The shard-00 floor (≈0.15%, ≈1,200 of 836,076, the Texas Fifteenth Court of Appeals feed) and its
   bearing on the numerator are in "Party filings in the opinion corpus".
10. **Fixed.** D9 "Not delivered" records the empty `court` field (not repaired; re-run out of scope) and the
    uninformative Chapman estimate; `primary.json` `capture_recapture.note` says so.
11. **Fixed.** Labels (tracked as `results/verification/*.csv`; `data/` is a symlink outside the repository) and D9
    committed in 9f6b26b at 20:18:29; `charlotin_matched.csv` 20:20:03 after `match_charlotin.py` 20:19:35;
    `primary.json` 20:36:17 after `analysis.py` 20:29:57; scoring commit 20:38:02. `flag_vs_database.json` is now a
    section of `primary.json` written by `flag_vs_database()`.
12. **Partly fixed.** Reproduced against `primary.json`, `prepare_summary.json`, `charlotin.csv` and the sheets:
    1,665,327; 23.96 M; 859,471; 851,400 (99.1%); 8,071; sheets 3,182/3,646/202/116; 335 and 350 candidates;
    1,027,677 screened-period misattributions; 2,203 database rows; 9 judge-attributed in window, 5 matched; 879
    rows/869 clusters; 465 and 42; 0.51 per 10k (0.38–0.69); 0–40.2 → "40"; 832 → "roughly 830"; 58 citations; 117
    of 1,036 labelled; 26 by cluster; the F1 and F2 caption texts. Title and plain terms match the Inconclusive
    verdict. Wrong: "all 43 … in the database" / "adds no unrecorded incidents" / "15 more by caption" / "the last 2 by
    hand" (finding 5) in four places; "42 cases" (41, finding 7); "1,532 US incidents" (the `NON_US` regex passes 58
    rows whose `State(s)` is not USA — South Korea 8, Belgium 8, Poland 6, Costa Rica 6, China 5, … — none of which
    matched a cluster, so 879/869 stand; the US count is 1,474).

## New issues introduced by the fixes

1. **`flag_vs_database()` name match is vacuous; the "all 43 in the database" headline is wrong — Major.** Mechanism
   and recount above (`reviewer_checks/confirm_flag_db.json` has the per-cluster recomputation and hand-search hits).
   Fix: in `flag_vs_database()` skip database captions with no token (`if not tokens_of(d)`), or filter the database
   on `State(s)` containing "USA" rather than the `NON_US` regex (which also corrects the 1,532 → 1,474); re-run
   `analysis.py score`; put *Puerto Rico Soccer League*, *Qamar* ("X v. Board of Trustees …"), *Flowz Digital* and
   *Brick* into `HAND_DB` with the database captions above, keeping *Zaykariya* and *Nwaubani*; report 26 by cluster
   + 6 by caption + 6 by hand = 38 of 43 in the database and name the 5 that are not; reword the verdict bullet,
   "In plain terms", the F2 caption (`figures.py`) and the conclusions. The supportable statement is the mirror of the
   draft's: the database holds 38 of the 43, and the screen adds five court-flagged opinions it does not list.
2. **"42 cases" should be 41** (Morgan ×2, Schoene ×2; Schoene's second is an amended re-issue) — Minor.
3. **`us_incidents_in_window` = 1,532 includes 58 non-US rows** — Minor; no match among them, recall unaffected.
4. **Same-day caption rule: no false match.** The 14 incidents I can identify as matched only by the `contained`
   rule (score < 75, or < 85 with the best-scoring cluster more than 3 days away) are all 0 days apart with every
   distinctive database token in the corpus caption: *Koeberer v. Weir*, *Davenport v. Churilla*, *Hack v. Preston*,
   *Peterkin v. McIntyre*, *Henry County Schools v. Grant*, *Williamson v. Meyers*, *Yaroshevsky v. Karlin*, *McDowell
   v. Turpen*, *Labonte v. BOKF*, *Duncan v. Gridhawk*, *Dorsey v. Ponce*, *University Mall v. Okorie*, *Cowden v. US
   Treasury*, *Clerk of the Court v. Rangel*. Not new, but visible while checking: the pre-existing 75-point same-day
   rule accepts a few plainly wrong pairs (*The JAAW Group* at GAO ↔ *McBride v. Crossings at Tunica*, 83.9, 3 days;
   *Ex parte Bradley Thomas* ↔ a multi-defendant criminal caption, 75.7, 3 days; *Matter of Samuel* ↔ *Matter of Ethan
   M.*, 75.0) — 2–3 of 869, no effect on any conclusion; a note for a future run.
