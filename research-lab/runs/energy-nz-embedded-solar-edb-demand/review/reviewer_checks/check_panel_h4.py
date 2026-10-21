"""Reviewer check: panel sanity, report numbers, H4 leverage and extra variants (farm units, btm-only, lead placebo,
jump filter, LOO on the contrasts). Uses the study's own fe_ols / fast_bootstrap."""
import sys, json
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/energy-nz-embedded-solar-edb-demand"
sys.path.insert(0, RUN + "/code")
from analysis import fe_ols, fast_bootstrap, summarise, spec, per_icp
a = pd.read_csv(RUN + "/results/tables/panel_annual.csv")
s = pd.read_csv(RUN + "/results/tables/panel_summer.csv")
print("annual cols:", list(a.columns)); print("summer cols:", list(s.columns))
# report's installed table
for y in (2015, 2020, 2025):
    r = a[a.disc_yr == y]
    print(y, "btm", round(r.btm_mw.sum()), "all", round(r.solar_all_mw.sum()), "delivered", round(r.delivered_gwh.sum()), "n", len(r), "months", r.months.unique().tolist())
# grid_net vs gxp - gxp_export
a["gn2"] = a.gxp_gwh - a.gxp_export_gwh
d = (a.grid_net_gwh - a.gn2)
print("grid_net - (gxp - gxp_export): abs>1 GWh rows:", int((d.abs() > 1).sum()), "of", int(d.notna().sum()), "; worst:", a.assign(d=d).sort_values("d", key=abs, ascending=False)[["edb","disc_yr","grid_net_gwh","gn2","d"]].head(5).round(1).values.tolist())
# summer panel sanity
print("days per unit-summer:", s.days.value_counts().sort_index().to_dict())
print("missing in summer panel:", s.isna().sum()[s.isna().sum() > 0].to_dict())
s["solar_pi"] = s.solar_all_mw * 1000 / s.icps; s["mid_pi"] = s.mid_mw * 1000 / s.icps
s["eve_pi"] = s.eve_mw * 1000 / s.icps; s["night_pi"] = s.night_mw * 1000 / s.icps
s["solar_all_pi"] = s.solar_pi
last = s[s.summer == 2025].sort_values("solar_pi", ascending=False)
print("2025/26: unit, solar MW, ICPs, kW/ICP, mid MW, eve MW, night MW:\n", last[["unit","solar_all_mw","icps","solar_pi","mid_mw","eve_mw","night_mw"]].round(2).to_string(index=False))
# weighted leverage on the within-transformed exposure
def within(df, col, w):
    x = df[col].copy()
    for _ in range(20):
        x = x - x.groupby(df.unit).transform(lambda v: np.average(v, weights=df.loc[v.index, w]))
        x = x - x.groupby(df.summer).transform(lambda v: np.average(v, weights=df.loc[v.index, w]))
    return x
s["xt"] = within(s, "solar_pi", "icps")
lev = (s.icps * s.xt**2).groupby(s.unit).sum(); lev = (lev / lev.sum()).sort_values(ascending=False)
print("share of weighted within-variance of solar/ICP by unit:", lev.head(6).round(3).to_dict())
def run(df, y, name, x="solar_all_pi", c=("tmax",), w="icps"):
    r = spec(df, y, x, list(c), unit="unit", time="summer", w=w)
    print(f"  {name:48s} est {r['estimate']:+.3f}  ci [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]  n={r['n']}")
    return r
print("H4 variants:")
run(s, "mid_pi", "preregistered (reproduce)")
run(s[~s.unit.isin(["EASH","TOPE"])], "mid_pi", "drop EASH and TOPE")
run(s[~s.unit.isin(["EASH","TOPE","MARL","HEDL","NPOW","ORON","POCO"])], "mid_pi", "drop 7 farm units")
run(s[s.summer <= 2023], "mid_pi", "summers to 2023/24 only")
# btm vs industrial exposure: need segment capacity by unit-summer -> rebuild from EA files via build_panel.capacity
import build_panel as bp
cap = bp.capacity(); log = json.load(open(RUN + "/results/tables/panel_log.json"))
unit = {pid: u for u, ms in log["h4_units"].items() for pid in ms}
c = cap[cap.pid.isin(bp.PARTICIPANT)].copy(); c["unit"] = c.pid.map(unit)
c = c[c.month.dt.month.isin([12,1,2])]; c["summer"] = c.month.dt.year - (c.month.dt.month <= 2)
c["ind_mw"] = c.solar_all_mw - c.btm_mw
e = c.groupby(["unit","summer","month"])[["btm_mw","ind_mw"]].sum().groupby(["unit","summer"]).mean().reset_index()
s = s.merge(e, on=["unit","summer"], how="left")
s["btm_pi"] = s.btm_mw * 1000 / s.icps; s["ind_pi"] = s.ind_mw * 1000 / s.icps
print("  check: btm+ind vs solar_all max abs diff MW:", round((s.btm_mw + s.ind_mw - s.solar_all_mw).abs().max(), 3))
run(s, "mid_pi", "exposure = behind-the-meter only", x="btm_pi")
run(s, "mid_pi", "exposure = industrial only", x="ind_pi")
r = spec(s, "mid_pi", "btm_pi", ["ind_pi", "tmax"], unit="unit", time="summer"); print(f"  {'btm with ind as control (btm coef)':48s} est {r['estimate']:+.3f}  ci [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]")
r = spec(s, "mid_pi", "ind_pi", ["btm_pi", "tmax"], unit="unit", time="summer"); print(f"  {'ind with btm as control (ind coef)':48s} est {r['estimate']:+.3f}  ci [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]")
# lead placebo for H4: solar two summers ahead alongside current
ld = s[["unit","summer","solar_all_pi"]].copy(); ld["summer"] -= 2; ld = ld.rename(columns={"solar_all_pi":"lead2_pi"})
s2 = s.merge(ld, on=["unit","summer"], how="left").dropna(subset=["lead2_pi"])
r = spec(s2, "mid_pi", "lead2_pi", ["solar_all_pi","tmax"], unit="unit", time="summer"); print(f"  {'lead-2 placebo coefficient (midday)':48s} est {r['estimate']:+.3f}  ci [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]  n={r['n']}")
r = spec(s2, "night_pi", "lead2_pi", ["solar_all_pi","tmax"], unit="unit", time="summer"); print(f"  {'lead-2 placebo coefficient (night)':48s} est {r['estimate']:+.3f}  ci [{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]")
# jump filter (plan s4) applied to H4
sd = s.sort_values(["unit","summer"]).copy(); sd["jump"] = np.log(sd.mid_mw).groupby(sd.unit).diff().abs()
print("  unit-summers with |dlog mid| > 0.15:", sd[sd.jump > 0.15][["unit","summer","jump"]].round(2).values.tolist())
run(sd[~(sd.jump > 0.15)], "mid_pi", "drop unit-summers with midday jump > 15%")
# contrasts, LOO and without farm units
s["mme"] = s.mid_pi - s.eve_pi; s["mmn"] = s.mid_pi - s.night_pi
for y, nm in (("mme","mid-eve"),("mmn","mid-night"),("eve_pi","eve"),("night_pi","night")):
    loo = {u: round(fe_ols(s[s.unit != u], y, "solar_all_pi", ["tmax"], "unit", "summer", "icps")[0], 3) for u in sorted(s.unit.unique())}
    v = pd.Series(loo); print(f"  LOO {nm:10s} range [{v.min():+.3f}, {v.max():+.3f}]  most influential: {v.sub(fe_ols(s, y, 'solar_all_pi', ['tmax'], 'unit', 'summer', 'icps')[0]).abs().sort_values(ascending=False).head(3).round(3).to_dict()}")
run(s[~s.unit.isin(["EASH","TOPE"])], "mme", "mid-eve, drop EASH and TOPE")
run(s[~s.unit.isin(["EASH","TOPE"])], "mmn", "mid-night, drop EASH and TOPE")
run(s[~s.unit.isin(["EASH","TOPE"])], "night_pi", "night placebo, drop EASH and TOPE")
run(s[~s.unit.isin(["EASH","TOPE"])], "eve_pi", "eve placebo, drop EASH and TOPE")
run(s, "mme", "mid-eve, exposure btm only", x="btm_pi"); run(s, "mmn", "mid-night, exposure btm only", x="btm_pi")
# how large is the night slope relative to night load: night MW per ICP typical
print("typical kW/ICP: mid", round(s.mid_pi.median(),3), "eve", round(s.eve_pi.median(),3), "night", round(s.night_pi.median(),3))
