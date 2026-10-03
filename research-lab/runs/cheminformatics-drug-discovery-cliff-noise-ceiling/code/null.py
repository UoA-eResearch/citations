#!/usr/bin/env python
"""Noise-only synthetic null (plan.md sec 6, H3).

For each target: a smooth potency surface f = out-of-fold kNN predictions (k = 5, Tanimoto, 5-fold, seed 0) on ECFP4.
Each draw r = 0..19: y* = f + noise with each molecule's s_i (from results/tables/molecules.parquet, primary noise model);
cliffs re-detected on y* over the fixed similar pairs (|y*_i - y*_j| > 1); the four models retrained on y* with the
published split (stochastic models with seed r); gap* = RMSE(test cliff*) - RMSE(test non-cliff*), averaged over models.
Usage: null.py [t|normal]   (t is primary, D3)
Output: results/tables/null_gaps.csv (t) or null_gaps_normal.csv (dataset, draw, model, gap, n_cliff_test)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models as MD  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
DRAWS = 20
NOISE = sys.argv[1] if len(sys.argv) > 1 else "t"           # primary: t (4 df), as chosen by the plan's coverage rule (D3)


def oof_knn(X, y, seed=0):
    rng = np.random.default_rng(seed)
    fold = rng.integers(0, 5, len(y))
    f = np.zeros(len(y))
    for k in range(5):
        te, tr = fold == k, fold != k
        S = MD.tanimoto(X[te], X[tr])
        nn = np.argsort(-S, axis=1)[:, :5]
        f[te] = y[tr][nn].mean(1)
    return f


def _job(name, r):
    df, X = MD.load(name)
    mol = pd.read_parquet(TAB / "molecules.parquet")
    mol = mol[mol.dataset == name].sort_values("idx")
    pairs = pd.read_parquet(TAB / "similar_pairs.parquet")
    pairs = pairs[pairs.dataset == name]
    y = df["y [pEC50/pKi]"].values
    f = oof_knn(X, y)
    rng = np.random.default_rng(1000 + r)
    e = rng.standard_t(4, len(f)) if NOISE == "t" else rng.standard_normal(len(f))
    ys = f + e * mol.s.values
    d = np.abs(ys[pairs.i.values] - ys[pairs.j.values]) > 1
    cm = np.zeros(len(y), bool)
    cm[pairs.i.values[d]] = True
    cm[pairs.j.values[d]] = True
    tr, te = (df.split == "train").values, (df.split == "test").values
    out = []
    for m in MD.MODELS:
        p = MD.fit_predict(m, X[tr], ys[tr], X[te], seed=r)
        g, _, _ = MD.gap(ys[te], p, cm[te])
        out.append(dict(dataset=name, draw=r, model=m, gap=g, n_cliff_test=int(cm[te].sum())))
    return out


def main():
    names = sorted(p.stem for p in MD.BENCH.glob("*.csv"))
    res = Parallel(n_jobs=28)(delayed(_job)(n, r) for n in names for r in range(DRAWS))
    out = pd.DataFrame([x for r in res for x in r])
    out.to_csv(TAB / ("null_gaps.csv" if NOISE == "t" else "null_gaps_normal.csv"), index=False)
    print(out.groupby("model").gap.mean().round(4).to_dict(), "| draws", len(out) // len(MD.MODELS))


if __name__ == "__main__":
    main()
