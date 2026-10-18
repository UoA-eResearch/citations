"""Horizon-resolved marginal emissions factors by 2SLS (plan section 4). Reads data/series.pkl.

For each horizon h (in half-hours): sum_{j<h} E_{t+j} = a + MEF(h) * sum_{j<h} D_{t+j} + controls, with the window's demand
instrumented by z_t, the population-weighted heating-degree anomaly (heating degrees max(0, 16 C - T) minus their
half-hour-of-day by day-of-year climatology, smoothed over 15 days). Controls: four six-hour means of z over the
previous day; D and E in the previous half-hour and their previous-day means; storage at the end of the previous day;
mean inflow over the previous 7 days; previous-day means of HVDC northward transfer and Tiwai offtake; wind generation
summed over the same window; fixed effects for half-hour-of-day x day type, month and year. Controls are partialled
out (Frisch-Waugh-Lovell) on one common sample (full lags, and 30 days of future data for every t). Inference: a
calendar-month block bootstrap (999 resamples, seed 20261018) on month-level sums of z~E~ and z~D~. Time-of-day MEFs
(H2) and storage-tercile MEFs (H3) re-partial every control within each subsample (fully interacted).
Writes results/tables/mef.json, results/tables/mef_horizons.csv and data/mef_draws.npz."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
H = [1, 2, 4, 8, 24, 48, 96, 336, 672, 1440]
LAB = {1: "0.5h", 2: "1h", 4: "2h", 8: "4h", 24: "12h", 48: "1d", 96: "2d", 336: "7d", 672: "14d", 1440: "30d"}
B, SEED = 999, 20261018


def wsum(x, h):
    cs = np.concatenate([[0.0], np.cumsum(x)])
    out = np.full(len(x), np.nan)
    out[: len(x) - h + 1] = cs[h:] - cs[: len(x) - h + 1]
    return out


def instrument(s):
    hdd = np.maximum(0.0, 16.0 - s.temp.values)
    loc = s.ts.dt.tz_convert("Pacific/Auckland")
    doy = np.minimum(loc.dt.dayofyear.values, 365)
    clim = pd.DataFrame(dict(hdd=hdd, hh=s.hh.values, doy=doy)).groupby(["hh", "doy"]).hdd.mean().unstack()   # hh x doy
    sm = clim.T
    sm = pd.concat([sm.iloc[-7:], sm, sm.iloc[:7]]).rolling(15, center=True).mean().iloc[7:-7].T          # circular 15-day smoothing
    c = sm.values[s.hh.values, doy - 1]
    return hdd - c


def design(s, idx):
    """Base control matrix on rows idx (fixed effects as dummies, plus continuous predetermined controls)."""
    d = s.iloc[idx]
    fe = pd.get_dummies(d.hh.astype(str) + "_" + d.daytype.astype(str), drop_first=False, dtype=float)
    fe = pd.concat([fe, pd.get_dummies(d.month, prefix="m", drop_first=True, dtype=float),
                    pd.get_dummies(d.year, prefix="y", drop_first=True, dtype=float)], axis=1)
    cont = d[["zl1", "zl2", "zl3", "zl4", "D1", "Dday", "E1", "Eday", "storage", "inflow7", "hvdc_day", "tiwai_day"]]
    cont = (cont - cont.mean()) / cont.std()
    return np.column_stack([fe.values, cont.values])


def resid(X, cols):
    q, _ = np.linalg.qr(X)
    return [c - q @ (q.T @ c) for c in cols]


def fit(s, idx, h_list, outcomes=("E",)):
    """Residualised month-level sums for each horizon on rows idx."""
    X = design(s, idx)
    z = s.z.values[idx]
    res = {}
    for h in h_list:
        cols = [s[f"D_{h}"].values[idx], s[f"W_{h}"].values[idx]] + [s[f"{o}_{h}"].values[idx] for o in outcomes]
        zr, Dr, Wr, *Ys = resid(X, [z] + cols)
        # partial out the window's wind (FWL, second step)
        bw = lambda v: v - Wr * (Wr @ v) / (Wr @ Wr)
        zr, Dr, Ys = bw(zr), bw(Dr), [bw(y) for y in Ys]
        m = s.ym.values[idx]
        g = pd.DataFrame(dict(m=m, zD=zr * Dr, zz=zr * zr, **{f"zY{k}": zr * y for k, y in enumerate(Ys)}))
        ms = g.groupby("m").sum()
        pi = (zr @ Dr) / (zr @ zr)
        u = Dr - pi * zr
        se_pi = np.sqrt(pd.Series(zr * u).groupby(m).sum().pow(2).sum()) / (zr @ zr)      # month-clustered
        res[h] = dict(ms=ms, F=float((pi / se_pi) ** 2), est={o: float(ms[f"zY{k}"].sum() / ms.zD.sum()) for k, o in enumerate(outcomes)})
    return res


def boot(res_list, months, rng):
    """Bootstrap draws (B x fits): every fit uses the same B resamples of calendar months."""
    S = rng.integers(0, len(months), size=(B, len(months)))
    draws = np.full((B, len(res_list)), np.nan)
    for j, (ms, k) in enumerate(res_list):
        a = ms.reindex(months).fillna(0)
        num, den = a[f"zY{k}"].values, a.zD.values
        draws[:, j] = num[S].sum(axis=1) / den[S].sum(axis=1)
    return draws


def ci(x):
    return [float(np.nanpercentile(x, 2.5)), float(np.nanpercentile(x, 97.5))]


def main():
    s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
    s["z"] = instrument(s)
    s["ym"] = s.year.astype(str) + "-" + s.month.astype(str).str.zfill(2)
    for k in range(4):
        s[f"zl{k + 1}"] = s.z.shift(1 + 12 * k).rolling(12).mean()
    s["D1"], s["E1"] = s.D.shift(1), s.E.shift(1)
    s["Dday"], s["Eday"] = s.D.shift(1).rolling(48).mean(), s.E.shift(1).rolling(48).mean()
    s["hvdc_day"], s["tiwai_day"] = s.hvdc_north.shift(1).rolling(48).mean(), s.tiwai.shift(1).rolling(48).mean()
    daily_inflow = s.groupby("date").inflow.first()
    s["inflow7"] = s.date.map(daily_inflow.shift(1).rolling(7).mean())
    for h in H:
        for v, src in (("D", "D"), ("E", "E"), ("W", "wind"), ("G", "geo"), ("Y", "hydro"), ("TH", "thermal"),
                       ("Eg05", "E_geo05"), ("Eg15", "E_geo15"), ("Erk", "E_rk70")):
            s[f"{v}_{h}"] = wsum(s[src].values, h)
    need = ["zl4", "Dday", "inflow7", "hvdc_day", "storage"] + [f"D_{max(H)}"]
    idx = np.where(s[need].notna().all(axis=1))[0]
    rng = np.random.default_rng(SEED)
    outs = ("E", "G", "Y", "TH", "Eg05", "Eg15", "Erk")
    full = fit(s, idx, H, outs)
    months = sorted(set(s.ym.values[idx]))
    draws = boot([(full[h]["ms"], 0) for h in H], months, rng)
    rows = []
    for j, h in enumerate(H):
        r = dict(h=h, label=LAB[h], mef=full[h]["est"]["E"], ci=ci(draws[:, j]), first_stage_F=full[h]["F"],
                 geo=full[h]["est"]["G"], hydro=full[h]["est"]["Y"], thermal=full[h]["est"]["TH"],
                 mef_geo05=full[h]["est"]["Eg05"], mef_geo15=full[h]["est"]["Eg15"], mef_rk70=full[h]["est"]["Erk"])
        rows.append(r)
    out = dict(n=int(len(idx)), months=len(months), horizons=rows)
    # placebo: geothermal response with bootstrap interval
    gd = boot([(full[h]["ms"], 1) for h in H], months, np.random.default_rng(SEED + 1))
    for j, r in enumerate(rows):
        r["geo_ci"] = ci(gd[:, j])
    # H1: MEF(30d) - MEF(1h)
    i30, i1 = H.index(1440), H.index(2)
    d = draws[:, i30] - draws[:, i1]
    weak = min(full[1440]["F"], full[2]["F"]) < 10
    lo, hi = ci(d)
    out["H1"] = dict(diff=rows[i30]["mef"] - rows[i1]["mef"], ci=[lo, hi], weak=weak,
                     verdict="Inconclusive (weak instrument)" if weak else "Supported" if lo > 0 else "Refuted" if hi < 0 else "Inconclusive")
    # time-of-day blocks (H2 input) and storage terciles (H3), h = 48, fully interacted (re-partialled within subsample)
    blk = s.hh.values // 12
    bfit = {b: fit(s, idx[blk[idx] == b], [48, 336]) for b in range(4)}
    bres = {b: bfit[b][48] for b in range(4)}
    bres7 = {b: bfit[b][336] for b in range(4)}
    rel = s.storage - s.groupby(s.ts.dt.tz_convert("Pacific/Auckland").dt.dayofyear).storage.transform("mean")
    terc = pd.qcut(rel.iloc[idx], 3, labels=False).values
    tres = {k: fit(s, idx[terc == k], [48])[48] for k in range(3)}
    rng2 = np.random.default_rng(SEED + 2)
    fits = [(bres[b]["ms"], 0) for b in range(4)] + [(bres7[b]["ms"], 0) for b in range(4)] + [(tres[k]["ms"], 0) for k in range(3)]
    bd = boot(fits, months, rng2)
    out["blocks_1d"] = [dict(block=f"{6 * b:02d}-{6 * b + 6:02d}", mef=bres[b]["est"]["E"], ci=ci(bd[:, b]), F=bres[b]["F"]) for b in range(4)]
    out["blocks_7d"] = [dict(block=f"{6 * b:02d}-{6 * b + 6:02d}", mef=bres7[b]["est"]["E"], ci=ci(bd[:, 4 + b]), F=bres7[b]["F"]) for b in range(4)]
    out["storage_terciles_1d"] = [dict(tercile=k, mef=tres[k]["est"]["E"], ci=ci(bd[:, 8 + k]), F=tres[k]["F"]) for k in range(3)]
    d3 = bd[:, 8] - bd[:, 10]
    weak3 = min(tres[0]["F"], tres[2]["F"]) < 10
    lo3, hi3 = ci(d3)
    out["H3"] = dict(diff_low_minus_high=tres[0]["est"]["E"] - tres[2]["est"]["E"], ci=[lo3, hi3], weak=weak3,
                     verdict="Inconclusive (weak instrument)" if weak3 else "Supported" if lo3 > 0 else "Refuted" if hi3 < 0 else "Inconclusive")
    np.savez(RUN / "data" / "mef_draws.npz", horizons=draws, blocks=bd, H=np.array(H))
    # secondary: OLS on demand innovations (residual of D on temperature splines and calendar)
    X = design(s, idx)
    tt = s.temp.values[idx]
    spl = np.column_stack([np.maximum(0, k - tt) for k in (8, 12, 16)] + [np.maximum(0, tt - k) for k in (18, 22)])
    Dc = s.D.values[idx]
    q, _ = np.linalg.qr(np.column_stack([X, spl]))
    u = np.full(len(s), np.nan); u[idx] = Dc - q @ (q.T @ Dc)
    uu = np.nan_to_num(u)
    ols = []
    for h in H:
        Uh = wsum(uu, h)[idx]
        Ur, Er, Wr = resid(X, [Uh, s[f"E_{h}"].values[idx], s[f"W_{h}"].values[idx]])
        bw = lambda v: v - Wr * (Wr @ v) / (Wr @ Wr)
        Ur, Er = bw(Ur), bw(Er)
        ols.append(dict(h=h, label=LAB[h], mef_ols=float((Ur @ Er) / (Ur @ Ur))))
    out["ols_innovations"] = ols
    pd.DataFrame(rows).to_csv(T / "mef_horizons.csv", index=False)
    json.dump(out, open(T / "mef.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("n", "H1", "H3")}, indent=1, default=float))
    print(pd.DataFrame(rows)[["label", "mef", "ci", "first_stage_F", "geo", "hydro", "thermal"]].to_string(index=False))


if __name__ == "__main__":
    main()
