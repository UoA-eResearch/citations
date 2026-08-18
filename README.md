# Citation Network Explorer

Interactive citation network explorer powered by live [OpenAlex](https://openalex.org/) data,
GPU-accelerated visualisation, and a built-in AI assistant.

**Live demo:** https://uoa-eresearch.github.io/citations/

## Features

- **Live OpenAlex search** — type in the search box to load the citation network of any author,
  paper (the paper + its references + citing papers), institution, topic, journal or funder.
  Up to 600 works are loaded per entity, most cited first.
- **Five views**, switchable from the top bar (both network views run on
  [cosmos.gl](https://github.com/cosmosgl/graph), the GPU force layout & rendering engine behind
  [Cosmograph](https://cosmograph.app)):
  - **3D** — GPU 3D force simulation with an orbit camera (drag to rotate, scroll to zoom),
    shaded sphere points with depth cueing. Uses cosmos.gl's `spaceDimensions: 3` mode, vendored
    from a pre-release build in `vendor/cosmos-gl/` (see its README to rebuild/upgrade).
  - **2D** — GPU 2D force layout that scales to very large graphs
  - **Map** — world map of author institutions and co-authorship collaborations
    ([deck.gl](https://deck.gl) arcs + scatter over a [MapLibre](https://maplibre.org)/CARTO basemap)
  - **Canvas** — task-adaptive multi-axis 3D scatter (the *dynamic canvas*): assign contextual
    dimensions to each axis — time, citations, field-weighted impact, topic / subfield / field
    (ordered by the OpenAlex ontology hierarchy domain → field → subfield → topic), country, venue —
    or pick a task preset (*Ideation over time*, *Geographic story*, *Impact landscape*,
    *Semantic map*) and the axes reconfigure to suit the task. The AI assistant can also
    reconfigure the canvas from natural language, e.g. *“where are the authors from and how has
    that shifted over time?”*
  - **Plots** — Plotly analytics dashboard (works & citations per year, top authors / journals /
    topics / fields, open-access status, work types)
- **Network styling** — group nodes by paper, author, institution, journal, topic or field;
  colour and size by citations, year, author count, institution count or field.
- **Timeline filter** — drag across the year histogram to filter every view to a year range.
- **AI assistant (✦ Ask AI)** — ask questions by typing or voice (Web Speech API), e.g.
  *“show Giovanni Coco's network on a map”*, *“plot citations per year”*, *“what's the most cited
  paper here?”*, *“which institutions does this author collaborate with?”*, *“what are the
  differing scholarly opinions around this work?”* (it samples abstracts of citing papers and
  synthesises the discourse). The assistant uses Claude with tool use to drive the app (load
  networks, switch views, reconfigure the canvas axes, restyle, filter, highlight plots) and to
  answer data questions via live OpenAlex queries — including aggregations the app doesn't chart.
  Optionally speaks its replies.

### AI setup

Open ✦ Ask AI → ⚙ settings and paste a Claude API key from
[console.anthropic.com](https://console.anthropic.com). The key is stored only in your browser's
localStorage and sent directly to the Anthropic API (no server in between). Model defaults to
Claude Opus 5; server-side refusal fallback is enabled for Opus 5-class models. Without a key,
only simple typed commands work (“show map”, “load *author name*”).

## Running locally

The app is a static site (ES modules — it needs an HTTP server, not `file://`):

```
python3 -m http.server
# then open http://localhost:8000/
```

## URL parameters

- `?data=Dan` — load a pre-fetched local dataset from `data/Dan.json`
- `?type=author&id=A5043686349&name=Giovanni%20Coco` — deep-link a live OpenAlex entity

## Pre-fetched sample datasets

`./fetch_author.py AUTHOR_NAME` and `./fetch_paper.py PAPER_ID` (after
`pip3 install -r requirements.txt`) save datasets into `data/` for offline use:

- [Daniel J. Exeter](https://uoa-eresearch.github.io/citations/?data=Dan) (default)
- [Giovanni Coco](https://uoa-eresearch.github.io/citations/?data=Giovanni)
- [Mark Gahegan](https://uoa-eresearch.github.io/citations/?data=Mark)
- [Quinn Asena](https://uoa-eresearch.github.io/citations/?data=Quinn)
- [Decolonizing Methodologies](https://uoa-eresearch.github.io/citations/?data=Decolonizing_Methodologies)
  ([map](https://uoa-eresearch.github.io/citations/Decolonizing_Methodologies/map.html),
  [3D map](https://uoa-eresearch.github.io/citations/Decolonizing_Methodologies/map3D.html))
