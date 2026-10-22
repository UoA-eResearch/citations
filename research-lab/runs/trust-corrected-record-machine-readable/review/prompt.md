You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/trust-corrected-record-machine-readable/ (read-only except your output in
review/).

**The question.** Do retracted articles carry a machine-readable retraction marker inside the full-text files that
retrieval and pretraining pipelines ingest? Corpus: the PMC Open Access bucket on AWS (`pmc-oa-opendata`), as listed
by its 2026-10-21 inventory; registry: the union of Retraction Watch, Crossref retraction assertions, PubMed
"Retracted Publication" and OpenAlex `is_retracted`; secondary corpus: peS2o v2.

- **Reported:** H1 (more than 50% of 18,061 documents retracted 180+ days before the snapshot are unmarked in the
  XML) Refuted: 2.4% (1.1-4.7), 2.8% after the D3 detector fix. H2 (PMC's sidecar `is_retracted` covers 90%)
  Supported: 95.6%. H3 (XML marked 5+ points more often than the .txt) Refuted: 1.2 points.
- **Secondary (peS2o v2):** 17,416 retracted papers matched by Semantic Scholar id; 11.9% carry a textual marker
  (12.0% with Retraction Watch dates), 7.1% of those added after their retraction. The headline contrasts this with
  PMC's 97%.
- **Deviations:** D1 (self-referencing notice identifiers, before any file was fetched), D2 (files rewritten in
  place), D3 (links inside reference lists; withdrawal wording), D4 (Crossref self-update dates are issue dates).

**What to read:** plan.md, deviations.md, report.md; code/ (registry.py, snapshot.py, match.py, fetch.py, markers.py,
analysis.py, sensitivity_d3.py, validation.py, overlay.py, pes2o.py, figures.py); results/tables/ and
results/overlay/; data/ (a symlink to /mnt/data/retraction-markers: raw registry layers, snapshot inventory,
cohort.parquet, parsed.parquet, the fetched files in data/files/, validation sheets and labels in data/validation/).

**Git.** Read-only git is fine. Check that plan.md preceded every fetch, that markers.py and analysis.py were
committed before any cohort file was parsed, and what D1-D4 changed after which results.

**Environment.** Python: /mnt/citations/research-lab/runs/trust-corrected-record-machine-readable/venv/bin/python
(pandas, lxml, pyarrow), with -I. Do NOT pip install. Scripts and outputs under review/reviewer_checks/. You may
fetch a few public objects from https://pmc-oa-opendata.s3.amazonaws.com/ and the Crossref REST API politely.

Check at least:

1. **The registry and D1.** Was the D1 change (self-referencing identifiers no longer mark notices; curated originals
   never excluded by identifier) right, and did it let notices into the cohort? The XML article-type check removed
   162. Sample cohort documents and confirm they are originals.
2. **Dates and strata.** Is the 180-day buffer applied correctly? How much of the unmarked residue is recent
   retractions misdated by Crossref self-updates (D4)? Should those documents leave the primary cohort, and would
   that change anything?
3. **The detector.** Are the structured and textual rules right? Is the reference-list problem (D3) fully fixed, or
   do other locations (e.g. notes, back matter, sub-articles) carry markers for *other* works? Spot-check documents
   counted as marked by `related-article` alone.
4. **Snapshot integrity.** Were the files fetched for the right versions, and does the in-place rewriting (D2)
   threaten the claim "as distributed"? Is the sidecar flag really the same metadata as the text header?
5. **Intervals.** Is the journal-cluster bootstrap right, and is the ISSN-or-journal cluster key sound?
6. **Validation.** Do the 8a and 8b labels in data/validation/ hold up on your own reading of a sample? Is the
   claim that the registry's errors make the true unmarked share lower justified?
7. **peS2o.** Is the matching (DOI to Semantic Scholar corpus id) sound, is the marker rule appropriate for
   plain-text title-and-abstract documents, and is the lower-bound framing right?
8. **The report.** Every number against the tables; plain terms; whether the headline ("the corrected record reaches
   PMC's files") and the caveat ("can find" is not "does find") are fair; whether the overlay's counts are right.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered
findings (severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
