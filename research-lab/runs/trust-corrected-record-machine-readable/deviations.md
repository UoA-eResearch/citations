# Deviations

## D1 — 2026-10-22 10:42 NZDT — notice exclusion: self-references are not notices

Before any cohort file was fetched, the first join excluded 22,588 registry entries as notices. That included 1,547
that Retraction Watch lists as retracted originals, 2,177 Crossref targets and 1,544 PubMed "Retracted Publication"
records. The cause is self-reference:
- 29,611 of Crossref's 113,832 retraction assertions point at the asserting work's own DOI. The publisher marks the
  original record itself as retracted, with no separate notice DOI.
- In Retraction Watch, 13,701 rows give the notice DOI as the original's DOI, and 34,349 give the notice PMID as the
  original's PMID.

The plan's rule ("their PMID or DOI is a notice's in Retraction Watch or Crossref") therefore removed originals.

Two changes:
1. An identifier marks a notice only when it differs from the original's.
2. A document that Retraction Watch, Crossref or PubMed lists as the retracted original is not excluded by
   identifier. The plan's other rule, XML `article-type` = "retraction", still removes true notices among them.

OpenAlex-only entries flagged by identifier remain excluded; OpenAlex marks notices as retracted, a known flaw.
`match_log.json` reports how many documents rule 2 keeps.

The same rule is applied to the peS2o registry (secondary 7), whose first run was stopped during its download.
There, a DOI listed as a retracted original with a date is never treated as a notice.

## D2 — 2026-10-22 11:08 NZDT — version folders are not immutable (noted after H1-H3 were computed)

The plan says the bucket's version folders are immutable, so the snapshot files could be fetched again. That is
false. Every primary-cohort sidecar, version 1 included, was last modified after its retraction date: 12,766 in June
2026, the rest between July and October 2026. PMC therefore regenerates files in place without a new version number.
The fetched copies (fetched 2026-10-22, 60,177 files, 2.9 GB in `data/files`) are now the frozen snapshot, and
their SHA-256 hashes are committed in `results/tables/snapshot_files_sha256.csv.gz`.

No analysis changes. The report must say what this implies: the measured coverage describes the bucket as it was on
2026-10-22. A pipeline that copied the bucket earlier may hold older files, which this study cannot see.

## D3 — 2026-10-22 11:15 NZDT — detector faults found by validation 8a (after H1-H3 were computed)

Reading the 100 validation documents found four errors by the preregistered detector:
- **One false positive.** PMC puts `related-article` of type retraction-forward *inside reference-list entries*,
  to flag a cited work that has been retracted. The detector counted that as the citing article's own marker.
- **Three misses.** Withdrawal notices and statements ("Withdrawal:", "has been withdrawn", Elsevier's withdrawal
  policy text) fall outside the retraction wording.

`code/sensitivity_d3.py` re-reads every primary-cohort document with markers counted only outside reference lists
(`markers.xml_markers_own`), with withdrawal wording added. For the text rendition it uses PMC's own "RETRACTED
ARTICLE" header line, or the textual rules applied before the References line. The preregistered figures in
`primary.json` stand as reported. The corrected ones (`sensitivity_d3.json`):
- unmarked 2.77% (1.24-5.65), against 2.41% preregistered;
- 75 documents had been marked only through their references; withdrawal wording adds 9;
- the XML-minus-text difference is 0.86 pp (0.46-1.53).
No verdict changes.

## D4 — 2026-10-22 11:15 NZDT — Elsevier self-update dates are publication dates (found in validation 8b)

For a retraction asserted by the article's own Crossref record (a self-update; mostly Elsevier, e.g. Heliyon), the
`updated` date is the article's issue date, not the retraction date. Ten of the 50 documents checked in 8b carry
a "RETRACTED:" title in Crossref, a 2026 erratum and an issue date in 2020-2024. Their retraction probably came in
2026, possibly inside the 180-day buffer. The primary cohort's 412 documents dated only this way (the overlay's `date_source`; a DOI with both a
self-update and a separate notice counts here) are 28.9% unmarked, against 1.9% for documents dated by Retraction Watch. They are reported as their own stratum; no verdict depends on
them. Validation 8b also found 6 of 50 unmarked documents not to be retractions of the document in question (errata,
corrigenda, earlier versions or the notice itself), and 1 unclear.

## D5 — 2026-10-23 09:53 NZDT — changes after the independent review (review/review.md, "fix first"), before re-scoring

1. **The peS2o marker rule** (finding 1). peS2o renders IEEE's retitled records as "Notice of RetractionThe Effects
   of…", with the title run into the notice and no separator. The STATEMENT pattern's closing word boundary, and the
   TITLE pattern, therefore missed 6,159 documents that carry the plan's own "notice of retraction" marker.
   - **Primary peS2o rule** (`code/pes2o_secondary.py`): the study rule, OR "notice of retraction" anywhere with no
     closing boundary, OR a first line beginning "Retracted", "Retraction" or "Withdrawn" followed by a separator or
     a capital letter (run-together titles).
   - **Sensitivity rule** (the reviewer's broader one): "retract" anywhere in the first line.
   - The PMC XML arm keeps its preregistered rules. Its JATS titles and statements are separate elements, and the
     review found its detector complete.
2. **Staleness, by-year, and the downstream comparison** (findings 2 and 3).
   - **Code.** These were computed by uncommitted code. They now come from `code/pes2o_secondary.py` and are written
     to `results/tables/pes2o_secondary.json`.
   - **Staleness.** Semantic Scholar's "added" date is mostly its 2017–18 bulk ingest, so the added-before/after split
     is confounded with retraction year. It is reported within retraction years 2015 and later only.
   - **The downstream test** is the subset of peS2o documents that are also in the PMC snapshot and are not notices,
     with no stratum filter: 3,235 documents, 2 of them undated. It compares PMC's own marker rate with peS2o's.
   - **Corrections from the confirmation pass:**
     - The stratum wording above was corrected.
     - The peS2o registry still dates 166 matched documents by Crossref self-updates. This is reported in the peS2o
       section: excluding them moves 47.2% to 47.6%, and the overlap to 96.2% / 9.1%.
     - The review-check files keep article titles, which are bibliographic metadata of the kind Retraction Watch
       publishes. Passages of article text are not committed.
3. **Self-update dates** (finding 4). The 412 documents dated only by an Elsevier Crossref self-update (D4) have no
   retraction date. They move from the primary cohort to the undated stratum. The headline residue becomes the dated
   documents plus an undatable count. The preregistered verdicts are unchanged (`sensitivity_d4.json`).
4. **Notice contamination** (finding 5). 73 primary documents (0.4%) are notices or retracted corrigenda that D1's
   type check let in. This is reported rather than excluded: excluding them moves the unmarked share from 2.77% to
   2.79%. Two of the three validation-8a "misses" are such notices, and the report says so.
5. **Wording and numbers** (findings 6–8):
   - the related-article share is 95.6% under D3;
   - 18,060 of 18,061 sidecars were modified after retraction;
   - B-011's erratum is of its own paper;
   - the journal-cluster key is described, with the alternative keys' intervals;
   - 8a was labelled from excerpts selected by regular expression;
   - the "errors fall on the unmarked side" sentence is replaced by the quantitative estimate (6 of 50 unmarked are
     registry errors, so the unmarked share conditional on a true retraction is about 2.4%).
