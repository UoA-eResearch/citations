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
