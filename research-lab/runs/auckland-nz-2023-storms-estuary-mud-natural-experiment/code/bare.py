"""Newly bare ground (plan section 2), on the 20 m routing grid.

For each 20.48 km block of the routing grid holding land that any site's C(10 km) or 10 km radius needs:
- every Sentinel-2 L2A scene of the window (catalogue cloud below 80%) that overlaps the block is read at 10 m on a
  NZTM grid (WarpedVRT); its SCL is read first at 20 m and a scene with under 2% clear land in the block is skipped;
- NDVI = (NIR - red) / (NIR + red) on clear land pixels (SCL 4 or 5), with the reflectance offset rule in s2.py;
- per pixel, the median NDVI over clear observations, before (1 Nov - 31 Dec 2022) and after (15 Feb - 30 Apr 2023);
  a pixel needs at least 2 clear observations in each window;
- newly bare: NDVI at least 0.5 before and at most 0.3 after.

Writes data/bare20.tif on the routing grid: band 1 = newly bare 10 m pixels per 20 m cell (0-4), band 2 = pixels
valid in both windows (0-4); and results/tables/bare_log.json.
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s2  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
BLK = 1024                     # 20 m cells per block side
MIN_OBS, NDVI_PRE, NDVI_POST, MIN_CLEAR = 2, 0.5, 0.3, 0.02


def needed_cells(shape):
    z = np.load(RUN / "data" / "contrib.npz")
    need = np.zeros(shape[0] * shape[1], bool)
    for k in z.files:
        if k.endswith("|10"):
            need[z[k]] = True
    return need.reshape(shape)


def footprint_bbox(f):
    import pyproj
    lo, la = np.array(f["bbox"][0::2]), np.array(f["bbox"][1::2])
    x, y = pyproj.Transformer.from_crs(4326, 2193, always_xy=True).transform(lo, la)
    return min(x), min(y), max(x), max(y)


def block_window(feats, tf20, r0, c0, h, w):
    """NDVI median and clear-observation count for one window on the block's 10 m grid."""
    x0, y1 = tf20.c + c0 * 20.0, tf20.f - r0 * 20.0
    x1, y0 = x0 + w * 20.0, y1 - h * 20.0
    tf10, tf20b = from_origin(x0, y1, 10.0, 10.0), from_origin(x0, y1, 20.0, 20.0)
    stack, used = [], 0
    for f in feats:
        fx0, fy0, fx1, fy1 = f["fp"]
        if fx1 < x0 or fx0 > x1 or fy1 < y0 or fy0 > y1:
            continue
        scl20 = s2.read_warped(f["assets"]["scl"]["href"], "EPSG:2193", tf20b, (h, w), Resampling.nearest)
        if np.isin(scl20, s2.CLEAR_LAND).mean() < MIN_CLEAR:
            continue
        r = s2.reflectance(f, ["red", "nir"], "EPSG:2193", tf10, (2 * h, 2 * w))
        if r is None:
            continue
        ref, scl, valid, strip = r
        ok = valid & np.isin(scl, s2.CLEAR_LAND)
        with np.errstate(invalid="ignore", divide="ignore"):
            nd = (ref["nir"] - ref["red"]) / (ref["nir"] + ref["red"])
        stack.append(np.where(ok, nd, np.nan).astype(np.float32))
        used += 1
    if not stack:
        return np.full((2 * h, 2 * w), np.nan, np.float32), np.zeros((2 * h, 2 * w), np.int16), 0
    a = np.stack(stack)
    n = np.isfinite(a).sum(axis=0).astype(np.int16)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            med = np.nanmedian(a, axis=0)
    return med, n, used


def main():
    with rasterio.open(RUN / "data" / "dem20.tif") as ds:
        tf20, shape, crs = ds.transform, ds.shape, ds.crs
    need = needed_cells(shape)
    feats = {w: s2.search(w, max_cloud=80) for w in ("pre", "post")}
    for w in feats:
        for f in feats[w]:
            f["fp"] = footprint_bbox(f)
    blocks = [(r0, c0) for r0 in range(0, shape[0], BLK) for c0 in range(0, shape[1], BLK)
              if need[r0:r0 + BLK, c0:c0 + BLK].any()]
    print(len(blocks), "blocks;", {w: len(v) for w, v in feats.items()}, "scenes", flush=True)
    bare = np.zeros(shape, np.uint8)
    valid = np.zeros(shape, np.uint8)
    log, t0 = [], time.time()

    def one(b):
        r0, c0 = b
        h, w = min(BLK, shape[0] - r0), min(BLK, shape[1] - c0)
        pre, npre, upre = block_window(feats["pre"], tf20, r0, c0, h, w)
        post, npost, upost = block_window(feats["post"], tf20, r0, c0, h, w)
        ok = (npre >= MIN_OBS) & (npost >= MIN_OBS)
        nb = ok & (pre >= NDVI_PRE) & (post <= NDVI_POST)
        agg = lambda m: m.reshape(h, 2, w, 2).sum(axis=(1, 3)).astype(np.uint8)
        return b, agg(nb), agg(ok), {"block": [r0, c0], "scenes_pre": upre, "scenes_post": upost,
                                      "valid_px": int(ok.sum()), "bare_px": int(nb.sum())}
    with ThreadPoolExecutor(4) as ex:
        for k, (b, nb, ok, info) in enumerate(ex.map(one, blocks), 1):
            r0, c0 = b
            bare[r0:r0 + nb.shape[0], c0:c0 + nb.shape[1]] = nb
            valid[r0:r0 + ok.shape[0], c0:c0 + ok.shape[1]] = ok
            log.append(info)
            print(f"{k}/{len(blocks)} {info} {time.time() - t0:.0f} s", flush=True)
    prof = {"driver": "GTiff", "dtype": "uint8", "count": 2, "height": shape[0], "width": shape[1], "crs": crs,
            "transform": tf20, "tiled": True, "compress": "deflate"}
    with rasterio.open(RUN / "data" / "bare20.tif", "w", **prof) as ds:
        ds.write(bare, 1)
        ds.write(valid, 2)
    json.dump({"blocks": log, "thresholds": {"ndvi_pre": NDVI_PRE, "ndvi_post": NDVI_POST, "min_obs": MIN_OBS},
               "scenes": {w: len(v) for w, v in feats.items()}},
              open(RUN / "results" / "tables" / "bare_log.json", "w"), indent=1)


if __name__ == "__main__":
    main()
