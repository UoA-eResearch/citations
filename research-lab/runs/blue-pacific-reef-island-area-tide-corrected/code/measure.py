"""Per-scene islet areas (plan section 2), read on the fly from cloud-optimised GeoTIFFs; only per-islet results kept.

  measure.py ATOLL SENSOR [--limit N] [--threads T]     SENSOR: s2 | ls | l1 (Collection 1 Level-1, D1)

For each scene, every islet window inside the scene's footprint is read once per band:
- green, SWIR1 and NIR are converted to reflectance with the item's own scale and offset;
- the 20 m Sentinel-2 bands are resampled to the 10 m green grid.

For each islet (at least 1 ha; engineered islets included and flagged):
- the area of interest is the islet ring buffered by 60 m (Sentinel-2) or 90 m (Landsat);
- the clear share comes from SCL classes 4, 5, 6 and 11, or Landsat QA_PIXEL clear or water, not fill;
- MNDWI with Otsu's threshold (primary), MNDWI at 0, and NDWI with Otsu;
- the area is the land pixels of the connected components that overlap the islet ring.

Writes data/areas/<atoll>_<sensor>.parquet (appending in chunks; resumable by scene id).
"""
import argparse
import json
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import rasterio
import shapely
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds
from skimage.filters import threshold_otsu
from skimage.measure import label

RUN = Path(__file__).resolve().parents[1]
os.environ.update({"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR", "AWS_NO_SIGN_REQUEST": "YES",
                   "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.TIF", "GDAL_HTTP_MULTIRANGE": "YES",
                   "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES", "GDAL_HTTP_MAX_RETRY": "5", "GDAL_HTTP_RETRY_DELAY": "2",
                   "VSI_CACHE": "TRUE"})
BUF = {"s2": 60.0, "ls": 90.0, "l1": 90.0}
MIN_HA = 1.0
S2_CLEAR = {4, 5, 6, 11}
_tok = {"t": None, "exp": 0.0}
_lock = threading.Lock()


def pc_token():
    with _lock:
        if time.time() > _tok["exp"]:
            with urllib.request.urlopen("https://planetarycomputer.microsoft.com/api/sas/v1/token/landsat-c2-l2",
                                        timeout=60) as r:
                _tok["t"] = json.loads(r.read())["token"]
            _tok["exp"] = time.time() + 40 * 60
        return _tok["t"]


def href(h, sensor):
    return f"{h}?{pc_token()}" if sensor == "ls" else h


def islets(atoll):
    inv = pd.read_csv(RUN / "data" / "inventory.csv")
    inv = inv[(inv.atoll == atoll) & (inv.area_ha >= MIN_HA)].reset_index(drop=True)
    inv["geom"] = shapely.from_wkt(inv.wkt)
    return inv


def windows_for(inv, epsg, buf, res, max_m=6000.0, gap=400.0):
    """Islet AOIs in the scene CRS, grouped into windows (bounding boxes merged when closer than `gap`)."""
    tr = pyproj.Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    geoms = [shapely.transform(g, lambda xy: np.column_stack(tr.transform(xy[:, 0], xy[:, 1]))) for g in inv.geom]
    aoi = [g.buffer(buf) for g in geoms]
    boxes = [list(a.bounds) for a in aoi]
    groups = [[i] for i in range(len(boxes))]
    gb = [b[:] for b in boxes]
    merged = True
    while merged:
        merged = False
        for i in range(len(gb)):
            for j in range(i + 1, len(gb)):
                a, b = gb[i], gb[j]
                u = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                near = not (a[2] + gap < b[0] or b[2] + gap < a[0] or a[3] + gap < b[1] or b[3] + gap < a[1])
                if near and (u[2] - u[0]) <= max_m and (u[3] - u[1]) <= max_m:
                    gb[i], groups[i] = u, groups[i] + groups[j]
                    del gb[j], groups[j]
                    merged = True
                    break
            if merged:
                break
    pad = 2 * res
    return [{"bounds": (b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad), "islets": g} for b, g in zip(gb, groups)], geoms, aoi


def read(ds, bounds, shape=None):
    w = from_bounds(*bounds, transform=ds.transform).round_offsets().round_lengths()
    w = w.intersection(Window(0, 0, ds.width, ds.height))
    if shape is None:
        return ds.read(1, window=w, boundless=False), ds.window_transform(w)
    return ds.read(1, window=w, out_shape=shape, resampling=Resampling.bilinear), None


def islet_area(mask_land, aoi_mask, ring_mask, pix):
    lab = label(mask_land & aoi_mask, connectivity=2)
    keep = np.unique(lab[ring_mask & (lab > 0)])
    return float(np.isin(lab, keep[keep > 0]).sum() * pix)


def coarse30(gR, sR, clear, tf, aoi_g, ring_g):
    """Sentinel-2 at 30 m for the sensor-step guard: 3x3 block means of reflectance; a block is clear only if all 9
    pixels are; MNDWI with Otsu inside the 30 m area of interest."""
    h, w = (gR.shape[0] // 3) * 3, (gR.shape[1] // 3) * 3
    if h < 6 or w < 6:
        return {}
    blk = lambda a: a[:h, :w].reshape(h // 3, 3, w // 3, 3).mean(axis=(1, 3))
    g3, s3 = blk(np.nan_to_num(gR)), blk(np.nan_to_num(sR))
    c3 = clear[:h, :w].reshape(h // 3, 3, w // 3, 3).all(axis=(1, 3))
    tf3 = tf * tf.scale(3)
    am = ~geometry_mask([aoi_g], out_shape=g3.shape, transform=tf3)
    rm = ~geometry_mask([ring_g], out_shape=g3.shape, transform=tf3)
    with np.errstate(divide="ignore", invalid="ignore"):
        m3 = (g3 - s3) / (g3 + s3)
    v = m3[am & c3]
    v = v[np.isfinite(v)]
    if v.size <= 10 or v.min() == v.max() or not rm.any():
        return {}
    t = float(threshold_otsu(v))
    return {"area_otsu_30m": islet_area(m3 < t, am, rm, abs(tf3.a * tf3.e)), "clear_30m": round(float(c3[am].mean()), 4)}


def precheck(q, sensor, islets_, shp, tf, geoms, aoi):
    """The D2 cloud test from the cloud band alone: would each islet pass it (nodata judged from the cloud band)?"""
    if sensor == "s2":
        cl_out, cl_in, nod = np.isin(q, [3, 8, 9, 10]), np.isin(q, [3, 9, 10]), q == 0
    else:
        cc, sc_ = (q >> 5) & 3, (q >> 7) & 3
        cl_out = (((q >> 4) & 1) == 1) | (cc >= 2) | (sc_ >= 2)
        cl_in, nod = (cc == 3) | (sc_ >= 2), (q & 1) == 1
    res = {}
    for i in islets_:
        am = ~geometry_mask([aoi[i]], out_shape=shp, transform=tf)
        inner = ~geometry_mask([geoms[i].buffer(2 * abs(tf.a))], out_shape=shp, transform=tf) & am
        outer = am & ~inner
        ok = bool(am.any() and outer.any() and inner.any() and nod[am].mean() <= 0.01
                  and cl_out[outer].mean() <= 0.05 and cl_in[inner].mean() <= 0.05)
        res[i] = ok
    return res


def scene(row, sensor, inv, wins, geoms, aoi):
    out = []
    try:
        with rasterio.Env():
            g = rasterio.open(href(row["green"], sensor))
            if not shapely.box(*g.bounds).intersects(shapely.box(*wins[0]["bounds"])) and not any(
                    shapely.box(*g.bounds).intersects(shapely.box(*w["bounds"])) for w in wins):
                return out
            sw = rasterio.open(href(row["swir16"], sensor))
            ni = rasterio.open(href(row["nir"], sensor))
            qa = rasterio.open(href(row["scl"] if sensor == "s2" else row["qa"], sensor))
            fb = shapely.box(*g.bounds)
            for w in wins:
                if not fb.contains(shapely.box(*w["bounds"])):
                    continue
                # the window's grid from the green band's header; the cloud band is read first, and the reflectance
                # bands only if some islet in the window passes the cloud test (efficiency; same decisions)
                win = from_bounds(*w["bounds"], transform=g.transform).round_offsets().round_lengths()
                win = win.intersection(Window(0, 0, g.width, g.height))
                shp, tf = (int(win.height), int(win.width)), g.window_transform(win)
                if shp[0] == 0 or shp[1] == 0:
                    continue
                q, _ = read(qa, w["bounds"], shp) if sensor == "s2" else read(qa, w["bounds"])
                q = q.astype(np.int64)
                if q.shape != shp:
                    q = q[:shp[0], :shp[1]]
                    if q.shape != shp:
                        continue
                pre = precheck(q, sensor, w["islets"], shp, tf, geoms, aoi)
                if not any(pre.values()):
                    for i in w["islets"]:
                        out.append({"atoll": inv.atoll[i], "islet": inv.islet[i], "scene": row["id"],
                                    "datetime": row["datetime"], "sensor": sensor if sensor == "s2" else row["platform"],
                                    "aoi_pixels": -1, "clear": 0.0, "skipped_by_cloud_precheck": 1})
                    continue
                gr = g.read(1, window=win)
                s1, _ = read(sw, w["bounds"], shp)
                n1, _ = read(ni, w["bounds"], shp)
                valid = (gr > 0) & (s1 > 0)
                off = {b: row[f"{b}_offset"] for b in ("green", "swir16", "nir")}
                if sensor == "s2" and off["swir16"] < 0 and valid.any() and np.percentile(s1[valid], 1) < 500:
                    # D4: clear water cannot have negative SWIR reflectance; DN this low means the +1000 offset is
                    # already removed from this item's data, so the metadata offset is not applied again
                    off = {b: 0.0 for b in off}
                gR = np.clip(gr * row["green_scale"] + off["green"], 0, None)     # D2: clip at 0
                sR = np.clip(s1 * row["swir16_scale"] + off["swir16"], 0, None)
                nR = np.clip(n1 * row["nir_scale"] + off["nir"], 0, None)
                # D2: cloud is judged separately over the water around the islet (any cloud or shadow) and over the
                # islet itself (high-confidence cloud, cirrus or shadow only), because the scene classification marks
                # bright coral sand and roofs as medium-probability cloud or unclassified
                if sensor == "s2":
                    cl_out = np.isin(q, [3, 8, 9, 10])
                    cl_in = np.isin(q, [3, 9, 10])
                else:                    # Collection 1 BQA: cloud bit 4, cloud confidence bits 5-6, shadow bits 7-8
                    cc, sc_ = (q >> 5) & 3, (q >> 7) & 3
                    cl_out = (((q >> 4) & 1) == 1) | (cc >= 2) | (sc_ >= 2)
                    cl_in = (cc == 3) | (sc_ >= 2)
                with np.errstate(divide="ignore", invalid="ignore"):
                    mndwi = (gR - sR) / (gR + sR)
                    ndwi = (gR - nR) / (gR + nR)
                mndwi[~valid] = np.nan
                ndwi[~valid] = np.nan
                pix = abs(tf.a * tf.e)
                for i in w["islets"]:
                    am = ~geometry_mask([aoi[i]], out_shape=shp, transform=tf)
                    rm = ~geometry_mask([geoms[i]], out_shape=shp, transform=tf)
                    inner = ~geometry_mask([geoms[i].buffer(2 * pix ** 0.5)], out_shape=shp, transform=tf) & am
                    outer = am & ~inner
                    n = int(am.sum())
                    vshare = float(valid[am].mean()) if n else 0.0
                    co = float(cl_out[outer].mean()) if outer.any() else 1.0
                    ci = float(cl_in[inner].mean()) if inner.any() else 1.0
                    rec = {"atoll": inv.atoll[i], "islet": inv.islet[i], "scene": row["id"], "datetime": row["datetime"],
                           "sensor": sensor if sensor == "s2" else row["platform"], "aoi_pixels": n,
                           "valid": round(vshare, 4), "cloud_outer": round(co, 4), "cloud_inner": round(ci, 4),
                           "clear": round(1 - max(co, ci), 4)}
                    if n and vshare >= 0.99 and co <= 0.05 and ci <= 0.05 and rm.any():
                        v = mndwi[am & valid]
                        v = v[np.isfinite(v)]          # 0/0 where both reflectances clip to 0 (bug fix, D4)
                        t = float(threshold_otsu(v)) if v.size > 10 and v.min() < v.max() else np.nan
                        vn = ndwi[am & valid]
                        vn = vn[np.isfinite(vn)]
                        tn = float(threshold_otsu(vn)) if vn.size > 10 and vn.min() < vn.max() else np.nan
                        if not (np.isfinite(t) and np.isfinite(tn)):
                            out.append(rec)
                            continue
                        rec.update({"otsu_t": round(t, 4), "area_otsu": islet_area(mndwi < t, am, rm, pix),
                                    "area_fixed": islet_area(mndwi < 0, am, rm, pix),
                                    "area_ndwi": islet_area(ndwi < tn, am, rm, pix), "pixel_m2": pix})
                        if sensor == "s2":
                            rec.update(coarse30(gR, sR, valid, tf, aoi[i], geoms[i]))
                    out.append(rec)
            for d in (g, sw, ni, qa):
                d.close()
    except Exception as e:
        out.append({"atoll": inv.atoll[0], "islet": "", "scene": row["id"], "datetime": row["datetime"],
                    "sensor": sensor, "error": repr(e)[:200]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("atoll"); ap.add_argument("sensor"); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--threads", type=int, default=32)
    a = ap.parse_args()
    inv = islets(a.atoll)
    sc = pd.read_parquet(RUN / "data" / "scenes" / f"{a.atoll}_{a.sensor}.parquet")
    outp = RUN / "data" / "areas" / f"{a.atoll}_{a.sensor}.parquet"
    outp.parent.mkdir(parents=True, exist_ok=True)
    done = set(pd.read_parquet(outp).scene) if outp.exists() else set()
    sc = sc[~sc.id.isin(done)]
    if a.limit:
        sc = sc.head(a.limit)
    res = 10.0 if a.sensor == "s2" else 30.0
    cache = {}
    rows, t0, k = [], time.time(), 0
    with ThreadPoolExecutor(a.threads) as ex:
        futs = []
        for _, r in sc.iterrows():
            ep = int(r["epsg"])
            if ep not in cache:
                cache[ep] = windows_for(inv, ep, BUF[a.sensor], res)
            futs.append(ex.submit(scene, r, a.sensor, inv, *cache[ep]))
        for f in as_completed(futs):
            rows += f.result()
            k += 1
            if k % 50 == 0 or k == len(futs):
                d = pd.DataFrame(rows)
                if outp.exists():
                    d = pd.concat([pd.read_parquet(outp), d], ignore_index=True)
                d.to_parquet(outp, index=False)
                rows = []
                print(f"{a.atoll} {a.sensor}: {k}/{len(futs)} scenes, {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
