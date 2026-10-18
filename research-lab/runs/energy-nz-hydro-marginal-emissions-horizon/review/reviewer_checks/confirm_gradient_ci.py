"""Confirmation check: bootstrap intervals of MEF(7 d) - MEF(1 h) and MEF(1 d) - MEF(1 h) under each of the 17
specifications in code/sensitivity.py (whose fit() returns the draws). Writes out_confirm_gradient_ci.json."""
import json, sys
from pathlib import Path
import numpy as np
RUN = Path(__file__).resolve().parents[2]; HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(RUN / "code"))
import sensitivity as S
s, idx = S.prepare()
BASE, LAGS_D, LAGS_E, FUEL, ZHIST, HS = S.BASE, S.LAGS_D, S.LAGS_E, S.FUEL, S.ZHIST, S.HS
nolag = [c for c in BASE if c not in LAGS_D + LAGS_E]
specs = {
    "preregistered": dict(cont=BASE), "no lagged D/E": dict(cont=nolag),
    "D lags only": dict(cont=[c for c in BASE if c not in LAGS_E]), "E lags only": dict(cont=[c for c in BASE if c not in LAGS_D]),
    "D, E and fuel lags": dict(cont=BASE + FUEL),
    "no lagged outcomes, 3 days of anomaly history": dict(cont=[c for c in nolag if not c.startswith("zl")] + ZHIST),
    "preregistered + window inflow": dict(cont=BASE, window=("W", "I")),
    "no lagged D/E + window inflow": dict(cont=nolag, window=("W", "I")),
    "3 days of anomaly history + window inflow": dict(cont=[c for c in nolag if not c.startswith("zl")] + ZHIST, window=("W", "I")),
    "no wind-window control": dict(cont=BASE, window=()), "half-hour x month fixed effects": dict(cont=BASE, hhmonth=True),
    "calendar-aligned climatology": dict(cont=BASE, zcol="z_cal"), "7-day-mean instrument": dict(cont=BASE, zcol="z_7d"),
    "next-24-h-mean instrument": dict(cont=BASE, zcol="z_24h"),
}
yr = s.year.values[idx]
subs = {"drop 2021 and 2024": ~np.isin(yr, [2021, 2024]), "2015-2019": yr <= 2019, "2020-2024": yr >= 2020}
out = {}
def ci(x): return [round(float(np.percentile(x, 2.5)), 3), round(float(np.percentile(x, 97.5)), 3)]
for name, sp in list(specs.items()) + [(k, None) for k in subs]:
    ii = idx if sp is not None else idx[subs[name]]
    sp = sp or dict(cont=BASE)
    r = S.fit(s, ii, HS, sp["cont"], sp.get("zcol", "z"), sp.get("window", ("W",)), hhmonth=sp.get("hhmonth", False))
    d1, d2, d336 = r["2"]["E_draws"], r["48"]["E_draws"], r["336"]["E_draws"]
    out[name] = dict(d_7d_1h=round(r["336"]["E"] - r["2"]["E"], 3), ci_7d_1h=ci(d336 - d1), share_pos_7d=round(float(np.mean(d336 > d1)), 3),
                     d_1d_1h=round(r["48"]["E"] - r["2"]["E"], 3), ci_1d_1h=ci(d2 - d1), share_pos_1d=round(float(np.mean(d2 > d1)), 3))
    print(f"{name:48s} 7d-1h {out[name]['d_7d_1h']:7.3f} {out[name]['ci_7d_1h']}  1d-1h {out[name]['d_1d_1h']:7.3f} {out[name]['ci_1d_1h']}", flush=True)
json.dump(out, open(HERE / "out_confirm_gradient_ci.json", "w"), indent=1)
n7 = sum(v["ci_7d_1h"][0] > 0 for v in out.values()); n1 = sum(v["ci_1d_1h"][0] > 0 for v in out.values())
print(f"specs with 95% interval of 7d-1h above zero: {n7}/17; of 1d-1h: {n1}/17")
