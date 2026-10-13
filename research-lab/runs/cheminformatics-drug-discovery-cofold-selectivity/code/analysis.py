"""Estimands, baselines and bootstrap intervals exactly as preregistered in plan.md §6-§8.

Everything is computed from two aligned matrices over the rectangle: `meas` (measured pKd, with censored
cells at 5.0) and `pred` (Boltz-2 on a pIC50-like scale, 6 - affinity_pred_value, so higher = stronger),
both indexed [ligand, kinase]. Censored cells stay in the primary statistic as ties at pKd 5 (P1) and are
dropped in P2.

The primary interval is a cluster bootstrap over ligands (2000 draws, seed 20261013); kinase resampling and
a two-way dyadic bootstrap are the sensitivity checks.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
SEED = 20261013
NBOOT = 2000
CENSOR_PKD = 5.0
MIN_UNC_P2 = 5


def rho(x, y):
    """Spearman with ties.

    nan when there is nothing to rank: fewer than 3 usable points, or no variation in the *measured*
    side. A predictor with no variation (every target scored the same) carries no rank information about
    a varying measurement, so it scores exactly 0 rather than nan — that is what makes the ligand-only
    baseline B0 equal to zero by construction, as plan.md §7 asserts.
    """
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3 or np.unique(y[m]).size < 2:
        return np.nan
    if np.unique(x[m]).size < 2:
        return 0.0
    return stats.spearmanr(x[m], y[m]).statistic


def within_ligand(pred, meas, uncensored_only=False):
    """One Spearman per ligand across kinases. Returns an array of length n_ligands (nan where undefined)."""
    out = np.full(pred.shape[0], np.nan)
    for i in range(pred.shape[0]):
        p, y = pred[i].copy(), meas[i].copy()
        if uncensored_only:
            keep = y > CENSOR_PKD
            if keep.sum() < MIN_UNC_P2:
                continue
            p, y = p[keep], y[keep]
        out[i] = rho(p, y)
    return out


def within_kinase(pred, meas):
    return np.array([rho(pred[:, j], meas[:, j]) for j in range(pred.shape[1])])


def med(v):
    v = np.asarray(v, float)
    return float(np.nanmedian(v)) if np.isfinite(v).any() else np.nan


def boot_ligand(fn, n_lig, rng, nboot=NBOOT):
    """Cluster bootstrap over ligands: fn(idx) -> statistic."""
    return np.array([fn(rng.integers(0, n_lig, n_lig)) for _ in range(nboot)])


def ci(draws, level=95):
    d = np.asarray(draws, float)
    d = d[np.isfinite(d)]
    if d.size == 0:          # nothing was estimable in any draw: say so rather than raise
        return float("nan"), float("nan")
    lo, hi = np.percentile(d, [(100 - level) / 2, 100 - (100 - level) / 2])
    return float(lo), float(hi)


def primary(pred, meas, uncensored_only=False, nboot=NBOOT):
    """P1 (or P2): median over ligands of the within-ligand Spearman, with a ligand cluster bootstrap."""
    r = within_ligand(pred, meas, uncensored_only)
    rng = np.random.default_rng(SEED)
    draws = boot_ligand(lambda idx: med(r[idx]), len(r), rng, nboot)
    lo, hi = ci(draws)
    return dict(point=med(r), lo=lo, hi=hi, n_ligands=int(np.isfinite(r).sum()),
                mean=float(np.nanmean(r)), per_ligand=r.tolist())


def paired_difference(pred, meas, base, uncensored_only=False, nboot=NBOOT):
    """Paired ligand bootstrap of median(rho_model) - median(rho_baseline)."""
    a = within_ligand(pred, meas, uncensored_only)
    b = within_ligand(base, meas, uncensored_only)
    rng = np.random.default_rng(SEED)
    draws = boot_ligand(lambda idx: med(a[idx]) - med(b[idx]), len(a), rng, nboot)
    lo, hi = ci(draws)
    return dict(point=med(a) - med(b), lo=lo, hi=hi, base_point=med(b))


def boot_kinase(pred, meas, uncensored_only=False, nboot=NBOOT):
    """Sensitivity: resample kinase columns instead of ligands."""
    rng = np.random.default_rng(SEED + 1)
    k = pred.shape[1]
    draws = [med(within_ligand(pred[:, c], meas[:, c], uncensored_only))
             for c in (rng.integers(0, k, k) for _ in range(nboot))]
    lo, hi = ci(draws)
    return dict(lo=lo, hi=hi, nboot=nboot)


def boot_dyadic(pred, meas, uncensored_only=False, nboot=NBOOT):
    """Sensitivity: resample ligands and kinases independently in the same draw."""
    rng = np.random.default_rng(SEED + 2)
    n, k = pred.shape
    draws = []
    for _ in range(nboot):
        ri, cj = rng.integers(0, n, n), rng.integers(0, k, k)
        draws.append(med(within_ligand(pred[np.ix_(ri, cj)], meas[np.ix_(ri, cj)], uncensored_only)))
    lo, hi = ci(draws)
    return dict(lo=lo, hi=hi, nboot=nboot)


# ---------------------------------------------------------------- baselines (plan.md §7)
def base_ligand_only(meas_full, rows, cols):
    """B0: one value per ligand - the ligand's mean measured pKd over all 442 panel assays."""
    v = np.nanmean(meas_full[rows], axis=1)
    return np.repeat(v[:, None], len(cols), axis=1)


def base_promiscuity(meas_full, rows, cols):
    """B1: each kinase's mean measured pKd over the other 67 Davis ligands (leave the ranked ligand out).
    Uses no chemistry: the same column vector for every ligand, bar the leave-one-out adjustment."""
    sub = meas_full[:, cols]
    out = np.empty((len(rows), len(cols)))
    for a, i in enumerate(rows):
        keep = np.ones(sub.shape[0], bool)
        keep[i] = False
        out[a] = sub[keep].mean(axis=0)
    return out


def base_promiscuity_full(meas_full, rows, cols):
    """B1 without the leave-one-out adjustment, so it is identical for every ligand. Used for the
    within-kinase axis P3: the leave-one-out version of B1 correlates exactly -1 with the measurement
    there, because leaving a strong binder out lowers that kinase's mean — an artefact of the
    adjustment, not a property of the baseline."""
    sub = meas_full[:, cols]
    return np.repeat(sub.mean(0)[None, :], len(rows), axis=0)


def base_neighbour(meas_full, rows, cols, smiles, nn=1):
    """B2: the measured pKd of the most ECFP4-similar other Davis ligand on the same kinase."""
    from rdkit import Chem, DataStructs
    from rdkit.Chem import rdFingerprintGenerator
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = [gen.GetFingerprint(Chem.MolFromSmiles(s)) for s in smiles]
    sub = meas_full[:, cols]
    out = np.empty((len(rows), len(cols)))
    for a, i in enumerate(rows):
        sims = np.array(DataStructs.BulkTanimotoSimilarity(fps[i], fps))
        sims[i] = -1
        j = int(np.argsort(-sims)[:nn][0])
        out[a] = sub[j]
    return out


def base_mw(mw, n_cols):
    return np.repeat(np.asarray(mw, float)[:, None], n_cols, axis=1)


# ---------------------------------------------------------------- decomposition and hit rates
def two_way(mat):
    """Least-squares mu + a_i + b_j + e_ij; returns the variance share of each term."""
    m = np.asarray(mat, float)
    mu = np.nanmean(m)
    a = np.nanmean(m, axis=1) - mu
    b = np.nanmean(m, axis=0) - mu
    fit_a = np.repeat(a[:, None], m.shape[1], axis=1)
    fit_b = np.repeat(b[None, :], m.shape[0], axis=0)
    e = m - mu - fit_a - fit_b
    tot = np.nansum((m - mu) ** 2)
    return dict(ligand=float(np.nansum(fit_a ** 2) / tot), kinase=float(np.nansum(fit_b ** 2) / tot),
                residual=float(np.nansum(e ** 2) / tot), sd_total=float(np.nanstd(m)),
                sd_ligand=float(np.nanstd(a)), sd_kinase=float(np.nanstd(b)))


def hit_vectors(pred, meas, top=3):
    """The per-ligand indicators behind hit_rates: (top-1 hit, precision@3), nan where undefined.

    Per ligand: is the model's top-ranked kinase among the ligand's true top-3 measured kinases, and what
    share of the model's top-3 is in the true top-3? Ties in the measured values are broken by counting
    any kinase whose pKd ties the 3rd-best value as part of the true top set.
    """
    n = pred.shape[0]
    t1, p3 = np.full(n, np.nan), np.full(n, np.nan)
    for i in range(n):
        y, p = meas[i], pred[i]
        if np.unique(y).size < 2:
            continue
        # A predictor with no variation has no ranking at all, and argsort would silently return the
        # first columns in panel order — which made the ligand-only and molecular-weight baselines look
        # like estimates (0.062) when they were really an artefact of the kinase column order. Under
        # random column orders the same statistic averages 0.104. Undefined is the honest value.
        if np.unique(p).size < 2:
            continue
        cut = np.sort(y)[-top]
        true = set(np.where(y >= cut)[0])
        order = np.argsort(-p)
        t1[i] = float(order[0] in true)
        p3[i] = len(set(order[:top]) & true) / top
    return t1, p3


def hit_rates(pred, meas, top=3):
    t1, p3 = hit_vectors(pred, meas, top)
    return dict(top1=float(np.nanmean(t1)), precision_at_3=float(np.nanmean(p3)),
                n=int(np.isfinite(t1).sum()))


def paired_hit_difference(pred, meas, base, top=3, nboot=NBOOT):
    """Paired ligand bootstrap of the top-1 and precision@3 differences, model minus baseline.

    Added after the plan (D8). The preregistered comparison against the baselines is on P1 alone, and P1
    and the hit rates disagree about how much the model adds: P1 puts it within noise of a baseline with
    no chemistry in it, while the top-1 rate is three times the baseline's. A difference that carries
    that much of the conclusion needs an interval, not a pair of point estimates.
    """
    a1, a3 = hit_vectors(pred, meas, top)
    b1, b3 = hit_vectors(base, meas, top)
    if not np.isfinite(b1).any():   # a constant baseline has no ranking, so there is no difference to take
        return dict(undefined=True, reason="baseline has no ranking (constant within each ligand)")
    out = {}
    for name, a, b in (("top1", a1, b1), ("precision_at_3", a3, b3)):
        rng = np.random.default_rng(SEED)
        draws = boot_ligand(lambda idx: float(np.nanmean(a[idx]) - np.nanmean(b[idx])), len(a), rng, nboot)
        lo, hi = ci(draws)
        out[name] = dict(point=float(np.nanmean(a) - np.nanmean(b)), lo=lo, hi=hi,
                         base_point=float(np.nanmean(b)))
    return out


# ---------------------------------------------------------------- rank statistics beyond P1 (D11)
# Added after the adversarial review, which showed that P1 is the single statistic on which the model does
# not separate from the chemistry-free baseline. These say what the profile looks like at the top, among
# real affinities, and on the binder/non-binder split that P1 mixes in with everything else.
def _dcg(gain, k=None):
    g = np.asarray(gain, float)
    if k:
        g = g[:k]
    return float(np.sum(g / np.log2(np.arange(2, len(g) + 2))))


def ndcg(pred, meas, k=None):
    """Per-ligand NDCG with gain = pKd - 5, so the censored block contributes exactly nothing and the
    statistic is dominated by how well the strong binders are placed near the top."""
    out = np.full(pred.shape[0], np.nan)
    for i in range(pred.shape[0]):
        g = np.maximum(meas[i] - CENSOR_PKD, 0.0)
        ideal = _dcg(np.sort(g)[::-1], k)
        if ideal <= 0 or np.unique(pred[i]).size < 2:
            continue
        out[i] = _dcg(g[np.argsort(-pred[i])], k) / ideal
    return out


def concordance_uncensored(pred, meas):
    """Per-ligand share of uncensored kinase pairs the prediction orders the way the measurement does."""
    out = np.full(pred.shape[0], np.nan)
    for i in range(pred.shape[0]):
        keep = meas[i] > CENSOR_PKD
        p, y = pred[i][keep], meas[i][keep]
        if p.size < 3:
            continue
        dp, dy = np.sign(p[:, None] - p[None, :]), np.sign(y[:, None] - y[None, :])
        ok = (dp != 0) & (dy != 0) & np.triu(np.ones((p.size, p.size), bool), 1)
        if ok.sum():
            out[i] = float(((dp == dy) & ok).sum() / ok.sum())
    return out


def auc_ceiling(pred, meas):
    """Per-ligand AUC for the one thing P1 spends 27 % of its weight on: telling the cells at the assay
    ceiling from the cells with a real measured affinity."""
    out = np.full(pred.shape[0], np.nan)
    for i in range(pred.shape[0]):
        pos = meas[i] > CENSOR_PKD
        n1, n0 = int(pos.sum()), int((~pos).sum())
        if n1 == 0 or n0 == 0 or np.unique(pred[i]).size < 2:
            continue
        r = stats.rankdata(pred[i])
        out[i] = float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    return out


def paired_vector_difference(a, b, nboot=NBOOT):
    """Paired ligand bootstrap of mean(a) - mean(b) for two per-ligand statistic vectors."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    rng = np.random.default_rng(SEED)
    draws = boot_ligand(lambda idx: float(np.nanmean(a[idx]) - np.nanmean(b[idx])), len(a), rng, nboot)
    lo, hi = ci(draws)
    return dict(point=float(np.nanmean(a) - np.nanmean(b)), lo=lo, hi=hi,
                model=float(np.nanmean(a)), base=float(np.nanmean(b)))


def rank_statistics(pred, meas, bases, nboot=NBOOT):
    """Every statistic in one table, each with a paired ligand bootstrap against each baseline."""
    stats_ = {"P2_uncensored": lambda p: within_ligand(p, meas, True),
              "concordance_uncensored": lambda p: concordance_uncensored(p, meas),
              "ndcg": lambda p: ndcg(p, meas), "ndcg_at_3": lambda p: ndcg(p, meas, 3),
              "ndcg_at_5": lambda p: ndcg(p, meas, 5),
              "auc_ceiling_vs_binders": lambda p: auc_ceiling(p, meas),
              "top1": lambda p: hit_vectors(p, meas)[0]}
    out = {}
    for name, fn in stats_.items():
        a = fn(pred)
        row = dict(model=float(np.nanmean(a)) if name != "P2_uncensored" else med(a), vs={})
        for bn, b in bases.items():
            v = fn(b)
            if not np.isfinite(v).any():
                row["vs"][bn] = dict(undefined=True)
                continue
            row["vs"][bn] = (paired_difference(pred, meas, b, True, nboot) if name == "P2_uncensored"
                             else paired_vector_difference(a, v, nboot))
        out[name] = row
    return out


def summarise(pred, meas, label, nboot=NBOOT):
    out = dict(label=label, P1=primary(pred, meas, False, nboot), P2=primary(pred, meas, True, nboot),
               P3=dict(point=med(within_kinase(pred, meas)),
                       per_kinase=within_kinase(pred, meas).tolist()),
               P4=hit_rates(pred, meas), P5_pred=two_way(pred), P5_meas=two_way(meas),
               kinase_boot=boot_kinase(pred, meas, False, nboot),
               dyadic_boot=boot_dyadic(pred, meas, False, nboot))
    return out


def verdict(p1, p3):
    """plan.md §6 decision rule."""
    if p1["lo"] >= 0.25:
        return "Refuted"
    if p1["hi"] < 0.25:
        return "Supported" if p3["point"] >= 0.4 else "Inconclusive (target-blind and ligand-blind)"
    return "Inconclusive"


def save(obj, name):
    TAB.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(TAB / name, "w"), indent=1, default=float)
    print("wrote", TAB / name)
