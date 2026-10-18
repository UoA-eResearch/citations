"""Post-review sensitivity analyses (review issues 1-8, 11; deviation D2). Not preregistered; the preregistered
estimates in results/tables/mef.json are unchanged. Reuses the estimator in code/mef.py with alternative
specifications on the same common sample:
  controls: preregistered; no lagged D/E; D lags only; E lags only; + lagged coal/gas/hydro; no lagged outcomes but
  three days of anomaly history; each with and without natural inflow summed over the window; no wind-window control;
  half-hour x month fixed effects.
  instruments: the preregistered half-hour anomaly; a calendar-aligned climatology (29 Feb mapped to 28 Feb); the mean
  anomaly over the next 7 days; the mean over the local calendar day; the mean over the next 24 h.
  subsamples: dropping 2021 and 2024; 2015-2019; 2020-2024.
Also: the composition (coal, gas, hydro) under several control sets, the inflow response to instrumented demand, and
H2 rescored with block MEFs from the calendar-day-mean instrument. Writes results/tables/sensitivity.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mef  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
HS = [2, 48, 336]
BASE = ["zl1", "zl2", "zl3", "zl4", "D1", "Dday", "E1", "Eday", "storage", "inflow7", "hvdc_day", "tiwai_day"]
LAGS_D, LAGS_E = ["D1", "Dday"], ["E1", "Eday"]
FUEL = ["coal1", "coalday", "gas1", "gasday", "hydro1", "hydroday"]
ZHIST = [f"zh{k}" for k in range(1, 13)]


def prepare():
    s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
    s["z"] = mef.instrument(s)
    loc = s.ts.dt.tz_convert("Pacific/Auckland")
    hdd = np.maximum(0.0, 16.0 - s.temp.values)
    md = loc.dt.strftime("%m-%d").replace("02-29", "02-28").values
    clim = pd.DataFrame(dict(hdd=hdd, hh=s.hh.values, md=md)).groupby(["hh", "md"]).hdd.mean().unstack()
    sm = clim.T
    sm = pd.concat([sm.iloc[-7:], sm, sm.iloc[:7]]).rolling(15, center=True).mean().iloc[7:-7].T
    s["z_cal"] = hdd - sm.loc[s.hh.values].values[np.arange(len(s)), [sm.columns.get_loc(m) for m in md]]
    s["z_7d"] = mef.wsum(s.z.values, 336) / 336
    s["z_24h"] = mef.wsum(s.z.values, 48) / 48
    s["z_day"] = s.groupby("date").z.transform("mean")
    s["ym"] = s.year.astype(str) + "-" + s.month.astype(str).str.zfill(2)
    for k in range(4):
        s[f"zl{k + 1}"] = s.z.shift(1 + 12 * k).rolling(12).mean()
    for k in range(12):
        s[f"zh{k + 1}"] = s.z.shift(1 + 12 * k).rolling(12).mean()
    s["D1"], s["E1"] = s.D.shift(1), s.E.shift(1)
    s["Dday"], s["Eday"] = s.D.shift(1).rolling(48).mean(), s.E.shift(1).rolling(48).mean()
    for f in ("coal", "gas", "hydro"):
        s[f"{f}1"] = s[f].shift(1); s[f"{f}day"] = s[f].shift(1).rolling(48).mean()
    s["hvdc_day"], s["tiwai_day"] = s.hvdc_north.shift(1).rolling(48).mean(), s.tiwai.shift(1).rolling(48).mean()
    di = s.groupby("date").inflow.first()
    s["inflow7"] = s.date.map(di.shift(1).rolling(7).mean())
    s["inflow_hh"] = s.inflow * 1000 / 48                                       # MWh of inflow energy per half-hour
    new = {}
    for h in sorted(set(HS + [1, 24, 96, 1440])):
        for v, src in (("D", "D"), ("E", "E"), ("W", "wind"), ("I", "inflow_hh"), ("C", "coal"), ("GS", "gas"), ("Y", "hydro"), ("G", "geo")):
            new[f"{v}_{h}"] = mef.wsum(s[src].values, h)
    s = pd.concat([s, pd.DataFrame(new)], axis=1)
    need = ZHIST + ["Dday", "inflow7", "hvdc_day", "storage", "coalday", "D_1440", "z_7d"]
    idx = np.where(s[need].notna().all(axis=1))[0]
    return s, idx


def design(s, idx, cont, hhmonth=False):
    d = s.iloc[idx]
    if hhmonth:
        fe = pd.get_dummies(d.hh.astype(str) + "_" + d.month.astype(str), dtype=float)
        fe = pd.concat([fe, pd.get_dummies(d.daytype, prefix="dt", drop_first=True, dtype=float)], axis=1)
    else:
        fe = pd.get_dummies(d.hh.astype(str) + "_" + d.daytype.astype(str), dtype=float)
        fe = pd.concat([fe, pd.get_dummies(d.month, prefix="m", drop_first=True, dtype=float)], axis=1)
    fe = pd.concat([fe, pd.get_dummies(d.year, prefix="y", drop_first=True, dtype=float)], axis=1)
    c = d[cont]; c = (c - c.mean()) / c.std()
    return np.column_stack([fe.values, c.values])


def fit(s, idx, hs, cont, zcol="z", window=("W",), outcomes=("E",), hhmonth=False, B=999, seed=20261018):
    X = design(s, idx, cont, hhmonth)
    q, _ = np.linalg.qr(X)
    R = lambda v: v - q @ (q.T @ v)
    z0 = R(s[zcol].values[idx]); m = s.ym.values[idx]; months = sorted(set(m))
    rng = np.random.default_rng(seed); S = rng.integers(0, len(months), size=(B, len(months)))
    out = {}
    for h in hs:
        zr, Dr = z0.copy(), R(s[f"D_{h}"].values[idx]); Ys = {o: R(s[f"{o}_{h}"].values[idx]) for o in outcomes}
        for w in window:
            Wr = R(s[f"{w}_{h}"].values[idx])
            bw = lambda v: v - Wr * (Wr @ v) / (Wr @ Wr)
            zr, Dr, Ys = bw(zr), bw(Dr), {o: bw(y) for o, y in Ys.items()}
            # (sequential FWL on several window controls is exact only after orthogonalising them; done below)
        if len(window) > 1:     # exact joint partialling of the window controls
            W = np.column_stack([R(s[f"{w}_{h}"].values[idx]) for w in window]); qw, _ = np.linalg.qr(W)
            P = lambda v: v - qw @ (qw.T @ v)
            zr, Dr, Ys = P(R(s[zcol].values[idx])), P(R(s[f"D_{h}"].values[idx])), {o: P(R(s[f"{o}_{h}"].values[idx])) for o in outcomes}
        g = pd.DataFrame(dict(m=m, zD=zr * Dr, **{f"zY_{o}": zr * y for o, y in Ys.items()})).groupby("m").sum().reindex(months).fillna(0)
        pi = (zr @ Dr) / (zr @ zr); u = Dr - pi * zr
        se = np.sqrt(pd.Series(zr * u).groupby(m).sum().pow(2).sum()) / (zr @ zr)
        r = dict(F=float((pi / se) ** 2))
        for o in outcomes:
            num, den = g[f"zY_{o}"].values, g.zD.values
            dr = num[S].sum(1) / den[S].sum(1)
            r[o] = float(num.sum() / den.sum()); r[f"{o}_ci"] = [float(np.percentile(dr, 2.5)), float(np.percentile(dr, 97.5))]
            r[f"{o}_draws"] = dr
        out[str(h)] = r
    return out


def main():
    s, idx = prepare()
    nolag = [c for c in BASE if c not in LAGS_D + LAGS_E]
    specs = {
        "preregistered": dict(cont=BASE),
        "no lagged D/E": dict(cont=nolag),
        "D lags only": dict(cont=[c for c in BASE if c not in LAGS_E]),
        "E lags only": dict(cont=[c for c in BASE if c not in LAGS_D]),
        "D, E and fuel lags": dict(cont=BASE + FUEL),
        "no lagged outcomes, 3 days of anomaly history": dict(cont=[c for c in nolag if not c.startswith("zl")] + ZHIST),
        "preregistered + window inflow": dict(cont=BASE, window=("W", "I")),
        "no lagged D/E + window inflow": dict(cont=nolag, window=("W", "I")),
        "3 days of anomaly history + window inflow": dict(cont=[c for c in nolag if not c.startswith("zl")] + ZHIST, window=("W", "I")),
        "no wind-window control": dict(cont=BASE, window=()),
        "half-hour x month fixed effects": dict(cont=BASE, hhmonth=True),
        "calendar-aligned climatology": dict(cont=BASE, zcol="z_cal"),
        "7-day-mean instrument": dict(cont=BASE, zcol="z_7d", hs=HS + [1440]),
        "next-24-h-mean instrument": dict(cont=BASE, zcol="z_24h"),
    }
    out = dict(n=int(len(idx)), specs={})
    for name, sp in specs.items():
        out["specs"][name] = fit(s, idx, sp.get("hs", HS), sp["cont"], sp.get("zcol", "z"), sp.get("window", ("W",)),
                                 hhmonth=sp.get("hhmonth", False))
        print(name, {h: (round(v["E"], 3), round(v["F"], 1)) for h, v in out["specs"][name].items()}, flush=True)
    yr = s.year.values[idx]
    for name, keep in (("drop 2021 and 2024", ~np.isin(yr, [2021, 2024])), ("2015-2019", yr <= 2019), ("2020-2024", yr >= 2020)):
        out["specs"][name] = fit(s, idx[keep], HS, BASE)
        print(name, {h: (round(v["E"], 3), round(v["F"], 1)) for h, v in out["specs"][name].items()}, flush=True)
    comp = {}
    for name, sp in (("preregistered", dict(cont=BASE)), ("D, E and fuel lags", dict(cont=BASE + FUEL)),
                     ("no lagged D/E", dict(cont=nolag)), ("preregistered + window inflow", dict(cont=BASE, window=("W", "I")))):
        r = fit(s, idx, [1, 336], sp["cont"], window=sp.get("window", ("W",)), outcomes=("C", "GS", "Y"), B=199)
        comp[name] = {h: {o: round(v[o], 3) for o in ("C", "GS", "Y")} for h, v in r.items()}
    out["composition"] = comp
    out["inflow_response"] = {h: dict(v=v["I"], ci=v["I_ci"]) for h, v in fit(s, idx, [2, 48, 336], BASE, outcomes=("I",)).items()}
    out["geothermal_response"] = {h: dict(v=v["G"], ci=v["G_ci"]) for h, v in fit(s, idx, [24, 48, 96], BASE, outcomes=("G",)).items()}
    # H2 rescored with block MEFs from the calendar-day-mean instrument (blocks fitted separately, as in mef.py)
    blk = s.hh.values // 12
    for name, cont in (("preregistered controls", BASE), ("no lagged D/E", nolag)):
        bb = [fit(s, idx[blk[idx] == b], [48], cont, zcol="z_day", B=999, seed=20261018)["48"] for b in range(4)]
        out[f"blocks_day_mean_{name}"] = [dict(mef=x["E"], ci=x["E_ci"], F=x["F"], draws=x["E_draws"]) for x in bb]
    # the 24-hour AEF scheduler of code/simulate.py, rescored with these block MEFs
    s["aef"] = s.E / s.D
    MWH = 10.0; fr, to = [], []
    for d, g in s.groupby("date"):
        if len(g) < 46:
            continue
        a = g.aef.values; k = int(np.argmin([a[i:i + 8].mean() for i in range(len(a) - 7)]))
        fr.append(g.index.values[np.isin(g.hh.values, range(20, 28))][:8]); to.append(g.index.values[k:k + 8])
    fr, to = np.concatenate(fr), np.concatenate(to)
    claimed = MWH * (s.aef.values[fr].sum() - s.aef.values[to].sum())
    cnt = np.bincount(blk[fr], minlength=4) - np.bincount(blk[to], minlength=4)
    out["moved_mwh_actual"] = float(MWH * (len(fr) - len(np.intersect1d(fr, to))))
    out["load_mwh"] = float(MWH * len(fr))
    for name in ("preregistered controls", "no lagged D/E"):
        bb = out[f"blocks_day_mean_{name}"]
        draws = np.column_stack([x.pop("draws") for x in bb])
        mefs = np.array([x["mef"] for x in bb])
        rd = MWH * (draws @ cnt) / claimed
        out[f"h2_day_mean_{name}"] = dict(claimed_t=float(claimed), realised_t=float(MWH * cnt @ mefs), capture=float(MWH * cnt @ mefs / claimed),
                                          ci=[float(np.percentile(rd, 2.5)), float(np.percentile(rd, 97.5))])
    # confirmation item 1: intervals of the horizon differences (same month resamples within each specification)
    out["gradient_differences"] = {}
    for k, v in out["specs"].items():
        e = {h: np.asarray(v[h]["E_draws"]) for h in v}
        dd = {}
        for a, b in (("336", "2"), ("48", "2")) + ((("1440", "2"),) if "1440" in e else ()):
            x = e[a] - e[b]
            dd[f"{a}-{b}"] = dict(diff=v[a]["E"] - v[b]["E"], ci=[float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))])
        out["gradient_differences"][k] = dd
    zz = s.z.values
    out["anomaly_autocorrelation"] = {str(l): float(np.corrcoef(zz[:-l], zz[l:])[0, 1]) for l in (48, 336, 1440)}
    for k in list(out["specs"]):
        for h in out["specs"][k]:
            out["specs"][k][h] = {a: b for a, b in out["specs"][k][h].items() if not a.endswith("_draws")}
    out["inflow_response"] = {h: {a: b for a, b in v.items()} for h, v in out["inflow_response"].items()}
    json.dump(out, open(T / "sensitivity.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("composition", "inflow_response", "h2_day_mean_preregistered controls", "h2_day_mean_no lagged D/E", "moved_mwh_actual")}, indent=1, default=float))


if __name__ == "__main__":
    main()
