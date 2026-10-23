"""Reviewer check: does co-location of positives and negatives in the 2014-15 survey cap what a 15 m circle can see?
Neighbourhood composition of each tree's 15 m circle, and univariate AUC of -dP95 (block bootstrap) on subsets of
trees whose circles are not contaminated by the other class. Aggregate output only."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.metrics import roc_auc_score

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-kauri-dieback-multitemporal-lidar")
OUT = RUN / "review" / "reviewer_checks"
raw = pd.read_parquet(RUN / "data" / "raw" / "obskauri.parquet")
t = pd.read_csv(RUN / "results" / "tables" / "trees.csv")
xy = pd.read_parquet(RUN / "data" / "trees_xy.parquet")
t["x"], t["y"] = xy.x.to_numpy(), xy.y.to_numpy()
t["block"] = (np.floor(t.x / 500).astype(int).astype(str) + "_" + np.floor(t.y / 500).astype(int).astype(str))
t["dp95"] = t.p95_e2_m_r15 - t.p95_e1_m_r15
t["dc15"] = t.c15_e2_m_r15 - t.c15_e1_m_r15


def boot_auc(y, s, blocks, B=2000, seed=9):
    ub, inv = np.unique(blocks, return_inverse=True)
    idx = [np.nonzero(inv == i)[0] for i in range(len(ub))]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(B):
        sel = np.concatenate([idx[i] for i in rng.integers(0, len(ub), len(ub))])
        if y[sel].min() != y[sel].max():
            out.append(roc_auc_score(y[sel], s[sel]))
    return round(float(roc_auc_score(y, s)), 3), [round(float(np.percentile(out, 2.5)), 3), round(float(np.percentile(out, 97.5)), 3)]


res = {}
for sv, name in (("Waitakere Track Survey 2014-2015", "s2014"), ("Waitakere Survey 2021", "s2021")):
    allrec = raw[(raw.SurveyName == sv)].dropna(subset=["x", "y"])            # every record of the survey, all statuses
    P = allrec[["x", "y"]].to_numpy()
    st = allrec.KDBFieldStatus.to_numpy()
    kd = cKDTree(P)
    d = t[(t.survey == name) & t.dp95.notna()].copy()
    y = d.status.isin([3, 4]).astype(int).to_numpy()
    nb = kd.query_ball_point(d[["x", "y"]].to_numpy(), 15.0)
    n_all = np.array([len(b) for b in nb])
    n_pos = np.array([int(np.isin(st[b], [3, 4]).sum()) for b in nb])
    n_s2 = np.array([int((st[b] == 2).sum()) for b in nb])
    n_neg = np.array([int((st[b] == 1).sum()) for b in nb])
    r = {"n_trees": int(len(d)), "positives": int(y.sum()),
         "records_within_15m_median": {"pos": float(np.median(n_all[y == 1])), "neg": float(np.median(n_all[y == 0]))},
         "share_of_circle_records_symptomatic_median": {"pos": round(float(np.median(n_pos[y == 1] / n_all[y == 1])), 3),
                                                        "neg": round(float(np.median(n_pos[y == 0] / n_all[y == 0])), 3)},
         "positives_with_healthy_record_within_15m": round(float((n_neg[y == 1] > 0).mean()), 3),
         "positives_whose_circle_is_mostly_healthy (>50% status 1)": round(float((n_neg[y == 1] > n_all[y == 1] / 2).mean()), 3),
         "negatives_with_any_status_2-4_within_15m": round(float(((n_pos + n_s2)[y == 0] > 0).mean()), 3)}
    # univariate AUCs on the full set and on 'clean' subsets
    s = -d.dp95.to_numpy()
    r["auc_neg_dp95_all"] = boot_auc(y, s, d.block.to_numpy())
    clean_neg = (y == 0) & ((n_pos + n_s2) == 0)                               # healthy trees with no symptomatic / ill-thrift record in the circle
    for lab, pos_mask in (("pos_no_healthy_within_5m", np.array([int((st[b][kd.query_ball_point(p, 5.0) and True] == 1).sum()) for b, p in zip(nb, d[["x", "y"]].to_numpy())]) if False else None),):
        pass
    # positives with no healthy record within 5 m / 10 m, versus clean negatives
    for rad in (5.0, 10.0, 15.0):
        nb_r = kd.query_ball_point(d[["x", "y"]].to_numpy(), rad)
        n_neg_r = np.array([int((st[b] == 1).sum()) for b in nb_r])
        pos_iso = (y == 1) & (n_neg_r == 0)
        keep = pos_iso | clean_neg
        if pos_iso.sum() >= 10:
            r[f"auc_neg_dp95_isolated_pos_no_healthy_within_{int(rad)}m_vs_clean_neg"] = {"n_pos": int(pos_iso.sum()), "n_neg": int(clean_neg.sum()),
                                                                                       "auc_ci": boot_auc(y[keep], s[keep], d.block.to_numpy()[keep])}
    # positives that are the majority of their circle's records
    maj = (y == 1) & (n_pos > n_all / 2)
    keep = maj | clean_neg
    if maj.sum() >= 10:
        r["auc_neg_dp95_pos_majority_of_circle_vs_clean_neg"] = {"n_pos": int(maj.sum()), "auc_ci": boot_auc(y[keep], s[keep], d.block.to_numpy()[keep])}
    # the same for dc15
    r["auc_neg_dc15_all"] = boot_auc(y, -d.dc15.to_numpy(), d.block.to_numpy())
    # correlation between a positive's dP95 and its nearest negative's dP95 (feature sharing)
    if y.sum() > 0:
        posxy, negxy = d[y == 1][["x", "y"]].to_numpy(), d[y == 0][["x", "y"]].to_numpy()
        dist, j = cKDTree(negxy).query(posxy)
        a, b = d[y == 1].dp95.to_numpy(), d[y == 0].dp95.to_numpy()[j]
        r["corr_dp95_positive_vs_nearest_negative"] = {"pearson": round(float(np.corrcoef(a, b)[0, 1]), 3), "median_dist_m": round(float(np.median(dist)), 1),
                                                       "share_identical_feature": round(float((np.abs(a - b) < 1e-6).mean()), 3)}
    res[name] = r
json.dump(res, open(OUT / "isolation_check.json", "w"), indent=1)
print(json.dumps(res, indent=1))
