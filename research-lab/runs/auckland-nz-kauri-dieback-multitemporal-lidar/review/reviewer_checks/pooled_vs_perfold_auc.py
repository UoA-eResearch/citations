"""Reviewer check: pooled out-of-fold AUC (the study's estimator) versus the mean of per-fold AUCs, with the
within-block label-shuffle null for each, and the spread of training prevalence across block folds. Aggregate only."""
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


def both_aucs(d, cols, y, stats=None):
    """pooled AUC of repeat-averaged OOF predictions (study) and mean per-fold AUC over repeats x folds."""
    blocks = d.block.to_numpy()
    ub = np.unique(blocks)
    preds, perfold = np.zeros(len(d)), []
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
            if y[te].min() != y[te].max():
                perfold.append(roc_auc_score(y[te], p[te]))
            if stats is not None:
                stats.append((int(y[te].sum()), float(y[tr].mean())))
        preds += p / len(SEEDS)
    return roc_auc_score(y, preds), float(np.mean(perfold))


res = {}
for sv in ("s2014", "s2021"):
    d = t[t.survey == sv].dropna(subset=CH + ST).reset_index(drop=True)
    y = d.status.isin([3, 4]).astype(int).to_numpy()
    st = []
    r = {}
    for name, cols in (("change", CH), ("static", ST), ("static_plus_change", ST + CH)):
        pooled, pf = both_aucs(d, cols, y, st if name == "change" else None)
        r[name] = {"pooled_oof_auc (study)": round(pooled, 4), "mean_per_fold_auc": round(pf, 4)}
    st = np.array(st)
    r["test_fold_positives_min_max"] = [int(st[:, 0].min()), int(st[:, 0].max())]
    r["training_prevalence_min_max"] = [round(float(st[:, 1].min()), 4), round(float(st[:, 1].max()), 4)]
    groups = list(d.groupby("block").indices.values())
    rng = np.random.default_rng(31)
    nulls = []
    for i in range(60):
        yp = y.copy()
        for g in groups:
            yp[g] = rng.permutation(yp[g])
        nulls.append(both_aucs(d, CH, yp))
    nulls = np.array(nulls)
    r["null_change_model"] = {"n": 60, "pooled_mean": round(float(nulls[:, 0].mean()), 4), "pooled_q05_q95": [round(float(np.percentile(nulls[:, 0], 5)), 4), round(float(np.percentile(nulls[:, 0], 95)), 4)],
                              "per_fold_mean": round(float(nulls[:, 1].mean()), 4), "per_fold_q05_q95": [round(float(np.percentile(nulls[:, 1], 5)), 4), round(float(np.percentile(nulls[:, 1], 95)), 4)],
                              "p_pooled": round(float((nulls[:, 0] >= r["change"]["pooled_oof_auc (study)"]).mean()), 3),
                              "p_per_fold": round(float((nulls[:, 1] >= r["change"]["mean_per_fold_auc"]).mean()), 3)}
    res[sv] = r
json.dump(res, open(OUT / "pooled_vs_perfold_auc.json", "w"), indent=1)
print(json.dumps(res, indent=1))
