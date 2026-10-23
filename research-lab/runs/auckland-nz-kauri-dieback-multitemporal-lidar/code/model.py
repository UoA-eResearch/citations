"""H1, H2 and the secondary analyses (plan sections 3-4), from results/tables/trees.csv and data/trees_xy.parquet.

Logistic regression on standardised features; spatially blocked 5-fold CV (500 m blocks, folds by block, 5 repeats
with seeds 20261023-27). D1: AUC is computed within each test fold and averaged over folds and repeats (pooling
out-of-fold predictions across folds is biased under blocked CV); 95% interval from a block bootstrap of the per-fold
AUC (B = 2,000; the gain is paired); a within-block label-shuffle null (200 shuffles) for the change model.
Writes results/tables/primary.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
SEEDS, B, BLOCK = range(20261023, 20261028), 2000, 500.0


def frame():
    t = pd.read_csv(T / "trees.csv")
    xy = pd.read_parquet(RUN / "data" / "trees_xy.parquet")
    t["x"], t["y"] = xy.x.to_numpy(), xy.y.to_numpy()
    t["block"] = (np.floor(t.x / BLOCK).astype(int).astype(str) + "_" + np.floor(t.y / BLOCK).astype(int).astype(str))
    for R in (10, 15, 20):
        for tag in ("m", "u"):
            if f"p95_e1_{tag}_r{R}" in t:
                t[f"dp95_{tag}_r{R}"] = t[f"p95_e2_{tag}_r{R}"] - t[f"p95_e1_{tag}_r{R}"]
                t[f"dp50_{tag}_r{R}"] = t[f"p50_e2_{tag}_r{R}"] - t[f"p50_e1_{tag}_r{R}"]
                t[f"dc15_{tag}_r{R}"] = t[f"c15_e2_{tag}_r{R}"] - t[f"c15_e1_{tag}_r{R}"]
    return t


def oof(d, cols, y):
    """D1: per repeat, out-of-fold predictions and fold ids (blocked 5-fold, 500 m blocks)."""
    blocks = d.block.to_numpy()
    ub = np.unique(blocks)
    P, F = [], []
    for s in SEEDS:
        rng = np.random.default_rng(s)
        fold_of = dict(zip(ub, rng.permutation(len(ub)) % 5))
        f = np.array([fold_of[b] for b in blocks])
        p = np.full(len(d), np.nan)
        X = d[cols].to_numpy()
        for k in range(5):
            tr, te = f != k, f == k
            if y[tr].min() == y[tr].max() or te.sum() == 0:
                continue
            m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
            m.fit(X[tr], y[tr])
            p[te] = m.predict_proba(X[te])[:, 1]
        P.append(p); F.append(f)
    return np.array(P), np.array(F)


def cv_auc(y, P, F, idx=None):
    """D1: mean over repeats and folds of the within-fold AUC (folds with both classes only)."""
    idx = np.arange(len(y)) if idx is None else idx
    vals = []
    for p, f in zip(P, F):
        for k in range(5):
            sel = idx[f[idx] == k]
            if len(sel) and 0 < y[sel].sum() < len(sel):
                vals.append(roc_auc_score(y[sel], p[sel]))
    return float(np.mean(vals)) if vals else float("nan")


def boot_auc(y, preds, blocks, seed=20261023):
    """Block bootstrap of the per-fold AUC for each (P, F) pair in preds (paired across models)."""
    ub, inv = np.unique(blocks, return_inverse=True)
    idx = [np.nonzero(inv == i)[0] for i in range(len(ub))]
    rng = np.random.default_rng(seed)
    est = [cv_auc(y, P, F) for P, F in preds]
    bs = []
    for _ in range(B):
        sel = np.concatenate([idx[i] for i in rng.integers(0, len(ub), len(ub))])
        bs.append([cv_auc(y, P, F, sel) for P, F in preds])
    return np.array(est), np.array(bs)


def shuffle_null(x, cols, y, n=200, seed=20261023):
    """D1: labels permuted within blocks; per-fold AUC of the refitted model (mean and 95th percentile)."""
    rng = np.random.default_rng(seed)
    blocks = x.block.to_numpy()
    vals = []
    for _ in range(n):
        yy = y.copy()
        for b in np.unique(blocks):
            m = np.nonzero(blocks == b)[0]
            yy[m] = rng.permutation(yy[m])
        P, F = oof(x, cols, yy)
        vals.append(cv_auc(yy, P, F))
    return {"mean": round(float(np.mean(vals)), 4), "p95": round(float(np.percentile(vals, 95)), 4)}


def ci(a):
    a = a[~np.isnan(a)]
    return [round(float(np.percentile(a, 2.5)), 4), round(float(np.percentile(a, 97.5)), 4)]


def run(d, pos, neg, R=15, tag="m", null=False):
    x = d[d.status.isin(pos + neg)].copy()
    ch = [f"dp95_{tag}_r{R}", f"dc15_{tag}_r{R}", f"dp50_{tag}_r{R}"]
    st = ["elev", "slope", f"p95_e1_{tag}_r{R}", "dist_track"]
    x = x.dropna(subset=ch + st).reset_index(drop=True)
    y = x.status.isin(pos).astype(int).to_numpy()
    m_ch, m_st, m_all = oof(x, ch, y), oof(x, st, y), oof(x, st + ch, y)
    est, bs = boot_auc(y, [m_ch, m_st, m_all], x.block.to_numpy())
    gain = bs[:, 2] - bs[:, 1]
    out = {"n": int(len(x)), "positives": int(y.sum()), "blocks": int(x.block.nunique()),
           "auc_change": round(float(est[0]), 4), "auc_change_ci": ci(bs[:, 0]),
           "auc_static": round(float(est[1]), 4), "auc_static_ci": ci(bs[:, 1]),
           "auc_static_plus_change": round(float(est[2]), 4), "auc_static_plus_change_ci": ci(bs[:, 2]),
           "gain": round(float(est[2] - est[1]), 4), "gain_ci": ci(gain)}
    if null:
        out["within_block_shuffle_null_change"] = shuffle_null(x, ch, y)
    return out


def verdicts(r):
    lo, hi = r["auc_change_ci"]
    h1 = "Supported" if (r["auc_change"] >= 0.70 and lo > 0.60) else "Refuted" if hi < 0.70 else "Inconclusive"
    glo, ghi = r["gain_ci"]
    h2 = "Supported" if (r["gain"] >= 0.05 and glo > 0) else "Refuted" if ghi < 0.05 else "Inconclusive"
    return h1, h2


def group_means(d, R=15, tag="m"):
    out = {}
    for name, g in d.groupby(["survey", "status"]):
        g = g.dropna(subset=[f"dp95_{tag}_r{R}"])
        if len(g) < 5:
            continue
        ub, inv = np.unique(g.block, return_inverse=True)
        idx = [np.nonzero(inv == i)[0] for i in range(len(ub))]
        rng = np.random.default_rng(20261023)
        v = {}
        for col in (f"dp95_{tag}_r{R}", f"dc15_{tag}_r{R}"):
            a = g[col].to_numpy()
            bs = [a[np.concatenate([idx[i] for i in rng.integers(0, len(ub), len(ub))])].mean() for _ in range(1000)]
            v[col] = {"mean": round(float(a.mean()), 3), "ci": ci(np.array(bs))}
        out[f"{name[0]}_status{name[1]}"] = {"n": int(len(g)), **v}
    return out


def main():
    d = frame()
    s14 = d[d.survey == "s2014"]
    out = {"labels_2014": s14.status.value_counts().to_dict(),
           "dropped_by_slip_mask_2014": int(s14[f"dp95_m_r15"].isna().sum())}
    r = run(s14, [3, 4], [1], null=True)
    out["primary"] = r
    out["H1"], out["H2"] = verdicts(r)
    sec = {"s2021": run(d[d.survey == "s2021"], [3, 4], [1], null=True),
           "severe_only_2014": run(s14, [4], [1]),
           "radius_10": run(s14, [3, 4], [1], R=10), "radius_20": run(s14, [3, 4], [1], R=20),
           "no_slip_mask": run(s14, [3, 4], [1], tag="u")}
    out["secondary"] = sec
    st = d[d.survey == "stable"]
    out["stable_area_dp95"] = {"n": int(st["dp95_m_r15"].notna().sum()),
                               "quantiles": {str(q): round(float(st["dp95_m_r15"].quantile(q)), 3) for q in (0.05, 0.25, 0.5, 0.75, 0.95)},
                               "mean": round(float(st["dp95_m_r15"].mean()), 3)}
    out["group_means"] = group_means(d)
    json.dump(out, open(T / "primary.json", "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("labels_2014", "dropped_by_slip_mask_2014", "primary", "H1", "H2")}, indent=1))


if __name__ == "__main__":
    main()
