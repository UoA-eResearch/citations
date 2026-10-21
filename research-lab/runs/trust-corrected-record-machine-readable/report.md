# Does the corrected record reach the machines? In PubMed Central's distributed files it does: 97% of retracted articles carry their own retraction marker

*The PMC Open Access bucket on AWS, which since August 2026 is the only distribution channel for PubMed Central's
Open Access subset, as listed on 21 October 2026, joined to the union of four retraction registries (Retraction
Watch, Crossref, PubMed, OpenAlex). Every retracted document's XML, plain text and metadata sidecar were read for a
machine-readable retraction marker. A secondary arm looks at peS2o, an open pretraining corpus derived from Semantic
Scholar.*

**Verdict: Refuted.** The lead's hypothesis was that most retracted articles in the open full-text corpora carry no
machine-readable marker. In the PMC bucket, the opposite holds.

- **H1 (more than 50% of retracted articles are unmarked in the distributed XML): Refuted.** 2.4% are unmarked
  (95% interval 1.1–4.7%; n = 18,061 documents retracted at least 180 days before the snapshot, 1,550 journals).
  A detector fault found in validation counted links on *cited* works; with it fixed, 2.8% (1.2–5.7%) are
  unmarked (D3).
- **H2 (PMC's own `is_retracted` flag covers at least 90%): Supported.** 95.6% (92.6–97.5%).
- **H3 (the plain-text rendition loses at least 5 points of markers relative to the XML): Refuted.** 1.2 points
  (0.7–2.0); 0.9 points (0.5–1.5) with the D3 fix. PMC writes "RETRACTED ARTICLE" into the header of the text
  file itself.
- **Where the corrected record does not reach:** 501 retracted documents in the cohort (2.8%) carry neither a marker
  of their own nor PMC's flag. They concentrate in Elsevier (26% of its 507 documents) and Cell Press (18% of 788),
  and among Elsevier articles whose retraction Crossref records only on the article itself, with the issue date in
  place of the retraction date (D4).
- **Markers arrive fast.** Of articles retracted in the last 30 days before the snapshot, 84% were already marked;
  after the first month, 98–100%.

PES2O_PLACEHOLDER

## In plain terms

When a scientific paper is retracted, the publisher posts a notice and the paper is supposed to be flagged
everywhere it appears. A worry behind this study is that the copies used to build AI search tools and to train
language models never get the flag, so a model keeps treating withdrawn research as sound.

We checked this at the biggest open source of full-text biomedical papers, PubMed Central's Open Access collection,
which is what most open AI pipelines download. Of about 18,000 papers retracted at least six months earlier, 97%
carried a marker in the file itself — almost always a structured link from the paper to its retraction notice —
and PubMed Central's own "retracted" flag covered 96%. Even the plain-text version is labelled "RETRACTED ARTICLE"
at the top. New retractions are marked within about a month. So the lead's claim that most retracted papers go
unmarked is false for this source.

The gap is narrower but real: about 500 retracted papers had no marker and no flag, most of them from Elsevier
journals. And the markers only help a pipeline that reads them. PES2O_PLAIN

## What was asked

The lead (`trust-corrected-record-machine-readable`, Advancing Trust in Knowledge) proposed that in the open
full-text corpora that retrieval-augmented generation (RAG) and pretraining pipelines ingest, more than half of the
documents retracted by the freeze date carry no machine-readable retraction marker in the file as distributed.
Retraction flags had been compared across bibliographic databases (Ortega & Delgado-Quirós 2024; Schneider et al.
2023; Hauschke & Nazarovets 2025), and propagation from Retraction Watch to Crossref and OpenAlex was being measured
(Lux 2026). Nobody had measured the marker inside the full-text files themselves. The plan (`plan.md`, committed
before any file was fetched) set three tests:

- **H1:** more than 50% of the primary cohort unmarked in the XML (Supported if the interval's lower bound exceeds
  50%, Refuted if its upper bound is below 50%).
- **H2:** PMC's sidecar flag covering at least 90%.
- **H3:** the XML marked at least 5 points more often than the text.

The lead's RAG testbed was dropped before any data were seen (it needs the shared GPU), and Europe PMC was not
treated as a separate corpus (its Open Access full text is built from the same XML).

## How it was done

- **Snapshot.** The bucket's daily inventory of 21 October 2026 lists 9,273,077 PMCIDs. For each, the latest
  version was taken.
- **Registry.** Four layers, fetched on 22 October 2026: Retraction Watch (67,896 retractions; reinstated papers
  dropped), the targets of Crossref retraction assertions (113,832), PubMed's "Retracted Publication" (35,195) and
  OpenAlex's `is_retracted` (137,044). Matched to PMC by PMID, else DOI, through NCBI's PMC-ids file.
- **Exclusions.** Retraction notices themselves: by identifier, and by XML `article-type` = retraction (162).
  OpenAlex flags notices as retracted, so 20,354 OpenAlex-only entries were excluded as notices. A first version of
  the rule also excluded originals whose registry entry reuses the original's own identifier for the notice. That
  covered 29,611 Crossref self-updates, and Retraction Watch rows giving the original's DOI or PMID as the notice's.
  This was corrected before any file was read (D1).
- **Cohort.** 18,061 documents retracted on or before 24 April 2026 (180 days before the snapshot), dated by
  Retraction Watch, else by Crossref. A further 1,106 retracted in the last 180 days are the latency set, and 730
  undated (PubMed-only or OpenAlex-only).
- **Markers** (code committed before any file was parsed):
  - Structured JATS: `related-article` of a retraction type; `notes`, `custom-meta`, a `pub-history` event or
    `article-version` naming retraction.
  - Textual: a title beginning "Retracted", "Retraction" or "Withdrawn"; a retraction statement; the token
    "RETRACTED".
  - Plain text: the textual rules.
  - Sidecar: `is_retracted`.
- **Intervals.** Cluster bootstrap over journals, 2,000 resamples.
- **Validation, by the study's AI agent.** (a) 100 documents stratified by the detector's verdict, read in full;
  (b) 50 unmarked documents checked against Crossref and Retraction Watch for a real retraction.

## Results

### What the markers are

The structured link does nearly all the work: 96.1% of the cohort carry a `related-article` of type
`retraction-forward` pointing to the notice. PMC adds it when the notice is deposited, and rewrites the article's
files in place (D2). Every cohort sidecar, version 1 included, was last modified after its retraction, and 99% of
the cohort is still at version 1. A title prefix ("RETRACTED:", "RETRACTED ARTICLE:", "Retracted:") appears in 9.6%,
a retraction statement in 13.6%. Only 1.5% are marked by text alone.

PMC's sidecar flag and the "RETRACTED ARTICLE" header of the text file are the same piece of PMC metadata. Both
appear on exactly 95.6% of the cohort, and never on a document without an XML marker. No document was flagged and
unmarked; 356 carry an XML marker without the flag.

### Where the marker is missing (`results/figures/F1_publishers.png`)

The unmarked residue is a publisher story:

| | documents | unmarked (D3) | sidecar flag not set |
|---|---:|---:|---:|
| Hindawi | 6,507 | 0.2% | 0.2% |
| Wiley | 1,641 | 1.3% | 2.4% |
| PLOS | 1,350 | 0% | 0% |
| Elsevier – Cell Press | 788 | 17.6% | 17.6% |
| Springer – Nature | 717 | 2.1% | 4.9% |
| Elsevier | 507 | 26.0% | 39.4% |
| Springer | 312 | 8.3% | 22.8% |

The mass Hindawi retractions of 2023 are almost all marked (0.2% unmarked, 0.07–0.5%), against 3.6% (1.7–6.8%) for
everything else.

### How fast (`results/figures/F2_latency.png`)

Of documents retracted in the 30 days before the snapshot, 84% carried an XML marker of their own and 83% the flag.
In each later month up to six, 98–100% carried the marker and 97.6–100% the flag. This is a cross-section, not a
follow-up of the same documents.

### The date problem (`results/figures/F3_date_source.png`)

Documents dated by Retraction Watch are 1.9% unmarked. Those dated by a separate Crossref notice are 4.8%. Those
dated only by a Crossref self-update are 28.9%: 412 documents, mostly Elsevier, where the article's own record
asserts the retraction. For these, the date Crossref carries is the article's issue date, not the retraction date.
In validation, ten of them had a "RETRACTED:" title in Crossref and a 2026 erratum, so their retraction probably came
in 2026, some of it inside the 180-day buffer. Part of the residue is therefore latency, not failure (D4).
Without the self-update-dated documents the unmarked share is 2.2% (1.1–4.1%); with Retraction Watch dates alone,
1.9% (0.8–4.0%) (`sensitivity_d4.json`).

### Validation

- **(a) Detector.** Of 50 documents the detector marked, 49 were marked. The one false positive was a retraction
  link on a *cited* work inside the reference list: PMC flags retracted references this way. Of 50 it left
  unmarked, 47 were unmarked. The three misses were withdrawal notices or statements ("Withdrawal:", "has been
  withdrawn"), which fall outside the retraction wording.
  - Corrected across the whole cohort: 75 documents had been marked only through their references, and withdrawal
    wording adds 9. The unmarked share becomes 2.77% (1.24–5.65), against 2.41% as preregistered (D3).
- **(b) Registry.** Of 50 unmarked documents, 43 were real retractions or withdrawals. Six were not retractions of
  the document in question:
  - two linked by Crossref to a withdrawn erratum of another paper;
  - a republished version flagged by its predecessor's retraction;
  - a corrigendum's retraction;
  - an earlier duplicate's withdrawal;
  - a withdrawal notice itself.
  One was unclear. The registry's errors fall almost entirely on the unmarked side, so the true unmarked share is
  likely lower than 2.8%.

### The other strata

- **Undated stratum** (730; PubMed-only or OpenAlex-only, mostly PubMed): 9.5% unmarked, flag 87%.
- **Author manuscripts** in the cohort (509): 5.9% unmarked, against 2.3% for publisher versions.

PES2O_SECTION

### The overlay

`results/overlay/retraction_overlay.csv.gz` is the released overlay. It holds 22,174 PMC documents in the union
registry, with their layers, the retraction date and its source, and, for the 19,898 in the snapshot, what their
own files say. 619 snapshot documents have neither a marker of their own nor PMC's flag. For those, the overlay is
the only machine-readable record of the retraction in this corpus. The rebuild procedure: `registry.py` →
`match.py` → `fetch.py` → `analysis.py parse` → `sensitivity_d3.py` → `overlay.py`.

## What this does and does not show

- **The lead's premise fails at the source.** PMC marks retracted articles inside the distributed files, in the
  structure (a JATS link), in its own metadata flag and in the text header. A pipeline that reads PMC XML or text and
  looks for the marker can find it for about 97% of retracted articles.
- **But "can find" is not "does find".** The marker is a `related-article` element and a header line. A pipeline
  that strips front matter, keeps body text only, or chunks paragraphs for retrieval discards both. This study
  measured the files, not any pipeline's handling of them.
- **Snapshots age.** PMC rewrites files in place (D2). A corpus copied from the bucket before an article's retraction
  keeps the unmarked file. This study saw the bucket as it was on 22 October 2026 and cannot see older copies.
- **Conditional on the registry.** Silent retractions are invisible here. Validation shows the registries' errors
  are mostly false retractions, not misses, on the unmarked side.
- **AI adjudication.** Both validations were done by the study's AI agent, which also wrote the detector.

## Process and deviations

- **Preregistration:** `plan.md`. Novelty search on 22 October 2026.
- **Deviations** (`deviations.md`):
  - D1 (self-referencing notice identifiers; before any file was fetched);
  - D2 (files rewritten in place; local copies hashed in `snapshot_files_sha256.csv.gz`);
  - D3 (reference-list links and withdrawal wording; a sensitivity, with the preregistered figures kept);
  - D4 (Crossref self-update dates).
  No verdict depends on a deviation.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

`code/registry.py`; `code/snapshot.py`; `code/match.py`; `code/fetch.py`; `code/analysis.py parse` and `run`;
`code/validation.py sheets` and `score` (labels in `data/validation/`); `code/sensitivity_d3.py`; `code/overlay.py`;
`code/pes2o.py`; `code/figures.py`. Python environment in `venv/` (pandas, lxml, pyarrow, matplotlib).
