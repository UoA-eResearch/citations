# Fabricated citations in US court opinions: courts catch litigants' fakes often, and a screen of 1.67 million opinions found no judge relying on one, but it could not have seen most

*Every US opinion in CourtListener's 2026-09-30 snapshot filed from 2019 to September 2026 (1,665,327 documents,
23.96 million full case citations) was screened for citations to cases that cannot be found by citation or by name.
The surviving candidates were verified by hand against the corpus and CourtListener's public search.*

**Verdict: Refuted by the preregistered rule; not robust.**

- **H1 (at least 20 opinions from 2023–2026 rely on a phantom citation): Refuted by rule.**
  - **The sample.** No verified case of a judge relying on a nonexistent authority. Of the 335 candidates in a
    seeded sample of 300 opinions, 332 were real cases mis-scored by the screen and one was an unidentifiable
    fragment. The other two sit in party filings, not opinions (D8). The sample was drawn from the 3,182 opinions
    with reliance-type candidates in reporter-volumes complete enough to judge.
  - **The interval.** The sample-based estimate is 0, but its 95% upper bound is **40 opinions**, which is above
    the Supported threshold.
  - **Recall.** It is poor for exactly this case. Of the 4 publicised judge-attributed incidents found in the
    corpus, none produced a reliance candidate.
  - **So.** The screen found none of the undetected judicial reliance the hypothesis predicts, but it cannot rule
    such cases out.
- **H2 (the 2019–2022 placebo period is near-empty): not scorable.** Both periods have zero verified reliance, so
  the ratio is undefined.
- **What the screen did find: courts catching litigants.** 45 opinions from 2023–2026 in which the court itself
  identifies a party's citation as nonexistent (0.54 per 10,000 opinions; 0.40–0.72). There are none in 2019–2022.
  19 of the 45 match no entry in the public AI-hallucination database.
- **And a corpus problem.** CourtListener's "opinions" include party filings: pro se motions with a judge's
  endorsement, a pro se bankruptcy filing, an appellant's reply brief. Two of these carry citations that exist
  nowhere. They are litigants' phantoms, not judges' (D8).

## In plain terms

Lawyers and self-represented litigants have been caught citing court cases that do not exist, often invented by AI
chatbots. A handful of judges have too. The worry behind this study is that the known cases are the tip of an
iceberg: that judges' opinions quietly rely on fake cases that nobody has noticed.

We screened every US court opinion from 2019 to September 2026 in the largest open archive, looking for cited cases
that cannot be found anywhere. After hand-checking a random sample of the suspicious ones, we found no judge relying
on a fake case. Nearly all the "suspicious" citations were real cases with typos, scanning errors or unusual citation
styles.

But the screen could not have caught most of the known judicial incidents either, so this is not proof that the
iceberg does not exist. What the screen found plainly was the other side of the problem: 45 opinions since 2023 in
which a court calls out a litigant's fake citations, none before 2023. Nineteen of those are not matched in the main
public list of such incidents.

## What was asked

The lead (`legal-digital-humanities-phantom-citations-judicial-opinions`) proposed a systematic screen of judicial
opinions, not filings, for citations to nonexistent authority. The public record of AI-hallucinated citations
(Charlotin's database: 2,203 incidents on 2026-10-21; about nine US matters attributed to a judge) is
incident-driven. It counts what someone noticed. The plan (`plan.md`, committed before any opinion text was
extracted) set two tests:

- **H1:** at least 20 verified opinions filed 2023-01-01 to 2026-09-30 that *rely* on a phantom citation (Supported
  if at least 20; Refuted if fewer than 10).
- **H2:** a placebo-period (2019–2022) reliance rate at most a quarter of the screened-period rate.

Opinions that *flag* somebody else's bad citation are the known phenomenon and are reported separately.

## How it was done

1. **Index.** 17.6 million citation rows (reporter-volume-page to case) and 10 million case names from the
   CourtListener bulk data (D1–D3).
2. **Screen** (`screen_shards.py`; frozen at D6, rescheduled in chunks at D7, 743 minutes on 26 workers).
   - eyecite extracts every full case citation in 1,665,327 opinions dated 2019-01-01 to 2026-09-30.
   - Each citation is resolved by reporter-volume-page. A resolved citation whose cited name shares a distinctive
     token with the case found there is consistent.
   - Otherwise the cited name is searched across all case names, with abbreviations expanded (D6). A citation that
     neither resolves to a matching case nor matches any name is a candidate: 859,471 of them (35.9 per 1,000
     citations).
3. **Completeness filter (preregistered).** Only citations into reporter-volumes where at least 98% of known pages
   are present can be phantoms; coverage is measured leave-one-opinion-out (D6). This drops 851,400 candidates
   (99.1%) and keeps 8,071.
4. **Reliance or flag**, by a fixed list of context words (sanction, fictitious, non-existent, AI, ...).
5. **Verification sheets** (`analysis.py prepare`). Every opinion is verified up to 300 per sheet; above that, a
   seeded random sample of 300. The screened-reliance sheet (3,182 opinions) and the placebo-reliance sheet (3,646)
   were sampled. The screened-flag (202) and placebo-flag (116) sheets were verified in full, as was a sample of 100
   misattributions.
6. **Verification** (D8). Each candidate was read with the index's names at the cited page (`verify_aid.py`, a
   reading aid). Doubtful ones were looked up in CourtListener's public search.
   - A case is **real** if the index or CourtListener holds it under the cited or a corrected citation, if
     independent opinions cite it, or if an official reporter lists it.
   - A citation is a **phantom** only if the case is found nowhere.
   - Courts' own statements that a case does not exist verify flag-type phantoms.
   - The document holding every phantom was read to confirm it is an opinion.

## Results

### The sample of reliance candidates (`results/figures/F1_funnel.png`)

Of the 335 candidates in the 300 sampled screened-period opinions, 332 were real cases and one was an
unidentifiable fragment. The remaining two sit in pro se filings that CourtListener holds as opinions (see below).
The real ones were mis-scored for four reasons:
- **Citation style the parser misread.** California's "(10th Cir. 1984) 732 F.2d 775" form made the cited "name"
  "10th cir". Other names came out as abbreviations: "DYFS v. A.W.", "NRDC v. FAA", "CREW v. FEC".
- **Typos by the courts themselves.** *Feist* cited as 499 U.S. 240 instead of 340. *Plyler v. Doe* as 457 U.S.
  2020. *Christiansburg Garment* as 484 U.S. 412 instead of 434. *Garamendi v. Henin* as 684 F.3d instead of 683.
  The sample holds 14 such volume or page slips and 3 wrong reporters.
- **OCR damage.** "Blurne v. State" for *Blume*, "Slricklana v. Washl ngton" for *Strickland*.
- **Index gaps.** Unpublished table decisions; cases missing from CourtListener. *State v. Liason*, 2026-Ohio-243,
  is missing from CourtListener but appears in the Ohio Reporter of Decisions.

In the placebo-period sample (350 candidates, 300 opinions) the picture is the same.

The verdict that follows from 0 of 300 is a sample-based estimate of 0 opinions (95% interval 0–40 of 3,182), and 0
of 836,076 screened-period opinions (per 10,000: 0–0.046).

### What the screen can and cannot see (recall)

- **Known incident orders.** Of 1,516 US incidents in Charlotin's database dated in the window, 854 were matched to
  an opinion in the corpus. For 453 of those (53%; 50–56%) the screen produced a candidate.
- **Judge-attributed incidents.** Four were matched in the corpus. None produced a candidate in a complete volume
  marked as reliance:
  - *H.C. v. Contreras* and *Payne v. State* produced no candidates at all.
  - *In re CorMedix* produced three Westlaw-only citations, outside the reporter index. That incident was mainly
    misquotation.
  - *Shahid v. Esaam* is an appellate opinion discussing the trial court's fakes, and it produced none.
- **Why so blind.** Most judicial incidents involve real cases misquoted or mischaracterised, or citations to
  Westlaw and neutral cites that the reporter index does not hold. Both are invisible to a screen that asks only
  whether a case exists. And the completeness filter, which is necessary to make a miss meaningful, discards 99% of
  candidates.

### Courts catching litigants (the flag sheets; `results/figures/F2_flagged_by_quarter.png`)

- **Screened period (2023–2026).** The 202 flag-sheet opinions were verified in full. In 45 of them the court
  identifies at least one cited case as nonexistent: 60 candidate citations, such as "Las Cruces Sun-News v. City of
  Las Cruces", "Petersen v. Iran Air", "Dowds v. Basehore", "Estate of Riddell v. City of Portland", and Missouri
  tables of "Fictitious citation" entries.
- **Placebo period (2019–2022).** The 116 flag-sheet opinions contain none. The only court-flagged citation there,
  "United States v. Kajakajian", is the real *Bajakajian* miscited.
- **The public database.** 26 of the 45 opinions are matched to a Charlotin entry; 19 are not. Some of the 19 may be
  listed there under a different order in the same case.

### Party filings in the opinion corpus

Reading the documents behind the candidates showed that CourtListener's opinion corpus includes papers that are not
opinions:
- a pro se motion carrying a magistrate judge's "Denied … SO ORDERED" endorsement;
- a pro se plaintiff's filing in the Bankruptcy Court for the Northern District of Texas;
- an appellant's reply brief in the Texas Fifteenth Court of Appeals, filed as a "combined opinion".

Two of these cite cases that exist nowhere (*El-Koury v. Hammer*, 198 S.W.3d 819; *Sterner v. Marriott Int'l*, 390
S.W.3d 599). They are recorded as litigants' phantoms and not counted. The share of filings among the 1.67 million
"opinions", and so in the rate denominators, was not measured.

### Misattributions

The 100 sampled misattributions are artefacts, with one exception. They are citations whose case is missing from the
index (Westlaw numbers, neutral citations, new F.4th cases), where resolution returned the case spanning that page.
The exception is a court noting that it "cannot locate the State v. Flores, 185 A.3d 1283 (Del. 2018) decision" a
party claimed it had issued.

## What this does and does not show

- **No hidden epidemic of judges relying on invented cases was found.** In a sample of the suspicious citations,
  every one traced to a real case.
- **But the instrument is weak where it matters.** The screen tests existence. Judicial incidents mostly involve real
  cases misused, or citations the index cannot resolve, and the completeness filter removes 99% of candidates to keep
  the remaining ones interpretable. The 0–40 interval and the 0-of-4 recall on judge incidents mean a modest number
  of undetected cases cannot be excluded. A better instrument would check quotations and holdings, not existence.
- **Courts calling out fabricated citations is real, recent and partly unrecorded.** There are 45 such opinions in
  the screened period, none in 2019–2022, and 19 not matched to the public database.
- **The corpus is not purely opinions.** Rates per 10,000 "opinions" have an unknown share of party filings in the
  denominator.
- **Adjudication.** All verification was done by the study's AI agent, which also wrote the screen. External lookup
  was CourtListener's public search, plus one official reporter.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - D1–D3: index construction, pilot fixes, the validator calling the screen's own `judge()`;
  - D4: the recall set;
  - D5: analysis parameters fixed before output;
  - D6: abbreviation-aware matching, coverage-based completeness, the freeze;
  - D7: chunked scheduling;
  - D8: verification rules, including party filings, applied while verifying and before scoring.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

`code/build_index.py`, `code/build_names.py`, `code/extract.py`, `code/screen_shards.py --workers 26`,
`code/analysis.py prepare`, `code/verify_aid.py` (reading aid), hand labels in `results/verification/` (copied from `data/screen/labels/`) assembled into
`verified.csv`, then `code/analysis.py score`. Outputs: `results/tables/prepare_summary.json`,
`primary.json`, `flag_vs_database.json`, `charlotin_coverage.json`, `detection_validation.json`.
