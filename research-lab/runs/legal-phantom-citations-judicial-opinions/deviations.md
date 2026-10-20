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
