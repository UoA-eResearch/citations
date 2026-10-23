"""Reviewer check: independent windowed recomputation of the 15 m circle features (prompt item 2) for a sample of
trees, compared with results/tables/trees.csv. Also an edge / water audit. Written from the plan's definitions, not
from the study's circle_stats. Aggregate output only."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-kauri-dieback-multitemporal-lidar")
OUT = RUN / "review" / "reviewer_checks"
R = 15
t = pd.read_csv(RUN / "results" / "tables" / "trees.csv")
xy = pd.read_parquet(RUN / "data" / "trees_xy.parquet")
assert (t.OBJECTID.to_numpy() == xy.OBJECTID.to_numpy()).all()
t["x"], t["y"] = xy.x.to_numpy(), xy.y.to_numpy()
rng = np.random.default_rng(11)
idx = np.concatenate([t.index[(t.survey == "s2014") & (t.status > 1)].to_numpy(),
                      rng.choice(t.index[(t.survey == "s2014") & (t.status == 1)].to_numpy(), 400, replace=False),
                      rng.choice(t.index[t.survey == "s2021"].to_numpy(), 200, replace=False),
                      rng.choice(t.index[t.survey == "stable"].to_numpy(), 100, replace=False),
                      t.index[t.valid_r15 < 0.999].to_numpy()])            # every tree with a partial circle
idx = np.unique(idx)
ds = {n: rasterio.open(RUN / "data" / f"mosaic_{n}.tif") for n in ("e1_dsm", "e1_dem", "e2_dsm", "e2_dem")}
tf = ds["e1_dsm"].transform
H, W = ds["e1_dsm"].height, ds["e1_dsm"].width
yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
disk = (xx ** 2 + yy ** 2) <= R * R
rows = []
# sort by row/col so GDAL's block cache is used
order = sorted(idx, key=lambda i: (int((5919640.0 - t.y[i]) // 256), int((t.x[i] - 1730269.0) // 256)))
for i in order:
    x, y = float(t.x[i]), float(t.y[i])
    c, r = (~tf) * (x, y)
    c, r = int(np.floor(c)), int(np.floor(r))
    r0, r1, c0, c1 = max(0, r - R), min(H, r + R + 1), max(0, c - R), min(W, c + R + 1)
    w = Window(c0, r0, c1 - c0, r1 - r0)
    a = {n: d.read(1, window=w) for n, d in ds.items()}
    m = disk[(r0 - (r - R)):(r1 - (r - R)), (c0 - (c - R)):(c1 - (c - R))]
    chm1, chm2 = (a["e1_dsm"] - a["e1_dem"])[m], (a["e2_dsm"] - a["e2_dem"])[m]
    ddem = (a["e2_dem"] - a["e1_dem"])[m]
    v = np.isfinite(chm1) & np.isfinite(chm2)
    vm = v & ~(np.abs(ddem) > 1.0)
    n = disk.sum()
    row = {"i": int(i), "survey": t.survey[i], "status": int(t.status[i]), "valid": v.sum() / n, "valid_masked": vm.sum() / n,
           "n_oob": int(n - m.sum()), "neg_chm1_share": float((chm1[v] < -0.5).mean()) if v.any() else np.nan,
           "centre_dsm1_nan": bool(not np.isfinite(a["e1_dsm"][r - r0, c - c0])) if (r0 <= r < r1 and c0 <= c < c1) else True}
    if vm.sum() >= 0.5 * n:
        b1, b2 = np.clip(chm1[vm], 0, None), np.clip(chm2[vm], 0, None)
        row.update(p95_e1=np.percentile(b1, 95), p95_e2=np.percentile(b2, 95), p50_e1=np.percentile(b1, 50), p50_e2=np.percentile(b2, 50),
                   c15_e1=(b1 > 15).mean(), c15_e2=(b2 > 15).mean())
    rows.append(row)
for d in ds.values():
    d.close()
m = pd.DataFrame(rows).set_index("i")
res = {"n_checked": int(len(m)), "by_survey": m.groupby("survey").size().to_dict()}
cmp = {}
for mine, theirs in (("valid", "valid_r15"), ("valid_masked", "valid_masked_r15"), ("p95_e1", "p95_e1_m_r15"), ("p95_e2", "p95_e2_m_r15"),
                     ("p50_e1", "p50_e1_m_r15"), ("c15_e1", "c15_e1_m_r15"), ("c15_e2", "c15_e2_m_r15")):
    a, b = m[mine].to_numpy(dtype=float), t.loc[m.index, theirs].to_numpy(dtype=float)
    both = np.isfinite(a) & np.isfinite(b)
    cmp[theirs] = {"n_both": int(both.sum()), "max_abs_diff": round(float(np.nanmax(np.abs(a[both] - b[both]))), 5) if both.any() else None,
                   "mine_nan_theirs_not": int((~np.isfinite(a) & np.isfinite(b)).sum()), "theirs_nan_mine_not": int((np.isfinite(a) & ~np.isfinite(b)).sum())}
res["agreement_with_trees_csv"] = cmp
res["dp95_max_abs_diff"] = round(float(np.nanmax(np.abs((m.p95_e2 - m.p95_e1) - (t.loc[m.index, "p95_e2_m_r15"] - t.loc[m.index, "p95_e1_m_r15"])))), 5)
# edge / water audit over the whole table
part = t[t.valid_r15 < 0.999]
res["edge_water_audit"] = {"trees_with_partial_circle": int(len(part)), "by_survey": part.groupby("survey").size().to_dict(),
                           "dropped_lt_50pct_masked": int(t.p95_e1_m_r15.isna().sum()),
                           "dropped_by_survey": t[t.p95_e1_m_r15.isna()].groupby("survey").size().to_dict(),
                           "partial_circle_valid_quantiles": {str(q): round(float(part.valid_r15.quantile(q)), 3) for q in (0.05, 0.25, 0.5, 0.75)},
                           "n_oob_cells_gt0 (true raster edge)": int((m.n_oob > 0).sum()),
                           "partial_circles_with_negative_chm_gt10pct": int((m.loc[m.valid < 0.999, "neg_chm1_share"] > 0.1).sum())}
res["negative_chm_share_in_circle_median"] = round(float(m.neg_chm1_share.median()), 4)
res["elev_nan"] = int(t.elev.isna().sum())
res["slope_nan"] = int(t.slope.isna().sum())
json.dump(res, open(OUT / "recompute_features.json", "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
