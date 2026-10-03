#!/usr/bin/env python
"""Second noise-only null, added after independent review (deviations.md D5).

Same smooth surface as null.py (out-of-fold kNN). Noise worlds:
  normal, t          : per-molecule noise as in null.py
  docfx_0.2/docfx_0.3: a document random effect plus within-document noise. Each molecule is assigned its first
                       pre-2022 ChEMBL document (its own pseudo-document if none); y* = f + u_doc + e, with
                       u_doc ~ N(0, sigma^2 - sigma_w^2) and e ~ N(0, sigma_w^2), so pairs sharing a document share u_doc.
5 draws per target and world. For each draw it records:
  - the full gap (re-detected cliffs) and the restricted gap: cliff molecules in at least one pair with confidence >= 0.9
    under the REAL data's Gaussian prior (npmle_prior_normal.npy) and the real pair noise SD, exactly the H2 rule;
  - calibration statistics to compare with the real data: SD of similar-pair differences, label SD, number of cliff
    test molecules, RMSE on non-cliff test molecules.
Output: results/tables/null_v2.csv, results/tables/null_v2_real_reference.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models as MD  # noqa: E402
import noise_eb as NE  # noqa: E402
import null as N1  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
WORLDS = ["normal", "t", "docfx_0.2", "docfx_0.3"]
DRAWS = 5


def _job(name, world, r):
    df, X = MD.load(name)
    mol = pd.read_parquet(TAB / "molecules.parquet")
    mol = mol[mol.dataset == name].sort_values("idx")
    cp = pd.read_parquet(TAB / "cliff_pairs_conf_normal.parquet")
    cp = cp[cp.dataset == name]
    w = np.load(TAB / "npmle_prior_normal.npy")
    docs = pd.read_parquet(TAB / "molecule_docs.parquet")
    docs = docs[docs.dataset == name].sort_values("idx")
    sigma = float(pd.read_csv(TAB / "noise_model.csv").set_index("standard_type").sigma[name.split("_")[1]])
    y = df["y [pEC50/pKi]"].values
    f = N1.oof_knn(X, y)
    rng = np.random.default_rng(5000 + r)
    n = len(f)
    if world == "normal":
        ys = f + rng.standard_normal(n) * mol.s.values
    elif world == "t":
        ys = f + rng.standard_t(4, n) * mol.s.values
    else:
        sw = float(world.split("_")[1])
        first = [d[0] if len(d) else -(i + 1) for i, d in enumerate(docs.docs)]
        uniq = {d: k for k, d in enumerate(sorted(set(first)))}
        u = rng.normal(0, np.sqrt(max(sigma ** 2 - sw ** 2, 0)), len(uniq))
        ys = f + u[[uniq[d] for d in first]] + rng.normal(0, sw, n)
    i, j = cp.i.values, cp.j.values
    dstar = ys[i] - ys[j]
    cliff = np.abs(dstar) > 1
    conf = NE.confidence(dstar, cp.sd.values, w, "normal")
    cm = np.zeros(n, bool); cm[i[cliff]] = True; cm[j[cliff]] = True
    hc = np.zeros(n, bool); h = cliff & (conf >= 0.9); hc[i[h]] = True; hc[j[h]] = True
    tr, te = (df.split == "train").values, (df.split == "test").values
    out = []
    for m in MD.MODELS:
        p = MD.fit_predict(m, X[tr], ys[tr], X[te], seed=r)
        g, rc, rn = MD.gap(ys[te], p, cm[te])
        gr = MD.gap(ys[te], p, hc[te])[0] if hc[te].any() else np.nan
        out.append(dict(dataset=name, world=world, draw=r, model=m, gap=g, gap_restricted=gr, rmse_noncliff=rn,
                        n_cliff_test=int(cm[te].sum()), n_hc_test=int(hc[te].sum()), pair_diff_sd=float(np.std(dstar)),
                        label_sd=float(np.std(ys))))
    return out


def real_reference():
    cp = pd.read_parquet(TAB / "cliff_pairs_conf_normal.parquet")
    gm = pd.read_csv(TAB / "gaps_by_model.csv")
    rows = []
    for p in sorted(MD.BENCH.glob("*.csv")):
        df = pd.read_csv(p)
        c = cp[cp.dataset == p.stem]
        g = gm[gm.dataset == p.stem].set_index("model")
        rows.append(dict(dataset=p.stem, pair_diff_sd=float(np.std(c.d)), label_sd=float(np.std(df["y [pEC50/pKi]"])),
                         n_cliff_test=int(((df.split == "test") & (df.cliff_mol == 1)).sum()),
                         rmse_noncliff_knn=float(g.rmse_noncliff["KNN"]), gap_knn=float(g.gap["KNN"]), gap_svr=float(g.gap["SVR"])))
    return pd.DataFrame(rows)


def main():
    names = sorted(p.stem for p in MD.BENCH.glob("*.csv"))
    res = Parallel(n_jobs=26)(delayed(_job)(n, wd, r) for n in names for wd in WORLDS for r in range(DRAWS))
    out = pd.DataFrame([x for r in res for x in r])
    out.to_csv(TAB / "null_v2.csv", index=False)
    ref = real_reference()
    ref.to_csv(TAB / "null_v2_real_reference.csv", index=False)
    s = out.groupby(["world", "dataset", "draw"]).agg(gap=("gap", "mean"), gap_r=("gap_restricted", "mean"),
                                                       pair_sd=("pair_diff_sd", "first"), label_sd=("label_sd", "first"),
                                                       ncl=("n_cliff_test", "first")).groupby(["world", "dataset"]).mean()
    knn = out[out.model == "KNN"].groupby(["world", "dataset"]).rmse_noncliff.mean()
    summ = s.groupby("world").mean()
    summ["rmse_noncliff_knn"] = knn.groupby("world").mean()
    print(summ.round(3).to_string())
    print("real:", ref[["pair_diff_sd", "label_sd", "n_cliff_test", "rmse_noncliff_knn"]].mean().round(3).to_dict())


if __name__ == "__main__":
    main()
