"""Ancillary layers (no canopy data): SA2 2023 and Territorial Authority Local Board 2026 boundaries (Stats NZ open
ArcGIS, CC BY 4.0) clipped to the Auckland residential extent, and train station points from the Auckland Transport
GTFS feed (copy kept in the CRL run). Output: data/raw/sa2.parquet, data/raw/talb.parquet, data/raw/stations.parquet
"""
import json
import time
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon

RUN = Path(__file__).resolve().parents[1]
BASE = "https://services2.arcgis.com/vKb0s8tBIA3bdocZ/arcgis/rest/services/"
GTFS = RUN.parent / "auckland-nz-crl-structural-uplift-prereg" / "data" / "gtfs_2026-10-03.zip"


def get(url, params):
    for k in range(6):
        try:
            return json.load(urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=300))
        except Exception:  # noqa: BLE001
            time.sleep(10 * (k + 1))
    raise RuntimeError(url)


def poly(rings):
    ps = [Polygon(r) for r in rings]
    outer = [p for p in ps if not p.exterior.is_ccw] or ps
    holes = [p for p in ps if p.exterior.is_ccw and p not in outer]
    out = [Polygon(o.exterior.coords, [h.exterior.coords for h in holes if o.contains(h.representative_point())]) for o in outer]
    g = out[0] if len(out) == 1 else MultiPolygon(out)
    return g if g.is_valid else g.buffer(0)


def fetch(svc, env):
    url = BASE + svc + "/FeatureServer/0/query"
    geo = {"geometry": ",".join(map(str, env)), "geometryType": "esriGeometryEnvelope", "inSR": 2193,
           "spatialRel": "esriSpatialRelIntersects"}
    n = get(url, {"where": "1=1", "returnCountOnly": "true", "f": "json"} | geo)["count"]
    base = {"where": "1=1", "outFields": "*", "outSR": 2193, "maxAllowableOffset": 2, "orderByFields": "OBJECTID",
            "resultRecordCount": 500, "f": "json"} | geo
    with ThreadPoolExecutor(4) as ex:
        feats = [f for p in ex.map(lambda o: get(url, base | {"resultOffset": o})["features"], range(0, n, 500)) for f in p]
    return gpd.GeoDataFrame(pd.DataFrame([f["attributes"] for f in feats]),
                            geometry=[poly(f["geometry"]["rings"]) for f in feats], crs=2193)


def main():
    z = gpd.read_parquet(RUN / "data" / "raw" / "aup_residential.parquet")
    env = z.total_bounds
    sa2 = fetch("Statistical_Area_2_2023", env)
    sa2.to_parquet(RUN / "data" / "raw" / "sa2.parquet")
    tl = fetch("Territorial_Authority_Local_Board_2026", env)
    tl.to_parquet(RUN / "data" / "raw" / "talb.parquet")
    zz = zipfile.ZipFile(GTFS)
    routes = pd.read_csv(zz.open("routes.txt"), dtype=str)
    trips = pd.read_csv(zz.open("trips.txt"), dtype=str, usecols=["route_id", "trip_id"])
    rail_trips = set(trips[trips.route_id.isin(routes[routes.route_type == "2"].route_id)].trip_id)
    st = pd.read_csv(zz.open("stop_times.txt"), dtype=str, usecols=["trip_id", "stop_id"])
    rail_stops = set(st[st.trip_id.isin(rail_trips)].stop_id)
    stops = pd.read_csv(zz.open("stops.txt"), dtype={"stop_id": str, "parent_station": str})
    s = stops[stops.stop_id.isin(rail_stops)]
    s = gpd.GeoDataFrame(s[["stop_id", "stop_name"]], geometry=gpd.points_from_xy(s.stop_lon, s.stop_lat), crs=4326).to_crs(2193)
    s.to_parquet(RUN / "data" / "raw" / "stations.parquet")
    print("SA2", len(sa2), list(sa2.columns)[:6], "| TALB", len(tl), list(tl.columns)[:6], "| rail stops", len(s))


if __name__ == "__main__":
    main()
