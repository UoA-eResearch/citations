"""Reviewer check: CV, bootstrap and positive controls on results/tables/trees.csv (prompt item 4), plus
within-block comparisons for the interpretation (item 5). Aggregate output only."""
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
for tag in ("m", "u"):
    t[f"dp95_{tag}"] = t[f"p95_e2_{tag}_r15"] - t[f"p95_e1_{tag}_r15"]
    t[f"dp50_{tag}"] = t[f"p50_e2_{tag}_r15"] - t[f"p50_e1_{tag}_r15"]
    t[f"dc15_{tag}"] = t[f"c15_e2_{tag}_r15"] - t[f"c15_e1_{tag}_r15"]
CH, ST = ["dp95_m", "dc15_m", "dp50_m"], ["elev", "slope", "p95_e1_m_r15", "dist_track"]


def oof(d, cols, y, per_repeat=False):
    blocks = d.block.to_numpy()
    ub = np.unique(blocks)
    preds, per = np.zeros(len(d)), []
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
        per.append(roc_auc_score(y, p))
        preds += p / len(SEEDS)
    return (preds, per) if per_repeat else preds


def block_boot(y, preds, blocks, B=2000, seed=1):
    ub, inv = np.unique(blocks, return_inverse=True)
    idx = [np.nonzero(inv == i)[0] for i in range(len(ub))]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(B):
        sel = np.concatenate([idx[i] for i in rng.integers(0, len(ub), len(ub))])
        if y[sel].min() == y[sel].max():
            continue
        out.append([roc_auc_score(y[sel], p[sel]) for p in preds])
    return np.array(out)


def ci(a):
    return [round(float(np.percentile(a, 2.5)), 3), round(float(np.percentile(a, 97.5)), 3)]


res = {}
s14 = t[(t.survey == "s2014")].dropna(subset=CH + ST).reset_index(drop=True)
y14 = s14.status.isin([3, 4]).astype(int).to_numpy()
# 1. reproduce the primary with a fresh bootstrap seed; per-repeat AUCs vs averaged
p_ch, per = oof(s14, CH, y14, per_repeat=True)
p_st, p_all = oof(s14, ST, y14), oof(s14, ST + CH, y14)
bs = block_boot(y14, [p_ch, p_st, p_all], s14.block.to_numpy())
res["primary_reproduced"] = {"n": int(len(s14)), "positives": int(y14.sum()), "auc_change": round(float(roc_auc_score(y14, p_ch)), 4),
                            "auc_change_ci_newseed": ci(bs[:, 0]), "per_repeat_auc_change": [round(float(a), 4) for a in per],
                            "auc_static": round(float(roc_auc_score(y14, p_st)), 4), "auc_all": round(float(roc_auc_score(y14, p_all)), 4),
                            "gain": round(float(roc_auc_score(y14, p_all) - roc_auc_score(y14, p_st)), 4), "gain_ci_paired": ci(bs[:, 2] - bs[:, 1]),
                            "gain_ci_unpaired_for_contrast": ci(np.random.default_rng(2).permutation(bs[:, 2]) - bs[:, 1])}
# 2. univariate AUCs (no model) for 2014 and 2021: sign so that AUC > 0.5 means 'symptomatic trees lower'
uni = {}
for sv in ("s2014", "s2021"):
    d = t[t.survey == sv].dropna(subset=CH + ST)
    y = d.status.isin([3, 4]).astype(int).to_numpy()
    uni[sv] = {c: round(float(roc_auc_score(y, -d[c].to_numpy())), 3) for c in CH + ["dp95_u", "dc15_u", "dp50_u"] + ST}
    uni[sv]["n"] = int(len(d))
res["univariate_auc_negated_feature"] = uni
# 3. positive controls through the same CV machinery
rng = np.random.default_rng(3)
z = (s14.dp95_m - s14.dp95_m.mean()) / s14.dp95_m.std()
ysyn = (rng.random(len(s14)) < 1 / (1 + np.exp(-(np.log(320 / 9039) - 1.5 * z)))).astype(int)   # synthetic label driven by dP95, same base rate
pc = {}
pc["synthetic_label_from_dp95"] = {"positives": int(ysyn.sum()), "auc_change": round(float(roc_auc_score(ysyn, oof(s14, CH, ysyn))), 3),
                                   "auc_static": round(float(roc_auc_score(ysyn, oof(s14, ST, ysyn))), 3)}
both = t[t.survey.isin(["s2014", "s2021"])].dropna(subset=CH + ST).reset_index(drop=True)
ysv = (both.survey == "s2021").astype(int).to_numpy()
pc["survey_membership_2021_vs_2014"] = {"auc_static": round(float(roc_auc_score(ysv, oof(both, ST, ysv))), 3),
                                        "auc_change": round(float(roc_auc_score(ysv, oof(both, CH, ysv))), 3)}
stv = t[t.survey.isin(["s2014", "stable"])].dropna(subset=CH + ST).reset_index(drop=True)
yst = (stv.survey == "stable").astype(int).to_numpy()
pc["stable_points_vs_2014_trees"] = {"auc_change": round(float(roc_auc_score(yst, oof(stv, CH, yst))), 3)}
# shuffled label null for the 2021 change model (within-block permutation keeps the spatial structure)
s21 = t[t.survey == "s2021"].dropna(subset=CH + ST).reset_index(drop=True)
y21 = s21.status.isin([3, 4]).astype(int).to_numpy()
p21 = oof(s21, CH, y21)
nulls = []
rng = np.random.default_rng(4)
for _ in range(20):
    yp = y21.copy()
    for b, g in s21.groupby("block").indices.items():
        yp[g] = rng.permutation(yp[g])
    nulls.append(roc_auc_score(yp, oof(s21, CH, yp)))
pc["s2021_change_auc"] = round(float(roc_auc_score(y21, p21)), 4)
pc["s2021_within_block_label_shuffle_null_auc"] = {"mean": round(float(np.mean(nulls)), 3), "max": round(float(np.max(nulls)), 3), "n": len(nulls)}
res["positive_controls_and_nulls"] = pc
# 4. within-block mean difference in dP95 (positives - negatives), to separate a tree effect from a place effect
wb = {}
for sv, d, y in (("s2014", s14, y14), ("s2021", s21, y21)):
    d = d.assign(y=y)
    g = d.groupby("block")
    mixed = g.filter(lambda h: h.y.min() != h.y.max())
    dm = mixed.groupby("block").apply(lambda h: h[h.y == 1].dp95_m.mean() - h[h.y == 0].dp95_m.mean(), include_groups=False)
    wts = mixed.groupby("block").apply(lambda h: min((h.y == 1).sum(), (h.y == 0).sum()), include_groups=False)
    raw = d[d.y == 1].dp95_m.mean() - d[d.y == 0].dp95_m.mean()
    # bootstrap over blocks of the weighted within-block difference
    rng = np.random.default_rng(5)
    arr, w = dm.to_numpy(), wts.to_numpy(dtype=float)
    bsw = [np.average(arr[s], weights=w[s]) for s in (rng.integers(0, len(arr), len(arr)) for _ in range(2000))]
    # also adjust for E1 P95 within block: residual dP95 after a linear fit on p95_e1
    X = np.column_stack([np.ones(len(d)), d.p95_e1_m_r15])
    beta = np.linalg.lstsq(X, d.dp95_m, rcond=None)[0]
    d["resid"] = d.dp95_m - X @ beta
    rm = d[d.block.isin(dm.index)].groupby("block").apply(lambda h: h[h.y == 1].resid.mean() - h[h.y == 0].resid.mean(), include_groups=False)
    wb[sv] = {"raw_diff_m": round(float(raw), 3), "mixed_blocks": int(len(dm)),
              "within_block_weighted_diff_m": round(float(np.average(arr, weights=w)), 3), "ci": ci(np.array(bsw)),
              "within_block_diff_after_p95e1_adjust_m": round(float(np.average(rm.to_numpy(), weights=w)), 3),
              "slope_dp95_on_p95e1": round(float(beta[1]), 4),
              "spearman_dp95_vs_p95e1": round(float(d[["dp95_m", "p95_e1_m_r15"]].corr("spearman").iloc[0, 1]), 3),
              "median_p95e1_pos": round(float(d[d.y == 1].p95_e1_m_r15.median()), 2), "median_p95e1_neg": round(float(d[d.y == 0].p95_e1_m_r15.median()), 2)}
res["within_block_dp95_difference"] = wb
# 5. 2021 static+change: what does change add once E1 P95 is in? and the AUC of E1 P95 alone
res["s2021_auc_p95e1_alone_negated"] = round(float(roc_auc_score(y21, -s21.p95_e1_m_r15)), 3)
res["s2021_auc_dist_track_alone"] = round(float(roc_auc_score(y21, s21.dist_track)), 3)
res["blocks"] = {"s2014": int(s14.block.nunique()), "s2014_blocks_with_positives": int(s14[y14 == 1].block.nunique()),
                 "s2014_trees_per_block_median": float(s14.groupby("block").size().median()),
                 "s2021": int(s21.block.nunique()), "s2021_blocks_with_positives": int(s21[y21 == 1].block.nunique())}
json.dump(res, open(OUT / "model_checks.json", "w"), indent=1)
print(json.dumps(res, indent=1))
