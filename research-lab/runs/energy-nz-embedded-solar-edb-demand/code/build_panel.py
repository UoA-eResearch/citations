"""Build the distributor-year panel (H1-H3) and the network-summer panel (H4) of plan section 2.

Writes results/tables/panel_annual.csv, results/tables/panel_summer.csv and results/tables/panel_log.json (unmatched
participants, merged units, coverage). Run after fetch.py.
"""
import io
import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import weather  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
OUT = RUN / "results" / "tables"
YEARS = range(2015, 2026)                          # disclosure years (April-March), DY2015 = Apr 2014 - Mar 2015
SUMMERS = range(2014, 2026)

# Electricity Authority network participant ID -> Commerce Commission distributor name (29 non-embedded networks)
PARTICIPANT = {
    "ALPE": "Alpine Energy", "DUNE": "Aurora Energy", "BUEL": "Buller Electricity", "CHBP": "Centralines",
    "COUP": "Counties Energy", "EASH": "EA Networks", "ELEC": "Electra", "ELIN": "Electricity Invercargill",
    "EAST": "Firstlight Network", "HEDL": "Horizon Networks", "MPOW": "MainPower NZ", "MARL": "Marlborough Lines",
    "NELS": "Nelson Electricity", "TASM": "Network Tasman", "WATA": "Network Waitaki", "NPOW": "Northpower",
    "ORON": "Orion NZ", "OTPO": "OtagoNet", "POCO": "Powerco", "SCAN": "Scanpower", "LINE": "The Lines Company",
    "TPCO": "The Power Company", "TOPE": "Top Energy", "HAWK": "Unison Networks", "VECT": "Vector Lines",
    "WAIK": "WEL Networks", "WAIP": "Waipa Networks", "CKHK": "Wellington Electricity", "WPOW": "Westpower",
}
MEASURES = {   # Schedule 9e(ii) description -> column
    "Total energy delivered to ICPs": "delivered_gwh",
    "Electricity entering system for supply to consumers' connection points": "entering_gwh",
    "Electricity supplied from distributed generation": "dg_supplied_gwh",
    "Electricity supplied from GXPs": "gxp_gwh",
    "Electricity exports to GXPs": "gxp_export_gwh",
    "Maximum coincident system demand": "peak_mw",
}
KWH_PER_ICP = "Total energy delivered to ICPs per average number of ICPs (kWh/ICP)"


def disclosure():
    t = pq.read_table(RAW / "comcom" / "EDB_ID_Full_2026-06-01.parquet",
                      columns=["edb", "network", "disc_yr", "schedule", "section", "category", "description",
                               "source", "value", "obs_yr", "fcast_yr"]).to_pandas()
    t = t[(t.network == "All") & t.source.str.contains("end", case=False, na=False) & t.disc_yr.isin(YEARS)]
    s9 = t[t.section.str.startswith("9e(ii)", na=False) & t.description.isin(MEASURES)]
    if s9.duplicated(["edb", "disc_yr", "category", "description"]).any():
        raise SystemExit("duplicate 9e(ii) rows: the measure is not unique per distributor-year")
    d = s9.pivot_table(index=["edb", "disc_yr"], columns="description", values="value", aggfunc="first")
    d = d.rename(columns=MEASURES).reset_index()
    r = t[t.section.str.startswith("1(iii)", na=False) & (t.description == KWH_PER_ICP)]
    r = r.groupby(["edb", "disc_yr"]).value.first().rename("kwh_per_icp").reset_index()
    d = d.merge(r, on=["edb", "disc_yr"], how="left")
    d["icps"] = d.delivered_gwh * 1e6 / d.kwh_per_icp
    d["grid_net_gwh"] = d.entering_gwh - d.dg_supplied_gwh
    d["disc_yr"] = d.disc_yr.astype(int)
    return d


def ea(name):
    lines = (RAW / "ea" / name).read_text().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("Month end,"))
    x = pd.read_csv(io.StringIO("\n".join(lines[i:])))
    x["month"] = pd.to_datetime(x["Month end"], dayfirst=True)
    x = x.rename(columns={"Region ID": "pid", "Total capacity installed (MW)": "mw", "ICP count": "icp_count",
                          "ICP uptake rate (%)": "uptake_pct"})
    return x[["pid", "month", "mw", "icp_count", "uptake_pct"]]


def capacity():
    """Monthly MW per participant for each exposure series."""
    seg = {s: ea(f"solar_{s}_All_Total.csv")[["pid", "month", "mw"]].rename(columns={"mw": s})
           for s in ("All", "Res", "Com", "Ind")}
    m = seg["All"]
    for s in ("Res", "Com", "Ind"):
        m = m.merge(seg[s], on=["pid", "month"], how="outer")
    m = m.fillna(0.0)
    m["btm_mw"] = m.Res + m.Com                                    # behind-the-meter (H2, H3)
    m["solar_all_mw"] = m.All                                      # all distribution-connected (H1, H4)
    m["res_mw"] = m.Res
    dg = ea("dg_All_All_All_Total.csv")[["pid", "month", "mw"]].rename(columns={"mw": "dg_all"})
    bat = ea("dg_All_All_standalonebatt.csv")[["pid", "month", "mw"]].rename(columns={"mw": "bat"})
    m = m.merge(dg, on=["pid", "month"], how="left").merge(bat, on=["pid", "month"], how="left").fillna(0.0)
    m["nonsolar_dg_mw"] = (m.dg_all - m.All - m.bat).clip(lower=0)
    return m[["pid", "month", "btm_mw", "solar_all_mw", "res_mw", "nonsolar_dg_mw"]]


def annual_exposure(cap):
    c = cap[cap.pid.isin(PARTICIPANT)].copy()
    c["edb"] = c.pid.map(PARTICIPANT)
    c["disc_yr"] = c.month.dt.year + (c.month.dt.month >= 4)
    cols = ["btm_mw", "solar_all_mw", "res_mw", "nonsolar_dg_mw"]
    g = c.groupby(["edb", "disc_yr"]).agg(**{k: (k, "mean") for k in cols}, months=("month", "nunique")).reset_index()
    return g


def summer_panel(cap, log):
    nsp = pd.read_csv(RAW / "emi" / "20261020_NetworkSupplyPointsTable.csv")
    rows = []
    for y in SUMMERS:
        for ym in (f"{y}12", f"{y + 1}01", f"{y + 1}02"):
            # EMI names flows from the grid's side: Grid_export (flow X) leaves the grid into a network (offtake);
            # Grid_import (flow I) enters the grid from it (embedded generation spilling upstream). Net offtake is
            # export minus import, at grid-exit (GN) points of connection only. Column case changed in 2020.
            for kind, sign in (("Grid_export", 1.0), ("Grid_import", -1.0)):
                x = pd.read_csv(RAW / "emi" / kind / f"{ym}_{kind}.csv", dtype=str)
                x.columns = [c.upper() for c in x.columns]
                x = x.rename(columns={"NWK_CODE": "NWK_Code"})
                tps = [f"TP{k}" for k in range(25, 31)]
                x = x[(x.UNIT_MEASURE.str.lower() == "kwh") & (x.GENERATION_TYPE == "GN")].copy()
                x["mid_kwh"] = x[tps].apply(pd.to_numeric, errors="coerce").sum(axis=1)
                x["date"] = pd.to_datetime(x.TRADING_DATE, format="mixed", dayfirst=True)
                g = x.groupby(["POC", "NWK_Code", "date"]).mid_kwh.sum().reset_index()
                g["mid_kwh"] *= sign
                g["summer"] = y
                rows.append(g)
    m = pd.concat(rows, ignore_index=True)
    m = m.groupby(["summer", "POC", "NWK_Code", "date"]).mid_kwh.sum().reset_index()
    # a POC recorded under more than one network code is shared: merge those networks into one unit
    codes = m.groupby("POC").NWK_Code.unique()
    shared = {p: sorted(c) for p, c in codes.items() if len(c) > 1}
    unit = {pid: pid for pid in PARTICIPANT}
    for p, cs in shared.items():
        cs = [c for c in cs if c in PARTICIPANT]
        root = min(unit[c] for c in cs) if cs else None
        for c in cs:
            old = unit[c]
            for k, v in unit.items():
                if v == old:
                    unit[k] = root
    log["h4_shared_pocs"] = shared
    log["h4_units"] = {u: sorted(k for k, v in unit.items() if v == u) for u in sorted(set(unit.values()))}
    m = m[m.NWK_Code.isin(PARTICIPANT)]
    m["unit"] = m.NWK_Code.map(unit)
    day = m.groupby(["unit", "summer", "date"]).mid_kwh.sum().reset_index()
    out = day.groupby(["unit", "summer"]).agg(mid_mwh_day=("mid_kwh", lambda v: v.mean() / 1000),
                                              days=("date", "nunique")).reset_index()
    out["mid_mw"] = out.mid_mwh_day / 3.0                       # six half-hours = 3 hours
    c = cap[cap.pid.isin(PARTICIPANT)].copy()
    c["unit"] = c.pid.map(unit)
    c = c[c.month.dt.month.isin([12, 1, 2])]
    c["summer"] = c.month.dt.year - (c.month.dt.month <= 2)
    e = c.groupby(["unit", "summer", "month"]).solar_all_mw.sum().groupby(["unit", "summer"]).mean()
    out = out.merge(e.rename("solar_all_mw").reset_index(), on=["unit", "summer"], how="left")
    # ICPs for H4 from the Authority's registry (ICPs with solar / uptake rate), so that summer 2025/26, which falls in
    # a disclosure year not yet published, has them too
    r = ea("solar_All_All_Total.csv")
    r = r[r.pid.isin(PARTICIPANT) & (r.uptake_pct > 0) & r.month.dt.month.isin([12, 1, 2])].copy()
    r["icps"] = r.icp_count / (r.uptake_pct / 100)
    r["unit"] = r.pid.map(unit)
    r["summer"] = r.month.dt.year - (r.month.dt.month <= 2)
    i = r.groupby(["unit", "summer", "month"]).icps.sum().groupby(["unit", "summer"]).mean()
    out = out.merge(i.rename("icps").reset_index(), on=["unit", "summer"], how="left")
    return out


def main():
    log = {}
    d = disclosure()
    cap = capacity()
    log["participants_excluded"] = sorted(set(cap.pid) - set(PARTICIPANT))
    log["participants_missing"] = sorted(set(PARTICIPANT) - set(cap.pid))
    a = d.merge(annual_exposure(cap), on=["edb", "disc_yr"], how="left")
    hdd, tmax = weather.controls()
    a = a.merge(hdd, on=["edb", "disc_yr"], how="left")
    log["annual_rows"] = len(a)
    log["annual_missing"] = {c: int(a[c].isna().sum()) for c in a.columns if a[c].isna().any()}
    log["distributors"] = int(a.edb.nunique())
    a.to_csv(OUT / "panel_annual.csv", index=False)
    s = summer_panel(cap, log)
    edb_unit = {}
    for u, members in log["h4_units"].items():
        for pid in members:
            edb_unit[PARTICIPANT[pid]] = u
    tmax["unit"] = tmax.edb.map(edb_unit)
    s = s.merge(tmax.groupby(["unit", "summer"]).tmax.mean().reset_index(), on=["unit", "summer"], how="left")
    log["summer_rows"] = len(s)
    s.to_csv(OUT / "panel_summer.csv", index=False)
    json.dump(log, open(OUT / "panel_log.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in log.items() if k != "h4_units"}, indent=1)[:3000])


if __name__ == "__main__":
    main()
