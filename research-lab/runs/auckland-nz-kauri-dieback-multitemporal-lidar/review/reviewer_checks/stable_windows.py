"""Reviewer check: between-epoch artefacts from random raster windows (prompt item 1), read as windows, not whole rasters.

Per random 128 x 128 window with >= 50% valid cells in all four mosaics:
  - median dDEM (E2 - E1 ground), and the share with |dDEM| > 1 m (the slip mask rate)
  - dCHM on E1-bare cells (E1 CHM < 0.3 m): a datum / processing shift unconfounded by canopy growth
  - share of negative CHM cells per epoch (DSM below DEM: alignment / processing)
  - window P95 of CHM per epoch and its change, by E1 canopy class (a different stable-area definition)
  - dP95 at 15 m circles centred on the window centre, for windows >= 50 m from any ObsKauri record, with and
    without the E1 P95 > 15 m filter the study used
Aggregate output only.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from scipy.spatial import cKDTree

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-kauri-dieback-multitemporal-lidar")
OUT = RUN / "review" / "reviewer_checks"
N, S, SEED = 1500, 128, 7
rng = np.random.default_rng(SEED)
ds = {n: rasterio.open(RUN / "data" / f"mosaic_{n}.tif") for n in ("e1_dsm", "e1_dem", "e2_dsm", "e2_dem")}
tf = ds["e1_dsm"].transform
H, W = ds["e1_dsm"].height, ds["e1_dsm"].width
allpts = pd.read_parquet(RUN / "data" / "raw" / "obskauri.parquet")[["x", "y"]].dropna().to_numpy()
kd = cKDTree(allpts)

rows = []
yy, xx = np.mgrid[-15:16, -15:16]
disk = (xx ** 2 + yy ** 2) <= 225
for i in range(N):
    r0, c0 = int(rng.integers(0, H - S)), int(rng.integers(0, W - S))
    w = Window(c0, r0, S, S)
    a = {n: d.read(1, window=w) for n, d in ds.items()}
    v = np.isfinite(a["e1_dsm"]) & np.isfinite(a["e1_dem"]) & np.isfinite(a["e2_dsm"]) & np.isfinite(a["e2_dem"])
    if v.mean() < 0.5:
        continue
    chm1, chm2 = a["e1_dsm"] - a["e1_dem"], a["e2_dsm"] - a["e2_dem"]
    ddem = a["e2_dem"] - a["e1_dem"]
    ddsm = a["e2_dsm"] - a["e1_dsm"]
    bare = v & (chm1 < 0.3)
    forest = v & (chm1 > 15)
    cx, cy = tf * (c0 + S / 2, r0 + S / 2)
    far = kd.query([cx, cy])[0] > 50
    # 15 m circle at the window centre
    m = disk & v[S // 2 - 15:S // 2 + 16, S // 2 - 15:S // 2 + 16] & ~(np.abs(ddem[S // 2 - 15:S // 2 + 16, S // 2 - 15:S // 2 + 16]) > 1)
    c1 = np.clip(chm1[S // 2 - 15:S // 2 + 16, S // 2 - 15:S // 2 + 16][m], 0, None)
    c2 = np.clip(chm2[S // 2 - 15:S // 2 + 16, S // 2 - 15:S // 2 + 16][m], 0, None)
    row = {"valid": float(v.mean()), "far": bool(far),
           "ddem_median": float(np.median(ddem[v])), "ddem_p05": float(np.percentile(ddem[v], 5)), "ddem_p95": float(np.percentile(ddem[v], 95)),
           "slip_share": float((np.abs(ddem[v]) > 1).mean()),
           "bare_share": float(bare.sum() / v.sum()),
           "dchm_bare_median": float(np.median((chm2 - chm1)[bare])) if bare.sum() >= 50 else np.nan,
           "ddsm_bare_median": float(np.median(ddsm[bare])) if bare.sum() >= 50 else np.nan,
           "neg_chm1_share": float((chm1[v] < -0.5).mean()), "neg_chm2_share": float((chm2[v] < -0.5).mean()),
           "zero_chm1_share": float((np.abs(chm1[v]) < 0.05).mean()), "zero_chm2_share": float((np.abs(chm2[v]) < 0.05).mean()),
           "p95_chm1": float(np.percentile(np.clip(chm1[v], 0, None), 95)), "p95_chm2": float(np.percentile(np.clip(chm2[v], 0, None), 95)),
           "p50_chm1": float(np.percentile(np.clip(chm1[v], 0, None), 50)), "p50_chm2": float(np.percentile(np.clip(chm2[v], 0, None), 50)),
           "forest_share": float(forest.sum() / v.sum()),
           "dchm_forest_median": float(np.median((chm2 - chm1)[forest])) if forest.sum() >= 50 else np.nan,
           "circ_valid": float(m.sum() / disk.sum()),
           "circ_p95_1": float(np.percentile(c1, 95)) if m.sum() >= 0.5 * disk.sum() else np.nan,
           "circ_p95_2": float(np.percentile(c2, 95)) if m.sum() >= 0.5 * disk.sum() else np.nan}
    rows.append(row)
for d in ds.values():
    d.close()
df = pd.DataFrame(rows)
df["dp95_window"] = df.p95_chm2 - df.p95_chm1
df["dp50_window"] = df.p50_chm2 - df.p50_chm1
df["circ_dp95"] = df.circ_p95_2 - df.circ_p95_1
df.to_csv(OUT / "stable_windows.csv", index=False)


def q(s):
    s = s.dropna()
    return {"n": int(len(s)), "mean": round(float(s.mean()), 3), "q05": round(float(s.quantile(.05)), 3), "q25": round(float(s.quantile(.25)), 3),
            "median": round(float(s.median()), 3), "q75": round(float(s.quantile(.75)), 3), "q95": round(float(s.quantile(.95)), 3)}


res = {"windows_used": int(len(df)),
       "ddem_median_per_window": q(df.ddem_median), "slip_share_per_window": q(df.slip_share),
       "dchm_on_E1_bare_cells_median_per_window": q(df.dchm_bare_median), "ddsm_on_E1_bare_cells": q(df.ddsm_bare_median),
       "neg_chm_share_e1": q(df.neg_chm1_share), "neg_chm_share_e2": q(df.neg_chm2_share),
       "zero_chm_share_e1": q(df.zero_chm1_share), "zero_chm_share_e2": q(df.zero_chm2_share),
       "dP95_window_all": q(df.dp95_window), "dP50_window_all": q(df.dp50_window),
       "dchm_forest_cells_median": q(df.dchm_forest_median),
       "circle15_dp95_far_E1P95_gt15 (study definition)": q(df[df.far & (df.circ_p95_1 > 15)].circ_dp95),
       "circle15_dp95_far_any_canopy": q(df[df.far].circ_dp95),
       "circle15_dp95_far_E1P95_gt25": q(df[df.far & (df.circ_p95_1 > 25)].circ_dp95),
       "circle15_dp95_far_E1P95_10to20": q(df[df.far & (df.circ_p95_1 > 10) & (df.circ_p95_1 <= 20)].circ_dp95),
       "circle15_dp95_near_records_lt50m": q(df[~df.far].circ_dp95)}
bins = [0, 5, 10, 15, 20, 25, 30, 60]
res["dP95_window_by_E1_P95_class"] = {f"{bins[i]}-{bins[i+1]}": q(df[(df.p95_chm1 > bins[i]) & (df.p95_chm1 <= bins[i + 1])].dp95_window) for i in range(len(bins) - 1)}
res["spearman_dp95_vs_p95_e1_window"] = round(float(df[["dp95_window", "p95_chm1"]].corr("spearman").iloc[0, 1]), 3)
json.dump(res, open(OUT / "stable_windows.json", "w"), indent=1)
print(json.dumps(res, indent=1))
