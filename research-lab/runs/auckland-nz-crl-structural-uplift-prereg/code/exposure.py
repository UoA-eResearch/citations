"""Bus-route exposure classes for H2 (plan.md section 5). Uses geometry only, no boardings after opening.

A bus route is exposed at radius r if any of its GTFS shapes (current feed, downloaded 2026-10-03) passes within r of
Te Waihorotiu, Karanga-a-Hape or Maungawhau train station (stops 131, 132, 136; parent train-station points).
Radii: 800 m primary, 400 m and 1,200 m sensitivity.
Also matches GTFS route_short_name to the 'Route Num' column of AT's monthly-by-route files and records which routes
have pre-period boardings (Oct 2025 - Mar 2026).
Output: results/tables/route_exposure.csv
"""
import sys
import zipfile
from pathlib import Path

import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily as D  # noqa: E402

GTFS = D.RUN / "data" / "gtfs_2026-10-03.zip"
STATIONS = {"131": "Te Waihorotiu", "132": "Karanga-a-Hape", "136": "Maungawhau"}
RADII = (400, 800, 1200)
TO_NZTM = Transformer.from_crs(4326, 2193, always_xy=True)


def monthly_routes(name):
    m = pd.read_excel(D.RAW / name, sheet_name="Monthly by Route", header=8)
    m = m[m["Mode"].astype(str).str.strip().str.lower() == "bus"].copy()
    m["route"] = m["Route Num"].astype(str).str.strip()
    return m


def month_cols(m, first, last):
    """Monthly columns (parsed by openpyxl as datetime.datetime) between two month starts, inclusive."""
    cols = []
    for c in m.columns:
        t = pd.to_datetime(c, errors="coerce") if not isinstance(c, str) or c[:2] in ("19", "20") else pd.NaT
        if pd.notna(t) and pd.Timestamp(first) <= t <= pd.Timestamp(last):
            cols.append(c)
    n = (pd.Timestamp(last).to_period("M") - pd.Timestamp(first).to_period("M")).n + 1
    assert len(cols) == n, (cols, n)
    return cols


def main():
    z = zipfile.ZipFile(GTFS)
    stops = pd.read_csv(z.open("stops.txt"), dtype={"stop_id": str})
    stops["code"] = stops.stop_id.str.split("-").str[0]
    st = stops[stops.code.isin(STATIONS)]
    assert len(st) == 3, st
    pts = {STATIONS[r.code]: Point(*TO_NZTM.transform(r.stop_lon, r.stop_lat)) for r in st.itertuples()}
    routes = pd.read_csv(z.open("routes.txt"), dtype=str)
    routes = routes[routes.route_type == "3"]
    trips = pd.read_csv(z.open("trips.txt"), dtype=str, usecols=["route_id", "shape_id"]).drop_duplicates()
    trips = trips.merge(routes[["route_id", "route_short_name"]], on="route_id")
    shapes = pd.read_csv(z.open("shapes.txt"), dtype={"shape_id": str})
    shapes = shapes[shapes.shape_id.isin(trips.shape_id)].sort_values(["shape_id", "shape_pt_sequence"])
    x, y = TO_NZTM.transform(shapes.shape_pt_lon.values, shapes.shape_pt_lat.values)
    shapes["x"], shapes["y"] = x, y
    dist = {}
    for sid, g in shapes.groupby("shape_id"):
        line = LineString(list(zip(g.x, g.y)))
        dist[sid] = min(line.distance(p) for p in pts.values())
    trips["dist"] = trips.shape_id.map(dist)
    r = trips.groupby("route_short_name").dist.min().rename("min_dist_m").reset_index()
    r = r.rename(columns={"route_short_name": "route"})
    for rad in RADII:
        r[f"exposed_{rad}"] = r.min_dist_m <= rad

    pre = monthly_routes("auckland-transport-monthly-bus-train-ferry-boardings-june-2026.xlsx")
    pre_cols = month_cols(pre, "2025-10-01", "2026-03-01")
    pre["pre_boardings"] = pre[pre_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=6)
    pre = pre.groupby("route", as_index=False).pre_boardings.sum(min_count=1)
    out = r.merge(pre, on="route", how="outer", indicator=True)
    out["in_gtfs"] = out._merge != "right_only"
    out["in_monthly_pre"] = out._merge != "left_only"
    out = out.drop(columns="_merge").sort_values("route")
    out.to_csv(D.RUN / "results" / "tables" / "route_exposure.csv", index=False)
    both = out[out.in_gtfs & out.in_monthly_pre & out.pre_boardings.notna()]
    print("GTFS bus routes", out.in_gtfs.sum(), "| monthly pre routes", out.in_monthly_pre.sum(),
          "| matched with 6 pre months", len(both))
    for rad in RADII:
        e = both[both[f"exposed_{rad}"] == True]  # noqa: E712
        print(f"radius {rad} m: exposed {len(e)} routes, {e.pre_boardings.sum() / both.pre_boardings.sum():.1%} of pre boardings")
    print("exposed at 800 m:", ", ".join(both[both.exposed_800 == True].route))  # noqa: E712
    print("GTFS-only:", ", ".join(out[~out.in_monthly_pre].route.astype(str))[:600])
    print("monthly-only:", ", ".join(out[~out.in_gtfs].route.astype(str))[:600])


if __name__ == "__main__":
    main()
