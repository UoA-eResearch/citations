#!/usr/bin/env python
"""Record margins, null models and H1-H4 (plan.md sec 4-5).

Stage 1 (per station, cached): for variable v in {txx, tx7x} and block length L in {3 (primary), 1, 5}:
  qualification; LOESS trend (statsmodels lowess, frac = 30 years / valid years, no robustness iterations);
  sigma_s = sd of residuals; 30-year record margins m_t (sigma units) for 1981-2025 where >= 25 of the 30 look-back
  years are valid; observed counts per era of m > 0, > 1, > 2; expected counts under the stationary null (residuals
  block-resampled) and the trend-preserving null (LOESS trend + resampled residuals), 500 surrogates each.
Stage 2 (pooled): ratios R1 (obs / stationary null, E2), R2 (obs / trend null, E2), R4 (E2 / E1 observed frequency),
  and the H3 slope, with a spatial block bootstrap over 5x5-degree cells (1,000 resamples).

Outputs: data/processed/station_results_<v>_L<L>.parquet, results/tables/pooled.csv, results/tables/h3.csv
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
YEARS = np.arange(1951, 2026)
E1, E2 = (1981, 2002), (2003, 2025)
LOOK, MIN_LOOK, NSUR = 30, 25, 500
THR = (0.0, 1.0, 2.0)


def loess(years, x, frac):
    from statsmodels.nonparametric.smoothers_lowess import lowess
    fit = lowess(x, years, frac=frac, it=0, return_sorted=True)
    return np.interp(YEARS, fit[:, 0], fit[:, 1])


HINGE = 1980


def detrend(years, x, method):
    """Trend for all YEARS and its number of fitted parameters. 'loess' (preregistered): 30-year LOESS.
    'hinge' (exploratory, deviations.md D4): flat until 1980, linear after (2 parameters, OLS).
    'pw' (sensitivity, deviations.md D6): continuous piecewise-linear with its own 1951-1980 slope (3 parameters, OLS),
    for stations whose early decades were not flat (e.g. the warm US 1950s)."""
    if method == "loess":
        return loess(years, x, min(1.0, 30 / len(years))), None
    cols = [np.ones(len(years)), np.maximum(0, years - HINGE)] + ([np.minimum(0, years - HINGE)] if method == "pw" else [])
    beta = np.linalg.lstsq(np.column_stack(cols), x, rcond=None)[0]
    trend = beta[0] + beta[1] * np.maximum(0, YEARS - HINGE)
    if method == "pw":
        trend = trend + beta[2] * np.minimum(0, YEARS - HINGE)
    return trend, len(cols)


def margins(X, valid):
    """X: (..., 75) values; valid: (75,) bool. Returns m: (..., 75) raw margins (NaN where undefined)."""
    m = np.full(X.shape, np.nan)
    for i, y in enumerate(YEARS):
        if y < E1[0] or not valid[i]:
            continue
        lo = i - LOOK
        w = valid[lo:i]
        if w.sum() < MIN_LOOK:
            continue
        prior = np.where(w, X[..., lo:i], -np.inf).max(axis=-1)
        m[..., i] = X[..., i] - prior
    return m


def block_resample(r, L, n_sur, rng):
    """Circular block bootstrap WITH replacement (the preregistered scheme). Flawed for record statistics: duplicated
    extreme values cannot be strictly exceeded, so surrogates under-produce records (deviations.md D4). Kept for the
    record; the analysis uses block_permute."""
    n = len(r)
    nb = int(np.ceil(n / L))
    starts = rng.integers(0, n, size=(n_sur, nb))
    idx = (starts[..., None] + np.arange(L)).reshape(n_sur, -1)[:, :n] % n
    return r[idx]


def block_permute(r, L, n_sur, rng):
    """Block permutation WITHOUT replacement: cut the residual sequence into consecutive blocks of length L (random
    phase) and shuffle the block order. Every residual appears exactly once, so the surrogate is exchangeable with the
    data under the null and record counts are unbiased (deviations.md D4)."""
    n = len(r)
    out = np.empty((n_sur, n))
    for k in range(n_sur):
        off = rng.integers(0, L)
        cuts = list(range(off, n, L)) if off else list(range(L, n, L))
        blocks = np.split(r, cuts)
        order = rng.permutation(len(blocks))
        out[k] = np.concatenate([blocks[i] for i in order])
    return out


RESAMPLE = {"bootstrap": block_resample, "permute": block_permute}


def station(args):
    sid, x, valid, L, seed = args[:5]
    method = args[5] if len(args) > 5 else "loess"
    resample = args[6] if len(args) > 6 else "bootstrap"
    nv = int(valid.sum())
    era = lambda a, b: (YEARS >= a) & (YEARS <= b)
    if nv < 60 or valid[era(*E1)].sum() < 18 or valid[era(*E2)].sum() < 19:
        return None
    trend, npar = detrend(YEARS[valid], x[valid], method)
    res = x[valid] - trend[valid]
    sig = float(np.std(res, ddof=npar or 1))
    if not np.isfinite(sig) or sig <= 0:
        return None
    m_obs = margins(x, valid) / sig
    rng = np.random.default_rng(seed)
    rs = RESAMPLE[resample](res, L, NSUR, rng)
    Xs = np.full((NSUR, len(YEARS)), np.nan)
    Xs[:, valid] = rs                                          # stationary null (constant base cancels in margins)
    m_stat = margins(Xs, valid) / sig
    Xt = Xs + trend[None, :]                                  # trend-preserving null
    m_tr = margins(Xt, valid) / sig
    out = dict(station=sid, n_valid=nv, sigma=sig, rate_c_per_decade=float((trend[-1] - trend[YEARS == 1981][0]) / 4.4))
    for name, (a, b) in (("E1", E1), ("E2", E2)):
        sel = era(a, b)
        elig = np.isfinite(m_obs[sel])
        out[f"elig_{name}"] = int(elig.sum())
        for k in THR:
            tag = f"{name}_gt{int(k)}"
            out[f"obs_{tag}"] = int((m_obs[sel][elig] > k).sum())
            out[f"stat_{tag}"] = float((m_stat[:, sel][:, elig] > k).sum(axis=1).mean())
            out[f"trend_{tag}"] = float((m_tr[:, sel][:, elig] > k).sum(axis=1).mean())
    out["m_obs"] = m_obs.tolist()
    for k in THR:                                            # per-year null expectations (for the two-way bootstrap)
        out[f"stat_py_gt{int(k)}"] = np.where(np.isfinite(m_obs), (m_stat > k).mean(axis=0), np.nan).tolist()
        out[f"trend_py_gt{int(k)}"] = np.where(np.isfinite(m_obs), (m_tr > k).mean(axis=0), np.nan).tolist()
    return out


def screen(ex, var, lat):
    """Plausibility screen (deviations.md D6; independent review): drop a station if any valid-season value is more than
    8 robust SDs (1.4826 * MAD) from its median, or if its TXx falls below 10 degC anywhere equatorward of 60 degrees."""
    bad = set()
    for sid, g in ex[ex.valid].groupby("station"):
        x = g[var].dropna().values
        if len(x) < 10:
            continue
        med = np.median(x)
        mad = 1.4826 * np.median(np.abs(x - med))
        if (mad > 0 and np.any(np.abs(x - med) / mad > 8)) or (abs(lat.get(sid, 0)) < 60 and np.any(x < 10)):
            bad.add(sid)
    return bad


def stage1(var, L, method="loess", resample="bootstrap"):
    tag = "" if (method, resample) == ("loess", "bootstrap") else f"_{method}_{resample}_screened"
    path = PROC / f"station_results_{var}_L{L}{tag}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    ex = pd.read_parquet(PROC / "extremes.parquet")
    lat = pd.read_parquet(PROC / "stations_meta.parquet").set_index("station").lat
    flagged = screen(ex, var, lat)
    jobs = []
    for k, (sid, g) in enumerate(ex.groupby("station")):
        if sid in flagged:
            continue
        g = g.set_index("year").reindex(YEARS)
        valid = g.valid.fillna(False).values.astype(bool) & np.isfinite(g[var].values)
        jobs.append((sid, g[var].values.astype(float), valid, L, 1000 + k, method, resample))
    with Pool(28) as pool:
        res = [r for r in pool.imap_unordered(station, jobs, chunksize=16) if r is not None]
    df = pd.DataFrame(res)
    meta = pd.read_parquet(PROC / "stations_meta.parquet")
    df = df.merge(meta, on="station", how="left")
    df["cell"] = (np.floor(df.lat / 5)).astype(int).astype(str) + "_" + (np.floor(df.lon / 5)).astype(int).astype(str)
    df.to_parquet(path, index=False)
    print(f"{var} L={L} {method}/{resample}: {len(df)} qualifying stations", flush=True)
    return df


def pooled(df, thr=1, nboot=1000, seed=0):
    k = f"gt{int(thr)}"
    cells = df.cell.values
    uc, ci = np.unique(cells, return_inverse=True)
    cols = [f"obs_E2_{k}", f"stat_E2_{k}", f"trend_E2_{k}", f"obs_E1_{k}", "elig_E2", "elig_E1"]
    A = np.zeros((len(uc), len(cols)))
    np.add.at(A, ci, df[cols].values.astype(float))

    def ratios(s):
        o2, st2, tr2, o1, e2, e1 = s
        return np.array([o2 / st2, o2 / tr2, (o2 / e2) / (o1 / e1), o2 / e2, st2 / e2, tr2 / e2, o1 / e1])
    est = ratios(A.sum(0))
    rng = np.random.default_rng(seed)
    bs = np.array([ratios(A[rng.integers(0, len(uc), len(uc))].sum(0)) for _ in range(nboot)])
    names = ["R1_obs_over_stationary", "R2_obs_over_trend", "R4_E2_over_E1", "freq_obs_E2", "freq_stat_E2",
             "freq_trend_E2", "freq_obs_E1"]
    return {n: dict(est=float(e), lo=float(np.percentile(bs[:, i], 2.5)), hi=float(np.percentile(bs[:, i], 97.5)))
            for i, (n, e) in enumerate(zip(names, est))}, len(uc)


def pooled_twoway(df, thr=1, nboot=5000, seed=0, block=3):
    """Two-way bootstrap (deviations.md D6): resample 5x5-degree cells AND, independently, blocks of `block` consecutive
    years within each era, so that heatwave years shared across many stations are treated as the correlated events
    they are. Needs the per-year null expectations stored by station()."""
    k = int(thr)
    O = np.array(df.m_obs.tolist())
    elig = np.isfinite(O)
    obs = np.where(elig, O > thr, 0.0)
    st = np.where(elig, np.nan_to_num(np.array(df[f"stat_py_gt{k}"].tolist())), 0.0)
    tr = np.where(elig, np.nan_to_num(np.array(df[f"trend_py_gt{k}"].tolist())), 0.0)
    uc, ci = np.unique(df.cell.values, return_inverse=True)
    C = np.zeros((4, len(uc), len(YEARS)))
    for i, M in enumerate((obs, st, tr, elig.astype(float))):
        np.add.at(C[i], ci, M)
    e1 = (YEARS >= E1[0]) & (YEARS <= E1[1])
    e2 = (YEARS >= E2[0]) & (YEARS <= E2[1])
    blocks = {name: [np.where(m)[0][j:j + block] for j in range(0, int(m.sum()), block)] for name, m in (("E1", e1), ("E2", e2))}

    def ratios(w, v):
        T = np.einsum("c,kcy,y->ky", w, C, v)
        o2, s2, t2, n2 = T[0][e2].sum(), T[1][e2].sum(), T[2][e2].sum(), T[3][e2].sum()
        o1, n1 = T[0][e1].sum(), T[3][e1].sum()
        return np.array([o2 / s2, o2 / t2, (o2 / n2) / (o1 / n1)])
    est = ratios(np.ones(len(uc)), np.ones(len(YEARS)))
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        w = np.bincount(rng.integers(0, len(uc), len(uc)), minlength=len(uc)).astype(float)
        v = np.zeros(len(YEARS))
        for name in ("E1", "E2"):
            bl = blocks[name]
            for j in rng.integers(0, len(bl), len(bl)):
                v[bl[j]] += 1
        bs.append(ratios(w, v))
    bs = np.array(bs)
    names = ["R1_obs_over_stationary", "R2_obs_over_trend", "R4_E2_over_E1"]
    return {n: dict(est=float(e), lo=float(np.nanpercentile(bs[:, i], 2.5)), hi=float(np.nanpercentile(bs[:, i], 97.5)))
            for i, (n, e) in enumerate(zip(names, est))}


def h3(df, nboot=1000, seed=1):
    e = (df.obs_E2_gt1 - df.stat_E2_gt1) / df.elig_E2
    x = df.rate_c_per_decade.values
    ok = np.isfinite(e) & np.isfinite(x)
    e, x, cells = e.values[ok], x[ok], df.cell.values[ok]
    slope = float(np.polyfit(x, e, 1)[0])
    uc, ci = np.unique(cells, return_inverse=True)
    groups = [np.where(ci == j)[0] for j in range(len(uc))]
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        idx = np.concatenate([groups[j] for j in rng.integers(0, len(uc), len(uc))])
        bs.append(np.polyfit(x[idx], e[idx], 1)[0])
    return dict(slope_per_c_per_decade=slope, lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)),
                n_stations=int(ok.sum()), mean_rate=float(x.mean()))


def verdict(r):
    return "supported" if r["lo"] > 1 else ("contradicted" if r["hi"] < 1 else "inconclusive")


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    method = sys.argv[1] if len(sys.argv) > 1 else "loess"
    resample = sys.argv[2] if len(sys.argv) > 2 else "bootstrap"
    suffix = "" if (method, resample) == ("loess", "bootstrap") else f"_{method}_{resample}"
    rows = []
    variants = [("txx", 3, "all", 1.0, "primary")]
    variants += [("txx", 3, "all", 0.0, "threshold 0"), ("txx", 3, "all", 2.0, "threshold 2"),
                 ("tx7x", 3, "all", 1.0, "TX7x"), ("txx", 3, "hq", 1.0, "HCN/CRN/GSN subset"),
                 ("txx", 3, "nonUS", 1.0, "excluding US"), ("txx", 3, "nonUS", 0.0, "excluding US, threshold 0"),
                 ("txx", 3, "US", 1.0, "US only"), ("txx", 3, "US", 0.0, "US only, threshold 0"), ("txx", 1, "all", 1.0, "block 1"),
                 ("txx", 5, "all", 1.0, "block 5")]
    for var, L, subset, thr, label in variants:
        df = stage1(var, L, method, resample)
        if subset == "hq":
            df = df[df.hcn_crn.isin(["HCN", "CRN"]) | df.gsn]
        elif subset == "nonUS":
            df = df[~df.station.str.startswith("US")]
        elif subset == "US":
            df = df[df.station.str.startswith("US")]
        res, ncell = pooled(df, thr)
        row = dict(analysis=label, variable=var, block=L, subset=subset, threshold=thr, n_stations=len(df), n_cells=ncell)
        for n, r in res.items():
            row[n] = r["est"]
            row[n + "_lo"] = r["lo"]
            row[n + "_hi"] = r["hi"]
        if f"stat_py_gt{int(thr)}" in df.columns:
            # D6: the two-way (cell x 3-year block) interval is the primary one; the cell-only interval is kept as *_cell
            for n, r in pooled_twoway(df, thr).items():
                row[n + "_lo_cell"], row[n + "_hi_cell"] = row[n + "_lo"], row[n + "_hi"]
                res[n] = dict(res[n], lo=r["lo"], hi=r["hi"])
                row[n + "_lo"], row[n + "_hi"] = r["lo"], r["hi"]
        for h, n in (("H1", "R1_obs_over_stationary"), ("H2", "R2_obs_over_trend"), ("H4", "R4_E2_over_E1")):
            row[f"{h}_verdict"] = verdict(res[n])
        rows.append(row)
        print(f"{label:22s} n={len(df):5d} cells={ncell:4d} | R1 {res['R1_obs_over_stationary']['est']:.2f} "
              f"[{res['R1_obs_over_stationary']['lo']:.2f}, {res['R1_obs_over_stationary']['hi']:.2f}] | R2 "
              f"{res['R2_obs_over_trend']['est']:.2f} [{res['R2_obs_over_trend']['lo']:.2f}, {res['R2_obs_over_trend']['hi']:.2f}] | R4 "
              f"{res['R4_E2_over_E1']['est']:.2f} [{res['R4_E2_over_E1']['lo']:.2f}, {res['R4_E2_over_E1']['hi']:.2f}] | freq obs E2 "
              f"{res['freq_obs_E2']['est']:.4f} stat {res['freq_stat_E2']['est']:.4f} trend {res['freq_trend_E2']['est']:.4f}", flush=True)
    pd.DataFrame(rows).to_csv(TAB / f"pooled{suffix}.csv", index=False)
    h = h3(stage1("txx", 3, method, resample))
    pd.DataFrame([h]).to_csv(TAB / f"h3{suffix}.csv", index=False)
    print("H3:", h)


if __name__ == "__main__":
    sys.exit(main())
