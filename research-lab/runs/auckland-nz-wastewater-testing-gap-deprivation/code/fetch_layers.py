"""Download Stats NZ open boundary layers (StatsNZGeospatial ArcGIS FeatureServer, CC BY 4.0) as GeoParquet (NZTM).

SA1 2023 and Urban Rural 2023 polygons, simplified server-side to 5 m (maxAllowableOffset) to keep them small.
Output: data/raw/sa1_2023.parquet, data/raw/ur_2023.parquet
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon

RUN = Path(__file__).resolve().parents[1]
BASE = "https://services2.arcgis.com/vKb0s8tBIA3bdocZ/arcgis/rest/services/"
LAYERS = {"sa1_2023": "Statistical_Area_1_2023", "ur_2023": "Urban_Rural_Areas_2023"}


def get(url, params, tries=6):
    q = url + "?" + urllib.parse.urlencode(params)
    for k in range(tries):
        try:
            with urllib.request.urlopen(q, timeout=300) as r:
                d = json.load(r)
            if "error" in d:
                raise RuntimeError(d["error"])
            return d
        except Exception as e:  # noqa: BLE001
            if k == tries - 1:
                raise
            print("retry", e, file=sys.stderr)
            time.sleep(10 * (k + 1))


def poly(rings):
    ps = [Polygon(r) for r in rings]
    outer = [p for p in ps if not p.exterior.is_ccw] or ps
    holes = [p for p in ps if p.exterior.is_ccw and p not in outer]
    out = []
    for o in outer:
        hs = [h.exterior.coords for h in holes if o.contains(h.representative_point())]
        out.append(Polygon(o.exterior.coords, hs))
    g = out[0] if len(out) == 1 else MultiPolygon(out)
    return g if g.is_valid else g.buffer(0)


def fetch(name, svc):
    url = BASE + svc + "/FeatureServer/0"
    n = get(url + "/query", {"where": "1=1", "returnCountOnly": "true", "f": "json"})["count"]
    page = 1000
    base = {"where": "1=1", "outFields": "*", "outSR": 2193, "maxAllowableOffset": 5, "orderByFields": "OBJECTID",
            "resultRecordCount": page, "f": "json"}
    with ThreadPoolExecutor(4) as ex:
        feats = [f for p in ex.map(lambda o: get(url + "/query", base | {"resultOffset": o})["features"],
                                   range(0, n, page)) for f in p]
    assert len(feats) == n, (len(feats), n)
    g = gpd.GeoDataFrame(pd.DataFrame([f["attributes"] for f in feats]),
                         geometry=[poly(f["geometry"]["rings"]) if f.get("geometry", {}).get("rings") else None for f in feats], crs=2193)
    g.to_parquet(RUN / "data" / "raw" / f"{name}.parquet")
    print(name, len(g), "no geometry:", int(g.geometry.isna().sum()), list(g.columns)[:12])


if __name__ == "__main__":
    for k, v in LAYERS.items():
        fetch(k, v)
