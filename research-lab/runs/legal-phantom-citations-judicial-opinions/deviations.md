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
