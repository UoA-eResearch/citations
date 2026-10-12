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
    """Spearman with ties; nan when either side has no variation or fewer than 3 points."""
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3 or np.unique(x[m]).size < 2 or np.unique(y[m]).size < 2:
        return np.nan
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
             for c in (rng.integers(0, k, k) for _ in range(nboot // 4))]
    lo, hi = ci(draws)
    return dict(lo=lo, hi=hi, nboot=nboot // 4)


def boot_dyadic(pred, meas, uncensored_only=False, nboot=NBOOT):
    """Sensitivity: resample ligands and kinases independently in the same draw."""
    rng = np.random.default_rng(SEED + 2)
    n, k = pred.shape
    draws = []
    for _ in range(nboot // 4):
        ri, cj = rng.integers(0, n, n), rng.integers(0, k, k)
        draws.append(med(within_ligand(pred[np.ix_(ri, cj)], meas[np.ix_(ri, cj)], uncensored_only)))
    lo, hi = ci(draws)
    return dict(lo=lo, hi=hi, nboot=nboot // 4)


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


def hit_rates(pred, meas, top=3):
    """Per ligand: is the model's top-ranked kinase among the ligand's true top-3 measured kinases, and
    what share of the model's top-3 is in the true top-3? Ties in the measured values are broken by
    counting any kinase whose pKd ties the 3rd-best value as part of the true top set."""
    t1, p3 = [], []
    for i in range(pred.shape[0]):
        y, p = meas[i], pred[i]
        if np.unique(y).size < 2:
            continue
        cut = np.sort(y)[-top]
        true = set(np.where(y >= cut)[0])
        order = np.argsort(-p)
        t1.append(int(order[0] in true))
        p3.append(len(set(order[:top]) & true) / top)
    return dict(top1=float(np.mean(t1)), precision_at_3=float(np.mean(p3)), n=len(t1))


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
