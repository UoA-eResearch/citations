"""Download Auckland Unitary Plan residential base zones (ZONE 19 Single House, 18 Mixed Housing Suburban,
60 Mixed Housing Urban, 8 Terrace Housing and Apartment Buildings) from Auckland Council's open FeatureServer (NZTM).
Output: data/raw/aup_residential.parquet
"""
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon

RUN = Path(__file__).resolve().parents[1]
U = "https://services1.arcgis.com/n4yPwebTjJCmXB6W/arcgis/rest/services/Unitary_Plan_Base_Zone/FeatureServer/0/query"
WHERE = "ZONE IN (19, 18, 60, 8)"


def get(params):
    for k in range(6):
        try:
            return json.load(urllib.request.urlopen(U + "?" + urllib.parse.urlencode(params), timeout=300))
        except Exception:  # noqa: BLE001
            time.sleep(10 * (k + 1))
    raise RuntimeError(params)


def poly(rings):
    ps = [Polygon(r) for r in rings]
    outer = [p for p in ps if not p.exterior.is_ccw] or ps
    holes = [p for p in ps if p.exterior.is_ccw and p not in outer]
    out = [Polygon(o.exterior.coords, [h.exterior.coords for h in holes if o.contains(h.representative_point())]) for o in outer]
    g = out[0] if len(out) == 1 else MultiPolygon(out)
    return g if g.is_valid else g.buffer(0)


def main():
    n = get({"where": WHERE, "returnCountOnly": "true", "f": "json"})["count"]
    base = {"where": WHERE, "outFields": "OBJECTID,ZONE,GROUPZONE,VERSIONSTATUS", "outSR": 2193, "orderByFields": "OBJECTID",
            "resultRecordCount": 1000, "f": "json"}
    with ThreadPoolExecutor(4) as ex:
        feats = [f for p in ex.map(lambda o: get(base | {"resultOffset": o})["features"], range(0, n, 1000)) for f in p]
    assert len(feats) == n
    g = gpd.GeoDataFrame(pd.DataFrame([f["attributes"] for f in feats]),
                         geometry=[poly(f["geometry"]["rings"]) for f in feats], crs=2193)
    g["zone"] = g.ZONE.map({19: "SH", 18: "MHS", 60: "MHU", 8: "THAB"})
    g.to_parquet(RUN / "data" / "raw" / "aup_residential.parquet")
    print(len(g), (g.groupby("zone").geometry.apply(lambda s: s.area.sum() / 1e6)).round(1).to_dict(), "km2")


if __name__ == "__main__":
    main()
