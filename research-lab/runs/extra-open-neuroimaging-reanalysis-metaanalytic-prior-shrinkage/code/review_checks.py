#!/usr/bin/env python
"""Checks added after independent review (deviations.md D4), on the same n = 15 draws as the primary run.

(1) False-positive rate of every method relative to S (from the primary draws).
(2) Mean squared error against the ground truth, as a ratio to S (a magnitude metric; the preregistered metrics, Pearson
    r and top-k Dice, are pattern metrics, invariant to rescaling the map).
(3) Mechanism: EB-0 refitted with s2_v randomly permuted across voxels. This keeps the distribution of shrinkage weights
    but breaks their link to effect size. If the loss in r shrinks, the effect-variance link is the main cause.
(4) Repetition time and number of volumes per task, and the subjects excluded for low coverage.
Output: results/tables/review_fpr.csv, review_mse_mechanism.csv, review_tr.csv, review_low_coverage.csv
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
N0, R = 15, 500


def _job(key):
    Y, gmask, _ = A.load(key)
    pri = np.load(RUN / "results" / "priors" / "priors.npz")
    _, q, w, _ = A.CONTRASTS[key]
    zq = (pri[q][gmask] - pri[q][gmask].mean()) / pri[q][gmask].std()
    zw = (pri[w][gmask] - pri[w][gmask].mean()) / pri[w][gmask].std()
    N = Y.shape[0]
    n_gt = N - max(eb.N_GRID)
    rng = np.random.default_rng(list(A.CONTRASTS).index(key) * 1000 + N0)
    prng = np.random.default_rng(99)
    rows = []
    for r in range(R):
        perm = rng.permutation(N)
        gt = Y[perm[:n_gt]].mean(0)
        X = Y[perm[n_gt:][:N0]]
        b = X.mean(0)
        s2 = X.var(0, ddof=1) / N0
        est = {"S": b, "EB-Q": eb.eb_fit(b, s2, zq)[0], "EB-W": eb.eb_fit(b, s2, zw)[0], "EB-0": eb.eb_fit(b, s2, None)[0],
               "EB-0 (s2 permuted)": eb.eb_fit(b, prng.permutation(s2), None)[0]}
        for m, e in est.items():
            rows.append(dict(key=key, draw=r, method=m, r=np.corrcoef(e, gt)[0, 1], mse=np.mean((e - gt) ** 2)))
    return pd.DataFrame(rows)


def main():
    keys = list(A.CONTRASTS)
    # (1) FPR ratios from the primary draws
    fr = []
    for k in keys:
        d = pd.read_parquet(TAB / f"draws_{k}.parquet")
        f = d[d.n == N0].groupby("method").fpr.mean()
        fr.append(dict(key=k, domain=A.CONTRASTS[k][0], **{f"fpr_{m}": f[m] for m in eb.METHODS},
                       **{f"ratio_{m}": f[m] / f["S"] for m in ("EB-Q", "EB-W", "EB-0")}))
    fr = pd.DataFrame(fr)
    fr.to_csv(TAB / "review_fpr.csv", index=False)
    print(fr.round(3).to_string(index=False))
    # (2) + (3)
    with Pool(len(keys)) as pool:
        d = pd.concat(pool.map(_job, keys), ignore_index=True)
    prim = pd.concat([pd.read_parquet(TAB / f"draws_{k}.parquet").assign(key=k) for k in keys])
    chk = prim[(prim.n == N0) & (prim.method == "S")].set_index(["key", "draw"]).r.sort_index()
    mine = d[d.method == "S"].set_index(["key", "draw"]).r.sort_index()
    assert np.allclose(chk.values, mine.values), "draws differ from the primary run"
    m = d.groupby(["key", "method"])[["r", "mse"]].mean().unstack("method")
    out = pd.DataFrame({"domain": [A.CONTRASTS[k][0] for k in m.index]}, index=m.index)
    for meth in ("EB-Q", "EB-W", "EB-0"):
        out[f"mse_ratio_{meth}"] = m["mse"][meth] / m["mse"]["S"]
    out["r_loss_EB0"] = m["r"]["S"] - m["r"]["EB-0"]
    out["r_loss_EB0_permuted_s2"] = m["r"]["S"] - m["r"]["EB-0 (s2 permuted)"]
    out["share_of_loss_from_effect_variance_link"] = 1 - out.r_loss_EB0_permuted_s2 / out.r_loss_EB0
    out = out.reindex(keys)
    out.to_csv(TAB / "review_mse_mechanism.csv")
    print(out.round(3).to_string())
    # (4) TR / volumes and low-coverage exclusions
    tr, low = [], []
    for k in keys:
        for f in sorted((A.FL / k).glob("sub-*.npz")):
            z = np.load(f)
            tr.append(dict(key=k, t_r=float(z["t_r"]), n_vols=int(z["n_vols"])))
            if float(z["coverage"]) < 0.90:
                low.append(dict(key=k, sub=f.stem, coverage=float(z["coverage"])))
    tr = pd.DataFrame(tr).groupby("key").agg(t_r=("t_r", lambda x: ", ".join(map(str, sorted(set(x))))),
                                             n_vols=("n_vols", lambda x: ", ".join(map(str, sorted(set(x))))))
    tr.to_csv(TAB / "review_tr.csv")
    pd.DataFrame(low).to_csv(TAB / "review_low_coverage.csv", index=False)
    print(tr.to_string())
    print(pd.DataFrame(low).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
