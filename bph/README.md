# Blue Pacific Research Landscape

A first pass at mapping the University of Auckland's research **in or about the Pacific**, and its ocean,
Earth and climate research, built by the
Centre for eResearch for **Mā Kiwa te moana nui e whakaumu | Blue Pacific Horizons** (BPH), one of the
University's Signature Research Areas. It responds to BPH's request (October 2026) for a pilot that
combines publications with grants, projects and researcher networks to show UoA's Pacific research
strengths, connections and opportunities, and to support a gap analysis against the SciVal Topics and
Topic Clusters used for the SRA last year.

## Views

| Tab | What it shows |
|---|---|
| **Strengths** | Output by year; plain-language research areas; topics; subfields with scholarly output, growth, FWCI, top-10% share and UoA's share of the world's Pacific-named output; SDGs; UoA's rank among universities, and why the leaders lead. |
| **Map** | Partners by country (or institution) with a regional summary and the Pacific Island countries with no joint work; Pacific, Aotearoa, ocean and polar places named as the subject of study; co-authorship ties (Pacific-centred). |
| **Researchers** | Faculty and unit breakdowns, the UoA co-authorship network, a sortable researcher table, and a check of the SRA's engagement list against the landscape (internal data). |
| **Grants & projects** | Public award records: UoA-led grants (HRC, Marsden to 2017, MBIE, overseas funders) and Marsden projects from the 2018-2025 rounds with a UoA researcher on the team; funders acknowledged in the works. |
| **SRA alignment & gaps** | Each work placed in its own SciVal Topic and Topic Cluster and tested against the SRA3 list (in the SRA dataset, screened out, never screened, not in SciVal); the SciVal Topics holding the Pacific research with UoA's SciVal metrics; where Pacific Island countries publish and UoA's output there; keyword probes that report the SciVal Topics new keywords land in. |
| **Workshop maps** | Where Workshop 2 participants placed their research on five maps, and what they wrote (internal data). |
| **About** | Data period and date, how to cite, using it as a baseline, definitions, sources and caveats. |

One filter bar (lenses, ocean themes and strength) drives every tab. After BPH's November meeting the page also
has: the data date under the title; a *How reliable is this picture?* table (coverage by research area: books and
chapters, single-authored, abstracts, SciVal coverage, works credited by author profile); every topic inside a
research area; a plain-language colour guide and an "extra works" figure on the SRA tab; a downloadable review
list of screened-out and never-screened SciVal Topics (CSV, with a column to mark reinstatements); a key-figures
CSV for baselines; and "Save image" buttons that export charts, maps and the network as PNGs with a title, legend,
source and data date. In claude.ai the downloads go through the artifact `downloads` capability (the viewer
confirms each save); elsewhere they are ordinary browser downloads. On the maps, small circles are drawn over large
ones and Pacific Island partners over the places studied.

## Definitions

- **Lenses.** *Pacific Islands & peoples* (a Pacific Island country, territory, people or the Pacific as a
  region or community is named, or a co-author is at a Pacific Island institution on a team of 20 or
  fewer); *Pacific Ocean & region* (the Pacific Ocean, its sub-regions, or ENSO/IPO/PDO); *Aotearoa
  environment & hazards* (Aotearoa / NZ / Māori named, and environment-earth-biodiversity research or an
  ocean, coast, climate or hazard word in the title), following the SRA's framing of Aotearoa as part of the
  Pacific; *Ocean, Earth & climate* (added November 2026 after BPH's review): marine & coastal ecosystems;
  ocean & climate processes (incl. paleoceanography, paleoclimate); seafloor, tectonics & hazards (Hikurangi,
  Chatham Rise, contourites, pockmarks, earthquakes, tsunami); Antarctica & the Southern Ocean; ocean law,
  governance & blue economy, whether or not the Pacific is named. A theme counts when its terms are in the
  title, or mentioned twice in the abstract/keywords of research in a fitting field (once in oceanography,
  aquatic science or ocean engineering); earthquake engineering of buildings is left out unless it also
  concerns tsunami, subduction or the seafloor, and disaster studies count only in Aotearoa or the Pacific.
  Search terms: `pipeline/lenses.py`; local checks: `pipeline/tagging.py`.
- **Research areas.** One plain-language area per work (`tagging.research_area`): the five ocean/Earth themes,
  then ten areas from the OpenAlex field and subfield of the work's primary topic.
- **Pacific places.** The search names all 22 Pacific Island countries and territories on the Pacific
  Community's list (as in the Pacific Data Hub's population statistics), with Hawaiʻi and Rapa Nui, in English
  and common local or people forms (November 2026: the Northern Mariana Islands, the states of the Federated
  States of Micronesia and adjective forms were added; possessives such as "Papua New Guinea's" now match).
- **UoA authorship.** An authorship counts as UoA when OpenAlex links it to UoA or when its written affiliation
  names the University of Auckland / Waipapa Taumata Rau (not AUT); candidates are fetched both ways. This
  catches UoA authors whom OpenAlex credits to a previous employer; the wrongly linked institution is not
  counted as a partner. Since 12 November 2026 (after BPH's meeting) an authorship with **no affiliation at all**
  on the record also counts when the author's OpenAlex profile places them at UoA in the publication year or the
  year before (`uoa_author_years.json`, built by `fetch_works.py` for every UoA author it sees); the four lens
  queries are rerun by author for these (routes `U*`). This recovers book chapters and law and humanities
  preprints and reports, which often carry no affiliation. Works found only this way are flagged (`up`).
- **More candidate routes (12 November 2026).** The search also uses the bare word "Pacific" and Pacific
  research concepts (talanoa, teu le vā, kakala, fonofale, fa'afaletui, tok stori, tivaevae, vanua, fonua;
  `lenses.LENS_P_EXTRA`, search only, so the world comparison is unchanged), and takes the UoA works of 2020
  onwards in the Vā Atlas corpus (`pacific/`, route `V`). The ocean governance theme became *Ocean & climate
  law, governance & blue economy*: high seas and BBNJ, ITLOS and climate advisory opinions, the Antarctic
  Treaty, fisheries law and governance, loss and damage, climate mobility and displacement, climate litigation.
  Peer reviews, supplementary files, errata, paratext and retractions are no longer counted.
- **Strength.** *Pacific-focused*: named in the title, a specific Pacific place/people/concept, a Pacific
  Island co-author, or the Pacific Ocean/climate named repeatedly. *Within wider studies*: generic
  "Pacific"/"Pasifika" only in the abstract (typically NZ health data by ethnicity). *Single mentions*.
  Default view: Pacific-focused + the Aotearoa and ocean, Earth & climate lenses.
- **Spot checks** (2026-10-30): 38/40 random Pacific-focused works and 24/25 random Aotearoa-lens works
  were judged correct; of 25 works that a "repeated mentions" rule would have called Pacific-focused,
  about three in four were NZ studies reporting Pacific results, so that rule was dropped. (2026-11-04):
  37/40 random works added by the ocean, Earth & climate lens alone were plainly marine, ocean,
  Earth-hazard or polar research (after the abstract rule was tightened; an earlier sample found ~35/40).

## Data and method

- **OpenAlex** (API, user's key in `~/.config/openalex/api_key`; responses cached in
  `/mnt/data/ubuntu/bph-cache`): works with a UoA author (institution lineage `I154130895`) 2020 to date,
  institutions, and awards (`institution_awarded` UoA, plus HRC awards whose lead affiliation names UoA).
- **SRA3 SciVal Topics & Topic Clusters** workbook and the SciVal dataset methodology (Research Services for
  the Research and Innovation Office). Parsed by `pipeline/parse_scival.py`; final status = narrative-team
  call where given, else Research Services' call.
- **Scopus and SciVal** (Elsevier APIs through the University's subscription; key in
  `~/.config/elsevier/api_key`, sent only as the `X-ELS-APIKey` header; calls must come from the University
  network; responses cached in `/mnt/data/ubuntu/bph-cache/els` with the key scrubbed, because SciVal echoes
  it in its `link` URLs). `pipeline/fetch_scival.py` finds each work's Scopus record (DOI in batches of 25,
  then exact normalised title and year ±1), asks SciVal for its Topic, Topic Cluster, FWCI and top-10% flag
  (100 IDs per call), and fetches UoA's Topic and Cluster portfolio, UoA's metrics in each Topic holding two
  or more Pacific-focused works, and the Topic portfolios of 22 Pacific Island countries and territories.
- **SRA alignment** (`pipeline/scival_topics.py`): the SRA3 names are matched to SciVal IDs by exact
  normalised name. A SciVal research area built from Topics and Topic Clusters holds every paper in them, so a
  work is *in the SRA dataset* when its Topic or its Cluster was included; *screened out* when its Topic or
  Cluster was on the list but marked "n"; *never screened* when neither was on the list; *not in SciVal* when
  it has no Scopus record or no Topic yet. (Before SciVal access, a text-similarity approximation stood in for
  this; it is retired, see Caveats.)
- **Marsden Fund 2018-2025** (`pipeline/fetch_marsden.py`): OpenAlex's Marsden records stop at the 2017
  round, so each later round is read from Royal Society Te Apārangi's public announcement workbook (project,
  contact investigator and institution, panel, category, funding, abstract, full team). Projects are kept when
  a UoA researcher is on the team, as lead or as a team member on a project led elsewhere; the year is the
  funding round, and grants from the last three rounds are marked "probably running" (three-year grants).
  All awards are classified from their title and description or abstract.
- **MFAT aid activities** (`pipeline/fetch_mfat.py`): the Ministry of Foreign Affairs and Trade publishes every
  New Zealand aid programme activity to the IATI Standard (reporting organisation NZ-1); they are read through
  d-portal.org's public read-only query service. An activity is kept when a participating organisation is the
  University of Auckland, Auckland UniServices or Waipapa Taumata Rau, or its title or description names UoA,
  UniServices or a UoA institute as the deliverer (MFAT lists university partners on only ~46 of its ~3,000
  activities, so most UoA-delivered short courses are found by their description), and it ran in 2020 or later.
  A Pacific Island recipient country counts as naming that place. The amount is MFAT's spend for the whole
  activity: scholarships and short courses include participants' costs, and multi-partner activities are not
  UoA's share (MFAT reports every transaction receiver as "Pending Approval"), so the page keeps MFAT spend out
  of the research-grant total and shows it separately. OpenAlex's MFAT award records have no titles or
  recipients, and MFAT funding outside the aid programme is not published there. November 2026: 25 activities,
  12 Blue Pacific-related (Pacific short courses, Cook Islands health literacy, Solomon Islands basic education,
  Pacific literacy and school leadership, the NZ Institute for Pacific Research, Samoa and Kiribati scholarships).
- **Engagement check** (`pipeline/engaged.py`, internal input): the SRA's stakeholder engagement workbook is
  merged across its sheets and each person matched to UoA authors by name (first name, initial or prefix, and
  surname incl. hyphenated parts and the surname in their email address). People not found are looked up
  in OpenAlex (UoA affiliation) to show whether they are at UoA but outside the current scope. Emails are
  used only for merging and never written out.
- **Workshop 2 maps** (internal input): dots and post-it notes transcribed from photos of the five maps
  (`$BPH_WORK/engagement/workshop2_maps.json`), dots counted by region because the Spilhaus projections
  cannot be read precisely from a photo; five photos (no people) are shown on the page.
- **Not included:** non-public data from the University's grant and ethics application systems (managed by
  the Research and Innovation Office; needs their permission).

## Map styles

The Map tab can be switched from the web map (deck.gl, Mercator) to five styles after the maps used at
Workshop 2, drawn with d3 (background on a canvas, interactive layer in SVG):

| Style | Projection and data |
|---|---|
| Spilhaus: the ocean in a square | Adams World in a Square II in an oblique aspect (centre 49.56371678 S 66.94970198 E, azimuth 40.17823482, as in PROJ's `spilhaus`). Ported from PROJ 9.8 (`adams.cpp`, `spilhaus.cpp`, sphere); the oblique step is the d3 rotation `[-66.94970198, 49.56371678, -139.82176518]`, so d3 cuts the map at the true seams. Checked against PROJ 9.8.1 on 400 points (max difference 1.6e-14, unit sphere). |
| Spilhaus with ocean depth | The same, shaded by Natural Earth 10m bathymetry (200 m to 10,000 m; public domain), `data/bathy.json`. |
| Equal Earth | `d3.geoEqualEarth`, centred on 165 E. |
| Large Ocean States | Mercator on the Pacific with exclusive economic zones: Flanders Marine Institute (2023), Maritime Boundaries Geodatabase: Maritime Boundaries and Exclusive Economic Zones (200NM), version 12, https://doi.org/10.14284/632, CC BY 4.0, via the Marine Regions web feature service; `data/eez.json`. |
| Navigator-centred (after Tupaia) | Azimuthal equidistant centred on Raʻiātea (16.83 S, 151.44 W), rings every 1,000 km. Inspired by Tupaia's chart; not a reconstruction of it. |

`pipeline/mapstyles.py` builds `data/bathy.json` and `data/eez.json` (needs shapely and pyshp; its outputs are
committed, so `run_all.sh` does not run it).

## Elsevier APIs used

Five Elsevier APIs, all called through `pipeline/els.py`: `GET https://api.elsevier.com/...`, with the key
in the `X-ELS-APIKey` header and `Accept: application/json`. Requests are counted for a full rebuild from an
empty cache (replayed from the cache on 2 November 2026); re-runs are served from the cache.

| API | Endpoint | Parameters | What it gives | Step | Requests |
|---|---|---|---|---|---:|
| [Scopus Search](https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl) | `/content/search/scopus` | `query=DOI("…") OR …` (25 DOIs a call), `count=25`, `field=dc:identifier,prism:doi` | Scopus ID of each atlas work, by DOI | `fetch_scival.py` | 105 |
| Scopus Search | `/content/search/scopus` | `query=TITLE("…") AND PUBYEAR > y-2 AND PUBYEAR < y+2`, then the title's words ANDed; `count=25`, `field=dc:identifier,dc:title,prism:coverDate` | Scopus ID by exact normalised title and year ±1 when the DOI fails | `fetch_scival.py` | 1,286 |
| Scopus Search | `/content/search/scopus` | `query=TITLE-ABS-KEY(terms)` [`AND AF-ID(60005686)`] [`AND TITLE-ABS-KEY(Pacific terms)`] `AND PUBYEAR > 2020 AND PUBYEAR < 2026`; `count=1` or `200`, `sort=relevancy`, `field=dc:identifier` | Keyword-probe counts (UoA, UoA Pacific, world Pacific) and the papers whose Topics are looked up | `probe_keywords.py` | 30 |
| [SciVal Publication](https://dev.elsevier.com/documentation/SciValPublicationAPI.wadl) | `/analytics/scival/publication/metrics` | `publicationIds` (up to 100 a call), `metricTypes=FieldWeightedCitationImpact,OutputsInTopCitationPercentiles,CitationCount` (probes: `CitationCount`), `byYear=false` | Each paper's SciVal Topic and Topic Cluster (ID and name), FWCI and top-10% flag | `fetch_scival.py`, `probe_keywords.py` | 48 |
| [SciVal Topic](https://dev.elsevier.com/documentation/SciValTopicAPI.wadl) | `/analytics/scival/topic/institutionId/212005` | `yearRange=5yrs`, `limit=100`, `offset` | UoA's Topic portfolio: each Topic's UoA output, world output and Prominence percentile | `fetch_scival.py` | 100 |
| SciVal Topic | `/analytics/scival/topic/metrics/institutionId/212005` | `topicId`, `yearRange=5yrs`, `metricTypes=ScholarlyOutput,FieldWeightedCitationImpact,PublicationShare,PublicationShareGrowth,CitationCount` | UoA's metrics in each Topic holding two or more Pacific-focused works; the data-release date | `fetch_scival.py` | 100 |
| SciVal Topic | `/analytics/scival/topic/countryId/{id}` | `yearRange=5yrs`, `limit=100`, `offset` | Topic portfolios of 22 Pacific Island countries and territories | `fetch_scival.py` | 63 |
| SciVal Topic | `/analytics/scival/topic/{id}` | none | The Topic Cluster of Topics not seen through a paper (SRA3 Topics, Pacific Island table) | `scival_topics.py` | 303 |
| SciVal Topic | `/analytics/scival/topic/metrics` | `topicIds` (up to 100), `metricTypes=ScholarlyOutput`, `yearRange=5yrs` | World output and prominence of Topics outside UoA's five-year portfolio | `scival_topics.py` | 1 |
| [SciVal Topic Cluster](https://dev.elsevier.com/documentation/SciValTopicClusterAPI.wadl) | `/analytics/scival/topicCluster/institutionId/212005` | `yearRange=5yrs`, `limit=100`, `offset` | UoA's Topic Cluster portfolio | `fetch_scival.py` | 15 |
| [SciVal Country](https://dev.elsevier.com/documentation/SciValCountryAPI.wadl) | `/analytics/scival/country/search` | `query=name(…)`, `limit=10` | SciVal country IDs (kept only on an exact ISO code match) | `fetch_scival.py` | 22 |

Total 2,073 requests: Scopus Search 1,421 (weekly quota 20,000) and SciVal 652 (weekly quota 5,000, shared
across the SciVal APIs). `212005` is The University of Auckland in SciVal and `60005686` its Scopus
affiliation ID. Development only, not in the pipeline: a few test calls to the
[SciVal Institution API](https://dev.elsevier.com/documentation/SciValInstitutionAPI.wadl)
(`/analytics/scival/institution/search`, to find 212005), the SciVal Publication lookup
(`/analytics/scival/publication/{id}`) and the
[Abstract Retrieval API](https://dev.elsevier.com/documentation/AbstractRetrievalAPI.wadl); the Topic API's
`keyContribOnly` option was tried and dropped because it returned every Topic.

## Keyword probes (the gap-check automation)

Put one probe per line in `probes.local.txt` (the SRA's own list, git-ignored) or `probes.txt` (public
examples) as `Label: term | term`, then run `pipeline/probe_keywords.py` and `pipeline/bundle.py`. Each probe searches Scopus (SciVal's five-year window) for the terms with and without
the Pacific search terms, for UoA and the world, then asks SciVal which Topics UoA's papers on the theme (the
200 most relevant) and the 200 most relevant Pacific-named world papers belong to, and what share of each
sits inside the SRA dataset. That is the "keywords to SciVal Topics" step, automated. `probes.txt` holds the
public example probes (themes from the BPH web page); the page uses `probes.local.txt` when present.

## Rebuild

```bash
bph/pipeline/run_all.sh "SRA3_Topics & Topic Clusters for approval.xlsx"
python bph/build_page.py          # app.html -> index.html (standalone)
```
`PY` needs requests, numpy, networkx (>= 3.4), openpyxl. A full rebuild from an empty cache costs about
US$0.10 of OpenAlex budget and 1,421 Scopus Search and 652 SciVal requests (weekly quotas 20,000 and
5,000); re-runs are served from the caches.

`app.html` is the page body (published as a claude.ai artifact with `data/bph.json` and
`data/land-50m.json`); `index.html` wraps it as a standalone page. Headless browser tests must unset a
stale `DISPLAY` (SSH X forwarding) or SwiftShader WebGL fails.

## Caveats

The atlas is built from OpenAlex, which indexes more than Scopus: works without a Scopus record (mostly
conference abstracts, preprints, datasets, book chapters and regional journals Scopus does not index) count as
"not in SciVal". SciVal's FWCI differs from OpenAlex's for the same papers; the page shows both, labelled.
SciVal's window is its last five complete years while the 2025 screening used 2020-2024, and SRA3 names that
SciVal has since renamed or merged cannot be matched (the page lists them). A small share of OpenAlex records
duplicate another (a preprint and its article, a chapter listed twice); counts are of OpenAlex records. A
text-similarity approximation used before SciVal access agreed poorly with SciVal's own assignments and has been
removed; do not reuse figures from it.

Faculty/unit come from affiliation
text (mapped to the 2026 faculty structure) and author identities from OpenAlex disambiguation; both have
errors. Award coverage is uneven (Marsden records in OpenAlex stop at 2017; HRC records carry no end dates;
2,074 HRC awards record no lead institution). Bibliometrics miss community reports, much Pacific-language
scholarship and the relationships behind the research.

## Data, licence and attribution

MFAT's aid activity data is published openly to the IATI Standard by the Ministry of Foreign Affairs and Trade
(reporting organisation NZ-1) and read through d-portal.org; the page cites it on the Grants view, in each
activity's panel and in About.

The built data files (`data/scival_sra3.json`, `data/bph.json`, `data/probes.json` and the intermediates) hold
the SRA's internal SciVal list and Scopus/SciVal data obtained under the University's licence, so they are
**not in the public repository** (`data/.gitignore`); rebuild them with `run_all.sh` from the University
network. Share the built page within the University only. Following Elsevier's Scopus and SciVal Attribution
Guides (dev.elsevier.com), the page names Scopus and SciVal as the source, with links to www.scopus.com,
www.scival.com and api.elsevier.com and the retrieval dates, on every view that shows their data, and links
each work to its Scopus record (`https://www.scopus.com/inward/record.uri?partnerID=HzOxMe3b&scp={id}&origin=inward`).
