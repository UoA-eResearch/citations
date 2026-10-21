# Preregistration: does the corrected record reach the machines?

Lead: `trust-corrected-record-machine-readable` (Advancing Trust in Knowledge). Written 2026-10-22, before any
retracted article's file was fetched or parsed and before any registry was joined to the corpus.

**Examined beforehand (nothing measured):**
- The layout of the PMC Open Access bucket on AWS (`pmc-oa-opendata`): one immutable folder per article version
  (`PMC<id>.<version>/` holding `.xml`, `.txt`, `.pdf`, `.json`), a `metadata/` folder of per-version JSON
  sidecars, and a daily S3 inventory of `metadata/` (CSV: key, last-modified, ETag). One sidecar was opened (an 1867
  editorial, PMC10000000.1); its fields include `pmid`, `doi`, `license_code` and `is_retracted`.
- The PMC readme of 25 August 2026: the legacy FTP datasets are being removed, and the cloud bucket is now the
  distribution channel for the Open Access subset. The bucket is therefore *the* file as distributed.
- Registry sizes only: Retraction Watch (Crossref Labs CSV, fetched 2026-10-22) has 73,335 rows, of which 67,896 are
  retractions; Crossref lists 76,358 retraction notices (`update-type:retraction`); PubMed has 35,195
  "Retracted Publication" records. peS2o is on Hugging Face (`allenai/peS2o`, versions v1 and v2).

**Novelty** (searches 2026-10-22, web and OpenAlex). Retraction flags have been compared across bibliographic
databases (Ortega & Delgado-Quirós, Scientometrics 2024; Schneider et al., STI 2023; Hauschke & Nazarovets, J Inf
Sci 2025), and propagation from Retraction Watch to Crossref and OpenAlex is being measured (Lux, OSF 2026; an
iLands report, Zenodo 2026). LLMs' awareness of retractions has been tested (Thelwall et al. 2025, 2026), and a
2026 essay argues that retractions are entering training data unfiltered, without measuring it. No study measures
the retraction marker inside the full-text files that retrieval and pretraining pipelines ingest.

**Scope changes from the lead, decided now.** The lead's RAG testbed is dropped: it needs the GPU, which is shared
with a served model. Europe PMC's full text for Open Access articles is built from the same PMC XML, so it is not a
separate corpus here. peS2o is kept as a secondary corpus.

## 1. Snapshot and registry

- **Corpus snapshot (S).** The bucket's `metadata/` inventory of 2026-10-21 (01:00 UTC). For each PMCID, the latest
  version listed there. Version folders are immutable, so the exact files are re-fetchable. S = 2026-10-21.
- **Registry (R): the union of four layers**, all fetched on 2026-10-22 (NZDT). An original paper (DOI or PMID) is
  retracted if any layer says so:
  1. Retraction Watch: `RetractionNature` = Retraction, and no later Reinstatement for the same original;
  2. Crossref: targets of publisher-deposited notices (`update-to` of type retraction);
  3. PubMed: "Retracted Publication" [pt];
  4. OpenAlex: `is_retracted` = true.
- **Retraction date:** from Retraction Watch; else the Crossref `update-to` date. PubMed-only and OpenAlex-only
  items have no date and form the **undated stratum**.
- **Matching to PMC:** by PMID, else DOI, through `PMC-ids.csv.gz` (NCBI, 2026-10-21), then to the snapshot.
- **Exclusions:** documents that are themselves retraction notices (their PMID or DOI is a notice's in Retraction
  Watch or Crossref, or the XML `article-type` is "retraction"); documents whose only registry entry is an
  expression of concern or correction.

**Primary cohort (C):** dated members of R retracted on or before **2026-04-24** (180 days before S), matched to a
document in the snapshot. Retractions in the last 180 days are reported separately, as latency (§3).

## 2. Markers

Detected by code written and committed before any cohort file is parsed. On the XML:

- **Structured.**
  - `related-article` whose `related-article-type` contains "retract" (e.g. retraction-forward);
  - `notes` whose `notes-type` contains "retract";
  - `custom-meta` whose name or value contains "retract";
  - a `pub-history` `event` whose `event-type` contains "retract";
  - `article-version` containing "retract".
- **Textual.**
  - The article title begins with "retracted", "retraction" or "withdrawn" (any case, after punctuation). Examples:
    "RETRACTED:", "RETRACTED ARTICLE:", "Retracted:".
  - Anywhere in the text, a retraction statement: "(this|the) (article|paper|manuscript|publication|study) (has
    been|was|is|have been) (formally |officially )?retracted", "retraction notice", "notice of retraction", or
    "retracted article".
  - The standalone upper-case token "RETRACTED".

On the **plain text** (`.txt`), the textual rules apply (the title rule to the first three non-empty lines). On the
**sidecar** (`.json`), the marker is `is_retracted` = true.

**Primary outcome:** a document is *unmarked* if its XML carries no marker of either kind. This counts the generous
textual rules as markers, so it is the definition least favourable to H1.

## 3. Hypotheses

Intervals are 95% cluster bootstraps over journals (ISSN from the XML; else the Retraction Watch journal name),
2,000 resamples, seed 20261022.

**H1 (the lead's primary): more than 50% of the primary cohort is unmarked in the distributed XML.**
- Supported if the interval's lower bound is above 50%; Refuted if its upper bound is below 50%; Inconclusive
  otherwise.

**H2 (the corpus's own flag): PMC's sidecar flag `is_retracted` is true for at least 90% of the primary cohort.**
- Supported if the lower bound is at least 90%; Refuted if the upper bound is below 90%; Inconclusive otherwise.

**H3 (text pipelines lose markers): the share marked in the XML exceeds the share marked in the `.txt` by at least
5 percentage points** (paired, same documents).
- Supported if the lower bound is at least 5 pp; Refuted if the upper bound is below 5 pp; Inconclusive otherwise.

**Secondary (descriptive):**
1. Marker types; by publisher (top 15) and retraction year; Hindawi apart from the rest.
2. **Latency.** For retractions in the 180 days before S, the marked share (XML, sidecar) by month since retraction.
3. The undated stratum, same outcomes.
4. Registry composition: per-layer presence for C and for all of R, and the layers' disagreements.
5. Versions: the share of C still at version 1, and the marked share by version.
6. Cross-tabulation of the sidecar flag and the XML marker.
7. **peS2o** (derived pretraining corpus). Documents in the latest version on Hugging Face are matched to R by
   Semantic Scholar corpus id (DOI → corpus id through the Semantic Scholar API). Retracted at least 180 days before
   that version's snapshot date, the share with a textual marker in the text is reported. Matching is lossy, so the
   count is a lower bound. If the Semantic Scholar API cannot be used, this item is reported as not done.
8. **Validation, by the study's AI agent** (disclosed as such):
   - the parser, on 100 cohort documents stratified by its verdict (50 marked, 50 unmarked), each read in full
     XML;
   - the registry, on 50 unmarked documents, each checked for a real retraction (notice located). Error rates are
     reported.
9. **The overlay.** A released table (PMCID, PMID, DOI, registry layers, retraction date, marker found or not) and
   the script that rebuilds it from the four layers. What it adds is the number of snapshot documents in R that have
   neither an XML marker nor the sidecar flag.

## 4. Threats and care

- **Registry completeness.** Retraction Watch and the other layers miss silent retractions, so every share is
  conditional on R. Registry errors (a notice's DOI recorded as the original's) are handled by the notice exclusion
  and measured by validation 8b.
- **Latency is not failure.** Hence the 180-day buffer and the separate latency curve.
- **Journal clustering.** Markers are publisher practice, so intervals are clustered by journal.
- **Precision.** n is expected in the thousands, and the intervals will be narrow; the publisher breakdown matters
  more than the headline.
- **Content.** The retracted articles' claims are not reproduced anywhere in the outputs; only identifiers and
  marker metadata are released.
- Any departure from this plan will be logged in `deviations.md` before the affected result is read.
