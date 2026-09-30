"""Shared definitions: published PP3/BP4 score intervals, interval assignment, LR targets, gene-cluster bootstrap and
Pejaver-style local posterior calibration (plan.md sec 4-5)."""
from __future__ import annotations

import numpy as np
import pandas as pd

PRIOR = 0.0441                      # Pejaver et al. 2022
C = 2.406                           # LR per evidence point (Supporting); Moderate c^2, (+3) c^3, Strong c^4


def lr_target(points: int) -> float:
    return C ** points


def posterior(lr, prior=PRIOR):
    lr = np.asarray(lr, float)
    return lr * prior / (lr * prior + 1 - prior)


# Published intervals (Bergquist et al. 2025 Table 1; CADD from Pejaver et al. 2022). Scores are rounded to the
# published precision first, so the closed intervals of the tables apply without gaps. For each tool:
# higher_is_pathogenic, decimals, pathogenic lower bounds {points: bound}, benign upper bounds {points: bound}
# (for ESM1b, where lower is pathogenic, the roles of the comparisons are mirrored).
TOOLS = {
    "revel":     dict(label="REVEL", hip=True, dec=3, path={4: 0.932, 3: 0.879, 2: 0.773, 1: 0.644},
                      ben={-4: 0.016, -3: 0.052, -2: 0.183, -1: 0.290}, primary=True),
    "am":        dict(label="AlphaMissense", hip=True, dec=3, path={4: 0.990, 3: 0.972, 2: 0.906, 1: 0.792},
                      ben={-3: 0.070, -2: 0.099, -1: 0.169}, primary=True),
    "bayesdel":  dict(label="BayesDel (noAF)", hip=True, dec=3, path={4: 0.500, 3: 0.410, 2: 0.270, 1: 0.130},
                      ben={-3: -0.520, -2: -0.360, -1: -0.180}, primary=False),
    "esm1b":     dict(label="ESM1b", hip=False, dec=1, path={4: -24.0, 3: -14.0, 2: -12.2, 1: -10.7},
                      ben={-3: 8.8, -2: -3.1, -1: -6.3}, primary=False),
    "varity_r":  dict(label="VARITY_R", hip=True, dec=3, path={4: 0.965, 3: 0.915, 2: 0.842, 1: 0.675},
                      ben={-4: 0.036, -3: 0.063, -2: 0.116, -1: 0.251}, primary=False),
    "cadd":      dict(label="CADD (phred)", hip=True, dec=2, path={2: 28.1, 1: 25.3},
                      ben={-4: 0.15, -2: 17.3, -1: 22.7}, primary=False),
}
# CADD's published benign intervals are half-open on the left: (0.15, 17.3] etc.; its pathogenic ones [25.3, 28.1).


def assign_points(tool: str, score: np.ndarray) -> np.ndarray:
    """Evidence points (-4..+4, 0 = indeterminate) for each score; NaN where the score is missing."""
    t = TOOLS[tool]
    s = np.round(np.asarray(score, float), t["dec"])
    pts = np.zeros(len(s))
    if t["hip"]:
        for k in sorted(t["ben"], reverse=True):          # -1, -2, ... : the most extreme bound wins last
            pts = np.where(s <= t["ben"][k], k, pts)
        for k in sorted(t["path"]):                        # +1, +2, ...
            pts = np.where(s >= t["path"][k], k, pts)
    else:                                                  # ESM1b: lower = more pathogenic
        for k in sorted(t["ben"], reverse=True):
            pts = np.where(s >= t["ben"][k], k, pts)
        for k in sorted(t["path"]):
            pts = np.where(s <= t["path"][k], k, pts)
    return np.where(np.isnan(s), np.nan, pts)


def intervals(tool: str) -> list[int]:
    t = TOOLS[tool]
    return sorted(t["ben"]) + sorted(t["path"])


def gene_counts(df: pd.DataFrame, pts_col: str, ivals: list[int]):
    """Per-gene counts: array (n_genes, n_intervals + 1 [all], 2 [P, B])."""
    d = df.dropna(subset=[pts_col])
    genes, gidx = np.unique(d.gene.astype(str).values, return_inverse=True)
    cols = {k: i for i, k in enumerate(ivals)}
    cnt = np.zeros((len(genes), len(ivals) + 1, 2))
    isb = (d.label.values == "B").astype(int)
    iv = np.array([cols.get(int(p), -1) for p in d[pts_col].values])
    np.add.at(cnt, (gidx, np.full(len(d), len(ivals)), isb), 1)          # totals
    m = iv >= 0
    np.add.at(cnt, (gidx[m], iv[m], isb[m]), 1)
    return genes, cnt


def interval_lr(cnt_sum: np.ndarray) -> np.ndarray:
    """cnt_sum (..., n_int + 1, 2) -> LR per interval (..., n_int)."""
    nP, nB = cnt_sum[..., -1, 0][..., None], cnt_sum[..., -1, 1][..., None]
    with np.errstate(divide="ignore", invalid="ignore"):
        return (cnt_sum[..., :-1, 0] / nP) / (cnt_sum[..., :-1, 1] / nB)


def bootstrap_lr(cnt: np.ndarray, n_boot=2000, seed=0) -> np.ndarray:
    """Gene-cluster bootstrap of interval LRs: (n_boot, n_int)."""
    rng = np.random.default_rng(seed)
    g = cnt.shape[0]
    out = np.empty((n_boot, cnt.shape[1] - 1))
    for b in range(n_boot):
        w = np.bincount(rng.integers(0, g, g), minlength=g).astype(float)
        out[b] = interval_lr(np.tensordot(w, cnt, axes=(0, 0)))
    # a resample with no benign (pathogenic) variants in an interval has LR = inf (0): keep it as a large finite
    # number so percentiles remain order statistics; 0/0 (interval empty on both sides) stays NaN
    return np.where(np.isposinf(out), 1e12, out)


def verdict(points: int, lr: float, lo: float, hi: float, n_min: int) -> str:
    """plan.md sec 5: one-sided 95% bounds (5th / 95th bootstrap percentiles) against the interval's target."""
    if n_min < 10:
        return "insufficient"
    tgt = lr_target(points)
    if points > 0:
        return "meets" if lo >= tgt else ("falls short" if hi < tgt else "inconclusive")
    return "meets" if hi <= tgt else ("falls short" if lo > tgt else "inconclusive")


def local_posterior_thresholds(score, label, tool, n_window=100, n_boot=1000, grid=None, seed=0):
    """Pejaver-style calibration (without their gnomAD window term or Delta stringency): for each grid score s the
    window is the n_window labelled variants nearest to s; LR(s) = (n_P/N_P)/(n_B/N_B); the one-sided 95% bound
    comes from a variant-level bootstrap. Returns {points: threshold} for the pathogenic and benign sides."""
    t = TOOLS[tool]
    s = np.asarray(score, float)
    y = (np.asarray(label) == "P").astype(int)
    ok = ~np.isnan(s)
    s, y = s[ok], y[ok]
    sign = 1.0 if t["hip"] else -1.0
    s = sign * s                                               # higher = more pathogenic
    grid = np.quantile(s, np.linspace(0.005, 0.995, 400)) if grid is None else sign * np.asarray(grid)
    rng = np.random.default_rng(seed)
    lr_b = np.empty((n_boot, len(grid)))
    for b in range(n_boot + 1):
        idx = np.arange(len(s)) if b == n_boot else rng.integers(0, len(s), len(s))
        sb, yb = s[idx], y[idx]
        o = np.argsort(sb)
        sb, yb = sb[o], yb[o]
        NP, NB = yb.sum(), len(yb) - yb.sum()
        cy = np.concatenate([[0], np.cumsum(yb)])
        c = np.searchsorted(sb, grid)                          # window: the n_window labelled variants around s
        lo = np.clip(c - n_window // 2, 0, len(sb) - n_window)
        hi = lo + n_window
        nP = cy[hi] - cy[lo]
        nB = n_window - nP
        with np.errstate(divide="ignore", invalid="ignore"):
            lrs = np.where(nB > 0, (nP / NP) / (nB / NB), np.inf)
        if b == n_boot:
            lr_hat = lrs
        else:
            lr_b[b] = lrs
    lr_b = np.where(np.isposinf(lr_b), 1e12, lr_b)                  # inf -> large finite (see bootstrap_lr)
    lo5, hi95 = np.nanpercentile(lr_b, 5, axis=0), np.nanpercentile(lr_b, 95, axis=0)
    out = {}
    for k in sorted(t["path"]):
        okk = lo5 >= lr_target(k)
        # smallest grid score from which the bound stays above target for all higher scores
        good = np.where(np.flip(np.cumprod(np.flip(okk))))[0]
        out[k] = float(sign * grid[good[0]]) if len(good) else np.nan
    for k in sorted(t["ben"], reverse=True):
        okk = hi95 <= lr_target(k)
        good = np.where(np.cumprod(okk))[0]
        out[k] = float(sign * grid[good[-1]]) if len(good) else np.nan
    return out, dict(grid=sign * grid, lr=lr_hat, lo5=lo5, hi95=hi95)
