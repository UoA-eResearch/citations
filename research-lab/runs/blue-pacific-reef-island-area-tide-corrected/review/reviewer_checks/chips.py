"""Imagery spot-check for the land screen and for the islets whose fitted tide slope has the wrong sign.
For each target: one Sentinel-2 scene the study measured (the clearest, or the lowest/highest water level), a 3-panel
PNG (true colour | MNDWI | Otsu land mask inside the 60 m buffer, with the OSM ring) and the study's own row.
Reads the same COGs as measure.py; writes only review/reviewer_checks/chip_*.png."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import rasterio
import shapely
from rasterio.enums import Resampling
from rasterio.features import geometry_mask, rasterize
from rasterio.windows import from_bounds
from skimage.filters import threshold_otsu
from skimage.io import imsave

RUN = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
os.environ.update({"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR", "AWS_NO_SIGN_REQUEST": "YES", "VSI_CACHE": "TRUE"})
TARGETS = [("penrhyn_126", "clear"), ("penrhyn_036", "clear"), ("penrhyn_LOWKEPT", "clear"), ("kwajalein_056", "clear"),
           ("kwajalein_078", "low"), ("kwajalein_078", "high"), ("tarawa_015", "low"), ("tarawa_015", "high"),
           ("kiritimati_001", "low"), ("kiritimati_001", "high"), ("tarawa_021", "high")]
inv = pd.read_csv(RUN / "data" / "inventory.csv").set_index("islet")
ls = pd.read_csv(RUN / "results" / "tables" / "land_screen.csv").set_index("islet")
lowkept = ls[ls.retained & (ls.atoll == "penrhyn")].sort_values("land_share").index[0]
sys.path.insert(0, str(RUN / "code"))
import rates as R  # noqa: E402

a = R.attach_levels(R.load_areas())
a = a[(a.sensor == "s2") & a.area_otsu.notna() & (a.valid >= 0.99)]
scn = pd.concat([pd.read_parquet(p) for p in sorted((RUN / "data" / "scenes").glob("*_s2.parquet"))]).drop_duplicates("id").set_index("id")


def stretch(x, lo, hi):
    return np.clip((x - lo) / (hi - lo), 0, 1)


for islet, pick in TARGETS:
    if islet == "penrhyn_LOWKEPT":
        islet = lowkept
    rows = a[a.islet == islet].dropna(subset=["level_m"])
    if rows.empty:
        print(islet, "no measured scene"); continue
    row = (rows.sort_values("clear", ascending=False).iloc[0] if pick == "clear" else
           rows.sort_values("level_m").iloc[0] if pick == "low" else rows.sort_values("level_m").iloc[-1])
    s = scn.loc[row.scene]
    geom = shapely.from_wkt(inv.wkt[islet])
    tr = pyproj.Transformer.from_crs("EPSG:4326", f"EPSG:{int(s.epsg)}", always_xy=True)
    g = shapely.transform(geom, lambda xy: np.column_stack(tr.transform(xy[:, 0], xy[:, 1])))
    aoi = g.buffer(60.0)
    b = aoi.buffer(120.0).bounds
    hrefs = {"B04": s.green.replace("B03", "B04"), "B03": s.green, "B02": s.green.replace("B03", "B02"), "B11": s.swir16}
    arr = {}
    with rasterio.Env():
        with rasterio.open(hrefs["B03"]) as ds:
            w = from_bounds(*b, transform=ds.transform).round_offsets().round_lengths()
            tf = ds.window_transform(w)
            arr["B03"] = ds.read(1, window=w).astype(float)
            shp = arr["B03"].shape
        for k in ("B04", "B02", "B11"):
            with rasterio.open(hrefs[k]) as ds:
                w2 = from_bounds(*b, transform=ds.transform).round_offsets().round_lengths()
                arr[k] = ds.read(1, window=w2, out_shape=shp, resampling=Resampling.bilinear).astype(float)
    off = float(s.swir16_offset)
    valid = (arr["B03"] > 0) & (arr["B11"] > 0)
    if off < 0 and valid.any() and np.percentile(arr["B11"][valid], 1) < 500:
        off = 0.0                                               # the study's D4 rule
    ref = {k: np.clip(v * 1e-4 + off, 0, None) for k, v in arr.items()}
    with np.errstate(divide="ignore", invalid="ignore"):
        mndwi = (ref["B03"] - ref["B11"]) / (ref["B03"] + ref["B11"])
    am = ~geometry_mask([aoi], out_shape=shp, transform=tf)
    rm = ~geometry_mask([g], out_shape=shp, transform=tf)
    v = mndwi[am & valid]; v = v[np.isfinite(v)]
    t = float(threshold_otsu(v)) if v.size > 10 and v.min() < v.max() else np.nan
    land = (mndwi < t) & am if np.isfinite(t) else np.zeros(shp, bool)
    dry = (mndwi < 0) & am
    ring = rasterize([(g.boundary.buffer(5.0), 1)], out_shape=shp, transform=tf).astype(bool)
    rgb = np.dstack([stretch(ref["B04"], 0.0, 0.25), stretch(ref["B03"], 0.0, 0.25), stretch(ref["B02"], 0.0, 0.25)])
    mn = np.repeat(stretch(np.nan_to_num(mndwi, nan=1.0), -1.0, 1.0)[..., None], 3, axis=2)
    mk = np.zeros(shp + (3,)); mk[..., 2] = 0.55                     # water: blue
    mk[land] = (0.85, 0.75, 0.35)                                     # Otsu land: sand
    mk[dry] = (0.2, 0.55, 0.2)                                        # MNDWI<0 'dry land': green
    mk[~am] *= 0.35
    for img in (rgb, mn, mk):
        img[ring] = (1.0, 0.1, 0.1)
    sep = np.ones((shp[0], 3, 3))
    panel = (np.hstack([rgb, sep, mn, sep, mk]) * 255).astype(np.uint8)
    scale = max(1, int(np.ceil(360 / shp[0])))
    panel = np.kron(panel, np.ones((scale, scale, 1), dtype=np.uint8))
    name = f"chip_{islet}_{pick}.png"
    imsave(OUT / name, panel, check_contrast=False)
    print(f"{name}: scene {row.scene} {row.datetime[:16]} level {row.level_m:+.2f} m clear {row.clear:.2f}; study row: area_otsu {row.area_otsu/1e4:.2f} ha, "
          f"area_fixed {row.area_fixed/1e4:.2f} ha, otsu_t {row.otsu_t:.3f}; OSM {inv.area_ha[islet]:.2f} ha; here: otsu_t {t:.3f}, land {land.sum()*100/1e4:.2f} ha, "
          f"dry {dry.sum()*100/1e4:.2f} ha; offset used {off}; px {shp}", flush=True)
