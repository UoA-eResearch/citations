"""Sea mask on the 20 m routing grid (D1).

Water: NDWI = (green - NIR) / (green + NIR) > 0 in the clearest post-storm Sentinel-2 scenes (up to 3 per tile,
lowest catalogue cloud cover first), read from the 20 m overview; a cell is water if it is water in most of its
clear observations (SCL not cloud, shadow or cirrus).

Sea (D1 and its addendum): DEM no-data, DEM at or below 0 m (the LiDAR surface over harbour water is hydro-flattened
near -1.15 m), or water, kept only where connected (8-neighbour) to the domain edge, so lakes and inland ponds are
not sea. The per-scene water counts are cached in data/water_counts.npz.

Writes data/sea20.tif (1 = sea, 0 = land) and results/tables/seamask_log.json.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s2  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PER_TILE = 3


def main():
    with rasterio.open(RUN / "data" / "dem20.tif") as ds:
        dem, tf, crs, shape = ds.read(1), ds.transform, ds.crs, ds.shape
    cache = RUN / "data" / "water_counts.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        water_n, clear_n, log = z["water_n"], z["clear_n"], list(z["log"])
    else:
        water_n, clear_n, log = scenes(shape, crs, tf)
        np.savez_compressed(cache, water_n=water_n, clear_n=clear_n, log=np.array(log, dtype=object))
    water = (clear_n > 0) & (2 * water_n > clear_n)
    low = ~np.isnan(dem) & (dem <= 0.0)
    cand = water | np.isnan(dem) | low
    lab, n = ndimage.label(cand, structure=np.ones((3, 3), bool))
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    sea = np.isin(lab, edge[edge > 0])
    prof = {"driver": "GTiff", "dtype": "uint8", "count": 1, "height": shape[0], "width": shape[1], "crs": crs,
            "transform": tf, "tiled": True, "compress": "deflate"}
    with rasterio.open(RUN / "data" / "sea20.tif", "w", **prof) as ds:
        ds.write(sea.astype(np.uint8), 1)
    out = {"scenes": log, "cells": int(sea.size), "sea_cells": int(sea.sum()),
           "sea_from_dem_nodata": int((sea & np.isnan(dem)).sum()),
           "sea_from_dem_at_or_below_0m_only": int((sea & low & ~water).sum()),
           "sea_from_s2_water_only": int((sea & water & ~low & ~np.isnan(dem)).sum()),
           "never_clear_land_cells": int(((clear_n == 0) & ~np.isnan(dem)).sum()),
           "water_not_connected_cells": int((water & ~sea).sum())}
    json.dump(out, open(RUN / "results" / "tables" / "seamask_log.json", "w"), indent=1, default=str)
    print({k: v for k, v in out.items() if k != "scenes"})


def scenes(shape, crs, tf):
    feats = s2.search("post", max_cloud=40)
    by_tile = {}
    for f in sorted(feats, key=lambda f: f["properties"]["eo:cloud_cover"]):
        by_tile.setdefault(f["tile"], [])
        if len(by_tile[f["tile"]]) < PER_TILE:
            by_tile[f["tile"]].append(f)
    use = [f for v in by_tile.values() for f in v]
    water_n = np.zeros(shape, np.uint8)
    clear_n = np.zeros(shape, np.uint8)
    log = []

    def one(f):
        r = s2.reflectance(f, ["green", "nir"], crs, tf, shape, ovr10=0)
        if r is None:
            return f["id"], None
        ref, scl, valid, strip = r
        ok = valid & ~np.isin(scl, s2.CLOUD)
        with np.errstate(invalid="ignore", divide="ignore"):
            ndwi = (ref["green"] - ref["nir"]) / (ref["green"] + ref["nir"])
        return f["id"], (ok, ok & (ndwi > 0), strip)
    with ThreadPoolExecutor(6) as ex:
        for fid, r in ex.map(one, use):
            if r is None:
                log.append({"scene": fid, "used": False}); continue
            ok, wat, strip = r
            clear_n += ok.astype(np.uint8)
            water_n += wat.astype(np.uint8)
            log.append({"scene": fid, "used": True, "clear_cells": int(ok.sum()), "offset_already_removed": strip})
            print(fid, int(ok.sum()), flush=True)
    return water_n, clear_n, log


if __name__ == "__main__":
    main()
