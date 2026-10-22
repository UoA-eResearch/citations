# Review: legal-phantom-citations-judicial-opinions (draft 09c9990)

Reviewer: independent adversarial review, 2026-10-22. Scripts and outputs in `review/reviewer_checks/`.
Only `review/` was written; nothing else in the study was touched.

## Verdict: **fix first**

The pipeline and the arithmetic are sound: I reproduced the completeness filter exactly (8,071 kept; all four sheet
sizes), the sampled interval (0 of 300 → 0–40.2 of 3,182), the per-10k rates, the 45 flag opinions (45 distinct
clusters), and 49 of 51 hand labels I re-checked, with no "real" that is a phantom. What is not sound is the
reading. The screen, as frozen, cannot see the fabrication pattern that appears in the known judicial incidents
(finding 2), its operative recall on known incident orders is 4.6%, not 53% (finding 3), and the report contradicts
`primary.json` on the judge incidents (finding 4). "Refuted by rule" is therefore not a defensible verdict line; the
verdict is Inconclusive (finding 1). The secondary headline, "19 of 45 not matched to the public database", is
wrong by about half (finding 5). None of this requires re-running the screen; it requires rewriting the recall
section, the verdict, and the flag-vs-database figure, and documenting the verification.

## Findings

### 1. H1 should be Inconclusive, not "Refuted by rule; not robust" — Major

- Evidence. `results/tables/primary.json` `screened_reliance.ci = [0.0, 40.2]`; my recomputation agrees
  (`wilson(0,300)` upper 0.01264 × 3,182 = 40.2). The interval covers the Refuted (<10), Inconclusive (10–19) and
  Supported (≥20) bands of `plan.md` §2. The plan's rule was written for a fully verified count; §5.2 says a sampled
  sheet is reported as a *sample-based estimate*, and an estimate whose interval spans all three bands cannot
  decide the rule. Findings 2 and 3 add that the population the sample speaks for (reliance candidates in complete
  volumes) excludes nearly all of the population H1 is about.
- The report (`report.md` line 7) says "Verdict: Refuted by the preregistered rule; not robust", and the
  review brief says the proposed tag is Inconclusive. Pick Inconclusive in the headline, the verdict line and
  `primary.json` (add a field recording that the rule was applied to a point estimate whose interval spans the bands).
- Fix. Verdict: **Inconclusive**. Keep "0 verified in a sample of 300 of 3,182 (95% upper bound 40)" as the result.

### 2. The frozen screen is blind to the fabrication pattern in the known judicial incidents, and the report's explanation of why is wrong — Major

I ran the frozen `parse.judge()` on the three in-corpus reviewing-court opinions that list a trial court's fictitious
cases (`reviewer_checks/judge_test.py`, output `judge_test.json`, `judge_test.log`):

- *H.C. v. Contreras* (opinion 11333339): the fictitious "Enrique M. v. Angelina V. (2005) 15 Cal.App.5th 788" is
  cited four times. eyecite returns an **empty party name** for the California "(year) vol Reporter page" format, the
  cite resolves into *Lopez v. Friant & Assocs.*, and `parse.py:175` (`if not ct or ...: verdict = "consistent"`)
  marks it **consistent** every time. Any fabricated California-format citation with a plausible volume and page is
  invisible to the screen. The report mentions the California format only as a source of false positives
  ("made the cited 'name' '10th cir'").
- *Shahid v. Esaam* (11086650): the court's appendix lists about twelve fictitious cases with full Georgia cites.
  The screen returns **0 phantom**: 10 **misattribution** (e.g. *Johnson v. Johnson*, 285 Ga. 408 → *Daniel v.
  State*; *Fleming v. Floyd*, 237 Ga. 76 → *Campbell v. State*; *Christie v. Christie*; *Mobley v. Murray
  County*; *Ramos v. Ramos*; *McRae v. McRae*; *Reynolds v. Reynolds*; *In the Interest of J.M.B.*), and
  **consistent** for *Brown v. Brown*, 264 Ga. 48 (resolved *Brown v. State*) and *Robinson v. Robinson*, 277 Ga. 75
  (resolved *Robinson v. State*) because `abbrev.shares_token` accepts one shared surname.
- *Payne v. State* (11320504): "Bryant v. State, 268 Ga. App. 362 … appears not to exist at all" → **misattribution**.

So for the three in-corpus documents that quote a judge's fabricated authorities, the screen produced no phantom
candidate before the completeness filter was even applied. None of these are Westlaw or neutral citations, and none
are misquotations of real cases; the report's explanation ("Most judicial incidents involve real cases misquoted or
mischaracterised, or citations to Westlaw and neutral cites …", `report.md` "Why so blind") is unsupported for 3 of
the 4 matched incidents. The mechanisms are: (a) empty cited name → consistent; (b) fabricated captions that reuse
common names land in the misattribution class (1,027,677 in the screened period, 100 sampled, never counted — the
D2 caveat realised); (c) one shared surname suffices for consistency.

- Fix. Report these three mechanisms with the examples above. State that on the in-corpus judicial-incident
  documents the screen's sensitivity to the fabricated citation itself is 0 of 3. Add the `not ct → consistent`
  rule and the California format to the limitations. A post hoc, clearly labelled sweep of misattributions with an
  "X v. X"/common caption and no shared token would be informative but must not feed H1.

### 3. Recall is reported pre-filter; the operative recall of the pipeline is 4.6%, and "flagged" does not mean the fabricated citation was flagged — Major

- `report.md`: "For 453 of those (53%; 50–56%) the screen produced a candidate." That is any candidate in the
  order, before the completeness filter. Re-deriving from `candidates.jsonl` (`reviewer_checks/scan_candidates.py`,
  `scan_candidates.json`): any-candidate 448 of 845 distinct clusters (the 453/854 counts rows; 9 clusters are matched
  by two incidents), but **after the completeness filter only 39 of 854 (4.6%; 95% 3.4–6.2%)** incident orders keep
  a candidate. The verified counts come from the post-filter sheets, so 4.6% is the recall that applies to them.
- "Flagged" is also permissive: *Henry County Schools v. Grant* (cluster 10873094, a Charlotin judge incident, see
  finding 5) has five candidates, all real cases in incomplete volumes (*Slay v. Ross*, 927 S.E.2d; *Atlanta Pub.
  Schools v. M.M.*, 926 S.E.2d; a WL cite) — none is a fabricated citation; *Shahid v. Esaam* lists twelve fakes and
  has no candidate at all. The 53% is an upper bound on detecting fabricated citations, not a measurement of it.
- The plan (§2, §4 step 6) promised recall-corrected counts; `primary.json` has `recall_corrected_screened_reliance
  = 0.0` using 0.53 and the report does not discuss correction. Dividing the sample upper bound by the operative
  recall gives roughly 40/0.046 ≈ 880 opinions, which is the honest statement of what the data cannot exclude.
- Fix. Report both recalls and say which one governs the verified counts; define detection as "a candidate for the
  fabricated citation" or label the 53% an upper bound; give the recall-corrected upper bound or say why not.

### 4. The report contradicts `primary.json` on the judge incidents, and three of the four "incidents in the corpus" are the reviewing court's opinion, not the opinion that relied — Major

- `primary.json` `recall_reliance = {judge_attributed_in_corpus: 4, flagged_as_reliance: 1}`; `report.md` verdict
  bullet: "Of the 4 publicised judge-attributed incidents found in the corpus, none produced a reliance candidate";
  review brief: "recall for judge incidents is 0 of 4". The 1 is *In re CorMedix* (opinion 11088208, the original
  2025-06-30 opinion): three reliance-type candidates, all Westlaw cites, dropped by the completeness filter
  (`scan_candidates.json` → `judge_candidates`). The results section says this correctly; the verdict bullet does not.
- I read the four matched documents (`reviewer_checks/pull_docs.py`, `pulled_docs.json`). *H.C. v. Contreras*
  (Cal. Ct. App. 5th), *Payne v. State* (Ga. Sup. Ct.) and *Shahid v. Esaam* (Ga. Ct. App.) are appellate opinions
  describing a *trial court's* order that relied on fictitious cases; those trial-court orders are not in
  CourtListener. Only CorMedix is itself the relying document. The "reliance recall" test therefore has n = 1, and
  that one was caught as reliance before the filter and lost only to the Westlaw exclusion.
- Fix. Correct the bullet to match `primary.json`; say that 3 of the 4 matched documents are flag-type by nature and
  that the relying orders are absent from the corpus; report reliance recall as 1 of 1 pre-filter, 0 of 1 post-filter.

### 5. "19 of the 45 not matched to Charlotin" is overstated by about half; the matcher has a bug and a design limit — Moderate

- `flag_vs_database.json` (26 / 19) has no code; it is a cluster-id intersection with `charlotin_matched.csv`.
  A date-free re-match of the 19 by case name (`reviewer_checks/flag_counts.py`, `flag_counts.json`) finds **at least
  11 of the 19 are the same case in the database**: *Puerto Rico Soccer League v. Federación*, *Jackson v.
  Auto-Owners*, *Gittemeier v. Liberty Mutual*, *Carter v. UZGlobal*, *Schoene v. Oregon DHS*, *Virgil v. Experian*,
  *In re Nwaubani*, *U.S. Bank v. Richmond*, *Morgan v. Community Against Violence* (two orders), *Zaykariya v.
  Freedom Mortgage*; *Flowz Digital* (same day, C.D. Cal.) is probable.
- Causes: (a) `match_charlotin.py` keeps only the nearest-dated cluster of a case, so a second order in the same
  case is "unmatched"; (b) the ±45-day window; (c) the `NON_US` regex contains `Mexico`, so every New Mexico court
  is treated as foreign — 16 in-window incidents dropped (`D. New Mexico` 13, `CA New Mexico` 2, `New Mexico SC` 1),
  which is why both *Morgan* orders are "unmatched" and why "1,516 US incidents" should be about 1,532; (d) the
  side-by-side scorer rejects same-day exact cases whose captions carry extra names (*Henry County Schools v. Grant*,
  score 62.5, 0 days — a **judge-attributed** incident, so judge incidents matched should be 5 of 9, not 4 of 9).
- The report's "19 … match no entry" and the plain-terms "Nineteen of those are not matched in the main public
  list" / "partly unrecorded" are not supported. At most 7–8 of the 45 are absent, and that was not hand-checked.
- Fix. Match by case (any order, any date), fix the regex, re-run `match_charlotin.py`, recompute recall and the
  flag-vs-database numbers, put the computation in `analysis.py`, and reword.

### 6. Verification is under-documented; my re-check agrees with 49 of 51 labels, and the two disagreements are the same misidentified item — Moderate

- Of 1,236 sheet rows, 1,118 carry no verdict or note in `data/screen/labels/*.csv`; `verified.csv` defaults them to
  "real". File times: sheets 11:34:07, aid 11:35:19, labels 11:45–12:01, `deviations.md` (D8) and `verified.csv`
  12:01:23, `primary.json` 12:05:56 — 1,236 rows plus 100 misattributions in 26 minutes, including the CourtListener
  lookups the report says were done for doubtful rows. The record cannot show that each unlabelled row was read.
- I re-verified 113 rows (`reviewer_checks/build_reverify.py`, `reverify_rows.tsv`, results in
  `reverify_results.tsv`): all 60 phantom rows, the 3 party-filing rows, the 2 unverifiable rows, and a seeded sample
  of 48 "real" rows (36 unnoted defaults, 12 noted) across the four sheets, using the index aid, the context and the
  corpus. Every sampled "real" is right: court typos (*Feist*, *Plyler*, *Christiansburg*, *Chiron* "11236",
  *Enslin* 237→327, *PETA v. Berosini* 394→894 P.2d, *State v. Weddle* "2000 ME 12"), OCR (*Slricklana*,
  *Baciley*, *Lundstrorn*, *Baghat*), parser artefacts ("Due Process Clause" for *Sandin*, "10th cir" for
  *Fratus*), unpublished table pages, and two courts flagging real cases miscited by litigants (*Hatahly*,
  *Kajakajian*). No "real" is a phantom. Two rows are unresolved only because CourtListener throttled my
  requests (placebo_reliance k=308, placebo_flag k=8; both read as real).
- The two **unverifiable** rows (screened k=141, placebo k=247, both "99 F.R.D. 465, 487-88 (1984)" with a garbled
  name) are the same identifiable item: Schwarzer, *Summary Judgment Under the Federal Rules: Defining Genuine Issues
  of Material Fact*, 99 F.R.D. 465 (1984) — an article in F.R.D., not a case. Label should be real/not-a-case (like
  the "97 A.R. 26" row). No count effect.
- The three party-filing documents were read (`pulled_docs_party_filings.json`): a pro se motion with a magistrate
  judge's "Denied … SO ORDERED" endorsement (S.D.N.Y.), a pro se "Memorandum of Authorities" (Bankr. N.D. Tex.) and
  an appellant's reply brief e-filed in the Texas Fifteenth Court of Appeals. D8 rule 3 is correctly applied.
- Fix. Record a verdict and a one-line reason for every row (even "real: index holds X at the cited page");
  relabel the two F.R.D. rows; state the verification pace plainly in the report's Adjudication paragraph.

### 7. Flag-type phantoms rest on the court's statement; a few rest on a party's — Moderate

- D8 rule 2 verifies a flag-type phantom from the opinion's own statement that the case does not exist. For
  screened_flag k=156 (*Dept. of Rev. v. Sec'y of State*, 16 OTR 350) the context is the *defendant's* request for
  sanctions "for Plaintiff citing 'a case that plainly does not exist'"; for k=115 (*Younker v. Farmers Ins.*) it is
  "Gittemeier also points out that two supposed cases … do not exi[st]"; k=161 (*McEwen v. McCullough*) is a list of
  "suspected" AI citations. The notes record "not on CourtListener" for only 3 of the 60 phantom rows.
- The other 57 read as the court's own finding ("The Court has been unable to locate", "does not exist", "Fictitious
  citation" tables) and the index holds a different case at each cited page. My CourtListener name lookups
  (`reviewer_checks/cl_lookup2.py`, `cl_lookup2.jsonl`) were throttled (HTTP 429, then timeouts) and completed for
  11 rows. Five phantom names return nothing (*Tatum v. Oklahoma City*, *Chilson v. Experian*, *Gen. Wire Spring v.
  O'Neal Steel*, *Petersen v. Iran Air*, *El-Koury v. Hammer*), as do *Matter of UFT v. Bd. of Educ.* and the two
  F.R.D. rows. One is borderline: for k=28/29, "Las Cruces Sun-News v. City of Las Cruces (2003-NMCA-099)", which the
  court calls "fake" (2003-NMCA-099 is *State v. Foster*), CourtListener holds *Board of Commissioners v. Las Cruces
  Sun-News*, 2003-NMCA-102, 134 N.M. 283 — a real case with a near-identical caption three numbers away. Under D8
  rule 1 ("a real case cited at a wrong citation is real, however wrong the citation") this could as well be a
  litigant's garbled real case; the court did not look for one. Reclassifying it would make the flag count 44.
- `analysis.score()` keys the H1 count on the sheet's regex type, not the hand label, so a court-flagged phantom
  that the FLAG regex missed (it misses "does not appear to exist": *Hatahly* sits on the placebo reliance sheet)
  would count as judicial reliance if labelled "phantom". No such row occurred, but the vocabulary needs a
  `phantom-flag` verdict.
- Fix. For k=115, 156, 161 show the court's own finding or an external check, or mark them "party-asserted";
  add `phantom-flag` to the label vocabulary and honour it in `score()`.

### 8. The completeness filter keeps a corpus of mostly pre-2020 federal citations — Moderate (interpretation)

- The leave-one-opinion-out computation is correct: I reproduced 8,071 kept and the four sheet sizes exactly.
- What survives (`scan_candidates.json`): F.4th **0 of 184** assessable volumes complete (9,252 candidates dropped,
  0 kept); WL 0 of 66 (650,611 dropped); So.3d 2/433, N.E.3d 1/267, A.3d 12/358, N.W.3d 0/36, P.3d 71/592;
  F. Supp. 3d 338/831 (21,852 dropped, 209 kept); Cal.App.5th 28 kept, 8,410 dropped. Of the 8,071 kept, 51% are
  F.3d, U.S. and F.2d, 67% are in those plus the other "2d" series, and 96% are "resolved-elsewhere", i.e. a cite that
  lands in a real case with a different name — typos and misparsed names in well-covered volumes.
- The threshold is fragile at the margin: 905 F. Supp. 2d (*Petersen v. Iran Air*) is 97.5% covered and the Mata
  sanctions opinion's Petersen cites survive only because that opinion cites it three or more times (leave-one-out).
- Fix. State in the report which reporters survive the filter and that H1's effective population is citations into
  older federal reporters and U.S. Reports; D6 says this qualitatively, the numbers should be given.

### 9. Party filings: a measurable floor, concentrated in one court's feed — Minor

- Shard 00 (1/32 of the corpus; `reviewer_checks/party_filing_scan.py`, `party_filing_scan_00.json`): 50 of 26,077
  screened-period documents (0.19%) carry two or more filing markers (caption, "Respectfully submitted",
  "Certificate of Service"); about 40 are filings on reading (precision ≈ 0.8; the Court of Federal Claims special
  master decisions are false positives), recall unknown. So a floor of about 0.15%, ≈ 1,200 of 836,076 documents.
  Most are e-filed briefs, petitions and docketing statements in the **Texas Fifteenth Court of Appeals**
  ("ACCEPTED … FILED IN 15th COURT OF APPEALS", 25+ of 50), plus S.D.N.Y. memo-endorsed pro se motions, Texas
  district-clerk records and attorney stipulations. 13 random documents were all opinions.
- Negligible for the per-10k denominators; material for the numerator, since 2 of the 3 phantom-type items in the
  reliance samples sit in such filings. Exclusion from judicial reliance is justified and consistently applied.
- Fix. Report the floor and the concentration; exclude documents opening with an e-filing banner in any re-run.

### 10. Plan items not delivered or not recorded — Minor

- Plan §4 step 8 promised rates "by court level and year". The `court` column of `opinions.tsv` is empty for all
  1,665,327 rows (`screen_shards.py:58` passes `""`); no by-court result exists and `deviations.md` does not say so.
- Capture–recapture (`primary.json` Chapman N = 4) is not mentioned in the report; say it is uninformative.

### 11. Provenance — Minor

- Checked (`git log`): plan 5f2176d 08:12 → index 326182c 08:41 → extraction 54eea59 17:52 (plan preceded
  extraction ✓); `VERIFY_ALL_UP_TO = 300` and `SEED = 20261021` present in 88925c2 (D5, 10:34 on the 21st), sheets
  written 11:34 on the 22nd ✓; D6 freeze cbeaf02 20:11 → D7 e3113ec 23:08 → screen 23:08–11:30 (`screen_full.log`
  742 min); `parse.py`, `namenorm.py`, `abbrev.py`, `analysis.py` unchanged after cbeaf02, `screen_shards.py`
  changed only in scheduling ✓.
- D8, the labels, `verified.csv`, `primary.json`, `flag_vs_database.json` and the report are all in one commit
  (09c9990); their order rests on file mtimes only (labels 11:45–12:01, D8 12:01:23, score 12:05:56). The 453/854
  recall uses rows not clusters (845 distinct). `flag_vs_database.json` has no generating code.
- Fix. Commit labels before scoring; add the flag-vs-database step to `analysis.py`.

### 12. Report numbers and wording — Minor

- Reproduced: 1,665,327 documents; 23,964,173 citations; 859,471 candidates (35.86/1,000); 851,400 dropped
  (99.06%); 8,071 kept; sheets 3,182/3,646/202/116; 335 and 350 sampled candidates; 332/1/2 split; 14 volume/page
  slips and 3 wrong reporters in the labels; 45 flag opinions = 45 clusters, 60 citations, 0.538/10k (0.402–0.720);
  0 placebo flags; 99 index-artefact misattributions + 1; 17.6 M citation rows; 10.17 M names; 743 minutes.
- Wrong or overstated: "none produced a reliance candidate" (finding 4); "19 … not matched"/"partly unrecorded"
  (finding 5); "1,516 US incidents" (New Mexico excluded); "453" (rows, not clusters); the recall paragraph
  (finding 3). "None in 2019–2022" for courts flagging should say none *flagging a nonexistent case in a complete
  volume*: two placebo rows are courts flagging litigants' miscited real cases (*Hatahly* 2019, *Kajakajian* 2021),
  and one of them was missed by the FLAG regex. "Courts catch litigants' fakes often" (title) is editorial for 45
  opinions in 45 months; "45 since 2023, a floor" is the supportable statement. The *Morgan* case contributes two
  of the 45 opinions (two orders), so 45 opinions is 44 cases.

## Answers to the brief's seven checks

1. Verification: 113 rows re-checked; "real" calls on typos and OCR are right; no "real" is a phantom; two
   "unverifiable" rows are an identifiable F.R.D. article (finding 6); three flag phantoms rest on a party's
   assertion (finding 7).
2. H1: arithmetic correct; verdict should be Inconclusive (finding 1).
3. Recall: 453/854 reproduces (448/845 distinct) but is pre-filter and permissive; post-filter 39/854 (4.6%);
   the "0 of 4" conflicts with `primary.json` (1 of 4 pre-filter) and three of the four documents are not the
   relying opinions; the stated explanation (Westlaw, misquotation) is wrong for them — the screen marks the
   fabricated cites consistent (empty California name, shared surname) or misattribution (findings 2–4).
4. Completeness filter: computed correctly (reproduced); it removes F.4th, WL, F. Supp. 3d and the modern state
   reporters almost entirely (finding 8).
5. Flag counts: 45 opinions, 45 clusters, no double counting; "19 not matched" is wrong by about half (finding 5).
6. Party filings: exclusion justified and consistent; floor ≈ 0.15% of documents, concentrated in the Texas
   Fifteenth Court of Appeals feed (finding 9).
7. Report: numbers reproduce except as listed in finding 12; the headline is supported only as "no judicial
   reliance found in a sample the instrument could barely see"; the "19 unrecorded" headline is not.

## Files

- `reviewer_checks/scan_candidates.py` → `scan_candidates.json`, `.log` (filter, recall, judge candidates, reporters)
- `reviewer_checks/build_reverify.py` → `reverify_rows.tsv`; `reverify_results.tsv` (reviewer's call per row)
- `reviewer_checks/cl_lookup.py`, `cl_lookup2.py` → `cl_lookup_partial.jsonl`, `cl_lookup2.jsonl` (throttled)
- `reviewer_checks/flag_counts.py` → `flag_counts.json` (45 flag opinions; date-free Charlotin re-match)
- `reviewer_checks/party_filing_scan.py` → `party_filing_scan_00.json`, `.log`
- `reviewer_checks/pull_docs.py` → `pulled_docs_party_filings.json`, `pulled_docs.json` (judge-incident documents)
- `reviewer_checks/judge_test.py` → `judge_test.json`, `judge_test.log` (frozen screen on the three flag opinions)
