"""Preregistered analysis (plan.md sections 3-5).

1. Combine per-tile 30 m cell counts per epoch (E1: per cell, the NZ16 collection with more valid 1 m cells).
2. Zone shares per 30 m cell from a 3 m rasterisation of the residential zones; keep cells with >= 90% in one zone.
3. Inclusion: >= 810 valid 1 m cells in every epoch; building share >= 10% at E0 and E1.
4. Covariates: local board and SA2 (cell centre), distance to Waitemata/Britomart (1757560, 5920780) and to the
   nearest rail stop.
5. OLS with stratum FE (local board x E1 canopy band x CBD-distance band x E1 collection), SEs clustered by SA2:
   dC_post = canopy E2 - E1 (pp) and dC_pre = E1 - E0 on high (MHU+THAB) and low (MHS) dose vs SH.
Outputs: data/units.parquet, results/tables/main_results.csv, unit_counts.csv, tiles.json
"""
import glob
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyfixest as pf
import rasterio.features
from rasterio.transform import from_origin
from scipy.spatial import cKDTree

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
CELL, SUB = 30, 3
CBD = (1757560, 5920780)
Z = 1.959964


def epoch_cells(ep, sub=None):
    fs = sorted(glob.glob(str(RUN / "data" / "cells" / (sub or ep) / "*.parquet")))
    parts = []
    for f in fs:
        d = pd.read_parquet(f)
        if len(d):
            d["coll"] = "S" if "_BB" in f or "SAuckland" in f else "N"
            parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    if ep == "2016":
        t = pd.read_parquet(RUN / "data" / "tiles_needed.parquet")
        coll = {Path(k).stem: ("S" if k.startswith("NZ16_S") else "N") for k in t[t.epoch == "2016"].key}
        d = pd.concat([pd.read_parquet(f).assign(coll=coll[Path(f).stem]) for f in fs if len(pd.read_parquet(f))])
        d = d.groupby(["cx", "cy", "coll"], as_index=False).sum()
        d = d.sort_values("n_valid", ascending=False).drop_duplicates(["cx", "cy"])
    else:
        d = d.drop(columns="coll").groupby(["cx", "cy"], as_index=False).sum()
    return d


def zone_shares(cells):
    z = gpd.read_parquet(RUN / "data" / "raw" / "aup_residential.parquet")
    code = {"SH": 1, "MHS": 2, "MHU": 3, "THAB": 4}
    x0, y0 = np.floor(z.total_bounds[0] / CELL) * CELL, np.ceil(z.total_bounds[3] / CELL) * CELL
    w = int(np.ceil((z.total_bounds[2] - x0) / SUB)); h = int(np.ceil((y0 - z.total_bounds[1]) / SUB))
    w, h = w + (-w) % 10, h + (-h) % 10
    r = rasterio.features.rasterize(((g, code[c]) for g, c in zip(z.geometry, z.zone)), out_shape=(h, w),
                                    transform=from_origin(x0, y0, SUB, SUB), fill=0, dtype="uint8")
    blocks = r.reshape(h // 10, 10, w // 10, 10)
    out = {}
    for nm, c in code.items():
        out[nm] = (blocks == c).sum(axis=(1, 3)) / 100.0
    # map cells (lower-left cx, cy) to block indices
    col = ((cells.cx - x0) / CELL).astype(int)
    row = ((y0 - (cells.cy + CELL)) / CELL).astype(int)
    ok = (col >= 0) & (col < w // 10) & (row >= 0) & (row < h // 10)
    sh = pd.DataFrame({nm: np.where(ok, a[row.clip(0, h // 10 - 1), col.clip(0, w // 10 - 1)], 0) for nm, a in out.items()},
                      index=cells.index)
    return sh


def build_units(e2_sub=None, out_name="units.parquet", seam_cap=False):
    e = {ep: epoch_cells(ep) for ep in ("2013", "2016")}
    e["2024"] = epoch_cells("2024", e2_sub)
    m = e["2016"].merge(e["2013"], on=["cx", "cy"], suffixes=("", "_e0")).merge(e["2024"], on=["cx", "cy"], suffixes=("", "_e2"))
    m = m.rename(columns={c: c + "_e1" for c in ["n_valid", "n_c2", "n_c3", "n_c5", "n_bld"]})
    if seam_cap:  # D6: 1 m cells on tile seams are counted in both tiles; rescale counts so n_valid <= 900
        for ep in ("e0", "e1", "e2"):
            f = np.minimum(1.0, 900.0 / m[f"n_valid_{ep}"])
            for t in ("valid", "c2", "c3", "c5", "bld"):
                m[f"n_{t}_{ep}"] = m[f"n_{t}_{ep}"] * f
    sh = zone_shares(m)
    m["zone"] = sh.idxmax(axis=1)
    m["zone_share"] = sh.max(axis=1)
    counts = {"cells in all three epochs": len(m)}
    m = m[m.zone_share >= 0.9]
    counts["in one residential zone (>= 90%)"] = len(m)
    m = m[(m.n_valid_e0 >= 810) & (m.n_valid_e1 >= 810) & (m.n_valid_e2 >= 810)]
    counts["valid coverage >= 90% in every epoch"] = len(m)
    for ep in ("e0", "e1", "e2"):
        for t in ("c2", "c3", "c5", "bld"):
            m[f"{t}_{ep}"] = 100 * m[f"n_{t}_{ep}"] / m[f"n_valid_{ep}"]
    m = m[(m.bld_e0 >= 10) & (m.bld_e1 >= 10)]
    counts["built up at E0 and E1 (>= 10% building)"] = len(m)
    pts = gpd.GeoDataFrame(m[["cx", "cy"]], geometry=gpd.points_from_xy(m.cx + 15, m.cy + 15), crs=2193)
    for nm, col in [("sa2", "SA22023_V1_00"), ("talb", "TALB2026_V1_00_NAME")]:
        g = gpd.read_parquet(RUN / "data" / "raw" / f"{nm}.parquet")[[col, "geometry"]]
        j = gpd.sjoin(pts, g, how="left", predicate="within")
        m[nm] = j[~j.index.duplicated()][col].values
    miss = m.sa2.isna() | m.talb.isna()
    counts["dropped: centre outside the (simplified) SA2 / local board polygons"] = int(miss.sum())
    m = m[~miss].copy()
    counts["analysis units"] = len(m)
    m["dist_cbd_km"] = np.hypot(m.cx + 15 - CBD[0], m.cy + 15 - CBD[1]) / 1000
    st = gpd.read_parquet(RUN / "data" / "raw" / "stations.parquet")
    m["dist_station_km"] = cKDTree(np.c_[st.geometry.x, st.geometry.y]).query(np.c_[m.cx + 15, m.cy + 15])[0] / 1000
    m["group"] = m.zone.map({"SH": "SH", "MHS": "low", "MHU": "high", "THAB": "high"})
    m["c1band"] = pd.cut(m.c3_e1, [-0.1, 5, 15, 30, 50, 100.1], labels=["0-5", "5-15", "15-30", "30-50", ">50"]).astype(str)
    m["dband"] = pd.cut(m.dist_cbd_km, [-1, 5, 10, 20, 1e3], labels=["0-5", "5-10", "10-20", ">20"]).astype(str)
    m["stratum"] = m.talb.astype(str) + "|" + m.c1band + "|" + m.dband + "|" + m.coll.astype(str)
    m.to_parquet(RUN / "data" / out_name)
    if out_name == "units.parquet":
        pd.Series(counts).to_csv(TAB / "unit_counts.csv")
    print(counts)
    return m


def fit(m, y, label, extra=None, fe="stratum"):
    ok = m.groupby(fe).group.agg(lambda g: ("high" in set(g)) and ("SH" in set(g)))
    q = m[m[fe].map(ok)].copy()
    q["high"] = (q.group == "high").astype(int)
    q["low"] = (q.group == "low").astype(int)
    q["y"] = q[y]
    terms = ["high"] + (["low"] if q.low.sum() > 0 else [])
    f = "y ~ " + " + ".join(terms) + " + dist_station_km" + (f" + {extra}" if extra else "") + f" | {fe}"
    r = pf.feols(f, data=q, vcov={"CRV1": "sa2"})
    b, se = r.coef(), r.se()
    out = []
    for k in terms:
        out.append(dict(analysis=label, outcome=y, term=k, est=b[k], lo=b[k] - Z * se[k], hi=b[k] + Z * se[k], se=se[k],
                        n_units=len(q), n_high=int(q.high.sum()), n_low=int(q.low.sum()), n_sh=int((q.group == "SH").sum()),
                        n_clusters=q.sa2.nunique()))
    return out


def verdict(post, pre):
    pre_ok = abs(pre["est"]) <= 0.5
    if pre_ok and post["est"] <= -1.0 and post["hi"] < 0:
        return "Supported"
    if pre_ok and post["lo"] > -1.0:
        return "Contradicted"
    return "Inconclusive"


def main(e2_sub=None):
    sfx = f"_{e2_sub}" if e2_sub else ""
    m = build_units(e2_sub=e2_sub, out_name=f"units{sfx}.parquet")
    for t in ("c2", "c3", "c5"):
        m[f"d_post_{t}"] = m[f"{t}_e2"] - m[f"{t}_e1"]
        m[f"d_pre_{t}"] = m[f"{t}_e1"] - m[f"{t}_e0"]
    rows = fit(m, "d_post_c3", "PRIMARY post (E1->E2)") + fit(m, "d_pre_c3", "PRIMARY pre-trend (E0->E1)")
    post, pre = rows[0], rows[2]
    v = verdict(post, pre)
    rows[0]["verdict"] = v
    # secondary
    for t in ("c2", "c5"):
        rows += fit(m, f"d_post_{t}", f"threshold {t[1]} m: post") + fit(m, f"d_pre_{t}", f"threshold {t[1]} m: pre")
    m["redev"] = (m.bld_e2 - m.bld_e1).abs() >= 10
    for lab, msk in [("not redeveloped (|d building| < 10 pp)", ~m.redev), ("redeveloped (|d building| >= 10 pp)", m.redev)]:
        rows += fit(m[msk], "d_post_c3", f"mechanism: {lab}")
    for c in ("N", "S"):
        rows += fit(m[m.coll == c], "d_post_c3", f"E1 collection {c}") + fit(m[m.coll == c], "d_pre_c3", f"E1 collection {c}: pre")
    # zone-boundary sample: units within 100 m of an SH | MHU/THAB boundary; FE = 500 m block of the nearest boundary point
    z = gpd.read_parquet(RUN / "data" / "raw" / "aup_residential.parquet")
    shu = z[z.zone == "SH"].buffer(1).union_all()
    hiu = z[z.zone.isin(["MHU", "THAB"])].buffer(1).union_all()
    bnd = gpd.GeoSeries([shu.intersection(hiu)], crs=2193).explode(index_parts=False)
    bnd = bnd[~bnd.is_empty]
    bp = bnd.boundary.explode(index_parts=False).segmentize(10).get_coordinates().values
    d_, i_ = cKDTree(bp).query(np.c_[m.cx + 15, m.cy + 15])
    m["bnd_dist"] = d_
    m["bnd_block"] = (np.floor(bp[i_, 0] / 500)).astype(int).astype(str) + "_" + (np.floor(bp[i_, 1] / 500)).astype(int).astype(str)
    nb = m[m.bnd_dist <= 100]
    rows += fit(nb[nb.group != "low"], "d_post_c3", "zone boundary (<= 100 m): post", fe="bnd_block")
    rows += fit(nb[nb.group != "low"], "d_pre_c3", "zone boundary (<= 100 m): pre", fe="bnd_block")
    res = pd.DataFrame(rows)
    res.to_csv(TAB / f"main_results{sfx}.csv", index=False)
    print(res[res.term == "high"][["analysis", "est", "lo", "hi", "n_units", "n_high", "n_sh"]].round(3).to_string(index=False))
    print("VERDICT:", v)
    share = m.groupby("group").agg(n=("cx", "size"), redev=("redev", "mean"), c3_e0=("c3_e0", "mean"), c3_e1=("c3_e1", "mean"),
                                   c3_e2=("c3_e2", "mean"), bld_e1=("bld_e1", "mean"), bld_e2=("bld_e2", "mean"))
    share.to_csv(TAB / f"group_means{sfx}.csv")
    print(share.round(2).to_string())


if __name__ == "__main__":
    main(*sys.argv[1:])
