# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-21 08:41 NZDT — building the resolution index, and what it showed about detection

Recorded while building the index, before any opinion text had been extracted.

1. **Out-of-range rows in the citations table.** Of 18,130,236 rows, 60,250 do not parse as integers (page
   numbers like `1339n`, blank volumes) and 511,529 carry values outside any plausible range — one page number
   is 5,837,932,014. Both groups are dropped and counted; the index holds 17,558,456 rows across 73,055
   reporter-volumes.
2. **Page resolution alone would miss the canonical fabrication, so name matching carries the detection.**
   The best-known hallucinated citation in the field — *Varghese v. China Southern Airlines Co.*, 925 F.3d 1339,
   invented in the filings behind *Mata v. Avianca* — **resolves**: page 1339 of volume 925 F.3d falls inside a
   real case that begins at page 1291. A screen that only asked "does this volume and page exist?" would clear
   it. The same is true of *Petersen v. Iran Air*, 905 F. Supp. 2d 121, which is an exact first-page match to a
   real but different case.

   This does not change the hypotheses or the definition of a phantom citation in `plan.md` §1, which already
   requires that no case be findable *either* by reporter-volume-page *or* by name, and it is the behaviour the
   plan's "misattribution" class anticipated. It does change which step does the work: the case-name lookup
   (plan §4 step 4) is the primary detector, not a refinement on top of citation resolution. In consequence:

   - the reporter-volume completeness filter matters less than expected for the dominant detection route, since
     most fabrications mimic a real citation format and land inside a covered volume;
   - the binding coverage question becomes whether the *cluster name index* is complete enough to support "this
     case name exists nowhere", which depends on the opinion-clusters snapshot rather than the citations table;
   - a citation whose numbers resolve but whose party names match nothing anywhere is the signature to hunt, and
     the verification burden shifts accordingly.

   The completeness filter is still applied as preregistered, and the share of candidates it removes will be
   reported, but the report will state plainly that it is not what finds the fabrications.

## D2 — 2026-10-21 09:30 NZDT — validating the screen on known cases, three defects fixed, and the parameters frozen

Run before any opinion was screened, using only the six citations invented in the *Mata v. Avianca* filings and
four well-known real cases (`code/validate_detection.py`, `results/tables/detection_validation.json`).

**Three defects, each of which would have distorted the count:**

1. **The index builder and the lookup used different stopword lists.** The builder omitted "board", so the
   lookup was told no case name contains it and reported *Brown v. Board of Education* as a case that does not
   exist. At scale this manufactures phantom citations out of ordinary captions. Both now import one definition
   (`code/namenorm.py`), and the stoplist is cut to connectives that carry no identity.
2. **A token too common to index looked the same as a token found nowhere.** Five tokens exceed the posting cap
   and are dropped (`inc`, `people`, `state`, `states`, `united`). Absence from the index meant either "in too
   many names to help" or "in no name at all" — opposite things. The dropped list is now recorded
   (`data/index/dropped_tokens.json`); lookups skip dropped tokens and report genuinely absent ones as evidence.
3. **Whole-name fuzzy scoring let a shared defendant carry the match.** *Martinez v. Delta Airlines* scored 90.9
   against *Doe v. Delta Airlines Inc* although the plaintiffs have nothing in common. Names are now scored side
   by side, the weaker side deciding, both orderings tried (`party_score`).

**Result after the fixes:** five of the six fabrications are reported as no such case; all four real cases are
found. The sixth, *Miller v. United Airlines*, 174 F.3d 366, is correctly *not* a phantom under plan §1: a real
*Miller v. United Airlines* exists in the corpus, at a different citation, while 174 F.3d 366 points into an
unrelated case. That is the plan's misattribution class (§4 step 4).

**Misattributions are now recorded as a secondary class**: a citation that resolves to a case whose name is
unrelated (side-by-side score below 50) while the cited name exists elsewhere. They do not count toward H1 and
will be reported separately, verified on a sample, because fabrications that reuse a common name land here
alongside ordinary wrong-volume errors.

**Frozen from this point**, before any opinion is screened: name-match threshold 80, misattribution cut 50,
the stoplist and posting cap in `namenorm.py` and `build_names.py`. The screen was adjusted on these ten
examples, so five of five is an in-sample figure and is reported as such. The independent check is the recall
calibration on Charlotin incidents present in the corpus (plan §4 step 6); that is a measurement and will not
be used to retune the screen.

## D3 — 2026-10-21 10:29 NZDT — the CSV dialect, a pilot on out-of-window opinions, and the freeze moved

D2 declared the screen frozen. That was premature: its first run on real opinion text, below, exposed problems
the ten validation cases could not. The freeze now applies from the end of the in-window pilot described at the
end of this entry, still before any in-window opinion is screened for counting.

**1. The bulk files' CSV dialect.** CourtListener writes its bulk CSVs with PostgreSQL `ESCAPE '\'`, so a quote
inside a field is `\"`, not doubled. Read with Python's default, a 315 MB sample of opinions — HTML-heavy text —
came back as 1,104,813 rows instead of 12,439. All readers now go through `code/clcsv.py`, with `newline=''` on
every stream. Both indices were rebuilt and compared with the old ones: across the whole snapshot the default
dialect had lost **1** cluster (outside the study window) and added 100 spurious ones; the citation index was
unchanged (numeric fields only). An earlier extrapolation of about 1,800 lost clusters, from a 400 MB sample, was
wrong — the sample had been cut mid-row. No opinion had been screened, so no result was affected.

**2. A pilot on out-of-window opinions.** The first downloaded part of the opinions archive decompresses on its
own and holds 12,438 opinions — 84% OCR'd, almost all filed before 2020, so outside the study window. Screening
1,500 of them flagged **99.5 phantom candidates per 1,000 citations**, far too many to verify. Four causes, each
fixed in shared code:

- *Noisy extracted names.* eyecite's party names carry bracketed years, star-page markers and leading citation
  signals (`Carlton v. Board [1969]`, `*464 Stratman`). They are now cleaned (`clean_cited`).
- *Intersecting the rarest tokens.* A single junk token — a year — could be the rarest and empty the candidate
  pool, scoring a real case 0. Candidates are now the union of the three rarest tokens' postings.
- *Whole-name consistency on the resolved route.* A correct citation with a noisy name failed to match its own
  case. The test is now whether any distinctive cited token appears in the resolved case's name. Checked first
  against the three *Mata* fabrications that resolve by page: each lands in an unrelated case (*J.D. v. Azar*,
  *United States v. ISS Marine Services*, *Greenleaf v. Garlock*) sharing no distinctive token.
- *One-word captions.* A cluster captioned just "petersen" scored 100 against "petersen v iran air", since a
  single word is a subset of any name containing it. A one-sided candidate must now match each cited party.

After the fixes the pilot flags **24.4 per 1,000**, all in OCR'd opinions citing nineteenth-century reporters,
and they read as OCR misspellings of real names: "thallhiner v brinkerhoff" against *Thalimer v. Brinkerhoff*
(77.8), "ewen v hobbs" against *Owen v. Hobbs* (75.0).

**3. Validation now tests the screen's own code.** The decision for one citation is a single function,
`parse.judge()`, and `validate_detection.py` calls it rather than reimplementing it. Of the six *Mata*
fabrications, four are phantoms and one (*Miller*) a misattribution; none of the four real cases is flagged.
*Martinez v. Delta Airlines* is missed: it matched *Martin v. Trans World Airlines Inc* at exactly the threshold,
80.0. It was deliberately **not** tuned away — that would be fitting the screen to one of its own ten test
cases. The screen resolves ambiguity toward "this case exists", so the phantom count it produces is a lower bound.

**4. Next, before the freeze:** a seeded random sample of 2,000 in-window opinions (2019-2026) will be drawn as a
pilot once the archive is complete. Tuning may use it and the out-of-window pilot only. The screen is then frozen,
and the full in-window screen run once. Manual verification remains the arbiter of every count.

## D4 — 2026-10-21 10:33 NZDT — building the recall-calibration set

Recorded before any opinion was screened. Nothing here touches the screen or the hypotheses; it fixes which
publicised incidents are used to *measure* the screen (plan §4 step 6).

1. **A larger calibration set than planned.** The plan anticipated calibrating on the roughly nine US
   judge-attributed incidents. But the Charlotin database's lawyer and pro se incidents mostly have a court order
   that discusses — and often quotes — the fabricated citations, so their orders are true positives for the
   *detection* step too. There are 1,516 plausibly US incidents dated inside the screened window. Recall is now
   measured two ways: **detection recall** (of the in-corpus orders discussing fabricated citations, the share
   the screen flags), and **reliance recall** (of the judge-attributed incidents, the share it flags as
   reliance rather than flag). These orders are flag-type by construction, so they also test the reliance/flag
   classifier's specificity.
2. **Matching incidents to clusters** (`code/match_charlotin.py`): party names scored side by side, filing date
   within 45 days. The name threshold is 85, stricter than the screen's 80, because a false calibration match
   would bias recall downward. An audit of borderline matches showed that 85 alone misses clear same-day matches
   (*Adams v. Board of Trustees* at 82.8; *Bell v. City of Clairton* at 84.2), whose corpus captions carry first
   names the database omits. A score of 75 is therefore accepted when the dates agree within three days. This
   added 46 matches; a seeded random audit of 12 found 11 plainly correct and one uncertain (*Twyla Leach*: same
   plaintiff and day, different defendant, possibly another case by the same litigant).
3. **Coverage:** 854 of the 1,516 in-window US incidents match a corpus cluster (56%), and 4 of the 9
   judge-attributed ones. The 44% not found are themselves informative — CourtListener does not hold every
   order — and bear on the capture-recapture estimate, which assumes both sources could in principle see a case.

## D5 — 2026-10-21 10:34 NZDT — analysis parameters fixed before any output

Set in `code/analysis.py`, committed before the screen has produced a single in-window candidate.

1. **Completeness needs enough citations to estimate.** Plan §1 sets the threshold at 98% but not how many
   citations a reporter-volume must receive before that rate means anything; a volume cited once and resolved
   once is "100% complete". A volume must receive at least **20** citations across the screened opinions to be
   assessed; below that it is unassessable, and candidates into it are dropped and counted.
2. **Sheet size.** Every opinion on a verification sheet is checked by hand up to **300**; above that, a seeded
   random sample of 300 opinions is verified and the count scaled, with a Wilson interval (plan §5.2).
3. **The flag classifier is measured, not assumed.** Reliance and flag are split by a lexicon on ±400 characters
   of context (fabricated, nonexistent, hallucinated, sanction, show cause, ChatGPT and the like). Some of these
   words occur for unrelated reasons, so a genuine reliance phantom near one would be routed to flag and silently
   leave the H1 count. The plan verifies only the reliance sheet in the screened period; the screened flag sheet
   will also be verified on its sample, recording for each whether it is truly flag-type, to measure that rate.
4. **Misattributions** are verified on a fixed seeded sample of 100 in the screened period and reported
   separately; they never count toward H1.

## D6 — 2026-10-21 20:11 NZDT — the in-window pilot, two more fixes, and the freeze

The seeded pilot of 2,000 in-window opinions (D3 item 4; seed 20261021; 28,620 full citations) was screened three
times while tuning. Tuning used only this pilot and the out-of-window pilot of D3. No other in-window opinion has
been screened.

**Run 1 (screen as frozen in D3):** 53.1 phantom candidates per 1,000 citations. Restricted to reporters that
resolved at least 98% of pilot citations, 90 candidates in 74 opinions remained, and every one read as a real case.
There were four causes:

- *Bluebook abbreviations.* "Mo. Pac. R.R. v. R.R. Comm'n of Tex." shares no token with the corpus's "Missouri
  Pacific Railroad v. Railroad Commission of Texas", and "Hosp. Bldg. Co. v. Rex Hosp. Tr." failed because "rex" is
  under four letters and "hosp" is not "hospital".
- *Misspellings in the opinion*, e.g. "Hotzclaw" for Holtzclaw and "Lownschuss" for Lowenschuss.
- *Truncated party names from eyecite.*
- *Real cases the corpus lacks.* A citation to a missing case still "resolves" by landing inside a neighbouring
  case's page range (*J.K.J. v. Polk County* landing in *United States v. Smithers*).

**Fix 1, `code/abbrev.py`.** A cited token now matches a corpus token in three further ways:
- through a table of Bluebook abbreviations;
- as a prefix of four letters or more;
- by near-identity (rapidfuzz ratio ≥ 85, both tokens five letters or more).

Abbreviations standing only for generic words (company, state, county and the like) or for tokens too common to
index are not used. The name search also runs on the name with abbreviations spelled out, and the better score is
kept. **Run 2:** 39 candidates in 34 opinions among the same reporters, and again every one read as a real case. Most
were cases the corpus lacks, so the citation landed in another case's page range.

**Fix 2, completeness measured as coverage.** Plan §1 defines a complete reporter-volume by whether the cited pages
are present in the corpus. D5 put that into practice as "at least 98% of citations into it resolve", but resolution
counts page-range landings, so volumes with missing modern cases passed. A citation now counts as **covered** when
the screen finds its case in the corpus, either by citation (verdict consistent) or by name (name-exists). A
volume is complete for a candidate when at least 98% of at least 20 citations into it are covered. The candidate's
own opinion's uncovered citations into that volume are left out, so one fabricated citation cannot disqualify its own
volume. **Run 3:** 86.5% of pilot citations are covered. Of the 89 volumes with at least 20 pilot citations, 42 reach
98%, most of them U.S. Reports volumes.

**Fix 3.** Ohio-style docket tails that eyecite keeps in the defendant's name ("8th Dist. Cuyahoga No. 94458",
"Franklin App. No.", "Case No.") are stripped.

**Validation after each fix:** unchanged. Of the six *Mata* fabrications, four are phantoms and one a
misattribution, and none of the four real cases is flagged. *Martinez* is still missed and was again not tuned.

**What this costs.** The screen is now confined to reporter-volumes that the corpus covers almost completely.
Fabricated citations into thinly covered modern volumes (F.4th, F. Supp. 3d, many state reporters) cannot produce a
finding. The Charlotin calibration (plan step 6) measures that loss of recall, and the counts remain a lower bound.

**Freeze.** `parse.py`, `namenorm.py`, `abbrev.py`, `screen_shards.py` and `analysis.py` are frozen at this
commit. The full in-window screen is run once from it.

## D7 — 2026-10-21 23:08 NZDT — the full screen rescheduled in chunks (no decision changed)

The first launch of the full screen (one task per shard: 32 shards on 22 workers) had read about a third of each of
its first 22 shards after three hours. The last 10 shards would then have run as a second wave on 10 workers, for
roughly 17 hours in all. It was stopped. No output had been written, since results were only returned at the end.

`screen_shards.py` now splits each shard into eight interleaved chunks (opinion *i* goes to chunk *i* mod 8),
giving 256 tasks on 26 workers. It saves each chunk's result as it completes, so an interrupted run resumes, and
merges the chunks in a fixed order. The decision for every opinion is still `parse.screen()`, which is unchanged
since the D6 freeze, as are `parse.py`, `namenorm.py`, `abbrev.py` and `analysis.py`. Output order changes; the
analysis sorts opinions by id before any sampling, so nothing downstream depends on it.

## D8 — 2026-10-22 12:01 NZDT — verification rules, applied while verifying, before scoring

The plan says only that candidates are "checked by hand against the corpus and against external lookup". These
rules were fixed while reading the sheets, before `analysis.py score` was run:

1. **External lookup.** CourtListener's public search API (anonymous). A cited case counts as **real** if any of
   the following holds:
   - the index or CourtListener holds it under the cited or a corrected citation (typo, wrong reporter, transposed
     digits);
   - independent CourtListener opinions cite it;
   - an official reporter lists it. One case, *State v. Liason*, 2026-Ohio-243, is absent from CourtListener and
     was confirmed on the Ohio Reporter of Decisions through a web search.

   A citation is a **phantom** only if the case is found nowhere. A real case cited at a wrong citation is
   **real**, however wrong the citation.
2. **Courts' own findings.** When the opinion itself states that a cited case does not exist or cannot be located,
   that statement, together with the index check, verifies the phantom (flag type). One exception: where the court
   adds that the case exists elsewhere (*Hatahly*; *Bajakajian* cited as "Kajakajian"; *Messina*; *Main St. Legal
   Servs.*), it is real.
3. **Party filings.** CourtListener's opinion corpus contains documents that are not court opinions:
   - pro se motions carrying a judge's memo endorsement;
   - a pro se plaintiff's filing in bankruptcy court;
   - an appellant's reply brief (Tex. App., filed as a "combined opinion").

   Every verified phantom's document was read. A phantom in a party filing is recorded as `phantom-party-filing`,
   or `party-filing-unverified` where the citation could not be resolved either way. These are not counted as
   judicial reliance; `score` counts `phantom` only. The rate denominators (opinions screened) include an
   unmeasured share of such filings. The report must say so.
4. **Unverifiable.** A citation whose case name is too garbled to identify (OCR) is `unverifiable` and not
   counted.
5. **Misattribution sample.** Verdicts are `index-artefact` when resolution merely returned the case spanning the
   page because the cited case is missing from the index (Westlaw, neutral and new F.4th citations), or a verdict
   from the categories above.
6. **Reading aid.** `code/verify_aid.py` adds the case names the index holds at the cited reporter-volume-page.
   It decides nothing.

## D9 — 2026-10-22 20:18 NZDT — changes after the independent review (review/review.md), before re-scoring

**Labels** (`data/screen/labels/`, assembled by the new `code/assemble_verified.py`):
- **New vocabulary.**
  - `phantom-flag`: the court itself identifies a cited case as nonexistent.
  - `phantom-party-asserted`: only a party says so.

  Previously both were "phantom" on a flag sheet. `score()` now counts a `phantom-flag` as a flag whatever sheet it
  sits on, so a court flag missed by the FLAG regex can never count as judicial reliance.
- **Two flag rows become party-asserted** (screened_flag k=115 and k=156). The court relays a party's statement and
  makes no finding of its own. Each is its opinion's only phantom, so opinions with a court-flagged phantom go from 45
  to 43; the two are reported separately.
- **k=161 stays a court finding:** the court itself says the cases "appear to be hallucinations".
- **Las Cruces stays a court finding**, with a CourtListener near-namesake noted (2003-NMCA-102).
- **The two "unverifiable" rows become real, not a case** (screened_reliance k=141, placebo_reliance k=247). Both are
  Schwarzer, 99 F.R.D. 465 (1984), an article in F.R.D.
- **Unwritten defaults stay real**, recorded with `labelled = 0`. 117 of the 1,036 sheet rows carry a written verdict.
  The pace of verification is stated in the report.

**Code:**
- **`match_charlotin.py`.**
  - The NON_US regex no longer drops New Mexico courts ("Mexico" now excludes "New Mexico").
  - A same-day match is also accepted when every distinctive token of the database caption appears in the cluster's
    name, on top of the existing name-score rules. This catches captions that carry extra names, such as *Henry
    County Schools v. Grant*.
- **`analysis.py score()`.**
  - **Recall** is computed per distinct cluster, both before the completeness filter (any candidate in the order) and
    after it (a candidate that survives the filter). The post-filter recall governs the verified counts, and the
    recall-corrected upper bound is the sample's upper bound divided by it.
  - **The judge-attributed matches** are classified as either the relying opinion or a reviewing court's opinion
    about a lower court's order. This is a fixed list, from reading each document.
  - **Flag opinions versus the database** is computed in code by a date-free name match, at the same thresholds,
    against all in-window US incidents.
  - **Reporters:** a table of the reporters that survive the completeness filter.
- **The H1 verdict for a sampled sheet** follows the interval: Supported if its lower bound is at least 20, Refuted
  if its upper bound is below 10, otherwise Inconclusive. The plan's rule was written for a full count, and a sample
  whose interval spans the bands cannot decide it.

**Not delivered:**
- Rates by court level (plan §4 step 8): the `court` field is empty for every document, because `screen_shards.py`
  never filled it. This is reported here rather than repaired, because re-running the screen is out of scope.
- The capture–recapture estimate (Chapman N = 4) rests on a single overlap of zero and is uninformative.

## D10 — 2026-10-23 00:29 NZDT — changes after the confirmation pass (review/confirmation.md), before re-scoring

The confirmation pass found that the D9 name match in `flag_vs_database()` was vacuous. The `NON_US` regex let three
Cyrillic captions (one Russian, two Ukrainian) into the "US in-window" incidents. `norm_name()` keeps only `[a-z0-9]`,
so they normalise to "v" or "1 v", and `party_score()` then scores "v" at 100 against any caption with a standalone
"v". The name match was therefore true for 41 of the 43 clusters whatever the database held, and "all 43 in the
database" was wrong.

**Code:**
- **US incidents are selected by the database's own `State(s)` field** (it contains "USA"), in both
  `match_charlotin.py` and `flag_vs_database()`, instead of the `NON_US` regex, which also passed 58 rows from other
  countries (South Korea, Belgium, Poland, Costa Rica, China and others). None of those 58 matched a cluster, so the
  matched set (879 rows, 869 clusters) and every recall figure are unchanged. The US in-window count becomes 1,474.
- **Database captions with no indexable token** (`tokens_of()` empty) are skipped in the name match.
- **`HAND_DB`** gains the four flag opinions that the reviewer found in the database under another caption or
  date, keeping Zaykariya and Nwaubani:
  - *Puerto Rico Soccer League v. Federación Puertorriqueña de Fútbol* (name score 84.2, just under the threshold;
    the same case, D.P.R. 2025-09-23);
  - *Qamar v. Board of Trustees of Governors State University* (the database anonymises it as "X v. Board of
    Trustees of Governors State University", N.D. Ill., same day);
  - *Flowz Digital v. Caroline Dalal* (the corpus caption reads "v. Flowz Staffing"; C.D. Cal., same day);
  - *Brick v. Gallatin County* (the corpus caption reads "Brick v. Breuner"; D. Mont., same day).
- **The five flag opinions found in no field of the database** are listed in `primary.json` by name, court and date.

**Wording:**
- "43 opinions are 42 cases" becomes **41 cases**: *Morgan* and *Schoene* each contribute two documents, and
  Schoene's second is an amended re-issue of the first.

The reviewer's expected result, which this re-run must reproduce: 26 by cluster, 6 by caption, 6 by hand, so 38 of
43 in the database and 5 unrecorded.
