#!/usr/bin/env python
"""EXPLORATORY analyses defined after the primary results (deviations.md D3), on the same draws as the primary run.

E1 homoscedastic EB: the EB model with s2_v replaced by its mean over voxels (uniform shrinkage weight); toward the
   matched (HEB-Q) and mismatched (HEB-W) maps, and flat (HEB-0).
E2 oracle ceiling: per draw, the best uniform mix lam * z(b) + (1 - lam) * z(m), lam in [0, 1], chosen using the ground
   truth (ORACLE-Q, ORACLE-W). Not a usable method: an upper bound for any uniform use of the prior map.
Check: S correlations must equal the primary run's (same seeds and permutations).
Output: results/tables/explore_draws_{key}.parquet, results/tables/explore_gains.csv
"""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import eb  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
LAM = np.linspace(0, 1, 101)


def _z(x):
    return (x - x.mean()) / x.std()


def oracle(b, m, gt):
    bz, mz, gz = _z(b), _z(m), _z(gt)
    cb, cm, rbm = np.mean(bz * gz), np.mean(mz * gz), np.mean(bz * mz)
    r = (LAM * cb + (1 - LAM) * cm) / np.sqrt(LAM ** 2 + (1 - LAM) ** 2 + 2 * LAM * (1 - LAM) * rbm)
    j = int(np.argmax(r))
    return r[j], LAM[j]


def _job(args):
    key, n, R = args
    Y, gmask, _ = A.load(key)
    pri = np.load(RUN / "results" / "priors" / "priors.npz")
    _, q, w, _ = A.CONTRASTS[key]
    zq, zw = _z(pri[q][gmask]), _z(pri[w][gmask])
    N = Y.shape[0]
    n_gt = N - max(eb.N_GRID)
    rng = np.random.default_rng(list(A.CONTRASTS).index(key) * 1000 + n)
    rows = []
    for r in range(R):
        perm = rng.permutation(N)
        gt = Y[perm[:n_gt]].mean(0)
        X = Y[perm[n_gt:][:n]]
        b = X.mean(0)
        s2 = X.var(0, ddof=1) / n
        s2u = np.full_like(s2, s2.mean())
        out = {"S": b, "HEB-Q": eb.eb_fit(b, s2u, zq)[0], "HEB-W": eb.eb_fit(b, s2u, zw)[0],
               "HEB-0": eb.eb_fit(b, s2u, None)[0]}
        for meth, est in out.items():
            rows.append(dict(n=n, draw=r, method=meth, r=np.corrcoef(est, gt)[0, 1], lam=np.nan))
        for meth, m in (("ORACLE-Q", zq), ("ORACLE-W", zw)):
            rr, lam = oracle(b, m, gt)
            rows.append(dict(n=n, draw=r, method=meth, r=rr, lam=lam))
    d = pd.DataFrame(rows)
    d["key"] = key
    return d


def main():
    R = 500
    jobs = [(k, n, R) for k in A.CONTRASTS for n in eb.N_GRID]
    with Pool(26) as pool:
        draws = pd.concat(pool.map(_job, jobs), ignore_index=True)
    rows = []
    for k in A.CONTRASTS:
        d = draws[draws.key == k].drop(columns="key")
        d.to_parquet(TAB / f"explore_draws_{k}.parquet", index=False)
        prim = pd.read_parquet(TAB / f"draws_{k}.parquet")
        a = prim[prim.method == "S"].set_index(["n", "draw"]).r.sort_index()
        b = d[d.method == "S"].set_index(["n", "draw"]).r.sort_index()
        assert np.allclose(a.values, b.values), f"draws differ from the primary run for {k}"
        g = eb.gains(d, n0=15)
        g["key"], g["domain"] = k, A.CONTRASTS[k][0]
        g["lam_median"] = g.method.map(d[d.n == 15].groupby("method").lam.median())
        rows.append(g)
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(TAB / "explore_gains.csv", index=False)
    print("S correlations identical to the primary run: yes")
    print(out.pivot_table(index="domain", columns="method", values="G", sort=False).round(2).to_string())
    print(out[out.method.str.startswith("ORACLE")].pivot_table(index="domain", columns="method", values="lam_median",
                                                                 sort=False).round(2).to_string())


if __name__ == "__main__":
    main()
