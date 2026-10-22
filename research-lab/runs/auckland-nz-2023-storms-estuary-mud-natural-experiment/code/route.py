"""Routing and contributing land (plan section 2, D1).

On the 20 m grid, receivers come from a priority-flood seeded at the sea and the domain edge (D2), which fills
depressions and drains flats in one pass; every land cell is traced down its flow path to the first sea cell (its
coastal outlet) by pointer jumping. A path that leaves the domain over land ends at an 'edge' outlet.

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
NB8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def priority_flood(dem, sea):
    """D2: receivers by priority-flood (Barnes, Lehman & Mulla 2014). Seeds: sea cells next to land (at -50 m) and land
    cells on the domain edge (at their elevation; they drain off the domain, receiver = self). Land is flooded upward
    in elevation order and each land cell drains to the 8-neighbour it was reached from. Sea cells absorb."""
    import numba

    @numba.njit(cache=False)
    def run(z, sea, seeds_r, seeds_c, seeds_z):
        h, w = z.shape
        rec = np.arange(h * w, dtype=np.int64)
        done = sea.copy()
        n = h * w
        hz = np.empty(n + 16, np.float64)            # binary min-heap of (elevation, cell)
        hi = np.empty(n + 16, np.int64)
        size = 0
        for k in range(len(seeds_r)):
            r, c = seeds_r[k], seeds_c[k]
            cell = r * w + c
            if not sea[r, c]:
                done[r, c] = True
            # push
            hz[size] = seeds_z[k]; hi[size] = cell; j = size; size += 1
            while j > 0:
                p = (j - 1) // 2
                if hz[p] <= hz[j]:
                    break
                hz[p], hz[j] = hz[j], hz[p]; hi[p], hi[j] = hi[j], hi[p]; j = p
        while size > 0:
            zc, cell = hz[0], hi[0]
            size -= 1
            hz[0] = hz[size]; hi[0] = hi[size]
            j = 0
            while True:
                l, rr, m = 2 * j + 1, 2 * j + 2, j
                if l < size and hz[l] < hz[m]:
                    m = l
                if rr < size and hz[rr] < hz[m]:
                    m = rr
                if m == j:
                    break
                hz[m], hz[j] = hz[j], hz[m]; hi[m], hi[j] = hi[j], hi[m]; j = m
            r, c = cell // w, cell % w
            for dr, dc in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= h or nc < 0 or nc >= w or done[nr, nc]:
                    continue
                done[nr, nc] = True
                rec[nr * w + nc] = cell
                zn = max(z[nr, nc], zc)
                hz[size] = zn; hi[size] = nr * w + nc; j = size; size += 1
                while j > 0:
                    p = (j - 1) // 2
                    if hz[p] <= hz[j]:
                        break
                    hz[p], hz[j] = hz[j], hz[p]; hi[p], hi[j] = hi[j], hi[p]; j = p
        return rec

    h, w = dem.shape
    land = ~sea
    from scipy import ndimage
    sea_seed = sea & ndimage.binary_dilation(land, structure=np.ones((3, 3), bool))
    edge = np.zeros_like(sea)
    edge[[0, -1], :] = True
    edge[:, [0, -1]] = True
    edge_seed = edge & land
    sr, sc = np.nonzero(sea_seed)
    er, ec = np.nonzero(edge_seed)
    seeds_r = np.concatenate([sr, er]).astype(np.int64)
    seeds_c = np.concatenate([sc, ec]).astype(np.int64)
    seeds_z = np.concatenate([np.full(len(sr), -50.0), dem[er, ec].astype(np.float64)])
    z = np.where(np.isnan(dem), -50.0, dem).astype(np.float64)
    return run(z, sea, seeds_r, seeds_c, seeds_z)


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
    out = outlets(priority_flood(dem, sea | np.isnan(dem)))
    flat_land = np.nonzero(land.ravel())[0]
    o = out[flat_land]
    is_sea_outlet = sea.ravel()[o]
    r_, c_ = np.divmod(o[~is_sea_outlet], w)
    on_edge = ((r_ == 0) | (r_ == h - 1) | (c_ == 0) | (c_ == w - 1)).mean() if (~is_sea_outlet).any() else 1.0
    print("land cells", len(flat_land), "draining to sea", round(float(is_sea_outlet.mean()), 4),
          "non-sea paths ending on the domain edge", round(float(on_edge), 4), flush=True)
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
