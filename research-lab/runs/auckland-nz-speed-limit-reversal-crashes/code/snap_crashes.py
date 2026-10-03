"""Snap CAS crashes (FY2017/18 onward) to segments. Usage: snap_crashes.py pre | post
pre  reads data/raw/cas_pre.parquet; post reads the sealed file (only after plan.md is committed; checks its SHA-256).
Output: data/crashes_<which>.parquet with seg, snap distance, name match, half-year period, severity flags.
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import snap as S  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def load(which):
    if which == "pre":
        c = pd.read_parquet(RUN / "data" / "raw" / "cas_pre.parquet")
        return c[c.crashFinancialYear >= "2017/2018"].copy()
    p = RUN / "data" / "sealed" / "cas_post.json.gz"
    want = (RUN / "data" / "sealed" / "cas_post.sha256").read_text().split()[0]
    assert hashlib.sha256(p.read_bytes()).hexdigest() == want, "sealed file changed"
    d = json.load(gzip.open(p, "rt"))
    return pd.DataFrame([f["attributes"] | {"X": f.get("geometry", {}).get("x"), "Y": f.get("geometry", {}).get("y")}
                         for f in d["features"]])


def period(c):
    """Half-year from crashYear + crashFinancialYear: FY 'a/b' with crashYear a -> Jul-Dec a (aH2); b -> Jan-Jun b."""
    fy0 = c.crashFinancialYear.str[:4].astype(int)
    return np.where(c.crashYear == fy0, fy0.astype(str) + "H2", c.crashYear.astype(str) + "H1")


def main(which):
    c = load(which)
    c = c[c.X.notna()].reset_index(drop=True)
    segs = gpd.read_parquet(RUN / "data" / "segments.parquet", columns=["seg", "name", "ref", "geometry"])
    segs["_norm"] = [S.norm_name(x) for x in segs.name]
    segs["_sh"] = [S.sh_numbers(x) for x in segs.ref]
    pts = gpd.GeoSeries(gpd.points_from_xy(c.X, c.Y), crs=2193)
    seg, dist, mm = S.snap(pts, c.crashLocation1.values, segs)
    out = pd.DataFrame({
        "OBJECTID": c.OBJECTID, "seg": seg, "snap_m": dist, "name_match": mm, "period": period(c),
        "fy": c.crashFinancialYear, "severity": c.crashSeverity, "cas_limit": c.speedLimit,
        "injury": c.crashSeverity.isin(["Fatal Crash", "Serious Crash", "Minor Crash"]),
        "ksi": c.crashSeverity.isin(["Fatal Crash", "Serious Crash"]), "sh": c.crashSHDescription == "Yes",
        "region": c.region, "urban": c.urban})
    out.to_parquet(RUN / "data" / f"crashes_{which}.parquet")
    if which == "pre":
        print(len(out), "crashes; snapped", (out.seg >= 0).mean().round(4), "; name/SH match among snapped",
              out[out.seg >= 0].name_match.mean().round(3), "; median snap m", np.nanmedian(out.snap_m).round(1))
        print(out.period.value_counts().sort_index().to_dict())
    else:
        print("post crashes snapped; counts deliberately not printed")


if __name__ == "__main__":
    main(sys.argv[1])
