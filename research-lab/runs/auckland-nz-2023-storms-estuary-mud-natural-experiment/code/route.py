"""Routing and contributing land (plan section 2, D1).

On the 20 m grid: sea cells are set to -50 m (sloping gently away from land) so that every land cell can drain to them; depressions are filled
and flats resolved (pysheds); D8 flow directions; every land cell is traced down its flow path to the first sea cell
(its coastal outlet) by pointer jumping. A path that leaves the domain over land ends at an 'edge' outlet.

Contributing land C(R) of a site: land cells whose coastal outlet lies within R km of the site (R = 2, 5, 10).
Radius-only land (D1 sensitivity): land cells within R km of the site.

Writes data/contrib.npz (flat cell indices per site and R, for both definitions) and
results/tables/contrib_summary.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import rasterio
from scipy.spatial import cKDTree

RUN = Path(__file__).resolve().parents[1]
RADII = (2, 5, 10)
# pysheds D8 codes: N, NE, E, SE, S, SW, W, NW
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)
STEP = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}


def flowdir(dem_path, sea):
    from pysheds.grid import Grid
    grid = Grid.from_raster(str(dem_path))
    dem = grid.read_raster(str(dem_path), band=1)
    a = np.asarray(dem, dtype=np.float64)
    # sea at -50 m, sloping gently away from land so that it holds no flats for resolve_flats to work through
    from scipy import ndimage
    dist = ndimage.distance_transform_edt(sea)
    a = np.where(np.isnan(a) | sea, -50.0 - 1e-3 * dist, a)
    dem[:] = a
    dem.nodata = -9999.0
    filled = grid.fill_depressions(grid.fill_pits(dem))
    inflated = grid.resolve_flats(filled)
    return np.asarray(grid.flowdir(inflated, dirmap=DIRMAP), dtype=np.int32)


def receivers(fd, sea):
    h, w = fd.shape
    idx = np.arange(h * w, dtype=np.int64).reshape(h, w)
    rec = idx.copy()
    for code, (dr, dc) in STEP.items():
        m = fd == code
        r = np.arange(h)[:, None] + dr
        c = np.arange(w)[None, :] + dc
        inside = (r >= 0) & (r < h) & (c >= 0) & (c < w)
        m &= inside
        rr, cc = np.nonzero(m)
        rec[rr, cc] = idx[rr + dr, cc + dc]
    rec = rec.ravel()
    rec[sea.ravel()] = np.nonzero(sea.ravel())[0]          # sea cells absorb
    return rec


def outlets(rec):
    r = rec.copy()
    for _ in range(64):
        nr = r[r]
        if np.array_equal(nr, r):
            break
        r = nr
    return r


def main():
    dem_path = RUN / "data" / "dem20.tif"
    with rasterio.open(dem_path) as ds:
        dem, tf = ds.read(1), ds.transform
    with rasterio.open(RUN / "data" / "sea20.tif") as ds:
        sea = ds.read(1).astype(bool)
    h, w = dem.shape
    land = ~sea & ~np.isnan(dem)
    fd = flowdir(dem_path, sea)
    out = outlets(receivers(fd, sea))
    flat_land = np.nonzero(land.ravel())[0]
    o = out[flat_land]
    is_sea_outlet = sea.ravel()[o]
    print("land cells", len(flat_land), "draining to sea", round(float(is_sea_outlet.mean()), 4), flush=True)
    # outlet coordinates
    orow, ocol = np.divmod(o, w)
    ox, oy = tf.c + (ocol + 0.5) * tf.a, tf.f + (orow + 0.5) * tf.e
    lrow, lcol = np.divmod(flat_land, w)
    lx, ly = tf.c + (lcol + 0.5) * tf.a, tf.f + (lrow + 0.5) * tf.e
    s = pd.read_csv(RUN / "results" / "tables" / "sites.csv")
    tr = pyproj.Transformer.from_crs(4326, 2193, always_xy=True)
    sx, sy = tr.transform(s.lon.to_numpy(), s.lat.to_numpy())
    uo, inv = np.unique(o[is_sea_outlet], return_inverse=True)
    uox, uoy = tf.c + (uo % w + 0.5) * tf.a, tf.f + (uo // w + 0.5) * tf.e
    otree = cKDTree(np.column_stack([uox, uoy]))
    ltree = cKDTree(np.column_stack([lx, ly]))
    sea_land_idx = flat_land[is_sea_outlet]
    store, rows = {}, []
    edge_cells = np.zeros(h * w, bool)
    edge_cells.reshape(h, w)[[0, -1], :] = True
    edge_cells.reshape(h, w)[:, [0, -1]] = True
    for i, site in enumerate(s.site_id):
        for R in RADII:
            near = otree.query_ball_point([sx[i], sy[i]], R * 1000.0)
            sel = np.isin(inv, near)
            cells = sea_land_idx[sel]
            rad = flat_land[ltree.query_ball_point([sx[i], sy[i]], R * 1000.0)]
            store[f"{site}|route|{R}"] = cells.astype(np.int64)
            store[f"{site}|radius|{R}"] = np.sort(rad).astype(np.int64)
            rows.append({"site_id": site, "R_km": R, "route_cells": int(len(cells)), "route_km2": len(cells) * 4e-4,
                         "radius_cells": int(len(rad)), "touches_edge": bool(edge_cells[cells].any()),
                         "outlets": len(near)})
    np.savez_compressed(RUN / "data" / "contrib.npz", **store)
    pd.DataFrame(rows).to_csv(RUN / "results" / "tables" / "contrib_summary.csv", index=False)
    d = pd.DataFrame(rows)
    print(d.groupby("R_km")[["route_km2", "outlets"]].describe().round(1).to_string())
    print("touching edge:", d[d.touches_edge][["site_id", "R_km"]].values.tolist())


if __name__ == "__main__":
    sys.exit(main())
