"""Confirmation pass (D1): independent per-fold AUC, short within-block shuffle null, within-block dP95 differences and
label-geometry shares on the D1 trees.csv (single-linkage merge). Aggregate output only."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-kauri-dieback-multitemporal-lidar")
OUT = RUN / "review" / "reviewer_checks"
SEEDS, BLOCK = range(20261023, 20261028), 500.0
t = pd.read_csv(RUN / "results" / "tables" / "trees.csv")
xy = pd.read_parquet(RUN / "data" / "trees_xy.parquet")
assert (t.OBJECTID.to_numpy() == xy.OBJECTID.to_numpy()).all()
t["x"], t["y"] = xy.x.to_numpy(), xy.y.to_numpy()
t["block"] = (np.floor(t.x / BLOCK).astype(int).astype(str) + "_" + np.floor(t.y / BLOCK).astype(int).astype(str))
t["dp95"] = t.p95_e2_m_r15 - t.p95_e1_m_r15
t["dp50"] = t.p50_e2_m_r15 - t.p50_e1_m_r15
t["dc15"] = t.c15_e2_m_r15 - t.c15_e1_m_r15
CH, ST = ["dp95", "dc15", "dp50"], ["elev", "slope", "p95_e1_m_r15", "dist_track"]


def perfold(d, cols, y):
    blocks = d.block.to_numpy()
    ub = np.unique(blocks)
    vals = []
    X = d[cols].to_numpy()
    for s in SEEDS:
        rng = np.random.default_rng(s)
        fold_of = dict(zip(ub, rng.permutation(len(ub)) % 5))
        f = np.array([fold_of[b] for b in blocks])
        for k in range(5):
            tr, te = f != k, f == k
            m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(X[tr], y[tr])
            if 0 < y[te].sum() < te.sum():
                vals.append(roc_auc_score(y[te], m.predict_proba(X[te])[:, 1]))
    return float(np.mean(vals))


res = {"counts": {f"{a}_{b}": int(n) for (a, b), n in t.groupby(["survey", "status"]).size().items()}}
raw = pd.read_parquet(RUN / "data" / "raw" / "obskauri.parquet")
for sv, svname in (("s2014", "Waitakere Track Survey 2014-2015"), ("s2021", "Waitakere Survey 2021")):
    d = t[t.survey == sv].dropna(subset=CH + ST).reset_index(drop=True)
    y = d.status.isin([3, 4]).astype(int).to_numpy()
    r = {"n": int(len(d)), "positives": int(y.sum()),
         "perfold_auc": {k: round(perfold(d, c, y), 4) for k, c in (("change", CH), ("static", ST), ("static_plus_change", ST + CH))}}
    rng = np.random.default_rng(41)
    groups = list(d.groupby("block").indices.values())
    nulls = []
    for _ in range(40):
        yp = y.copy()
        for g in groups:
            yp[g] = rng.permutation(yp[g])
        nulls.append(perfold(d, CH, yp))
    r["null_change_40_shuffles"] = {"mean": round(float(np.mean(nulls)), 4), "p95": round(float(np.percentile(nulls, 95)), 4),
                                    "p_one_sided": round(float((np.array(nulls) >= r["perfold_auc"]["change"]).mean()), 3)}
    # within-block dP95 difference (positives - negatives), weighted by min class count, block bootstrap
    dd = d.assign(y=y)
    mixed = dd.groupby("block").filter(lambda h: h.y.min() != h.y.max())
    dm = mixed.groupby("block").apply(lambda h: h[h.y == 1].dp95.mean() - h[h.y == 0].dp95.mean(), include_groups=False).to_numpy()
    w = mixed.groupby("block").apply(lambda h: min((h.y == 1).sum(), (h.y == 0).sum()), include_groups=False).to_numpy(dtype=float)
    rng = np.random.default_rng(5)
    bsw = [np.average(dm[s], weights=w[s]) for s in (rng.integers(0, len(dm), len(dm)) for _ in range(2000))]
    r["within_block_dp95_diff_m"] = {"est": round(float(np.average(dm, weights=w)), 3), "ci": [round(float(np.percentile(bsw, 2.5)), 3), round(float(np.percentile(bsw, 97.5)), 3)],
                                     "mixed_blocks": int(len(dm))}
    # label geometry on the D1 positives, against all raw records of the survey
    allrec = raw[raw.SurveyName == svname].dropna(subset=["x", "y"])
    kd, st = cKDTree(allrec[["x", "y"]].to_numpy()), allrec.KDBFieldStatus.to_numpy()
    pos = d[y == 1]
    nb = kd.query_ball_point(pos[["x", "y"]].to_numpy(), 15.0)
    n_all = np.array([len(b) for b in nb]); n_pos = np.array([int(np.isin(st[b], [3, 4]).sum()) for b in nb]); n_neg = np.array([int((st[b] == 1).sum()) for b in nb])
    neg_xy = allrec[allrec.KDBFieldStatus == 1][["x", "y"]].to_numpy()
    dpn = cKDTree(neg_xy).query(pos[["x", "y"]].to_numpy())[0]
    r["geometry_D1_positives"] = {"median_dist_to_nearest_healthy_record_m": round(float(np.median(dpn)), 2),
                                  "share_with_healthy_record_within_15m": round(float((n_neg > 0).mean()), 3),
                                  "median_share_of_circle_records_symptomatic": round(float(np.median(n_pos / n_all)), 3)}
    res[sv] = r
json.dump(res, open(OUT / "confirm_checks.json", "w"), indent=1)
print(json.dumps(res, indent=1))
