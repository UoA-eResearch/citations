# Deviations from the preregistration

## D1 — 2026-10-23 00:59 NZDT — elevation source, grid and sea mask for the exposure (before any exposure is computed)

The plan (§2) reads the LINZ Auckland 2024 1 m DEM at 10 m, with gaps filled from the 2016–2018 collections. Three
details change. No exposure or outcome has been computed.

1. **Source.** LINZ's national LiDAR 1 m DEM mosaic (`new-zealand/new-zealand/dem_1m`) replaces the separate
   Auckland collections.
   - It is the same LiDAR, merged across survey boundaries, and it also covers southern Northland, where streams
     draining to the southern Kaipara begin.
   - Any land it leaves empty is filled from LINZ's national 8 m contour DEM. LINZ calls that DEM unsuitable for
     terrain analysis, so the filled share of contributing land is reported.
2. **Grid.** Routing is done on a 20 m grid, read from the tiles' internal overviews. The domain is the sites'
   bounding box plus 40 km, about 100 million cells. Contributing land at the 2–10 km scale does not depend on
   10 m detail.
   - Newly bare ground is still mapped from Sentinel-2 at 10 m, and its share is computed inside the 20 m
     contributing-land mask.
   - Sites whose contributing land touches the domain edge are reported, and the domain is enlarged if any do.
3. **Where the land ends.** LiDAR DEMs carry values over some harbour water, so "where the flow path leaves the land"
   needs a sea mask. The sea is:
   - DEM no-data;
   - plus water in a clear Sentinel-2 mosaic (NDWI from green and NIR above 0) that is connected to the open sea, so
     lakes and inland ponds are not sea.

   The mosaic uses the clearest scene per tile from the "after" window. A flow path ends at its first sea cell.

**Added sensitivity analysis.** Newly bare share of all land within R km of the site, with no routing.

**D1 addendum — sea cells at or below 0 m (before any exposure is computed).** A plot of the first sea mask against
the DEM showed two problems:
- The LiDAR DEM carries values over harbour water. The Waitematā is hydro-flattened at about −1.15 m (NZVD2016).
- The Sentinel-2 test (the 3 clearest after-window scenes per tile) missed most of the upper Waitematā. Some of it
  was under cloud, and some was exposed mudflat.

The sea is now every cell connected to the open sea that meets any of these:
- it is DEM no-data;
- its elevation is at or below 0 m (about mean sea level);
- it is Sentinel-2 water.

Intertidal flats above 0 m stay land and route down to the harbour. The share of sea cells contributed by each source
is logged.

## D2 — 2026-10-23 01:30 NZDT — routing by priority-flood (before any exposure is computed)

The first routing run (pysheds: fill pits, fill depressions, resolve flats, D8) left 2,484 land cells with no
outflow (pysheds codes −1 and −2). Flow paths ending there absorbed 5.3 million of the 23.0 million land cells, 23% of
the land. Only 70.8% of land reached the sea, and 21% of the remaining paths ended at the domain edge. The largest
interior sink took about 620,000 cells (248 km²). Contributing land built on that routing would have silently lost
whole catchments.

Routing is now a priority-flood (Barnes, Lehman and Mulla 2014):
- Every sea cell next to land, and every land cell on the domain edge, is a seed.
- Land is flooded upward in elevation order, and each land cell drains to the neighbour (of 8) it was reached from.
- This is depression filling and D8 drainage in one pass. Every land cell drains either to a sea cell or off the
  domain edge, and no interior sinks remain.

The outlet, C(R), the radius-only sensitivity and every threshold are unchanged. The share of land draining to the sea
and to the edge is logged.

## D3 — 2026-10-23 09:22 NZDT — an added exposure sensitivity: slip-sized patches (after the exposure froze, before any outcome result was read)

**Why.** A map of the frozen newly bare layer (descriptive, after the `exposure.csv` commit d2411cf) shows that it is
dominated by large, blocky patches:
- market-garden harvest around Pukekohe;
- plantation-forest harvest, for example Woodhill.

The forested Waitākere slip country shows few newly bare cells. The primary exposure therefore mixes storm slips with
seasonal harvest. It stays primary, as preregistered.

**Added secondary analysis** (reported as such):
- Newly bare 20 m cells are grouped into 8-connected patches.
- The exposure counts only patches of at most 1 ha (25 cells), the size of most rainfall-triggered slips.
- Terciles and the H1 and H2 models are re-run on this exposure.

It was defined while `analysis.py` was running and before any of its output was read. The share of newly bare area in
patches larger than 5 ha is reported, as a measure of how much of the primary exposure is harvest-like.

## D4 — 2026-10-23 09:35 NZDT — metals reported as not estimable (after the analysis ran)

The first analysis run reported copper, zinc and lead as β = 0 with interval [0, 0]. In 2023 those metals were
sampled at 12 Auckland sites: 8 in the bottom exposure tercile and none in the top. The treatment column was therefore
all zeros, and the pseudo-inverse returned 0. These outcomes are now reported as not estimable whenever there are
fewer than 3 top-tercile and 3 bottom-tercile rows in 2023. Nothing else changes, and no verdict depends on these
outcomes.

## D5 — 2026-10-23 15:22 NZDT — changes after the independent review (review/review.md, "publish with edits")

No computation changes. The verdicts stand: H1 and H2 Inconclusive. The text changes as follows.

1. **The exposure.** It measures newly bare land, which is mostly harvest. Newly bare density is 3.3% at Pukekohe and
   1.1% at Woodhill, against 0.02–0.12% in the known slip clusters. H1 and H2 therefore did not test storm exposure,
   and the title and conclusions no longer say the mud "did not follow the stripped land".
2. **H2 is a two-site test.** 87% of its identifying variation is in Manukau (Auckland Airport 59%, Clarks Beach 28%);
   the effective number of clusters is 1.3 of 13. The CR2 interval is anti-conservative here, so "would read as
   Refuted" is struck.
3. **The 2023 top-minus-bottom difference.** At +1.96 it is the largest in the 15-year series (2.9 SD of 2010–2021) and
   larger than every placebo. But 2022 was already +1.45 (event study) or +1.61 (same estimator), so 2023 exceeds the
   pre-storm year by about 0.3–0.5 pp.
4. **The region-wide pulse** survives the review's artefact checks:
   - continuous sites +4.58 against returning sites +2.98;
   - the 2024 fade holds within the same 42 sites;
   - leaving each year out, 2023 is still the largest;
   - the value format changed in 2020, not 2023.

   But it is concentrated: 6 harbours at +4 to +16, and 7 at +2.6 or less; the site median is +2.6, and the
   harbour-clustered interval 2.3–7.0. The Waikato comparison sites are the Firth of Thames, Raglan and Tairua, and
   their +5.4 comes from one site at +24.6. `regional_2023.json` carries two Auckland 2024 values (1.10 and 2.26)
   because the site sets differ (the 56 frozen sites against all Auckland sites with at least 5 pre-years).
5. **Smaller items:**
   - Dropping year-only rows drops the 11 biennially sampled Waitematā Central sites.
   - Co-located sites share almost all their contributing land (Jaccard 0.92–1.00), so the top tercile holds about 7
     distinct exposures; H1's effective number of clusters is 7.6 of 11.
   - LAWA's own label is "Macrofauna – benthic health score".
   - The sea mask also classes the lower Waikato River, Lakes Waikare and Whangape, and the Aka Aka polder as sea. All
     are more than 20 km from any site, with no effect on contributing land.
6. **F3's title** no longer claims "no dose-response".
