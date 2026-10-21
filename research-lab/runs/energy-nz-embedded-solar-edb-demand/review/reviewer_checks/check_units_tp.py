"""Reviewer check: (1) offtake series of the two identifying units and HEDL; (2) H4 with non-solar DG capacity as a
control; (3) trading-period alignment from EA Networks' GXP after the Lauriston farm; (4) zero-midday anomalies at
large GXPs."""
import sys, json, numpy as np, pandas as pd
from pathlib import Path
RUN = "/mnt/citations/research-lab/runs/energy-nz-embedded-solar-edb-demand"; RAW = Path("/mnt/data/edb-solar/raw/emi")
sys.path.insert(0, RUN + "/code")
from analysis import fe_ols, spec
import build_panel as bp
s = pd.read_csv(RUN + "/results/tables/panel_summer.csv")
for u in ("TOPE", "EASH", "HEDL"):
    r = s[s.unit == u].set_index("summer")
    print(u, "mid MW by summer:", r.mid_mw.round(0).astype(int).to_dict()); print("     night MW:", r.night_mw.round(0).astype(int).to_dict()); print("     solar MW:", r.solar_all_mw.round(1).to_dict())
# (2) non-solar DG per ICP as a control in H4
cap = bp.capacity(); log = json.load(open(RUN + "/results/tables/panel_log.json"))
unit = {pid: u for u, ms in log["h4_units"].items() for pid in ms}
c = cap[cap.pid.isin(bp.PARTICIPANT)].copy(); c["unit"] = c.pid.map(unit)
c = c[c.month.dt.month.isin([12,1,2])]; c["summer"] = c.month.dt.year - (c.month.dt.month <= 2)
e = c.groupby(["unit","summer","month"]).nonsolar_dg_mw.sum().groupby(["unit","summer"]).mean().reset_index()
s = s.merge(e, on=["unit","summer"], how="left")
for col in ("mid", "eve", "night", "solar_all", "nonsolar_dg"):
    s[col + "_pi"] = s[col + "_mw"] * 1000 / s.icps
print("TOPE non-solar DG MW by summer:", s[s.unit=="TOPE"].set_index("summer").nonsolar_dg_mw.round(0).astype(int).to_dict())
for y in ("mid_pi", "eve_pi", "night_pi"):
    r = spec(s, y, "solar_all_pi", ["tmax", "nonsolar_dg_pi"], unit="unit", time="summer")
    print(f"  H4 {y:9s} with non-solar DG/ICP control: est {r['estimate']:+.3f} ci [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]")
s["mmn"] = s.mid_pi - s.night_pi; s["mme"] = s.mid_pi - s.eve_pi
for y in ("mmn", "mme"):
    r = spec(s, y, "solar_all_pi", ["tmax", "nonsolar_dg_pi"], unit="unit", time="summer")
    print(f"  {y} with non-solar DG/ICP control: est {r['estimate']:+.3f} ci [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]")
# (3) TP alignment: EASH's GXP(s)
def load(kind, ym):
    x = pd.read_csv(RAW / kind / f"{ym}_{kind}.csv", dtype=str); x.columns = [c.upper() for c in x.columns]
    return x[(x.GENERATION_TYPE == "GN") & (x.UNIT_MEASURE.str.lower() == "kwh")]
pocs = load("Grid_export", "202512").query("NWK_CODE == 'EASH'").POC.unique().tolist(); print("EASH GN POCs:", pocs)
for ym in ("202312", "202412", "202501", "202512", "202602"):
    prof = {}
    for kind in ("Grid_export", "Grid_import"):
        try:
            x = load(kind, ym); x = x[x.POC.isin(pocs)]
        except FileNotFoundError:
            x = pd.DataFrame()
        prof[kind] = (x[[f"TP{k}" for k in range(1, 49)]].astype(float).mean().to_numpy() / 500.0) if len(x) else np.zeros(48)
    net = prof["Grid_export"] - prof["Grid_import"]; k = int(np.argmin(net[19:36])) + 20
    print(f"{ym} EASH net MW: min at TP{k} ({(k-1)/2:.1f}-{k/2:.1f} clock); TP22-33: {np.round(net[21:33],0).astype(int).tolist()}; TP37-42 (18-21h): {np.round(net[36:42],0).astype(int).tolist()}; TP5-10: {np.round(net[4:10],0).astype(int).tolist()}")
# (4) zero-midday anomalies at large GXPs in panel networks
rows = []
for y in range(2014, 2026):
    for ym in (f"{y}12", f"{y+1}01", f"{y+1}02"):
        x = load("Grid_export", ym); x = x[x.NWK_CODE.isin(bp.PARTICIPANT)]
        x["mid"] = x[[f"TP{k}" for k in range(25, 31)]].apply(pd.to_numeric, errors="coerce").sum(axis=1)
        rows.append(x[["POC", "NWK_CODE", "TRADING_DATE", "mid"]].assign(summer=y))
m = pd.concat(rows); med = m.groupby("POC").mid.median()
m["big"] = m.POC.map(med) > 30000     # > 10 MW average midday
z = m[m.big & (m.mid == 0)]
print("zero-midday days at POCs whose median midday > 10 MW:", len(z), "of", int(m.big.sum()), "big POC-days")
print(z.groupby(["NWK_CODE", "summer"]).size().sort_values(ascending=False).head(12).to_dict())
