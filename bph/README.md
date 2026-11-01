# Blue Pacific Research Landscape

A first pass at mapping the University of Auckland's research **in or about the Pacific**, built by the
Centre for eResearch for **Mā Kiwa te moana nui e whakaumu | Blue Pacific Horizons** (BPH), one of the
University's Signature Research Areas. It responds to BPH's request (October 2026) for a pilot that
combines publications with grants, projects and researcher networks to show UoA's Pacific research
strengths, connections and opportunities, and to support a gap analysis against the SciVal Topics and
Topic Clusters used for the SRA last year.

## Views

| Tab | What it shows |
|---|---|
| **Strengths** | Output by year; topics; subfields with scholarly output, growth, FWCI, top-10% share and UoA's share of the world's Pacific-named output; SDGs; UoA's rank among universities. |
| **Map** | Pacific places named as the subject of study, partner institutions and co-authorship ties (Pacific-centred). |
| **Researchers** | Faculty and unit breakdowns, the UoA co-authorship network, and a sortable researcher table. |
| **Grants & projects** | Public award records for UoA-led grants (HRC, Marsden, MBIE, overseas funders) and funders acknowledged in the works. |
| **SRA alignment & gaps** | Each work placed in its own SciVal Topic and Topic Cluster and tested against the SRA3 list (in the SRA dataset, screened out, never screened, not in SciVal); the SciVal Topics holding the Pacific research with UoA's SciVal metrics; where Pacific Island countries publish and UoA's output there; keyword probes that report the SciVal Topics new keywords land in. |
| **About** | Definitions, sources and caveats. |

One filter bar (lenses and strength) drives every tab.

## Definitions

- **Lenses.** *Pacific Islands & peoples* (a Pacific Island country, territory, people or the Pacific as a
  region or community is named, or a co-author is at a Pacific Island institution on a team of 20 or
  fewer); *Pacific Ocean & region* (the Pacific Ocean, its sub-regions, or ENSO/IPO/PDO); *Aotearoa
  environment & hazards* (Aotearoa / NZ / Māori named, and environment-earth-biodiversity research or an
  ocean, coast, climate or hazard word in the title), following the SRA's framing of Aotearoa as part of the
  Pacific. Search terms: `pipeline/lenses.py`; local checks: `pipeline/tagging.py`.
- **Strength.** *Pacific-focused*: named in the title, a specific Pacific place/people/concept, a Pacific
  Island co-author, or the Pacific Ocean/climate named repeatedly. *Within wider studies*: generic
  "Pacific"/"Pasifika" only in the abstract (typically NZ health data by ethnicity). *Single mentions*.
  Default view: Pacific-focused + Aotearoa lens.
- **Spot checks** (2026-10-30): 38/40 random Pacific-focused works and 24/25 random Aotearoa-lens works
  were judged correct; of 25 works that a "repeated mentions" rule would have called Pacific-focused,
  about three in four were NZ studies reporting Pacific results, so that rule was dropped.

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
- **Not included:** non-public data from the University's grant and ethics application systems (managed by
  the Research and Innovation Office; needs their permission).

## Keyword probes (the gap-check automation)

Put one probe per line in `probes.txt` (`Label: term | term`), then run `pipeline/probe_keywords.py` and
`pipeline/bundle.py`. Each probe searches Scopus (SciVal's five-year window) for the terms with and without
the Pacific search terms, for UoA and the world, then asks SciVal which Topics the 200 most relevant world
papers and UoA's own papers (up to 200) belong to, and what share of each sits inside the SRA dataset. That
is the "keywords to SciVal Topics" step, automated. The probes shipped are **examples only** (themes from
the BPH web page) until BPH supplies its list of missing areas.

## Rebuild

```bash
bph/pipeline/run_all.sh "SRA3_Topics & Topic Clusters for approval.xlsx"
python bph/build_page.py          # app.html -> index.html (standalone)
```
`PY` needs requests, numpy, networkx (>= 3.4), openpyxl. A full rebuild from an empty cache costs about
US$0.10 of OpenAlex budget and roughly 1,500 Scopus Search and 600 SciVal calls (weekly quotas 20,000 and
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

The built data files (`data/scival_sra3.json`, `data/bph.json`, `data/probes.json` and the intermediates) hold
the SRA's internal SciVal list and Scopus/SciVal data obtained under the University's licence, so they are
**not in the public repository** (`data/.gitignore`); rebuild them with `run_all.sh` from the University
network. Share the built page within the University only. Following Elsevier's Scopus and SciVal Attribution
Guides (dev.elsevier.com), the page names Scopus and SciVal as the source, with links to www.scopus.com,
www.scival.com and api.elsevier.com and the retrieval dates, on every view that shows their data, and links
each work to its Scopus record (`https://www.scopus.com/inward/record.uri?partnerID=HzOxMe3b&scp={id}&origin=inward`).
