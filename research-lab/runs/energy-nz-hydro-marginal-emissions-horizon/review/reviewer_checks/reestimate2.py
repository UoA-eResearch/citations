"""Reviewer check 3b: the cold-and-dry channel. Does the cold anomaly predict inflow over the window, and does controlling for
window inflow (as wind is controlled) change the horizon gradient? Also the storage response. Writes out_reestimate2.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out_reestimate2.json"
sys.path.insert(0, str(RUN / "code"))
import mef as theirs  # noqa: E402

out = {}
s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
s["z"] = theirs.instrument(s)
s["ym"] = s.year.astype(str) + "-" + s.month.astype(str).str.zfill(2)
for k in range(4):
    s[f"zl{k + 1}"] = s.z.shift(1 + 12 * k).rolling(12).mean()
s["D1"], s["E1"] = s.D.shift(1), s.E.shift(1)
s["Dday"], s["Eday"] = s.D.shift(1).rolling(48).mean(), s.E.shift(1).rolling(48).mean()
s["hvdc_day"], s["tiwai_day"] = s.hvdc_north.shift(1).rolling(48).mean(), s.tiwai.shift(1).rolling(48).mean()
di = s.groupby("date").inflow.first()
s["inflow7"] = s.date.map(di.shift(1).rolling(7).mean())
s["inflow_hh"] = s.inflow * 1000 / s.groupby("date").inflow.transform("size")      # MWh of inflow energy per half-hour (daily GWh spread over the day)
s["dstor"] = s.storage.shift(-48) - s.storage                                       # not used in regressions (storage is daily)
s["temp_hh"] = s.temp
H = [1, 2, 4, 8, 24, 48, 96, 336, 672, 1440]
LAB = theirs.LAB


def wsum(x, h):
    cs = np.concatenate([[0.0], np.cumsum(x)])
    o = np.full(len(x), np.nan); o[: len(x) - h + 1] = cs[h:] - cs[: len(x) - h + 1]; return o


SRC = {"D": "D", "E": "E", "W": "wind", "Y": "hydro", "TH": "thermal", "C": "coal", "GS": "gas", "I": "inflow_hh", "T": "temp_hh", "HV": "hvdc_north", "TW": "tiwai"}
new = {f"{v}_{h}": wsum(s[src].values, h) for h in H for v, src in SRC.items()}
s = pd.concat([s, pd.DataFrame(new)], axis=1)
# storage at the end of the window's last day minus storage at the start (GWh -> MWh)
day_idx = s.groupby("date").ngroup().values
stor_by_day = s.groupby("date").storage.first().values
nd = len(stor_by_day)
def stor_change(h):
    # storage column is end-of-previous-day; storage at end of day d = storage column of day d+1
    end_day = day_idx + (h + 47) // 48      # the window's last day index
    end_day = np.minimum(end_day + 1, nd - 1)
    return (stor_by_day[end_day] - stor_by_day[np.minimum(day_idx + 1, nd - 1)]) * 1000
for h in H:
    s[f"S_{h}"] = stor_change(h)
need = ["zl4", "Dday", "inflow7", "hvdc_day", "storage", f"D_{max(H)}"]
IDX = np.where(s[need].notna().all(axis=1))[0]


def design(d):
    fe = [pd.get_dummies(d.hh.astype(str) + "_" + d.daytype.astype(str), dtype=float),
          pd.get_dummies(d.month, prefix="m", drop_first=True, dtype=float),
          pd.get_dummies(d.year, prefix="y", drop_first=True, dtype=float)]
    cont = d[["zl1", "zl2", "zl3", "zl4", "storage", "inflow7", "hvdc_day", "tiwai_day", "D1", "Dday", "E1", "Eday"]]
    cont = (cont - cont.mean()) / cont.std()
    return np.column_stack([pd.concat(fe, axis=1).values, cont.values])


def iv(idx, h, outcomes, extra=()):
    d = s.iloc[idx]
    X = np.column_stack([design(d), d[f"W_{h}"].values] + [d[f"{e}_{h}"].values for e in extra])
    q, _ = np.linalg.qr(X)
    def res(v): return v - q @ (q.T @ v)
    zr = res(d.z.values); Dr = res(d[f"D_{h}"].values)
    pi = (zr @ Dr) / (zr @ zr); u = Dr - pi * zr
    sc = pd.Series(zr * u).groupby(d.ym.values).sum().values
    r = dict(F=float((pi / (np.sqrt((sc ** 2).sum()) / (zr @ zr))) ** 2), pi_MWh_per_degree=float(pi))
    for o in outcomes:
        Yr = res(d[f"{o}_{h}"].values)
        b = float((zr @ Yr) / (zr @ Dr)); e = Yr - b * Dr
        sc2 = pd.Series(zr * e).groupby(d.ym.values).sum().values
        r[o] = b; r[f"{o}_se"] = float(np.sqrt((sc2 ** 2).sum()) / abs(zr @ Dr))
        # reduced form per unit of z
        r[f"{o}_rf_per_z"] = float((zr @ Yr) / (zr @ zr))
    return r


HS = [2, 8, 48, 96, 336, 672]
res = {}
for h in HS:
    base = iv(IDX, h, ["E", "Y", "TH", "C", "GS", "I", "S", "T", "HV", "TW"])
    infl = iv(IDX, h, ["E", "Y", "TH", "C", "GS"], extra=("I",))
    res[LAB[h]] = dict(baseline=base, window_inflow_controlled=infl)
    print(LAB[h], "base MEF", round(base["E"], 4), "F", round(base["F"], 1), "| inflow resp (MWh/MWh)", round(base["I"], 3), "+-", round(base["I_se"], 3),
          "| storage change resp", round(base["S"], 3), "+-", round(base["S_se"], 3), "| temp sum resp", round(base["T"], 4),
          "| hvdc resp", round(base["HV"], 3), "| tiwai resp", round(base["TW"], 3),
          "|| MEF with window inflow ctrl", round(infl["E"], 4), "F", round(infl["F"], 1), "hydro", round(infl["Y"], 3), "thermal", round(infl["TH"], 3))
out["by_horizon"] = res
# how persistent is the anomaly: autocorrelation of z at 1 d, 7 d, 14 d, 30 d; and R2 of the window-mean anomaly on z_t
z = s.z.values
out["z_autocorr"] = {lab: float(np.corrcoef(z[:-h], z[h:])[0, 1]) for h, lab in ((48, "1d"), (336, "7d"), (672, "14d"), (1440, "30d"))}
out["corr_z_with_window_mean_z"] = {LAB[h]: float(pd.Series(z).corr(pd.Series(wsum(z, h) / h))) for h in (48, 336, 672, 1440)}
json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps({k: out[k] for k in ("z_autocorr", "corr_z_with_window_mean_z")}, indent=1))
print("written", OUT)
