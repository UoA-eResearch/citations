"""Feasibility probe (before the plan): time a windowed read of one Sentinel-2 COG band over a small atoll AOI."""
import json
import sys
import time

import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

href = sys.argv[1]
bbox = (179.17, -8.56, 179.23, -8.50)          # part of Funafuti atoll, lon/lat
with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", AWS_NO_SIGN_REQUEST="YES", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
    t0 = time.time()
    with rasterio.open(href) as src:
        b = transform_bounds("EPSG:4326", src.crs, *bbox)
        w = from_bounds(*b, transform=src.transform)
        a = src.read(1, window=w)
    print(json.dumps({"shape": a.shape, "seconds": round(time.time() - t0, 2), "mean": float(a.mean())}))
