"""Reviewer probe: is MEF(14 d)/MEF(30 d) identifiable with a window-mean weather instrument (not preregistered)? Writes out_h1_probe.json."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path(__file__).resolve().parents[2]; HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN / "code")); import mef as theirs
s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
s["z"] = theirs.instrument(s); s["ym"] = s.year.astype(str) + "-" + s.month.astype(str).str.zfill(2)
for k in range(4): s[f"zl{k+1}"] = s.z.shift(1 + 12 * k).rolling(12).mean()
s["D1"], s["E1"] = s.D.shift(1), s.E.shift(1); s["Dday"], s["Eday"] = s.D.shift(1).rolling(48).mean(), s.E.shift(1).rolling(48).mean()
s["hvdc_day"], s["tiwai_day"] = s.hvdc_north.shift(1).rolling(48).mean(), s.tiwai.shift(1).rolling(48).mean()
di = s.groupby("date").inflow.first(); s["inflow7"] = s.date.map(di.shift(1).rolling(7).mean())
def wsum(x, h):
    cs = np.concatenate([[0.0], np.cumsum(x)]); o = np.full(len(x), np.nan); o[: len(x) - h + 1] = cs[h:] - cs[: len(x) - h + 1]; return o
H = [2, 48, 336, 672, 1440]
for h in H:
    for v, src in (("D", "D"), ("E", "E"), ("W", "wind"), ("Z", "z")): s[f"{v}_{h}"] = wsum(s[src].values, h)
s["z7"] = s.Z_336 / 336; s["z14"] = s.Z_672 / 672; s["z30"] = s.Z_1440 / 1440; s["z1"] = s.Z_48 / 48
IDX = np.where(s[["zl4", "Dday", "inflow7", "hvdc_day", "storage", "D_1440"]].notna().all(axis=1))[0]
d = s.iloc[IDX]
fe = pd.concat([pd.get_dummies(d.hh.astype(str) + "_" + d.daytype.astype(str), dtype=float), pd.get_dummies(d.month, prefix="m", drop_first=True, dtype=float), pd.get_dummies(d.year, prefix="y", drop_first=True, dtype=float)], axis=1).values
cont = d[["zl1","zl2","zl3","zl4","D1","Dday","E1","Eday","storage","inflow7","hvdc_day","tiwai_day"]]; cont = ((cont - cont.mean()) / cont.std()).values
months = sorted(set(d.ym.values)); M = len(months); rng = np.random.default_rng(20261018); S = rng.integers(0, M, size=(999, M))
out = {}
for inst in ("z", "z1", "z7", "z14", "z30"):
    res = {}; dr = {}
    for h in H:
        X = np.column_stack([fe, cont, d[f"W_{h}"].values]); q, _ = np.linalg.qr(X)
        r = lambda v: v - q @ (q.T @ v)
        zr, Dr, Er = r(d[inst].values), r(d[f"D_{h}"].values), r(d[f"E_{h}"].values)
        pi = (zr @ Dr) / (zr @ zr); u = Dr - pi * zr; sc = pd.Series(zr * u).groupby(d.ym.values).sum().values
        F = float((pi / (np.sqrt((sc ** 2).sum()) / (zr @ zr))) ** 2)
        g = pd.DataFrame(dict(m=d.ym.values, zD=zr * Dr, zE=zr * Er)).groupby("m").sum().reindex(months).fillna(0)
        draws = g.zE.values[S].sum(1) / g.zD.values[S].sum(1); dr[h] = draws
        res[theirs.LAB[h]] = dict(mef=round(float((zr @ Er) / (zr @ Dr)), 4), F=round(F, 1), ci=[round(float(np.percentile(draws, 2.5)), 3), round(float(np.percentile(draws, 97.5)), 3)])
    dd = dr[1440] - dr[2]
    res["H1_30d_minus_1h"] = dict(point=round(res["30d"]["mef"] - res["1h"]["mef"], 3), ci=[round(float(np.percentile(dd, 2.5)), 3), round(float(np.percentile(dd, 97.5)), 3)], weak=bool(min(res["30d"]["F"], res["1h"]["F"]) < 10))
    out[inst] = res; print(inst, json.dumps(res))
json.dump(out, open(HERE / "out_h1_probe.json", "w"), indent=1)
