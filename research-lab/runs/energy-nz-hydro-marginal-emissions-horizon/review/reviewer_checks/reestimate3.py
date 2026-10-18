"""Reviewer check 3c: (a) which lagged controls drive the short-horizon level and the coal-up/gas-down composition;
(b) time-of-day blocks at 1 d with the daily-mean anomaly as instrument, with a joint month-block bootstrap, and H2 rescored
with them (not preregistered; a probe of whether H2 is decidable with a usable instrument). Writes out_reestimate3.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out_reestimate3.json"
sys.path.insert(0, str(RUN / "code"))
import mef as theirs  # noqa: E402

out = {}
s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
s["z"] = theirs.instrument(s)
s["ym"] = s.year.astype(str) + "-" + s.month.astype(str).str.zfill(2)
for k in range(12):      # 6-hour means of z over the previous 3 days
    s[f"zl{k + 1}"] = s.z.shift(1 + 12 * k).rolling(12).mean()
for v in ("D", "E", "coal", "gas", "hydro"):
    s[f"{v}1"] = s[v].shift(1); s[f"{v}day"] = s[v].shift(1).rolling(48).mean()
s["hvdc_day"], s["tiwai_day"] = s.hvdc_north.shift(1).rolling(48).mean(), s.tiwai.shift(1).rolling(48).mean()
di = s.groupby("date").inflow.first()
s["inflow7"] = s.date.map(di.shift(1).rolling(7).mean())
s["inflow_hh"] = s.inflow * 1000 / s.groupby("date").inflow.transform("size")
H = [1, 2, 8, 48, 336]
LAB = theirs.LAB


def wsum(x, h):
    cs = np.concatenate([[0.0], np.cumsum(x)])
    o = np.full(len(x), np.nan); o[: len(x) - h + 1] = cs[h:] - cs[: len(x) - h + 1]; return o


SRC = {"D": "D", "E": "E", "W": "wind", "Y": "hydro", "TH": "thermal", "C": "coal", "GS": "gas", "G": "geo", "I": "inflow_hh", "Z": "z"}
new = {f"{v}_{h}": wsum(s[src].values, h) for h in H for v, src in SRC.items()}
s = pd.concat([s, pd.DataFrame(new)], axis=1)
s["zday"] = s.groupby("date").z.transform("mean")
s["zbar24"] = wsum(s.z.values, 48) / 48
need = ["zl12", "Dday", "inflow7", "hvdc_day", "storage", "D_336"]
# common sample as theirs (30 days of future data), for comparability
s["D_1440"] = wsum(s.D.values, 1440)
IDX = np.where(s[need + ["D_1440"]].notna().all(axis=1))[0]


def design(d, cont_cols):
    fe = [pd.get_dummies(d.hh.astype(str) + "_" + d.daytype.astype(str), dtype=float),
          pd.get_dummies(d.month, prefix="m", drop_first=True, dtype=float),
          pd.get_dummies(d.year, prefix="y", drop_first=True, dtype=float)]
    cont = d[cont_cols]; cont = (cont - cont.mean()) / cont.std()
    return np.column_stack([pd.concat(fe, axis=1).values, cont.values])


BASE = ["zl1", "zl2", "zl3", "zl4", "storage", "inflow7", "hvdc_day", "tiwai_day"]
LAGS = ["D1", "Dday", "E1", "Eday"]


def iv(idx, h, outcomes, cont_cols, inst="z", extra=()):
    d = s.iloc[idx]
    X = np.column_stack([design(d, cont_cols), d[f"W_{h}"].values] + [d[f"{e}_{h}"].values for e in extra])
    q, _ = np.linalg.qr(X)
    def res(v): return v - q @ (q.T @ v)
    zr = res(d[inst].values.astype(float)); Dr = res(d[f"D_{h}"].values)
    pi = (zr @ Dr) / (zr @ zr); u = Dr - pi * zr
    sc = pd.Series(zr * u).groupby(d.ym.values).sum().values
    r = dict(F=round(float((pi / (np.sqrt((sc ** 2).sum()) / (zr @ zr))) ** 2), 1))
    for o in outcomes:
        Yr = res(d[f"{o}_{h}"].values); r[o] = round(float((zr @ Yr) / (zr @ Dr)), 4)
    r["_zr"], r["_Dr"], r["_Er"], r["_m"] = zr, Dr, res(d["E_%d" % h].values), d.ym.values
    return r


OUTC = ["E", "Y", "TH", "C", "GS", "G"]
specs = {
    "preregistered (D,E lags)": dict(cont_cols=BASE + LAGS),
    "no lags": dict(cont_cols=BASE),
    "D lags only": dict(cont_cols=BASE + ["D1", "Dday"]),
    "E lags only": dict(cont_cols=BASE + ["E1", "Eday"]),
    "D,E lags + coal,gas,hydro lags": dict(cont_cols=BASE + LAGS + ["coal1", "coalday", "gas1", "gasday", "hydro1", "hydroday"]),
    "no lags + 3 days of z history": dict(cont_cols=BASE + [f"zl{k}" for k in range(5, 13)]),
    "no lags + window inflow": dict(cont_cols=BASE, extra=("I",)),
    "D,E lags + window inflow": dict(cont_cols=BASE + LAGS, extra=("I",)),
    "no lags + 3d z history + window inflow": dict(cont_cols=BASE + [f"zl{k}" for k in range(5, 13)], extra=("I",)),
}
tab = {}
for name, kw in specs.items():
    row = {}
    for h in H:
        r = iv(IDX, h, OUTC, **kw)
        row[LAB[h]] = {k: v for k, v in r.items() if not k.startswith("_")}
    tab[name] = row
    print(name); print(pd.DataFrame(row).T.to_string())
out["lag_control_variants"] = tab

# ---------- (b) blocks at 1 d with the daily-mean instrument; joint bootstrap; H2 rescored ----------
blk = s.hh.values // 12
sim = json.load(open(RUN / "results" / "tables" / "simulation.json"))
claimed = sim["24h"]["claimed_t"]
net = np.array([-11990.0, 8293.0, 8429.0, -4732.0])    # net half-hour counts removed from each block by the 24-h scheduler (reviewer's recomputation)
rng = np.random.default_rng(20261018)
months = sorted(set(s.ym.values[IDX])); M = len(months)
S = rng.integers(0, M, size=(999, M))
blocks_out = {}
for inst in ("z", "zday", "zbar24"):
    for specname in ("preregistered (D,E lags)", "no lags"):
        kw = specs[specname]
        ests, draws = [], []
        for b in range(4):
            idb = IDX[blk[IDX] == b]
            r = iv(idb, 48, ["E", "Y", "TH"], inst=inst, **kw)
            g = pd.DataFrame(dict(m=r["_m"], zD=r["_zr"] * r["_Dr"], zE=r["_zr"] * r["_Er"])).groupby("m").sum().reindex(months).fillna(0)
            dr = g.zE.values[S].sum(1) / g.zD.values[S].sum(1)
            ests.append(dict(block=f"{6 * b:02d}-{6 * b + 6:02d}", mef=r["E"], F=r["F"], ci=[float(np.percentile(dr, 2.5)), float(np.percentile(dr, 97.5))], hydro=r["Y"], thermal=r["TH"]))
            draws.append(dr)
        D4 = np.column_stack(draws)
        realised = 10.0 * (net @ np.array([e["mef"] for e in ests]))
        cr = 10.0 * (D4 @ net) / claimed
        key = f"{inst} | {specname}"
        blocks_out[key] = dict(blocks=ests, h2_realised_t=realised, h2_capture_ratio=realised / claimed,
                               h2_capture_ci=[float(np.percentile(cr, 2.5)), float(np.percentile(cr, 97.5))],
                               weak_block=bool(any(e["F"] < 10 for e in ests)),
                               verdict_if_identified=("Supported" if np.percentile(cr, 97.5) < 0.5 else "Refuted" if np.percentile(cr, 2.5) >= 0.5 else "Inconclusive"))
        print(key); print(pd.DataFrame(ests).to_string()); print("  H2 capture", round(realised / claimed, 2), blocks_out[key]["h2_capture_ci"], blocks_out[key]["verdict_if_identified"])
out["blocks_1d_by_instrument"] = blocks_out
json.dump(out, open(OUT, "w"), indent=1, default=float)
print("written", OUT)
