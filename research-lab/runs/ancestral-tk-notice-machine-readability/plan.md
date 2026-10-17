# Does Indigenous-governance metadata survive the open-data pipeline? Preregistration

Lead: `ancestral-tk-notice-machine-readability` (Ancestral Futures). Written 2026-10-17, before any census query or
machine-view fetch.

**Examined beforehand (no outcome):**
- the Local Contexts vocabulary (`results/tables/vocabulary.json`: 30 Labels, 20 TK and 10 BC; 12 Notices, 4
  disclosure and 8 institution);
- one scouting fact from the lead, the DataCite rightsUri count (48,351, 99.96% from prefix 10.21233, Neotoma). It is
  treated as known, not as a result.

## 1. Question and hypotheses

Local Contexts Notices (placed by researchers and institutions) and TK/BC Labels (applied by communities) carry
Indigenous provenance and protocols. DataCite, Dryad, Dataverse and RAiD have built integrations since 2022, but
nobody has counted uptake across platforms or tested whether the element survives the machine views through which
metadata actually travels.

- **H1 (Labels are rare).** Across the platforms in section 2, fewer than 0.1% of records carrying any Local Contexts
  element carry a community-authored TK or BC Label resolvable to a Local Contexts Hub project.
  - Supported if the upper end of the exact 95% interval is < 0.1%.
  - Refuted if the lower end is ≥ 0.1%.
  - Reported with and without Neotoma (prefix 10.21233).
- **H2 (crosswalks drop it).** In a stratified sample of element-bearing DOIs, the element is dropped in at least 40%
  of record × machine-view pairs.
  - Supported if the record-cluster bootstrap interval's lower end is ≥ 0.40.
  - Refuted if its upper end is < 0.40.
  - Inconclusive otherwise.
- **H2b (silence).** No view that drops or degrades the element signals that a rights element was omitted. This is
  descriptive: any warning string is recorded.

## 2. Census (limb 1)

Every query and its raw response are saved.

- **Element-bearing record:** any record whose structured rights fields, or any text field, contains a
  localcontexts.org / localcontextshub.org URI or an exact vocabulary name ("TK Notice", "BC Provenance", …).
- **Platforms and channels:**
  - **DataCite:** REST API; structured `rightsList.rightsUri:*localcontexts*`, plus free text `localcontexts`.
  - **Zenodo:** records API, `q=localcontexts`.
  - **Dryad:** API v2 search.
  - **Harvard Dataverse:** search API.
  - **figshare:** articles search.
  - **OSF:** SHARE index-card search.
  - **GBIF:** dataset search, and machine tags.
  - **RAiD:** the public registry if queryable, otherwise reported as "not queryable".
  - **re3data:** repository-level policy mentions.
- **Free-text precision.** 200 free-text hits are hand-adjudicated (or all, if fewer), and the platform counts are
  reported as lower bounds with that precision.
- **Classification per element:**
  - **Label** — a /label/ URI or a Label name;
  - **Notice** — a /notice/ URI or a Notice name;
  - **Hub project** — a localcontextshub.org/projects/<id> URI.

  A Label counts as community-authored and resolvable only if a Hub project URI accompanies it and resolves (HTTP 200).
  Every distinct URI is resolved and its status recorded.
- **Concentration:** share from the top publisher or client, and HHI, by platform, resource type and year.

## 3. Crosswalk fidelity (limb 2)

**Sample.** Up to 2,000 element-bearing DOIs, stratified: all non-Neotoma DOIs (up to 1,500), with Neotoma filling
the rest (seed 20261021).

**Views per DOI:**
- six DOI content-negotiation formats via doi.org: DataCite XML, schema.org JSON-LD, Crosscite JSON, CSL-JSON,
  BibTeX, formatted citation;
- DataCite OAI-PMH `oai_dc` and `oai_datacite`;
- the OpenAIRE Graph record, where one exists.

**Scoring, by a deterministic parser:**
- **preserve:** the element's URI or name is present in a rights- or terms-type field, distinguishable from the
  licence;
- **degrade:** present only merged into the licence field (e.g. JSON-LD `license`) or in free text;
- **drop:** absent.

A view that returns no record is "unavailable" and is excluded from the H2 denominator. 100 record-views are checked
by hand.

## 4. Analysis (`code/analysis.py`)

- **H1:** an exact binomial interval on Labels among element-bearing records, pooled across platforms; per-platform
  Wilson intervals; with and without Neotoma.
- **H2:** the share of record × view pairs dropped, with a record-cluster bootstrap (2,000; seed 20261021); per view
  (exact intervals); preserve/degrade/drop matrix by view and by stratum.
- **Descriptive:** URI resolution (live, redirect, dead); Hub projects found; concentration; trend by year.

## 5. Threats and care

1. **By design?** Labels may legitimately live in the Hub and on landing pages rather than in DOI metadata.
   Low DOI-layer prevalence is then not a defect, and the report must say so. The study measures what machine
   consumers can see, not whether communities want more visibility.
2. **Concentration.** Neotoma's bulk minting dominates the DataCite count. Every figure caption states it, and every
   statistic is also given without Neotoma.
3. **Free-text recall** is unknown outside structured fields, so counts are lower bounds.
4. **Named organisations.** Counts describe repository systems, not communities. No community's data is analysed,
   and no collection is judged. Engagement with Local Contexts, the repositories and Te Mana Raraunga / Pacific data
   governance advisers is recommended before any use of the results to rank platforms. It is a care note, not a gate
   (lab policy).
5. **Prior art for H2's mechanism:** Dataverse issues on the dc:rights / oai_dc crosswalk (#8129, #5920, #4176).
