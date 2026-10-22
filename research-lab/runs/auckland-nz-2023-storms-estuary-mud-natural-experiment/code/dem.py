"""20 m elevation grid for routing (plan section 2, D1).

Domain: the sites' bounding box plus 40 km, in NZTM (EPSG:2193), snapped to 20 m.
- LINZ national LiDAR 1 m DEM mosaic, read from each tile's internal overviews by block average;
- cells it leaves empty are filled from the national 8 m contour DEM (flagged in a second band).

Writes data/dem20.tif (band 1 elevation, NaN = no data; band 2 = 1 where the 8 m DEM filled the cell).
"""
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.windows import from_bounds

RUN = Path(__file__).resolve().parents[1]
BUCKET = "https://nz-elevation.s3.ap-southeast-2.amazonaws.com/"
COLL = {"lidar": "new-zealand/new-zealand/dem_1m/2193/", "contour": "new-zealand/new-zealand-contour/dem_8m/2193/"}
RES, PAD = 20.0, 40_000.0


def domain():
    s = pd.read_csv(RUN / "results" / "tables" / "sites.csv")
    tr = pyproj.Transformer.from_crs(4326, 2193, always_xy=True)
    x, y = tr.transform(s.lon.to_numpy(), s.lat.to_numpy())
    x0, x1 = np.floor((x.min() - PAD) / RES) * RES, np.ceil((x.max() + PAD) / RES) * RES
    y0, y1 = np.floor((y.min() - PAD) / RES) * RES, np.ceil((y.max() + PAD) / RES) * RES
    return x0, y0, x1, y1


def items(coll):
    c = json.load(urllib.request.urlopen(BUCKET + COLL[coll] + "collection.json", timeout=60))
    hrefs = [l["href"] for l in c["links"] if l["rel"] == "item"]

    def get(h):
        it = json.load(urllib.request.urlopen(BUCKET + COLL[coll] + h.lstrip("./"), timeout=60))
        a = next(iter(it["assets"].values()))["href"]
        return it["bbox"], a if a.startswith("http") else BUCKET + COLL[coll] + a.lstrip("./")
    with ThreadPoolExecutor(32) as ex:
        return list(ex.map(get, hrefs))


def mosaic(coll, bounds, shape, tf):
    x0, y0, x1, y1 = bounds
    tr = pyproj.Transformer.from_crs(2193, 4326, always_xy=True)
    lo, la = tr.transform([x0, x1, x0, x1], [y0, y0, y1, y1])
    sel = [h for b, h in items(coll) if not (b[2] < min(lo) or b[0] > max(lo) or b[3] < min(la) or b[1] > max(la))]
    out = np.full(shape, np.nan, np.float32)

    def one(h):
        with rasterio.open(h) as ds:
            ib = ds.bounds
            ox0, oy0 = max(ib.left, x0), max(ib.bottom, y0)
            ox1, oy1 = min(ib.right, x1), min(ib.top, y1)
            if ox0 >= ox1 or oy0 >= oy1:
                return None
            # snap the overlap to the 20 m grid
            ox0, ox1 = np.ceil((ox0 - x0) / RES) * RES + x0, np.floor((ox1 - x0) / RES) * RES + x0
            oy0, oy1 = np.ceil((oy0 - y0) / RES) * RES + y0, np.floor((oy1 - y0) / RES) * RES + y0
            if ox0 >= ox1 or oy0 >= oy1:
                return None
            h_, w_ = int(round((oy1 - oy0) / RES)), int(round((ox1 - ox0) / RES))
            a = ds.read(1, window=from_bounds(ox0, oy0, ox1, oy1, ds.transform), out_shape=(h_, w_),
                        resampling=Resampling.average, masked=True)
            r0, c0 = int(round((y1 - oy1) / RES)), int(round((ox0 - x0) / RES))
            return r0, c0, a.filled(np.nan).astype(np.float32)
    with ThreadPoolExecutor(16) as ex:
        for r in ex.map(one, sel):
            if r is None:
                continue
            r0, c0, a = r
            blk = out[r0:r0 + a.shape[0], c0:c0 + a.shape[1]]
            m = np.isnan(blk) & ~np.isnan(a)
            blk[m] = a[m]
    print(coll, len(sel), "tiles", flush=True)
    return out


def main():
    x0, y0, x1, y1 = domain()
    shape = (int(round((y1 - y0) / RES)), int(round((x1 - x0) / RES)))
    tf = from_origin(x0, y1, RES, RES)
    print("domain", (x0, y0, x1, y1), "shape", shape, flush=True)
    lid = mosaic("lidar", (x0, y0, x1, y1), shape, tf)
    con = mosaic("contour", (x0, y0, x1, y1), shape, tf)
    fill = np.isnan(lid) & ~np.isnan(con)
    dem = np.where(fill, con, lid)
    prof = {"driver": "GTiff", "dtype": "float32", "count": 2, "height": shape[0], "width": shape[1], "crs": "EPSG:2193",
            "transform": tf, "nodata": np.nan, "tiled": True, "compress": "deflate", "BIGTIFF": "YES"}
    with rasterio.open(RUN / "data" / "dem20.tif", "w", **prof) as ds:
        ds.write(dem.astype(np.float32), 1)
        ds.write(fill.astype(np.float32), 2)
    print("lidar cells", int((~np.isnan(lid)).sum()), "filled from contour", int(fill.sum()),
          "contour-only share of valid", round(float(fill.sum() / max(1, (~np.isnan(dem)).sum())), 4), flush=True)


if __name__ == "__main__":
    sys.exit(main())
