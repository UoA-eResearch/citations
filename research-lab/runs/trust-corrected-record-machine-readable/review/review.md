# Review: trust-corrected-record-machine-readable (draft 72af844)

Reviewer: Fable 5.1, 2026-10-23. Scripts and logs in `review/reviewer_checks/` (`xml_pass.py` + `xml_summary.py`:
independent pass over all 20,059 XML files; `tables_check.py`: recomputation and independent bootstrap;
`pes2o_check.py`: re-scoring of the 17,416 peS2o matches; `crossref_d4.py`, `crossref_notices.log`: 30 Crossref
records; `s3_refetch.py`: 12 bucket objects; `misc_checks.py` output in `misc_checks.log`; `val8a_reread.log`).

## Verdict: fix first

The PMC arm stands. H1 Refuted (2.4%, 1.1–4.7; 2.8% after D3), H2 Supported (95.6%), H3 Refuted (1.2 pp) are
reproduced from the intermediate tables with an independent cluster bootstrap, the detector's reference-list fix is
complete, the snapshot is what the hashes say it is, and the validation labels hold on re-reading. The peS2o arm does
not stand. Its marker rule misses 6,159 documents whose peS2o text begins "Notice of Retraction<title>" (IEEE's
2009–2011 retractions, run together without a separator), so the headline "peS2o keeps the marker on 12%" is a regex
artefact: by the plan's own textual rules at least 47% of the matched documents are marked (59% of
title-and-abstract records). The staleness result and the by-year result are consequences of the same miss and
invert when it is fixed. The title, the verdict paragraph, the plain-terms paragraph, the peS2o section and F4 must
be rewritten before publication; the PMC-overlap subset is the comparison that actually supports a downstream-loss
claim and should carry it.

## Findings

### 1. MAJOR — the peS2o marker rule misses the single largest class of marked documents

`code/markers.py:12-15`: STATEMENT ends in `\b`, so `notice\s+of\s+retraction\b` does not match "Notice of
RetractionThe Effects of HRT…", which is how peS2o renders IEEE's retitled records (title and subtitle concatenated
with no separator). The TITLE rule (`^\W*(retracted|retraction|withdrawn)`) does not accept "Notice of Retraction"
as a prefix either. `pes2o_check.log`:

- 6,181 of 17,416 matched documents begin "Notice of Retraction" (spaces ignored); the study's rule marked 22 of them.
  6,159 of the misses have DOI prefix 10.1109.
- Marked share: study rule 11.86%; "retract" anywhere in the title line 44.7%; study rule OR title-line "retract"
  47.4% (s2ag 59.1%, s2orc 12.6%). The plan's rule (§2) names "notice of retraction" as a marker, so these documents
  are marked by the preregistered definition; the implementation failed on a formatting artefact.
- The report's 11.9% / 12.5% / 11.6% (`report.md:31-32, 176-180`), the title (`report.md:1`), the verdict
  paragraph (`report.md:9-11`, "the marker is gone for 88%"), the plain-terms sentence ("only about one retracted
  paper in eight still says so", `report.md:52-54`) and F4 are all wrong as stated.

Fix: re-score with a rule that tolerates the run-together title (e.g. `notice\s*of\s*retraction` without the
trailing boundary, and the title rule applied to the first 40 characters of the first line with "notice of
retraction" added), report the corrected share as the lower bound it is, and rebuild F4. Rewrite the title and
verdict: the honest statement is that the PMC marker is lost downstream for PMC-derived documents (finding 2b), not
that peS2o as a whole keeps 12%.

### 2. MAJOR — the staleness and by-year claims are artefacts of finding 1 and confounded

`report.md:35-36, 181-185`: "added after retraction 7.1% (n 11,155) vs added before 20.3% (n 6,261), so stale
ingestion is not the explanation"; "1.5% of the 3,688 retracted in 2011, 33% of 2022".

- `added` is Semantic Scholar's ingestion date: 7,494 of the matched documents were added in 2017 and 4,548 in 2018.
  Every 2009–2011 retraction was therefore "added after retraction", and those are the IEEE documents the rule
  missed. With the corrected rule the split inverts: added-after 62.7% marked, added-before 20.5%. Restricted to
  retractions from 2015 on, where both groups exist, the two are identical (20.6% vs 20.6%, n 2,305 vs 6,281).
  There is no evidence either way on staleness.
- By retraction year, the 2011 cohort is 91.1% marked under the corrected rule, not 1.5%; 2010 89.2%; 2009 74.4%.
  "Earlier retraction cohorts are marked least" inverts.

(b) What does survive, and is the fairer "one step downstream" test: 3,238 matched peS2o documents are in the PMC
snapshot and are not notices. Their PMC own-marker rate is 95.7%; their peS2o marked rate is 9.1% (9.3% corrected;
2,960 are s2orc full text). For documents not in the PMC registry the corrected rate is 59.5%. The downstream-loss
claim should be made on this subset, with those numbers, and the title's "built from them" should go: only 3,238 of
the 17,416 matched documents come from PMC.

Fix: drop the staleness paragraph or report it as null; replace the by-year sentence; move the downstream claim to
the PMC-overlap subset.

### 3. MODERATE — peS2o results not produced by the committed code

`results/tables/pes2o.json` carries `by_added_vs_retraction` and `retraction_watch_dated_only`, which
`code/pes2o.py:111-115` never writes (its `out` dict has seven keys). `pes2o.json` was rewritten at 13:09:39, five
minutes after `pes2o_documents.csv` (13:04:09) and after `pes2o.cpython-312.pyc` (13:05). The by-year figures in
`report.md:181-182` appear in no table and no script. The lab's rule is code before results; here the results that
carry the report's strongest downstream sentence have no code. Fix: add the computations to `pes2o.py` (or a
committed `pes2o_secondary.py`), rerun, and cite the table.

### 4. MODERATE — the 412 self-update-dated documents have no retraction date and should leave the primary cohort

`deviations.md:54-62`, `report.md:137-145`. My Crossref check of 15 unmarked documents dated only by a Crossref
self-update (`crossref_d4.log`): on 15 of 15 the `update-to.updated` date equals the issue month; 10 are Heliyon
records with a 2026 erratum and a record deposit between June and October 2026, consistent with a 2026 retraction
(latency, not failure); 4 were deposited in 2024–25 with no erratum, so some are genuine old misses. The plan's
rule (§1, "else the Crossref update-to date") presupposes that the field is a retraction date; D4 establishes it is
not. These documents belong in the undated stratum. The preregistered verdicts do not move (without them 2.2%,
1.1–4.1; `sensitivity_d4.json`), but the headline residue should read 382 dated documents (2.2%) plus 119
undatable, not "501 (2.8%)" (`report.md:21`), and the "28.9%" stratum should be presented as undated rather than as
part of the primary cohort. The 5 self-update documents in the recent stratum are immaterial.

### 5. MINOR — D1 let a small number of notices and retracted corrigenda into the cohort

`xml_summary.log`. Among the 18,061 primary documents, 45 have a title beginning with a notice word and 59 carry a
notice-to-original link (`retracted-article`, `corrected-article`, `object-of-concern`) in `article-meta`; the union
is 73 (0.4%), 46 of them with bodies under 3,000 characters. Most are retracted corrigenda and corrections (30 with
`article-type="correction"`), which are retracted items but not the research articles the lead is about; a few are
true notices whose `article-type` is not "retraction" and so escaped the plan's check: PMC9399278 (JBC
"Withdrawal:", typed `correction`), PMC3279244 (editorial "Paper Withdrawn Before the Issue Release"), PMC7347305 and
PMC6900581 ("Retraction and republication"). 98% of the 73 count as marked, so excluding them moves the unmarked share
from 2.77% to 2.79%. Two of the three 8a "misses" (A-009, A-038; `8a_labels.csv`) are such notices, not detector
misses; `report.md:151-152` should say so. D1 itself was right: the 129 primary documents it kept are 60
research articles, 32 corrections and the rest reviews, case reports and letters, with 6.2% unmarked.

Fix: exclude documents whose `article-type` is correction/expression-of-concern or whose title begins with a notice
word and whose body is empty, or state the 0.4% contamination; reword the validation sentence.

### 6. MINOR — three report numbers need edits

- `report.md:104`: "96.1% of the cohort carry a `related-article` of type retraction-forward" is the preregistered
  count, which includes the 75 documents whose only link sits in a reference list. The D3 structured share is 95.6%
  (`documents_d3.csv.gz`, `misc_checks.log`).
- `report.md:106` and `deviations.md:28-29`: "Every cohort sidecar … was last modified after its retraction" is
  18,060 of 18,061: PMC8736302 (10.1007/s11115-021-00583-9) was last modified 2026-02-22 and is dated 2026-03-24.
- `report.md:160`: B-011's "withdrawn erratum" (10.1016/j.vas.2019.100088) is the erratum to B-011's own paper,
  deposited by Elsevier as a retraction of ten different papers; "of another paper" fits B-030 only.

### 7. MINOR — cluster key mixes ISSN and journal-name clusters

`analysis.py:110`. 24 Retraction Watch journal names are split across more than one ISSN cluster (2,531 documents;
print and electronic ISSNs appear first in different files), and 32 ISSNs carry more than one journal name. Only one
document lacks an ISSN, so the name fallback is never reached. Effect: journal-name-first key 2.77% (1.39–4.87);
publisher-level clusters 2.77% (1.03–6.90); reported 2.77% (1.24–5.65). Nothing changes. Note it in the methods.

### 8. NOTE — validation design and the "lower share" sentence

- 8a was labelled from regex-selected excerpts (`validation.py:27-38`: title, front-matter elements, passages
  matching `retract|withdraw`), not "each read in full XML" (`plan.md:100-101`). The check is therefore not
  independent of the detector's vocabulary; a marker phrased otherwise ("removed", "retirado") is invisible to both.
  My re-read of the 4 disagreements and 12 agreeing items (`val8a_reread.log`) found every label correct.
- 8b: all 6 "no" and the "unclear" label hold on the Crossref records (`crossref_d4.log`, `crossref_notices.log`;
  10.1016/j.ijpx.2025.100319 is a retracted corrigendum; 10.1186/1556-276x-8-419 is the notice of the earlier
  version), as do the five Crossref-only "yes" labels I checked.
- `report.md:162-163`: "the registry's errors fall almost entirely on the unmarked side" is tautological, since only
  the unmarked side was sampled. The defensible statement is quantitative: 6 of 50 unmarked documents (12%) are not
  retractions of that document, so about 60 of the 501 are registry errors and the true unmarked share, conditional
  on R, is near 2.4%.

### 9. NOTE — confirmations

- Order of work (git): `plan.md` 10:15:38; `markers.py` 10:16:41 and `analysis.py` 10:25:33, both unchanged in
  their preregistered functions since; `cohort.parquet` 10:44:23, D1 commit 10:44:35, first file fetched 10:44:39,
  `parsed.parquet` 11:07:04. `xml_markers_own` was appended to `markers.py` at 11:10 and committed with the results
  at 11:16; the preregistered `xml_markers` is byte-identical. D1's counts recomputed from the raw files: 29,611 of
  113,832 Crossref assertions self-pointing; 34,349 Retraction Watch rows with notice PMID = original PMID.
- 180-day buffer: S − CUT = 180 days; primary max date 2026-04-24, recent min 2026-04-25.
- Independent bootstrap (index resampling, different seed): H1 2.41% (1.15–4.79), H2 95.62% (92.50–97.46), H3 1.21 pp
  (0.63–2.05), D3 own 2.77% (1.24–5.63). Reported: (1.14–4.73), (92.64–97.49), (0.67–2.00), (1.24–5.65).
- Detector: retraction-type `related-article` instances sit in `article-meta` 17,298, `front` 775, `ref` 5,485,
  `back` 1, `body`/`sub-article` 0. 180 documents carry sub-articles (review reports); 52 have retraction wording in
  them, none as the sole marker. Statement hits only in the body: 2, both the article's own ("the article has been
  retracted so the authors can readdress"; "A previous version of this Article has been retracted"). No "paper about
  retractions" false positive. My strict own-marker definition agrees with D3 on 18,044 of 18,061; the 17
  disagreements are my rule's artefact (documents carrying both a forward and a backward link).
- Snapshot: inventory version = sidecar `version` = `xml_url` folder = XML `pmcid-ver` on all 20,059 documents
  (including the four at version 319). 30 of 30 SHA-256 match. Twelve objects refetched on 2026-10-23 are identical to
  the frozen copies, with Last-Modified equal to the inventory's for json and xml; two `.txt` files are older than
  their XML (not regenerated with it). PMC10018472, unmarked, retracted 2025-08-07, was regenerated 2026-06-27 still
  without a marker, so the residue is not merely stale files.
- Sidecar flag and text header: identical on every document (791 neither, 17,270 both, 0 off-diagonal). Flag set
  with own marker absent: 0.
- Report numbers against tables: all of H1–H3, the publisher table, Hindawi vs rest, latency (own marker month 0
  84.4%, flag 82.9%; months 1–5 98.2–100% and 97.6–100%), date-source strata (1.89% / 4.84% / 28.9%, n 412),
  manuscripts (509; 5.9% vs 2.3% with the preregistered detector), undated (730; 9.45%, 87.0%), overlay (22,174;
  19,898; 619; 501), registry sizes and the 9,273,077 PMCIDs check. peS2o ids and DOIs are unique (17,416).
- The headline for PMC ("the corrected record reaches PMC's files") and the caveat ("can find is not does find")
  are fair; the caveat is the right one and should stay prominent.

## Required before publication

1. Re-score peS2o with a rule robust to the run-together title; rewrite title, verdict, plain terms, §peS2o, F4
   (findings 1–2); move the downstream claim to the PMC-overlap subset.
2. Commit the code that produces every peS2o number in the report (finding 3).
3. Present the 412 self-update-dated documents as undated and restate the residue (finding 4).
4. The edits in findings 5, 6 and 8.
