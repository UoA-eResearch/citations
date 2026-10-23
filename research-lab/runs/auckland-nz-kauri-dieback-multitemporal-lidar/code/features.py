"""Labels and LiDAR features (plan sections 1-2).

  features.py mosaics   1 m DSM/DEM mosaics of the Waitakere survey extent (+100 m) for E1 (North 2016-18) and E2
                        (2024 Parts 1 and 2), cached as data/mosaic_<name>.tif
  features.py trees     labels (2014-15 and 2021 surveys; duplicates within 2 m with the same status merged), circle
                        features at 10, 15 and 20 m, the slip mask, static features, OSM track distance, and 1,000
                        random stable-area points -> results/tables/trees.csv (no coordinates) and data/trees_xy.parquet
"""
import json
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.windows import from_bounds

RUN = Path(__file__).resolve().parents[1]
DATA = RUN / "data"
BUCKET = "https://nz-elevation.s3.ap-southeast-2.amazonaws.com/"
COLL = {"e1_dsm": ["auckland/auckland-north_2016-2018/dsm_1m/2193/"],
        "e1_dem": ["auckland/auckland-north_2016-2018/dem_1m/2193/"],
        "e2_dsm": ["auckland/auckland-part-1_2024/dsm_1m/2193/", "auckland/auckland-part-2_2024/dsm_1m/2193/"],
        "e2_dem": ["auckland/auckland-part-1_2024/dem_1m/2193/", "auckland/auckland-part-2_2024/dem_1m/2193/"]}
SURVEYS = {"Waitakere Track Survey 2014-2015": "s2014", "Waitakere Survey 2021": "s2021"}
RADII, SEED = (10, 15, 20), 20261023


def extent():
    d = pd.read_parquet(DATA / "raw" / "obskauri.parquet")
    d = d[d.SurveyName.isin(SURVEYS)]
    return (np.floor(d.x.min() - 100), np.floor(d.y.min() - 100), np.ceil(d.x.max() + 100), np.ceil(d.y.max() + 100))


def items(prefix):
    c = json.load(urllib.request.urlopen(BUCKET + prefix + "collection.json", timeout=60))

    def get(l):
        it = json.load(urllib.request.urlopen(BUCKET + prefix + l["href"].lstrip("./"), timeout=60))
        a = next(iter(it["assets"].values()))["href"]
        return it["bbox"], a if a.startswith("http") else BUCKET + prefix + a.lstrip("./")
    with ThreadPoolExecutor(32) as ex:
        return list(ex.map(get, [l for l in c["links"] if l["rel"] == "item"]))


def mosaic(name):
    import pyproj
    x0, y0, x1, y1 = extent()
    W, H = int(x1 - x0), int(y1 - y0)
    out = np.full((H, W), np.nan, np.float32)
    tr = pyproj.Transformer.from_crs(2193, 4326, always_xy=True)
    lo, la = tr.transform([x0, x1, x0, x1], [y0, y0, y1, y1])
    sel = [h for p in COLL[name] for b, h in items(p)
           if not (b[2] < min(lo) or b[0] > max(lo) or b[3] < min(la) or b[1] > max(la))]

    def one(h):
        with rasterio.open(h) as ds:
            ib = ds.bounds
            ox0, oy0, ox1, oy1 = max(ib.left, x0), max(ib.bottom, y0), min(ib.right, x1), min(ib.top, y1)
            if ox0 >= ox1 or oy0 >= oy1:
                return None
            a = ds.read(1, window=from_bounds(ox0, oy0, ox1, oy1, ds.transform), masked=True,
                        out_shape=(int(round(oy1 - oy0)), int(round(ox1 - ox0))), resampling=Resampling.nearest)
            return int(round(y1 - oy1)), int(round(ox0 - x0)), a.filled(np.nan).astype(np.float32)
    with ThreadPoolExecutor(12) as ex:
        for r in ex.map(one, sel):
            if r is None:
                continue
            r0, c0, a = r
            blk = out[r0:r0 + a.shape[0], c0:c0 + a.shape[1]]
            m = np.isnan(blk) & ~np.isnan(a)
            blk[m] = a[m]
    prof = {"driver": "GTiff", "dtype": "float32", "count": 1, "height": H, "width": W, "crs": "EPSG:2193",
            "transform": from_origin(x0, y1, 1.0, 1.0), "nodata": np.nan, "tiled": True, "compress": "deflate",
            "BIGTIFF": "YES"}
    with rasterio.open(DATA / f"mosaic_{name}.tif", "w", **prof) as ds:
        ds.write(out, 1)
    print(name, len(sel), "tiles; valid share", round(float((~np.isnan(out)).mean()), 4), flush=True)


def labels():
    d = pd.read_parquet(DATA / "raw" / "obskauri.parquet")
    d = d[d.SurveyName.isin(SURVEYS) & d.KDBFieldStatus.isin([1, 3, 4])].copy()
    d["survey"] = d.SurveyName.map(SURVEYS)
    d["status"] = d.KDBFieldStatus.astype(int)
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    from scipy.spatial import cKDTree
    rows = []
    for (sv, st), g in d.groupby(["survey", "status"]):
        g = g.sort_values("OBJECTID").reset_index(drop=True)
        # D1: single-linkage merge of records within 2 m of each other with the same status (the plan's rule)
        pairs = cKDTree(g[["x", "y"]].to_numpy()).query_pairs(2.0, output_type="ndarray")
        n = len(g)
        adj = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n)) if len(pairs) else coo_matrix((n, n))
        _, comp = connected_components(adj, directed=False)
        rows.append(g.loc[~pd.Series(comp).duplicated().to_numpy()])
    t = pd.concat(rows)
    return t[["OBJECTID", "survey", "status", "x", "y"]].reset_index(drop=True)


def tracks(bounds):
    import pyproj
    x0, y0, x1, y1 = bounds
    tr = pyproj.Transformer.from_crs(2193, 4326, always_xy=True)
    lo, la = tr.transform([x0, x1], [y0, y1])
    q = f'[out:json][timeout:180];way["highway"~"^(path|footway|track)$"]({la[0]},{lo[0]},{la[1]},{lo[1]});out geom;'
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode(),
                                 headers={"User-Agent": "research-lab (University of Auckland)"})
    cache = DATA / "raw" / "osm_tracks.json"
    if cache.exists():
        r = json.load(open(cache))
    else:
        import time
        for k in range(5):
            try:
                r = json.loads(urllib.request.urlopen(req, timeout=300).read())
                break
            except Exception as e:
                print("overpass retry", k, repr(e)[:80], flush=True)
                time.sleep(30 * (k + 1))
        else:
            raise RuntimeError("Overpass failed repeatedly")
        json.dump(r, open(cache, "w"))
    back = pyproj.Transformer.from_crs(4326, 2193, always_xy=True)
    pts = []
    for w in r["elements"]:
        g = w.get("geometry") or []
        xs, ys = back.transform([p["lon"] for p in g], [p["lat"] for p in g])
        for i in range(len(xs) - 1):                    # densify to 2 m so a KD-tree gives the distance to the line
            n = max(1, int(np.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) // 2))
            pts += list(zip(np.linspace(xs[i], xs[i + 1], n, endpoint=False), np.linspace(ys[i], ys[i + 1], n, endpoint=False)))
    return np.array(pts), len(r["elements"])


def circle_stats(rs, x, y, R):
    """P95, P50 and share > 15 m of CHM in each epoch, the valid share, and the masked share, within radius R."""
    with rasterio.open(DATA / "mosaic_e1_dsm.tif") as ds:
        tf = ds.transform
    c0, r0 = ~tf * (x, y)
    c0, r0 = np.floor(c0).astype(int), np.floor(r0).astype(int)
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
    disk = (xx ** 2 + yy ** 2) <= R * R
    dy, dx = yy[disk], xx[disk]
    e1, e2, dem1, dem2 = rs
    H, W = e1.shape
    out = []
    for r, c in zip(r0, c0):
        rr, cc = r + dy, c + dx
        ok = (rr >= 0) & (rr < H) & (cc >= 0) & (cc < W)
        rr, cc = rr[ok], cc[ok]
        a1, a2 = e1[rr, cc] - dem1[rr, cc], e2[rr, cc] - dem2[rr, cc]
        slip = np.abs(dem2[rr, cc] - dem1[rr, cc]) > 1.0
        v = np.isfinite(a1) & np.isfinite(a2)
        vm = v & ~slip
        n = len(dy)
        row = {"valid": v.sum() / n, "valid_masked": vm.sum() / n, "slip_share": float(slip[v].mean()) if v.any() else np.nan}
        for tag, m in (("m", vm), ("u", v)):
            if m.sum() >= 0.5 * n:
                b1, b2 = np.clip(a1[m], 0, None), np.clip(a2[m], 0, None)
                row[f"p95_e1_{tag}"], row[f"p95_e2_{tag}"] = np.percentile(b1, 95), np.percentile(b2, 95)
                row[f"p50_e1_{tag}"], row[f"p50_e2_{tag}"] = np.percentile(b1, 50), np.percentile(b2, 50)
                row[f"c15_e1_{tag}"], row[f"c15_e2_{tag}"] = (b1 > 15).mean(), (b2 > 15).mean()
        out.append(row)
    return pd.DataFrame(out)


def trees():
    t = labels()
    rng = np.random.default_rng(SEED)
    x0, y0, x1, y1 = extent()
    rs = []
    for n in ("e1_dsm", "e2_dsm", "e1_dem", "e2_dem"):
        with rasterio.open(DATA / f"mosaic_{n}.tif") as ds:
            rs.append(ds.read(1))
    e1, e2, dem1, dem2 = rs
    # stable-area points: random forest points (E1 P95 > 15 m) at least 50 m from any survey record
    from scipy.spatial import cKDTree
    allpts = pd.read_parquet(DATA / "raw" / "obskauri.parquet")[["x", "y"]].dropna().to_numpy()
    kd = cKDTree(allpts)
    cand = np.column_stack([rng.uniform(x0 + 50, x1 - 50, 20000), rng.uniform(y0 + 50, y1 - 50, 20000)])
    far = kd.query(cand)[0] > 50
    cand = cand[far]
    s = pd.DataFrame({"OBJECTID": -1 - np.arange(len(cand)), "survey": "stable", "status": 0, "x": cand[:, 0], "y": cand[:, 1]})
    allt = pd.concat([t, s], ignore_index=True)
    feats = []
    for R in RADII:
        f = circle_stats((e1, e2, dem1, dem2), allt.x.to_numpy(), allt.y.to_numpy(), R).add_suffix(f"_r{R}")
        feats.append(f)
    allt = pd.concat([allt] + feats, axis=1)
    keep_stable = allt[(allt.survey == "stable") & (allt.get("p95_e1_m_r15") > 15)].head(1000).index
    allt = allt[(allt.survey != "stable") | allt.index.isin(keep_stable)].copy()
    # static: elevation and slope from E1 DEM (3x3 at 1 m, then mean over the 15 m circle via the centre cell)
    with rasterio.open(DATA / "mosaic_e1_dem.tif") as ds:
        tf = ds.transform
    c, r = ~tf * (allt.x.to_numpy(), allt.y.to_numpy())
    r, c = np.floor(r).astype(int), np.floor(c).astype(int)
    gy, gx = np.gradient(dem1)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    allt["elev"] = dem1[r, c]
    allt["slope"] = np.array([np.nanmean(slope[max(0, a - 7):a + 8, max(0, b - 7):b + 8]) for a, b in zip(r, c)])
    tp, nways = tracks((x0, y0, x1, y1))
    allt["dist_track"] = cKDTree(tp).query(allt[["x", "y"]].to_numpy())[0] if len(tp) else np.nan
    allt[["OBJECTID", "x", "y"]].to_parquet(DATA / "trees_xy.parquet", index=False)
    allt.drop(columns=["x", "y"]).to_csv(RUN / "results" / "tables" / "trees.csv", index=False)
    print(allt.groupby(["survey", "status"]).size().to_dict(), "osm ways", nways, flush=True)


if __name__ == "__main__":
    {"mosaics": lambda: [mosaic(n) for n in COLL], "trees": trees}[sys.argv[1]]()
