"""Reviewer check: (a) is the chance-level change AUC a property of the data or of the 3-feature logistic model?
CV AUC of a one-feature model (dP95) under the study's blocked CV, and per-fold coefficient signs of the 3-feature
model; (b) within-block label-shuffle nulls (place effect kept, tree effect destroyed) for the CV change model and
for the univariate -dP95 AUC, 2014 and 2021. Aggregate output only."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-kauri-dieback-multitemporal-lidar")
OUT = RUN / "review" / "reviewer_checks"
SEEDS, BLOCK = range(20261023, 20261028), 500.0
t = pd.read_csv(RUN / "results" / "tables" / "trees.csv")
xy = pd.read_parquet(RUN / "data" / "trees_xy.parquet")
t["x"], t["y"] = xy.x.to_numpy(), xy.y.to_numpy()
t["block"] = (np.floor(t.x / BLOCK).astype(int).astype(str) + "_" + np.floor(t.y / BLOCK).astype(int).astype(str))
t["dp95"] = t.p95_e2_m_r15 - t.p95_e1_m_r15
t["dp50"] = t.p50_e2_m_r15 - t.p50_e1_m_r15
t["dc15"] = t.c15_e2_m_r15 - t.c15_e1_m_r15
CH, ST = ["dp95", "dc15", "dp50"], ["elev", "slope", "p95_e1_m_r15", "dist_track"]


def oof(d, cols, y, coefs=None):
    blocks = d.block.to_numpy()
    ub = np.unique(blocks)
    preds = np.zeros(len(d))
    for s in SEEDS:
        rng = np.random.default_rng(s)
        fold_of = dict(zip(ub, rng.permutation(len(ub)) % 5))
        f = np.array([fold_of[b] for b in blocks])
        p = np.zeros(len(d))
        for k in range(5):
            tr, te = f != k, f == k
            m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
            m.fit(d.loc[tr, cols].to_numpy(), y[tr])
            p[te] = m.predict_proba(d.loc[te, cols].to_numpy())[:, 1]
            if coefs is not None:
                coefs.append(m[-1].coef_[0])
        preds += p / len(SEEDS)
    return preds


res = {}
for sv in ("s2014", "s2021"):
    d = t[t.survey == sv].dropna(subset=CH + ST).reset_index(drop=True)
    y = d.status.isin([3, 4]).astype(int).to_numpy()
    r = {"n": int(len(d)), "positives": int(y.sum())}
    co = []
    r["auc_cv_change_3feat"] = round(float(roc_auc_score(y, oof(d, CH, y, co))), 4)
    co = np.array(co)
    r["coef_sign_share_negative_per_feature (dp95, dc15, dp50)"] = [round(float((co[:, j] < 0).mean()), 2) for j in range(3)]
    r["coef_mean (dp95, dc15, dp50)"] = [round(float(co[:, j].mean()), 3) for j in range(3)]
    r["feature_corr"] = d[CH].corr().round(2).to_dict()
    r["auc_cv_change_dp95_only"] = round(float(roc_auc_score(y, oof(d, ["dp95"], y))), 4)
    r["auc_cv_change_dp95_dc15"] = round(float(roc_auc_score(y, oof(d, ["dp95", "dc15"], y))), 4)
    r["auc_cv_static_plus_dp95_only"] = round(float(roc_auc_score(y, oof(d, ST + ["dp95"], y))), 4)
    r["auc_cv_static"] = round(float(roc_auc_score(y, oof(d, ST, y))), 4)
    r["auc_univariate_neg_dp95"] = round(float(roc_auc_score(y, -d.dp95)), 4)
    # within-block label shuffles
    groups = list(d.groupby("block").indices.values())
    rng = np.random.default_rng(21)
    null_uni, null_cv = [], []
    for i in range(500):
        yp = y.copy()
        for g in groups:
            yp[g] = rng.permutation(yp[g])
        null_uni.append(roc_auc_score(yp, -d.dp95))
        if i < 100:
            null_cv.append(roc_auc_score(yp, oof(d, CH, yp)))
    null_uni, null_cv = np.array(null_uni), np.array(null_cv)
    obs_u, obs_c = r["auc_univariate_neg_dp95"], r["auc_cv_change_3feat"]
    r["null_within_block_shuffle_univariate"] = {"n": 500, "mean": round(float(null_uni.mean()), 4), "q95": round(float(np.percentile(null_uni, 95)), 4),
                                                 "p_one_sided": round(float((null_uni >= obs_u).mean()), 3)}
    r["null_within_block_shuffle_cv_3feat"] = {"n": 100, "mean": round(float(null_cv.mean()), 4), "q95": round(float(np.percentile(null_cv, 95)), 4),
                                               "p_one_sided": round(float((null_cv >= obs_c).mean()), 3)}
    res[sv] = r
json.dump(res, open(OUT / "cv_variants.json", "w"), indent=1)
print(json.dumps(res, indent=1))
