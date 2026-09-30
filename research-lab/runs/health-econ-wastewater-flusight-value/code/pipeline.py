#!/usr/bin/env python
"""Paired real-time forecasts of weekly confirmed influenza admissions, with and without state wastewater features
(plan.md sec 3-4; deviations.md D2 for the real-time vintage rule).

Usage: pipeline.py VARIANT [LAG_DAYS]
  VARIANT: main      base and with-wastewater models (primary)
           oracle    V1 positive control: features from next week's final admissions + N(0, 0.3^2)
           derange   V2 negative control: each state gets another state's wastewater features
           flowpop   S2: flow- and population-normalised concentration where a series reports it
           level     S3: level feature W0 only
           basefull  S4: base model trained on all state-weeks (not only those with wastewater features)
           wval      S6: state signal from CDC site-level wastewater viral activity levels
  LAG_DAYS: wastewater availability lag (default 10; S1 uses 5 and 17)
Output: results/forecasts/{variant}_lag{L}.parquet (one row per round x location x horizon x model, 23 quantiles)
"""
from __future__ import annotations

import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.regression.quantile_regression import QuantReg

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
RAW, PROC, OUT = RUN / "data" / "raw", RUN / "data" / "processed", RUN / "results" / "forecasts"
QLEVELS = np.array([0.01, 0.025] + [round(0.05 * i, 2) for i in range(1, 20)] + [0.975, 0.99])
TRAIN_START = pd.Timestamp("2022-09-03")
MIN_WINDOWS = 10
HORIZONS = (0, 1, 2, 3)


# ----------------------------------------------------------------------------------------------- hospital data
def load_hosp():
    ts = pd.read_csv(RAW / "hub" / "time-series.csv", dtype={"location": str}, parse_dates=["as_of", "target_end_date"])
    h = ts[(ts.target == "wk inc flu hosp") & (ts.location != "US")][["as_of", "target_end_date", "location", "observation"]]
    return h


def vintage_for(h_asof: pd.DatetimeIndex, R: pd.Timestamp) -> pd.Timestamp:
    """Latest vintage released on or before the due date R - 3 (deviations.md D2)."""
    rel = pd.Series([a + pd.Timedelta(days=4) if a.dayofweek == 5 else a for a in h_asof], index=h_asof)
    return rel[rel <= R - pd.Timedelta(days=3)].index.max()


def locations():
    loc = pd.read_csv(RAW / "locations.csv", dtype={"location": str})
    return loc[loc.location != "US"].set_index("location")


# ----------------------------------------------------------------------------------------------- wastewater
def ww_series(value_col="pcr_target_avg_conc_lin"):
    """Samples with a series id (site x source), log10 value and a weight (population served / number of sources
    sampling that site)."""
    d = pd.read_parquet(PROC / "ww_samples.parquet")
    loc = locations()
    abbr2loc = dict(zip(loc.abbreviation, loc.index))
    d["location"] = d.state_territory.str.upper().map(abbr2loc)
    d = d[d.location.notna() & d.collect.notna()]
    d = d[np.isfinite(d[value_col]) & (d[value_col] > 0)]
    d["series"] = d.site.astype(str) + "|" + d.source.astype(str)
    d["lv"] = np.log10(d[value_col])
    pop = d.groupby("series").population_served.median()
    pop = pop.fillna(pop.groupby(d.groupby("series").location.first()).transform("median")).fillna(pop.median())
    nsrc = d.groupby("site").source.nunique()
    meta = d.groupby("series").agg(location=("location", "first"), site=("site", "first"))
    meta["weight"] = pop.reindex(meta.index) / nsrc.reindex(meta.site).values
    return d[["series", "collect", "lv"]], meta


def window_grid(lag: int):
    """Weekly window end dates: for a round R, window 0 ends at R - 3 - lag; all rounds share one weekday grid."""
    first = pd.Timestamp("2021-09-04") - pd.Timedelta(days=3 + lag)
    return pd.date_range(first, "2026-12-31", freq="7D")


def ww_windows(samples: pd.DataFrame, lag: int) -> pd.DataFrame:
    """Series x window-end matrix of the mean log10 value of samples in (end - 7 days, end]."""
    ends = window_grid(lag)
    idx = np.searchsorted(ends.values, samples.collect.values, side="left")   # window whose end >= collect
    s = samples.assign(end=ends[np.minimum(idx, len(ends) - 1)])
    return s.groupby(["series", "end"]).lv.mean().unstack("end").reindex(columns=ends)


def state_signal(win: pd.DataFrame, meta: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Location x window-end state anomaly using only windows ending on or before cutoff (= R - 3 - lag).
    Each series is centred on its median over available windows (at least MIN_WINDOWS)."""
    w = win.loc[:, win.columns <= cutoff]
    n = w.notna().sum(axis=1)
    w = w[n >= MIN_WINDOWS]
    anom = w.sub(w.median(axis=1), axis=0)
    m = meta.reindex(anom.index)
    wt = anom.notna().mul(m.weight.values, axis=0)
    num = anom.fillna(0).mul(m.weight.values, axis=0).groupby(m.location.values).sum()
    den = wt.groupby(m.location.values).sum()
    return (num / den.replace(0, np.nan))


# ----------------------------------------------------------------------------------------------- features
def yweek(hv: pd.DataFrame, pop: pd.Series) -> pd.DataFrame:
    """Location x week matrix of y = log((count + 1) / population * 1e5)."""
    m = hv.pivot_table(index="location", columns="target_end_date", values="observation", aggfunc="last")
    return np.log((m + 1).div(pop.reindex(m.index), axis=0) * 1e5)


def mmwr_week(dates: pd.DatetimeIndex) -> np.ndarray:
    return np.array([((d - pd.Timestamp(d.year, 1, 1)).days // 7) + 1 for d in dates])


def build_rows(Y: pd.DataFrame, S: pd.DataFrame | None, k: int, lag: int, t_from: pd.Timestamp, t_to: pd.Timestamp,
               with_target: bool):
    """Feature rows for last-data weeks t in [t_from, t_to] and k steps ahead. Wastewater window 0 for data week t is the
    window ending t + 4 - lag (the analogue of R - 3 - lag with R = t + 7)."""
    weeks = Y.columns
    ts = weeks[(weeks >= t_from) & (weeks <= t_to)]
    rows = []
    for t in ts:
        t1, t2 = t - pd.Timedelta(weeks=1), t - pd.Timedelta(weeks=2)
        if t2 not in Y.columns:
            continue
        tgt_week = t + pd.Timedelta(weeks=k)
        if with_target and tgt_week not in Y.columns:
            continue
        f = pd.DataFrame({"location": Y.index, "t": t, "yT": Y[t].values, "d1": (Y[t] - Y[t1]).values,
                          "d2": (Y[t1] - Y[t2]).values})
        wk = mmwr_week(pd.DatetimeIndex([tgt_week]))[0]
        f["s1"], f["c1"] = np.sin(2 * np.pi * wk / 52), np.cos(2 * np.pi * wk / 52)
        if with_target:
            f["z"] = (Y[tgt_week] - Y[t]).values
        if S is not None:
            e0 = t + pd.Timedelta(days=4 - lag)
            e1, e2 = e0 - pd.Timedelta(weeks=1), e0 - pd.Timedelta(weeks=2)
            g = lambda e: S[e].reindex(Y.index).values if e in S.columns else np.full(len(Y.index), np.nan)
            w0, w1, w2 = g(e0), g(e1), g(e2)
            f["W0"], f["dW1"], f["dW2"] = w0, w0 - w1, w1 - w2
        rows.append(f)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


BASE = ["yT", "d1", "d2", "s1", "c1"]


def fit_predict(train: pd.DataFrame, pred: pd.DataFrame, cols: list[str]) -> np.ndarray:
    X = np.column_stack([np.ones(len(train))] + [train[c].values for c in cols])
    Xp = np.column_stack([np.ones(len(pred))] + [pred[c].values for c in cols])
    out = np.empty((len(pred), len(QLEVELS)))
    for j, q in enumerate(QLEVELS):
        try:
            beta = QuantReg(train.z.values, X).fit(q=q, max_iter=5000).params
        except Exception:                                              # noqa: BLE001
            beta = np.linalg.lstsq(X, train.z.values, rcond=None)[0]
        out[:, j] = Xp @ beta
    return np.sort(out, axis=1)


# ----------------------------------------------------------------------------------------------- one round
CTX = {}


def run_round(R: pd.Timestamp):
    h, loc, variant, lag = CTX["h"], CTX["loc"], CTX["variant"], CTX["lag"]
    pop = loc.population
    v = vintage_for(CTX["asof"], R)
    Y = yweek(h[h.as_of == v], pop)
    T = Y.columns.max()
    cutoff = R - pd.Timedelta(days=3 + lag)
    if variant == "oracle":
        yf = CTX["Yfinal"]
        rng = np.random.default_rng(int(R.strftime("%Y%m%d")))
        O = yf.shift(-1, axis=1)                                        # O_t = final y_{t+1}
        O = O + rng.normal(0, 0.3, O.shape)
        S = O.copy()
        S.columns = [c + pd.Timedelta(days=4 - lag) for c in O.columns]  # align to the window grid used by build_rows
        S = S.loc[:, [c <= T + pd.Timedelta(days=4 - lag) for c in S.columns]]
    else:
        S = state_signal(CTX["win"], CTX["meta"], cutoff)
        if variant == "derange":
            perm = CTX["derange"][season_of(R)]
            S = S.rename(index=perm)
    out = []
    ks = sorted({int((R + pd.Timedelta(weeks=hh) - T).days // 7) for hh in HORIZONS})
    for k in ks:
        tr = build_rows(Y, S, k, lag, TRAIN_START, T - pd.Timedelta(weeks=k), True)
        tr = tr[np.isfinite(tr[BASE + ["z"]]).all(axis=1)]
        wwcols = ["W0"] if variant == "level" else ["W0", "dW1", "dW2"]
        tr_ww = tr[np.isfinite(tr[wwcols]).all(axis=1)]
        pr = build_rows(Y, S, k, lag, T, T, False)
        pr = pr[np.isfinite(pr[BASE]).all(axis=1)]
        base_train = tr if variant == "basefull" else tr_ww
        qb = fit_predict(base_train, pr, BASE)
        qw = fit_predict(tr_ww, pr, BASE + wwcols)
        has = np.isfinite(pr[wwcols]).all(axis=1).values
        qw[~has] = qb[~has]
        hh = int((T + pd.Timedelta(weeks=k) - R).days // 7)
        for model, q in (("base", qb), ("ww", qw)):
            cnt = np.maximum(0, np.exp(pr.yT.values[:, None] + q) * pop.reindex(pr.location).values[:, None] / 1e5 - 1)
            df = pd.DataFrame(cnt, columns=[f"q{x:g}" for x in QLEVELS])
            df.insert(0, "model", model)
            df.insert(0, "has_ww", has)
            df.insert(0, "horizon", hh)
            df.insert(0, "location", pr.location.values)
            df.insert(0, "reference_date", R)
            df["steps_ahead"], df["vintage"], df["n_train"] = k, v, len(tr_ww)
            out.append(df)
    return pd.concat(out, ignore_index=True)


def season_of(r):
    return f"{r.year}-{str(r.year + 1)[2:]}" if r.month >= 8 else f"{r.year - 1}-{str(r.year)[2:]}"


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "main"
    lag = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    h = load_hosp()
    loc = locations()
    CTX.update(h=h, loc=loc, variant=variant, lag=lag, asof=pd.DatetimeIndex(sorted(h.as_of.unique())))
    if variant == "oracle":
        final = h[h.as_of == h.as_of.max()]
        CTX["Yfinal"] = yweek(final, loc.population)
    elif variant == "wval":
        w = pd.read_csv(RAW / "nwss_wval_atcp-73re.csv", dtype=str)
        w.columns = [c.lower().replace("/", "_") for c in w.columns]
        w = w[w.pathogen_target.str.lower().str.contains("influenza")]
        name2loc = dict(zip(loc.location_name.str.lower(), loc.index))
        w = w.assign(collect=pd.to_datetime(w.week_end.str[:10]), location=w.state_territory.str.lower().map(name2loc),
                     lv=np.log10(pd.to_numeric(w.site_wval, errors="coerce").clip(lower=0) + 0.1),
                     series=w.site.astype(str) + "|" + w.source.astype(str))
        w = w[w.location.notna() & np.isfinite(w.lv) & w.collect.notna()]
        # WVAL is reported by week ending Saturday; its sample week ends before the window grid's weekday
        meta = w.groupby("series").agg(location=("location", "first"),
                                       weight=("population_served", lambda s: pd.to_numeric(s, errors="coerce").median()))
        meta["weight"] = meta.weight.fillna(meta.weight.median())
        CTX.update(win=ww_windows(w[["series", "collect", "lv"]], lag), meta=meta)
    else:
        samples, meta = ww_series("pcr_target_flowpop_lin" if variant == "flowpop" else "pcr_target_avg_conc_lin")
        CTX.update(win=ww_windows(samples, lag), meta=meta)
    refs = pd.to_datetime(open(RAW / "ensemble_reference_dates.txt").read().split())
    if variant == "derange":
        rng = np.random.default_rng(7)
        perms = {}
        for s in sorted({season_of(r) for r in refs}):
            ids = list(loc.index)
            while True:
                p = rng.permutation(ids)
                if not any(a == b for a, b in zip(ids, p)):
                    break
            perms[s] = dict(zip(p, ids))                                   # the features of state p[i] are given to ids[i]
        CTX["derange"] = perms
    with Pool(28) as pool:
        res = pool.map(run_round, list(refs), chunksize=1)
    df = pd.concat(res, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / f"{variant}_lag{lag}.parquet", index=False)
    print(variant, lag, "rounds", df.reference_date.nunique(), "rows", len(df), "with ww share %.2f" % df.has_ww.mean(),
          "median n_train", int(df.n_train.median()))


if __name__ == "__main__":
    sys.exit(main())
