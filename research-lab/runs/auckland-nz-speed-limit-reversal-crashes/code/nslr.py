"""Speed-limit history from an NSLR snapshot.

load(snapshot) -> GeoDataFrame of Permanent speed-limit records (NZTM) with integer `value`, `eff`, `ineff`
(NZ-local timestamps; ineff NaT = still in force), `rca`, `reason`.
history(points, recs) -> long table: one row per (point, record covering the point).
value_at(hist, t) -> per-point limit in force at time t (whenEffective <= t < whenIneffective):
    the value if every record in force agrees, NaN if none is in force, -1 if records in force disagree (ambiguous).
"""
import gzip
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon

RUN = Path(__file__).resolve().parents[1]
SNAP = RUN / "data" / "nslr_snapshots"
TZ = "Pacific/Auckland"


def _poly(rings):
    """Esri rings -> shapely geometry (outer rings clockwise, holes counter-clockwise)."""
    outers, holes = [], []
    for r in rings:
        p = Polygon(r)
        (outers if not p.exterior.is_ccw else holes).append(p)
    if not outers:
        outers, holes = holes, []
    polys = []
    for o in outers:
        hs = [h.exterior.coords for h in holes if o.contains(h.representative_point())]
        polys.append(Polygon(o.exterior.coords, hs))
    g = polys[0] if len(polys) == 1 else MultiPolygon(polys)
    return g if g.is_valid else g.buffer(0)


def load(snapshot="2026-10-03_full.json.gz", category="Permanent"):
    cache = SNAP / (snapshot.replace(".json.gz", "") + f"_{category.lower()}.parquet")
    if cache.exists():
        return gpd.read_parquet(cache)
    d = json.load(gzip.open(SNAP / snapshot, "rt"))
    rows, geoms = [], []
    for f in d["features"]:
        a = f["attributes"]
        if a["speedCategoryName"] != category or not f.get("geometry", {}).get("rings"):
            continue
        rows.append(a)
        geoms.append(_poly(f["geometry"]["rings"]))
    g = gpd.GeoDataFrame(pd.DataFrame(rows), geometry=geoms, crs=2193)
    for c in ["whenEffective", "whenIneffective"]:
        g[c] = pd.to_datetime(g[c], unit="ms", utc=True).dt.tz_convert(TZ)
    g["value"] = pd.to_numeric(g.speedLimitZoneValue, errors="coerce")
    g = g.rename(columns={"whenEffective": "eff", "whenIneffective": "ineff", "rcaZoneReferenceName": "rca",
                          "speedLimitZoneReasonName": "reason"})
    g = g[["OBJECTID", "speedLimitZoneId", "value", "eff", "ineff", "rca", "reason", "geometry"]]
    g.to_parquet(cache)
    return g


def history(points, recs):
    """points: GeoDataFrame (NZTM) with a unique `pid` column."""
    j = gpd.sjoin(points[["pid", "geometry"]], recs, how="inner", predicate="within")
    return pd.DataFrame(j[["pid", "OBJECTID", "value", "eff", "ineff", "rca", "reason"]])


def value_at(hist, t):
    t = pd.Timestamp(t, tz=TZ) if pd.Timestamp(t).tzinfo is None else pd.Timestamp(t)
    live = hist[(hist.eff <= t) & (hist.ineff.isna() | (hist.ineff > t))]
    g = live.groupby("pid").value.agg(["min", "max"])
    v = g["min"].where(g["min"] == g["max"], -1)
    return v


def effective_of_value(hist, t):
    """whenEffective of the record in force at t (latest eff if several agree)."""
    t = pd.Timestamp(t, tz=TZ) if pd.Timestamp(t).tzinfo is None else pd.Timestamp(t)
    live = hist[(hist.eff <= t) & (hist.ineff.isna() | (hist.ineff > t))]
    return live.groupby("pid").eff.max()
