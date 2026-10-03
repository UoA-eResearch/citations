"""Assign NSLR speed-limit histories to OSM segments and classify them (plan.md section 3).

Dates (NZ local): t22 = 2022-06-01 (first full month of NSLR history), t0 = 2024-10-29 (day before the Setting of
Speed Limits Rule 2024 came into force), t1 = 2025-11-01, plus the 1st of every month from 2024-11 to 2026-07.
Classes:
  treated   : one raise between t0 and t1 (v1 - v0 in 10..40 km/h, not 100->110), no other change up to 2026-07-01
  expressway: 100 -> 110 in the same window (analysed separately)
  control   : the same limit at every check date from t0 to 2026-07-01
  excluded  : anything else (lowered, several changes, ambiguous overlaps, no coverage at t0 or t1)
From 2026-05 onward the public register has growing coverage gaps (records ended without replacements); a check
date with no record in force counts as 'unknown', not as a change. Ambiguous (-1) at any check date excludes.
Output: data/seg_class.parquet
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nslr  # noqa: E402

RUN = nslr.RUN
T22, T0, T1 = "2022-06-01", "2024-10-29", "2025-11-01"
MONTHS = [d.strftime("%Y-%m-%d") for d in pd.date_range("2024-11-01", "2026-07-01", freq="MS")]


def half(ts):
    return f"{ts.year}H{1 if ts.month <= 6 else 2}"


def cls_group(c):
    return {"motorway": "highway", "trunk": "highway", "primary": "arterial", "secondary": "arterial"}.get(c, "local")


def main():
    segs = gpd.read_parquet(RUN / "data" / "segments.parquet")
    pts = gpd.GeoDataFrame({"pid": segs.seg.values}, geometry=gpd.points_from_xy(segs.mx, segs.my), crs=2193)
    recs = nslr.load()
    h = nslr.history(pts, recs)
    h.to_parquet(RUN / "data" / "hist_segments.parquet")
    dates = [T22, T0] + MONTHS[: MONTHS.index("2025-11-01")] + [T1] + MONTHS[MONTHS.index("2025-11-01") + 1:]
    V = pd.DataFrame({d: nslr.value_at(h, d) for d in dates}).reindex(segs.seg.values)
    win = [T0] + [m for m in MONTHS if m <= "2025-10-01"] + [T1]  # t0 .. t1
    after = [m for m in MONTHS if m > "2025-11-01"]  # stability window, Dec 2025 .. Jul 2026
    v0, v1 = V[T0], V[T1]
    amb = (V[[T0] + MONTHS] == -1).any(axis=1)
    covered = v0.notna() & v1.notna() & (v0 > 0) & (v1 > 0)

    def nchanges(row):
        x = [v for v in row if pd.notna(v)]
        return sum(a != b for a, b in zip(x, x[1:]))

    ch_win = V[win].apply(nchanges, axis=1)
    stable_after = pd.Series(True, index=V.index)
    for m in after:
        stable_after &= V[m].isna() | (V[m] == v1)
    d = segs.drop(columns="geometry").set_index("seg").copy()
    d["v22"], d["v0"], d["v1"] = V[T22], v0, v1
    d["n_unknown_after"] = V[after].isna().sum(axis=1)
    raise_ = covered & ~amb & (v1 > v0) & (ch_win == 1) & stable_after
    step = v1 - v0
    d["klass"] = "excluded"
    d.loc[covered & ~amb & (ch_win == 0) & stable_after & (v0 == v1), "klass"] = "control"
    d.loc[raise_ & (v0 == 100) & (v1 == 110), "klass"] = "expressway"
    d.loc[raise_ & ~((v0 == 100) & (v1 == 110)) & (step >= 10) & (step <= 40), "klass"] = "treated"
    # effective date of the raise -> cohort half-year
    eff = nslr.effective_of_value(h[h.pid.isin(d.index[d.klass.isin(["treated", "expressway"])])], T1)
    d["eff_raise"] = eff.reindex(d.index)
    d["cohort"] = d.eff_raise.map(lambda t: half(t) if pd.notna(t) else "")
    # reduction history between t22 and t0, and its half-year
    red = (d.v22 > 0) & (d.v0 > 0) & (d.v22 > d.v0)
    eff0 = nslr.effective_of_value(h[h.pid.isin(d.index[red])], T0)
    d["reduced"] = red
    d["red_half"] = eff0.reindex(d.index).map(lambda t: half(t) if pd.notna(t) else "none")
    d.loc[~red, "red_half"] = "none"
    # road controlling authority of the record in force at t0
    live0 = h[(h.eff <= pd.Timestamp(T0, tz=nslr.TZ)) & (h.ineff.isna() | (h.ineff > pd.Timestamp(T0, tz=nslr.TZ)))]
    d["rca"] = live0.groupby("pid").rca.first().reindex(d.index).fillna("")
    d["clsg"] = d.cls.map(cls_group)

    def ttype(r):
        if r.klass != "treated":
            return ""
        if r.v0 <= 40:
            return "urban_30_40_to_50"
        if r.v0 == 50:
            return "urban_50_up"
        if r.v0 in (60, 70):
            return "periurban_60_70_up"
        return "rural_80_90_up"
    d["ttype"] = d.apply(ttype, axis=1)
    d["stratum"] = d.rca + "|" + d.v0.astype("Int64").astype(str) + "|" + d.red_half + "|" + d.clsg
    d.reset_index().to_parquet(RUN / "data" / "seg_class.parquet")
    print(d.klass.value_counts().to_dict())
    t = d[d.klass == "treated"]
    print("treated km by type:", (t.groupby("ttype").length_m.sum() / 1000).round(0).to_dict())
    print("treated cohorts:", t.cohort.value_counts().to_dict())
    print(pd.crosstab(t.v0, t.v1))


if __name__ == "__main__":
    main()
