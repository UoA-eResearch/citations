"""Islet inventory for the gauge atolls (before the plan's outcomes): OSM coastline -> islet polygons, areas, and an
engineered-shoreline flag (an airstrip, harbour, pier, breakwater or causeway on or touching the islet).

Writes data/raw/osm_<atoll>.json (raw Overpass) and data/inventory.csv (atoll, islet, area_ha, engineered, wkt).
"""
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pyproj
import shapely
from shapely.geometry import LineString, Point, shape
from shapely.ops import linemerge, polygonize, unary_union

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
UA = "research-lab-reef-islands/0.1 (academic; noreply@anthropic.com)"
# atolls with an on-atoll UHSLC gauge (id) and a bounding box (south, west, north, east)
ATOLLS = {
    "tarawa": (2, (1.30, 172.85, 1.75, 173.25)), "majuro": (5, (7.02, 171.00, 7.25, 171.42)),
    "funafuti": (25, (-8.72, 179.03, -8.43, 179.27)), "kwajalein": (55, (8.65, 166.65, 9.50, 167.80)),
    "kanton": (13, (-2.88, -171.76, -2.75, -171.62)), "kiritimati": (11, (1.65, -157.60, 2.10, -157.10)),
    "penrhyn": (24, (-9.10, -158.10, -8.88, -157.88)), "kapingamarangi": (29, (0.95, 154.70, 1.15, 154.86)),
}
ENGINEERED = '(way["aeroway"~"runway|aerodrome"]({b});way["harbour"]({b});way["man_made"~"pier|breakwater|groyne"]({b});' \
             'way["landuse"="port"]({b});way["bridge"]({b});way["embankment"]({b});way["causeway"]({b}););'


def overpass(q):
    for t in range(6):
        try:
            req = urllib.request.Request("https://overpass-api.de/api/interpreter",
                                         data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except Exception as e:
            print("retry", t, repr(e)[:100], flush=True)
            time.sleep(20 * (t + 1))
    raise RuntimeError("overpass failed")


def utm(lon, lat):
    zone = int((lon + 180) // 6) + 1
    return f"EPSG:{32600 + zone if lat >= 0 else 32700 + zone}"


def main():
    rows = []
    for name, (gid, (s, w, n, e)) in ATOLLS.items():
        b = f"{s},{w},{n},{e}"
        p = RAW / f"osm_{name}.json"
        if not p.exists():
            d = overpass(f'[out:json][timeout:120];(way["natural"="coastline"]({b}););out geom;')
            eng = overpass(f'[out:json][timeout:120];{ENGINEERED.format(b=b)}out geom;')
            json.dump({"coast": d, "engineered": eng}, open(p, "w"))
            time.sleep(10)
        d = json.load(open(p))
        lines = [LineString([(q["lon"], q["lat"]) for q in el["geometry"]]) for el in d["coast"]["elements"]
                 if el.get("geometry") and len(el["geometry"]) > 1]
        polys = list(polygonize(linemerge(unary_union(lines))))
        eng = [LineString([(q["lon"], q["lat"]) for q in el["geometry"]]) if len(el.get("geometry") or []) > 1
               else Point(el["geometry"][0]["lon"], el["geometry"][0]["lat"])
               for el in d["engineered"]["elements"] if el.get("geometry")]
        engu = unary_union(eng) if eng else None
        c = shapely.centroid(unary_union(polys)) if polys else None
        tr = pyproj.Transformer.from_crs("EPSG:4326", utm(c.x, c.y), always_xy=True) if c else None
        for i, poly in enumerate(sorted(polys, key=lambda g: -g.area)):
            a = shapely.transform(poly, lambda xy: __import__("numpy").column_stack(tr.transform(xy[:, 0], xy[:, 1]))).area / 1e4
            rows.append({"atoll": name, "gauge": gid, "islet": f"{name}_{i:03d}", "area_ha": round(a, 2),
                         "engineered": int(bool(engu is not None and poly.buffer(0.0003).intersects(engu))),
                         "wkt": poly.wkt})
        n_ok = [r for r in rows if r["atoll"] == name]
        print(name, len(polys), "islets;", sum(r["area_ha"] >= 1 for r in n_ok), ">=1 ha;",
              sum(r["engineered"] for r in n_ok), "engineered", flush=True)
    with open(RUN / "data" / "inventory.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)


if __name__ == "__main__":
    main()
