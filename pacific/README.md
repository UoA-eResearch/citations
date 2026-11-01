# Vā Atlas of Pacific Research

Built by the **Centre for eResearch** Researcher Consultancy for a meeting with **Blue Pacific
Horizons** (Mā Kiwa te moana nui e whakaumu), a University of Auckland Signature Research Area. It
sketches the two-fold analysis **Lisa Uperesa** describes for research on Pacific Research
Methodologies (PRM):

1. **Citation network analysis**: maps the unfolding networks of the field over time, including
   relative influence within the scholarship.
2. **Situational network analysis**: maps vā relations over space and time to identify important
   co-locations, key institutions and key events shaping the history and genealogies of the field.

In that design, the literature review and network analysis yield key thinkers to prioritise for
individual talanoa, and networked scholars to invite to group talanoa and wānanga.

## Views

| View | What it shows |
|---|---|
| **Vā map** | Pacific-centred map (deck.gl): institutions sized by works, co-authorship ties, citation flows (where ideas are taken up), co-locations of key scholars by five-year window, and verified milestone events. A timeline at the foot replays the field year by year. |
| **Genealogy** | 4,123 works and 12,579 in-field citation links, as a ForceAtlas2 network or a timeline with one lane per school of thought (Louvain communities). The main path (search path count) traces the field's backbone. Select a work to light up what it draws on and what cites it. |
| **Key thinkers** | Scholars ranked by in-field citations, influence (author PageRank) and bridging (betweenness over co-authorship and citation ties), with lenses for key thinkers, networked scholars and emerging voices, and a talanoa shortlist that copies to CSV. |
| **What's missing** | Seed texts the open record does not hold, works without reference lists or affiliations, theses, and the record shape the project's curated datasets would need. |
| **About** | Method, caveats (citations are not mana; data sovereignty) and a staged offer of CeR support. |

A **Guided tour** walks through the demo in six steps.

## Data and method

- `pipeline/seeds.py`: 52 starter seed texts across five strands (Oceanic and Indigenous
  foundations; talanoa; vā and tā-vā; Pacific frameworks; research paradigm and guidelines).
  `resolve_seeds.py` matches them in OpenAlex (core + expansion corpus) by title and byline:
  46 found; the other 6 are confirmed to exist (evidence URLs in `seeds.py`) but are not indexed.
- `pipeline/build_corpus.py`: the corpus is every work that is a seed record; cites a
  PRM-specific seed; cites a broadly cited seed (Smith, Hauʻofa, Wendt, Bishop, Gegeo, Meyer,
  Thaman 1993) **and** names a Pacific place or people; or names a PRM concept in its title or
  abstract (`pipeline/queries.py`).
- `pipeline/analyse.py`: networks and measures, written to `data/corpus.json`.
- `pipeline/events.json`: hand-checked milestones, each with a source URL.
- `data/land-50m.json`: Natural Earth 50m countries via world-atlas 2.0.2 (public domain / ISC).

## Rebuild

```bash
# OpenAlex API key in ~/.config/openalex/api_key (or $OPENALEX_API_KEY); responses cache to
# $PACIFIC_CACHE (default /mnt/data/ubuntu/pacific-cache), intermediates to $PACIFIC_WORK.
python pacific/pipeline/resolve_seeds.py   # ~$0.05 of API budget
python pacific/pipeline/build_corpus.py    # ~$0.04, a few minutes
python pacific/pipeline/analyse.py         # ~5 minutes (ForceAtlas2 layout)
python pacific/build_page.py               # app.html -> index.html
```

Requires `requests`, `numpy` and `networkx>=3.4`. `app.html` is the page body (published as a
claude.ai artifact with `data/` alongside); `index.html` wraps it as a standalone page.

## Caveats

Citations capture one kind of relation and miss oral scholarship, community knowledge and much
Pacific publishing. Author identities and affiliations come from OpenAlex's automated
disambiguation. The seed list is a starter for the project's literature review to replace. The page
names scholars only from their published bibliographic records; a production version should be
governed by the research team under the CARE principles for Indigenous data governance.
