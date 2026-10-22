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
