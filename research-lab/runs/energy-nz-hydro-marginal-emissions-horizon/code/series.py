"""Half-hourly national series and the emissions ledger (plan sections 2-3; deviation D1). Writes data/series.pkl
(one row per UTC half-hour, 2015-01-01 to 2024-12-31 local) and results/tables/ledger_calibration.csv.

Columns: ts (UTC), local date, hh (local half-hour of day 0-47), daytype (0 weekday, 1 Saturday, 2 Sunday/holiday),
month, year; D (total metered generation, MWh), hydro, wind, geo, solar, thermal (coal+gas+diesel), coal, gas, diesel
(MWh); E (t CO2, calibrated), E_raw (uncalibrated), E_geo05/E_geo15/E_rk70 (sensitivity ledgers, calibrated the same
way); tiwai (MWh), hvdc_north (MWh, Benmore export minus import); temp (population-weighted 2 m temperature, C);
storage (national controlled storage at the end of the previous local day, GWh); inflow (energy-weighted natural
inflow to the controlled lakes, GWh/day, same day)."""
import datetime as dt
import glob
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import holidays
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
NZ = ZoneInfo("Pacific/Auckland")
GAS, COAL, DIESEL = 54.14, 1.991 / 21.5 * 1000, 2.660 / 38.4 * 1000          # kg CO2 per GJ (D1)
HEAT = {"huntly_1_4": (10.3, "coal"), "huntly_e3p": (7.2, "gas"), "huntly_p40": (9.6, "gas"), "otahuhu_b": (7.0, "gas"),
        "southdown": (8.0, "gas"), "stratford": (8.0, "gas"), "McKee": (9.5, "gas"), "junctionroad": (9.5, "gas"),
        "te_rapa": (6.0, "gas"), "kapuni": (6.0, "gas"), "whareroa": (6.0, "gas"), "whirinaki": (11.0, "diesel"),
        "glenbrook_kilns": (0.0, "gas")}
FUELF = {"coal": COAL, "gas": GAS, "diesel": DIESEL}
GEO_EF = 0.10
CITIES = {"auckland": 1.70, "hamilton": 0.18, "wellington": 0.42, "christchurch": 0.39, "dunedin": 0.13}  # millions, approx. 2023
LAKE_INFLOW = {"TPO": "NI_TPO_Natural_LakeTaupo_Inflow", "WKA": "NI_WKA_Natural_LakeWaikaremoana_Inflow",
               "TKA": "SI_TEK_Natural_LakeTekapo_Inflow", "PKI": "SI_PKI_Natural_LakePukaki_Inflow", "OHA": "SI_OHU_Natural_LakeOhau_Inflow",
               "HWE": "SI_HWE_Natural_LakeHawea_Inflow", "WAN": "SI_WAN_Natural_LakeWanaka_Outflow",
               "MAN": "SI_MAN_Natural_LakeManapouri(NoMararoaSpill)_Inflow", "TAU": "SI_TAU_Natural_LakeTeAnau_Inflow"}


def utc_index(dates, tp):
    """UTC timestamp of trading period tp (1-based) on local trading date: local midnight in UTC plus (tp-1) half-hours."""
    mid = {d: dt.datetime.combine(dt.date.fromisoformat(d), dt.time(0), NZ).astimezone(dt.timezone.utc) for d in pd.unique(dates)}
    base = pd.to_datetime(pd.Series(dates).map(mid).values, utc=True)
    return base + pd.to_timedelta((np.asarray(tp) - 1) * 30, unit="min")


def long_tp(f, keep):
    d = pd.read_csv(f)
    canon = {k.lower(): k for k in keep}
    d = d.rename(columns={c: canon[c.lower()] for c in d.columns if c.lower() in canon})   # headers change case across years
    td = d.Trading_Date.astype(str)
    d["Trading_Date"] = np.where(td.str.contains("/"), pd.to_datetime(td, format="%d/%m/%Y", errors="coerce").dt.strftime("%Y-%m-%d"), td.str[:10])
    tps = [c for c in d.columns if re.fullmatch(r"TP\d+", c)]
    m = d.melt(id_vars=keep, value_vars=tps, var_name="tp", value_name="kwh").dropna(subset=["kwh"])
    m["tp"] = m.tp.str[2:].astype(int)
    return m


def generation():
    parts = []
    for f in sorted(glob.glob(str(RAW / "generation" / "*.csv"))):
        m = long_tp(f, ["Gen_Code", "Fuel_Code", "Trading_Date"])
        parts.append(m)
    g = pd.concat(parts)
    g["fuel"] = g.Fuel_Code.str.lower().map({"hydro": "hydro", "hyd": "hydro", "wind": "wind", "geo": "geo", "solar": "solar", "sol": "solar",
                                             "coal": "coal", "gas": "gas", "diesel": "diesel", "wood": "wood", "ele": "battery"}).fillna("other")
    g["ts"] = utc_index(g.Trading_Date.values, g.tp.values)
    g["mwh"] = g.kwh / 1000
    return g


def main():
    g = generation()
    unknown = sorted(set(g[g.fuel.isin(["coal", "gas", "diesel"])].Gen_Code) - set(HEAT))
    assert not unknown, f"thermal units without a heat rate: {unknown}"
    w = g.pivot_table(index="ts", columns="fuel", values="mwh", aggfunc="sum").fillna(0)
    out = pd.DataFrame(index=w.index)
    for c in ("hydro", "wind", "geo", "solar", "coal", "gas", "diesel", "wood", "battery", "other"):
        out[c] = w[c] if c in w else 0.0
    out["thermal"] = out.coal + out.gas + out.diesel
    out["D"] = w.sum(axis=1)
    th = g[g.fuel.isin(["coal", "gas", "diesel"])].copy()
    th["hr"] = th.Gen_Code.map(lambda u: HEAT[u][0]); th["ff"] = th.Gen_Code.map(lambda u: FUELF[HEAT[u][1]])
    th["t"] = th.mwh * th.hr * th.ff / 1000.0                                   # t CO2
    rk = th.Gen_Code == "huntly_1_4"
    th["t_rk70"] = np.where(rk, th.mwh * th.hr * (0.7 * COAL + 0.3 * GAS) / 1000.0, th.t)
    fossil = th.groupby("ts")[["t", "t_rk70"]].sum().reindex(out.index).fillna(0)
    # trading dates and local calendar
    loc = out.index.tz_convert(NZ)
    out["date"] = loc.date; out["hh"] = loc.hour * 2 + loc.minute // 30; out["month"] = loc.month; out["year"] = loc.year
    hol = holidays.country_holidays("NZ", years=range(2014, 2026))
    dow = loc.dayofweek
    out["daytype"] = np.where([d in hol for d in out.date], 2, np.where(dow == 6, 2, np.where(dow == 5, 1, 0)))
    out = out[(out.year >= 2015) & (out.year <= 2024)].copy()
    fossil = fossil.loc[out.index]
    # annual calibration to the MfE grid-average CO2 factor (D1)
    ef = pd.read_csv(RAW / "mfe" / "emission_factors_2026_v2_long.csv", encoding="utf-8-sig")
    ef = ef[(ef.SubSection == "Annual Averages") & (ef.GHG == "GHG_CO2_KGCO2_e") & ef.EmissionsFactorLabel.str.startswith("Electricity Used")]
    mfe = {int(l[-4:]): v for l, v in zip(ef.EmissionsFactorLabel, ef.EmissionFactor)}
    cal = []
    for name, fcol, geo in (("E", "t", GEO_EF), ("E_geo05", "t", 0.05), ("E_geo15", "t", 0.15), ("E_rk70", "t_rk70", GEO_EF)):
        e = pd.Series(0.0, index=out.index)
        for y, idx in out.groupby("year").groups.items():
            target = mfe[y] * out.loc[idx, "D"].sum()                          # t CO2 (kg/kWh x MWh = t)
            geo_t = geo * out.loc[idx, "geo"].sum()
            k = (target - geo_t) / fossil.loc[idx, fcol].sum()
            e.loc[idx] = k * fossil.loc[idx, fcol] + geo * out.loc[idx, "geo"]
            cal.append(dict(ledger=name, year=y, mfe_kg_per_kwh=mfe[y], scale=k, raw_t=float(fossil.loc[idx, fcol].sum() + geo_t), target_t=target))
        out[name] = e
    out["E_raw"] = fossil.t + GEO_EF * out.geo
    pd.DataFrame(cal).to_csv(RUN / "results" / "tables" / "ledger_calibration.csv", index=False)
    # Tiwai and HVDC
    tw = pd.concat([long_tp(f, ["POC", "Flow_Direction", "Trading_Date"]) for f in sorted(glob.glob(str(RAW / "tiwai" / "*.csv")))])
    tw = tw[tw.Flow_Direction == "X"]; tw["ts"] = utc_index(tw.Trading_Date.values, tw.tp.values)
    out["tiwai"] = tw.groupby("ts").kwh.sum().reindex(out.index) / 1000
    hv = pd.concat([long_tp(f, ["POC", "Flow_Direction", "Trading_Date"]) for f in sorted(glob.glob(str(RAW / "hvdc" / "*.csv")))])
    hv = hv[hv.POC == "BEN2201"]; hv["ts"] = utc_index(hv.Trading_Date.values, hv.tp.values)
    hv["s"] = np.where(hv.Flow_Direction == "X", 1, -1) * hv.kwh / 1000
    out["hvdc_north"] = hv.groupby("ts").s.sum().reindex(out.index)
    # temperature: hourly UTC, population-weighted, linear to half-hours
    temps = []
    for c, wgt in CITIES.items():
        j = json.load(open(RAW / "temperature" / f"{c}.json"))
        s = pd.Series(j["hourly"]["temperature_2m"], index=pd.to_datetime(j["hourly"]["time"], utc=True), dtype=float)
        temps.append(s * wgt)
    t = sum(temps) / sum(CITIES.values())
    t = t.resample("30min").interpolate("time")
    out["temp"] = t.reindex(out.index)
    # storage: energy = active storage (Mm3) x the lake's specific energy (GWh per Mm3, from the HMD capacity series)
    capf = glob.glob(str(RAW / "hmd" / "1_InfrastructureAndHydroConstraintAttributes" / "DerivedSeriesForStorageCapacityAndSpecificEnergy" / "20241231_*.csv"))[0]
    cap = pd.read_csv(capf).sort_values("Date").groupby("SiteCode").last()
    se = (cap.ActiveStorageCapacityScheme_GigaWattHours / cap.ActiveStorageCapacityScheme_MillionCubicMeters).to_dict()
    st = []
    for f in glob.glob(str(RAW / "hmd" / "3_StorageAndSpill_20241231" / "3_1_Storage" / "*_Storage_*.csv")):
        site = Path(f).name.split("_")[1]
        d = pd.read_csv(f, usecols=[0, 3]); d.columns = ["date", "mm3"]
        d["gwh"] = d.mm3 * se[site]; d["site"] = site
        st.append(d)
    st = pd.concat(st); st["date"] = pd.to_datetime(st.date).dt.date
    daily = st.pivot_table(index="date", columns="site", values="gwh", aggfunc="last").sort_index()
    nat = daily.interpolate(limit=3).sum(axis=1, min_count=daily.shape[1])
    prev = {d + dt.timedelta(1): v for d, v in nat.items()}
    out["storage"] = [prev.get(d, np.nan) for d in out.date]
    infl = []
    for site, stem in LAKE_INFLOW.items():
        f = [x for x in glob.glob(str(RAW / "hmd" / "2_Flows_20241231" / "*.csv")) if Path(x).name.startswith(stem)]
        assert len(f) == 1, (stem, f)
        d = pd.read_csv(f[0], usecols=[0, 2]); d.columns = ["date", "q"]
        d["gwh"] = d.q * 86400 / 1e6 * se[site]; d["date"] = pd.to_datetime(d.date).dt.date
        infl.append(d.groupby("date").gwh.mean().rename(site))
    inflow = pd.concat(infl, axis=1).sort_index().sum(axis=1, min_count=len(infl))
    out["inflow"] = [inflow.get(d, np.nan) for d in out.date]
    out["date"] = out.date.astype(str)
    out.reset_index().rename(columns={"index": "ts"}).to_pickle(RUN / "data" / "series.pkl")
    print(len(out), "half-hours;", out[["D", "E", "tiwai", "hvdc_north", "temp", "storage", "inflow"]].isna().sum().to_dict())
    print(pd.DataFrame(cal).query("ledger == 'E'")[["year", "scale"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
