"""Sentinel-2 L2A access shared by the sea mask and the bare-ground composites (Earth Search, open COGs).

Reflectance: DN x scale + offset, where the metadata offset (-0.1 for processing baseline 04.00 and later) is applied
only if the data still carry it. Within each read window, if the 0.5th percentile of valid red DN is below 900, the
+1000 DN offset is taken as already removed (with it present, such DN would mean reflectance below -0.01), as in
the reef study's D4.
"""
import json
import urllib.request

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT

STAC = "https://earth-search.aws.element84.com/v1/search"
BBOX = [173.85, -37.5, 175.45, -35.95]
WINDOWS = {"pre": "2022-11-01T00:00:00Z/2022-12-31T23:59:59Z", "post": "2023-02-15T00:00:00Z/2023-04-30T23:59:59Z"}
CLOUD = (3, 8, 9, 10)          # SCL: cloud shadow, medium and high cloud, cirrus
CLEAR_LAND = (4, 5)            # SCL: vegetation, not vegetated


def search(window, max_cloud=80):
    body = {"collections": ["sentinel-2-l2a"], "bbox": BBOX, "datetime": WINDOWS[window], "limit": 200,
            "query": {"eo:cloud_cover": {"lt": max_cloud}}}
    feats, url = [], STAC
    while url:
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "research-lab"})
        r = json.load(urllib.request.urlopen(req, timeout=120))
        feats += r["features"]
        nxt = [l for l in r.get("links", []) if l["rel"] == "next"]
        url, body = (nxt[0]["href"], nxt[0].get("body", body)) if nxt else (None, None)
    for f in feats:
        f["tile"] = f["properties"].get("s2:mgrs_tile") or f["id"].split("_")[1]
    return feats


def band_meta(f, b):
    rb = (f["assets"][b].get("raster:bands") or [{}])[0]
    return rb.get("scale", 1e-4), rb.get("offset", 0.0)


def read_warped(href, crs, transform, shape, resampling, ovr=None):
    with rasterio.open(href, **({} if ovr is None else {"overview_level": ovr})) as src:
        with WarpedVRT(src, crs=crs, transform=transform, width=shape[1], height=shape[0], resampling=resampling,
                       src_nodata=0, nodata=0) as v:
            return v.read(1)


def reflectance(f, bands, crs, transform, shape, ovr10=None):
    """Reflectance of `bands` and the SCL class on a target grid; None where the scene has no data. `ovr10` reads the
    10 m bands from that internal overview (0 = 20 m)."""
    dn = {b: read_warped(f["assets"][b]["href"], crs, transform, shape, Resampling.average,
                         ovr10 if b in ("blue", "green", "red", "nir") else None) for b in bands}
    scl = read_warped(f["assets"]["scl"]["href"], crs, transform, shape, Resampling.nearest)
    valid = scl > 0
    for b in bands:
        valid &= dn[b] > 0
    if not valid.any():
        return None
    red = dn.get("red")
    ref = red if red is not None else dn[bands[0]]
    strip = np.percentile(ref[valid], 0.5) < 900
    out = {}
    for b in bands:
        sc, off = band_meta(f, b)
        if strip:
            off = 0.0
        out[b] = np.where(valid, np.clip(dn[b] * sc + off, 0, None), np.nan).astype(np.float32)
    return out, scl, valid, bool(strip)
