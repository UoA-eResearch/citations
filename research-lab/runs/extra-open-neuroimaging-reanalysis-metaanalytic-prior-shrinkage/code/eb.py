"""Empirical-Bayes shrinkage toward a prior map and the subsampling experiment (plan.md sec 4-6).

Model per voxel v: b_v ~ N(theta_v, s2_v), theta_v ~ N(alpha + beta * m_v, tau2). (alpha, beta, tau2) maximise the
marginal likelihood sum_v log N(b_v; alpha + beta m_v, tau2 + s2_v). It is maximised by profiling: for fixed tau2,
(alpha, beta) is the closed-form weighted least-squares solution (beta >= 0: if negative, beta = 0 and alpha is the
weighted mean); log tau2 is then optimised by a bounded 1-D search. This reaches the same maximum as the joint L-BFGS-B fit
named in plan.md (deviations.md D1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize, stats

N_GRID = [10, 15, 20, 25, 30, 40, 50, 60, 80]
METHODS = ["S", "EB-Q", "EB-W", "EB-0"]


def _wls(b, m, w, nonneg):
    """Weighted least squares of b on [1, m] with weights w; returns alpha, beta (beta >= 0 if nonneg)."""
    if m is None:
        return np.sum(w * b) / np.sum(w), 0.0
    sw, swm, swmm = w.sum(), (w * m).sum(), (w * m * m).sum()
    swb, swmb = (w * b).sum(), (w * m * b).sum()
    det = sw * swmm - swm * swm
    beta = (sw * swmb - swm * swb) / det
    if nonneg and beta < 0:
        return swb / sw, 0.0
    alpha = (swb - beta * swm) / sw
    return alpha, beta


def eb_fit(b, s2, m=None, nonneg=True):
    """Returns posterior mean theta_hat, posterior z, and (alpha, beta, tau2). m=None: flat prior (beta = 0)."""
    vb = np.var(b)

    def negll(lt):
        t2 = np.exp(lt)
        v = t2 + s2
        a, be = _wls(b, m, 1 / v, nonneg)
        mu = a + (be * m if m is not None else 0.0)
        return 0.5 * np.sum(np.log(v) + (b - mu) ** 2 / v)

    lo, hi = np.log(vb * 1e-6 + 1e-12), np.log(vb * 10 + 1e-12)
    res = optimize.minimize_scalar(negll, bounds=(lo, hi), method="bounded", options={"xatol": 1e-4})
    t2 = np.exp(res.x)
    a, be = _wls(b, m, 1 / (t2 + s2), nonneg)
    mu = a + (be * m if m is not None else 0.0)
    w = t2 / (t2 + s2)
    theta = w * b + (1 - w) * mu
    z = theta / np.sqrt(w * s2)
    return theta, z, (a, be, t2)


def _t_to_z(t, df):
    return stats.norm.isf(stats.t.sf(t, df))


def _metrics(est, z, gt, gt_null, top_gt10, top_gt5):
    V = len(gt)
    r = np.corrcoef(est, gt)[0, 1]
    k10, k5 = int(round(0.10 * V)), int(round(0.05 * V))
    top10 = np.argpartition(-est, k10)[:k10]
    top5 = np.argpartition(-est, k5)[:k5]
    d10 = np.isin(top10, top_gt10).sum() / k10
    d5 = np.isin(top5, top_gt5).sum() / k5
    fpr = np.mean(z[gt_null] > 3.09) if gt_null.mean() >= 0.01 else np.nan
    return r, d10, d5, fpr


def run_draws(Y, prior_q, prior_w, n_grid=N_GRID, R=500, seed=0, nonneg=True, n_gt=None):
    """Y: subjects x voxels. prior_q / prior_w: matched / mismatched prior vectors (z-scored here).
    Returns one row per (n, draw, method) with r, dice10, dice5, fpr, r_alt (ground truth = all non-subsample subjects)."""
    N, V = Y.shape
    n_gt = N - max(n_grid) if n_gt is None else n_gt
    zq = (prior_q - prior_q.mean()) / prior_q.std()
    zw = (prior_w - prior_w.mean()) / prior_w.std()
    rows = []
    for n in n_grid:
        rng = np.random.default_rng(seed * 1000 + n)
        for r in range(R):
            perm = rng.permutation(N)
            gt_idx, rest = perm[:n_gt], perm[n_gt:]
            sub = rest[:n]                                            # rest is already a random order
            G = Y[gt_idx]
            gt = G.mean(0)
            gt_z = _t_to_z(gt / (G.std(0, ddof=1) / np.sqrt(n_gt)), n_gt - 1)
            gt_null = np.abs(gt_z) < 1.96
            k10, k5 = int(round(0.10 * V)), int(round(0.05 * V))
            top_gt10, top_gt5 = np.argpartition(-gt, k10)[:k10], np.argpartition(-gt, k5)[:k5]
            alt_mask = np.ones(N, bool)
            alt_mask[sub] = False
            gt_alt = Y[alt_mask].mean(0)
            X = Y[sub]
            b = X.mean(0)
            s2 = X.var(0, ddof=1) / n
            outs = {"S": (b, _t_to_z(b / np.sqrt(s2), n - 1), (np.nan, np.nan, np.nan))}
            outs["EB-Q"] = eb_fit(b, s2, zq, nonneg)
            outs["EB-W"] = eb_fit(b, s2, zw, nonneg)
            outs["EB-0"] = eb_fit(b, s2, None, nonneg)
            for meth, (est, z, (a, be, t2)) in outs.items():
                rr, d10, d5, fpr = _metrics(est, z, gt, gt_null, top_gt10, top_gt5)
                rows.append(dict(n=n, draw=r, method=meth, r=rr, dice10=d10, dice5=d5, fpr=fpr,
                                 r_alt=np.corrcoef(est, gt_alt)[0, 1], alpha=a, beta=be, tau2=t2,
                                 null_share=gt_null.mean()))
    return pd.DataFrame(rows)


def n_equivalent(rbar_s: pd.Series, target: float, n_grid=N_GRID):
    """Solve rbar_S(n_eq) = target by linear interpolation of rbar_S against log n over the grid.
    Returns (n_eq, flag) with flag '' inside the grid, '>' above the largest n, '<' below the smallest."""
    x = np.log(np.array(n_grid, float))
    y = rbar_s.reindex(n_grid).values
    y = np.maximum.accumulate(y)                                       # monotone for inversion
    if target > y[-1]:
        return float(n_grid[-1]), ">"
    if target < y[0]:
        return float(n_grid[0]), "<"
    j = np.searchsorted(y, target)
    j = min(max(j, 1), len(y) - 1)
    if y[j] == y[j - 1]:
        return float(np.exp(x[j])), ""
    f = (target - y[j - 1]) / (y[j] - y[j - 1])
    return float(np.exp(x[j - 1] + f * (x[j] - x[j - 1]))), ""


def gains(draws: pd.DataFrame, n0=15, nboot=2000, seed=1, metric="r"):
    """Effective-sample-size gain G = n_eq / n0 for each method at n0, with paired bootstrap over draws."""
    piv = draws.pivot_table(index=["n", "draw"], columns="method", values=metric)
    ns = sorted(draws.n.unique())
    R = draws.draw.nunique()
    point_s = piv["S"].groupby(level=0).mean()
    out = []
    rng = np.random.default_rng(seed)
    boot_idx = rng.integers(0, R, size=(nboot, R))
    arr = {m: np.stack([piv.loc[n][m].values for n in ns]) for m in piv.columns}   # n x R
    for m in piv.columns:
        ne, flag = n_equivalent(point_s, piv.loc[n0][m].mean(), ns)
        bs = []
        for k in range(nboot):
            idx = boot_idx[k]
            rs = pd.Series(arr["S"][:, idx].mean(1), index=ns)
            bs.append(n_equivalent(rs, arr[m][ns.index(n0)][idx].mean(), ns)[0])
        lo, hi = np.percentile(bs, [2.5, 97.5])
        out.append(dict(method=m, n0=n0, rbar=piv.loc[n0][m].mean(), n_eq=ne, flag=flag, G=ne / n0, G_lo=lo / n0,
                        G_hi=hi / n0))
    return pd.DataFrame(out)


def paired_diff(draws, a, b, n0=15, metric="r", nboot=2000, seed=2, ratio=False):
    """Mean difference (or ratio of means) of metric between methods a and b at n0, bootstrap over draws."""
    piv = draws[draws.n == n0].pivot_table(index="draw", columns="method", values=metric)
    x, y = piv[a].values, piv[b].values
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(nboot, len(x)))
    if ratio:
        est = np.nanmean(x) / np.nanmean(y)
        bs = np.nanmean(x[idx], 1) / np.nanmean(y[idx], 1)
    else:
        est = np.nanmean(x - y)
        bs = np.nanmean((x - y)[idx], 1)
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    return est, lo, hi
