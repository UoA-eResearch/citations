"""Reviewer check 2: the emissions ledger. Recomputes unit emissions from the raw generation files with the D1 heat
rates and fuel factors, the annual calibration, E consistency, the sensitivity ledgers and the quarterly check.
Writes out_ledger.json."""
import glob
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[2]
RAW = RUN / "data" / "raw"
OUT = Path(__file__).resolve().parent / "out_ledger.json"
out = {}

# D1 constants, typed independently from deviations.md
GAS = 54.14                       # kg/GJ
COAL = 1.991 / 21.5 * 1000        # 92.6 kg/GJ
DIESEL = 2.660 / 38.4 * 1000      # 69.3 kg/GJ
out["fuel_factors_kg_per_GJ"] = dict(gas=GAS, coal=COAL, diesel=DIESEL)
HR = {"huntly_1_4": (10.3, COAL), "huntly_e3p": (7.2, GAS), "huntly_p40": (9.6, GAS), "otahuhu_b": (7.0, GAS), "southdown": (8.0, GAS),
      "stratford": (8.0, GAS), "McKee": (9.5, GAS), "junctionroad": (9.5, GAS), "te_rapa": (6.0, GAS), "kapuni": (6.0, GAS),
      "whareroa": (6.0, GAS), "whirinaki": (11.0, DIESEL), "glenbrook_kilns": (0.0, GAS)}
out["implied_t_per_MWh_by_unit"] = {u: round(h * f / 1000, 3) for u, (h, f) in HR.items()}

s = pd.read_pickle(RUN / "data" / "series.pkl").sort_values("ts").reset_index(drop=True)
cal = pd.read_csv(RUN / "results" / "tables" / "ledger_calibration.csv")

# annual fossil emissions straight from the raw files (unit x year totals)
tot = {}
for f in sorted(glob.glob(str(RAW / "generation" / "*.csv"))):
    y = int(Path(f).stem[:4])
    d = pd.read_csv(f)
    d.columns = [c if not c.lower().startswith("trading") else "Trading_Date" for c in d.columns]
    tps = [c for c in d.columns if re.fullmatch(r"TP\d+", c)]
    th = d[d.Fuel_Code.str.lower().isin(["coal", "gas", "diesel"])]
    for u, g in th.groupby("Gen_Code"):
        tot.setdefault(y, {}).setdefault(u, 0.0)
        tot[y][u] += g[tps].sum().sum() / 1000.0  # MWh
raw_fossil_t = {}
raw_fossil_rk70 = {}
mwh_by_unit = {}
for y, units in tot.items():
    unk = sorted(set(units) - set(HR))
    assert not unk, unk
    raw_fossil_t[y] = sum(m * HR[u][0] * HR[u][1] / 1000 for u, m in units.items())
    raw_fossil_rk70[y] = sum(m * HR[u][0] * ((0.7 * COAL + 0.3 * GAS) if u == "huntly_1_4" else HR[u][1]) / 1000 for u, m in units.items())
    mwh_by_unit[y] = {u: round(m / 1000, 1) for u, m in units.items()}  # GWh
out["thermal_GWh_by_unit_year"] = mwh_by_unit

# note: the raw-file year is the trading-date year (local). series.pkl's 'year' is the local year of the UTC half-hour: identical.
ef = pd.read_csv(RAW / "mfe" / "emission_factors_2026_v2_long.csv", encoding="utf-8-sig")
ann = ef[(ef.SubSection == "Annual Averages") & (ef.GHG == "GHG_CO2_KGCO2_e") & ef.EmissionsFactorLabel.str.startswith("Electricity Used")]
mfe = {int(l[-4:]): float(v) for l, v in zip(ann.EmissionsFactorLabel, ann.EmissionFactor)}
rows = []
for y in range(2015, 2025):
    sy = s[s.year == y]
    D = sy.D.sum(); geo = sy.geo.sum()
    target = mfe[y] * D
    for name, fos, gf in (("E", raw_fossil_t[y], 0.10), ("E_geo05", raw_fossil_t[y], 0.05), ("E_geo15", raw_fossil_t[y], 0.15), ("E_rk70", raw_fossil_rk70[y], 0.10)):
        k = (target - gf * geo) / fos
        c = cal[(cal.ledger == name) & (cal.year == y)].iloc[0]
        # does the series' E for the year equal k * fossil + gf * geo, and does E/D reproduce the MfE factor?
        e_series = sy[name].sum()
        rows.append(dict(ledger=name, year=y, scale_mine=k, scale_theirs=float(c.scale), target_mine_t=target, target_theirs_t=float(c.target_t),
                         series_E_t=e_series, series_E_over_D_kg_per_kWh=e_series / D, mfe=mfe[y],
                         fossil_raw_mine_t=fos, raw_t_theirs=float(c.raw_t), raw_mine_incl_geo=fos + gf * geo))
cmp = pd.DataFrame(rows)
out["calibration_compare"] = cmp.round(6).to_dict(orient="records")
out["max_abs_scale_diff"] = float((cmp.scale_mine - cmp.scale_theirs).abs().max())
out["max_rel_E_over_D_vs_mfe"] = float(((cmp.series_E_over_D_kg_per_kWh - cmp.mfe) / cmp.mfe).abs().max())

# E_raw consistency: E_raw should be the uncalibrated fossil + 0.10 * geo
chk = s.groupby("year").apply(lambda g: pd.Series(dict(E_raw=g.E_raw.sum(), E=g.E.sum(), geo=g.geo.sum())))
chk["fossil_raw_mine"] = pd.Series(raw_fossil_t)
chk["E_raw_mine"] = chk.fossil_raw_mine + 0.10 * chk.geo
out["E_raw_consistency_max_rel_diff"] = float(((chk.E_raw - chk.E_raw_mine) / chk.E_raw_mine).abs().max())

# within-year: E/E_raw ratio must be constant within a year (one scale per year), and E_geo05 etc. share the same geo term structure
r = (s.E - 0.10 * s.geo) / (s.E_raw - 0.10 * s.geo)
r = r[(s.E_raw - 0.10 * s.geo) > 1]
out["within_year_scale_constant"] = {int(y): [float(v.min()), float(v.max())] for y, v in r.groupby(s.year)}

# AEF and thermal intensity
s["aef"] = s.E / s.D
out["aef_mean"] = float(s.aef.mean()); out["aef_by_block"] = s.groupby(s.hh // 12).aef.mean().round(4).to_dict()
out["fossil_t_per_thermal_MWh_by_year"] = ((s.E - 0.10 * s.geo).groupby(s.year).sum() / s.thermal.groupby(s.year).sum()).round(3).to_dict()
out["geo_share_of_E_by_year"] = ((0.10 * s.geo).groupby(s.year).sum() / s.E.groupby(s.year).sum()).round(3).to_dict()

# quarterly check recomputed
q = ef[(ef.SubSection == "Quarterly Averages") & (ef.GHG == "GHG_CO2_KGCO2_e")]
mon = {"Mar": 1, "Jun": 2, "Sep": 3, "Dec": 4}
qrows = []
for lab, v in zip(q.EmissionsFactorLabel, q.EmissionFactor):
    k = lab.split(" - ")[1]; qq, yy = mon[k[:3]], int(k[-4:])
    if yy > 2024:
        continue
    sel = s[(s.year == yy) & (((s.month - 1) // 3 + 1) == qq)]
    led = sel.E.sum() / sel.D.sum()
    qrows.append(dict(quarter=f"{yy}Q{qq}", mfe=float(v), ledger=float(led), diff=float(led - float(v)), within_0_01=bool(abs(led - float(v)) < 0.01)))
qrows = sorted(qrows, key=lambda r: r["quarter"])
out["quarterly_check"] = qrows
out["quarters_within_0_01"] = sum(r["within_0_01"] for r in qrows)
# the annual calibration forces the generation-weighted mean of the four quarters to the annual factor, so quarterly errors sum to ~0 within a year
for yy in (2023, 2024):
    sub = [r for r in qrows if r["quarter"].startswith(str(yy))]
    out[f"quarterly_mean_diff_{yy}"] = float(np.mean([r["diff"] for r in sub]))
# RMSE of the ledger's quarterly shape vs MfE, relative to the MfE quarterly spread
out["quarterly_rmse"] = float(np.sqrt(np.mean([r["diff"] ** 2 for r in qrows])))
out["quarterly_mfe_std"] = float(np.std([r["mfe"] for r in qrows]))

# how the Huntly Rankine coding affects the "coal" vs "gas" labels: Rankine share of 'coal' series, and of fossil E
out["coal_series_is_huntly_1_4_only"] = bool(all(set(k for k in mwh_by_unit[y] if k == "huntly_1_4") == {"huntly_1_4"} for y in mwh_by_unit))
out["coal_GWh_series_vs_huntly_1_4_raw"] = {y: [float(s[s.year == y].coal.sum() / 1000), mwh_by_unit[y].get("huntly_1_4", 0)] for y in range(2015, 2025)}

json.dump(out, open(OUT, "w"), indent=1, default=float)
print(json.dumps({k: out[k] for k in out if k not in ("calibration_compare", "thermal_GWh_by_unit_year")}, indent=1, default=float))
print(cmp[["ledger", "year", "scale_mine", "scale_theirs", "series_E_over_D_kg_per_kWh", "mfe"]].round(5).to_string(index=False))
print(pd.DataFrame(mwh_by_unit).T.fillna(0).round(0).to_string())
