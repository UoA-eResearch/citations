"""The interruption panel (plan section 1).

  panel.py load     the three interruption sources -> data/interim/{dpp3,dpp4,id2025}.parquet (common columns)
  panel.py check    overlap agreement 2014-2019, Centralines/Unison, 2025 class identification
                    -> results/tables/panel_checks.json
  panel.py build    the spliced unplanned panel -> data/interim/unplanned.parquet, results/tables/panel_annual.csv

Common columns: edb, disc_yr, start (naive local time), pu (planned/unplanned), saidi, saifi, icp_min.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
COM = RAW / "comcom"
INT = RUN / "data" / "interim"
T = RUN / "results" / "tables"
ALIAS = {"Eastland Network": "Firstlight Network"}


def _ts(v):
    """Excel datetimes as read, text as day-first "dd/mm/yyyy hh:mm" (as the Commission's as_date())."""
    if isinstance(v, str):
        v = v.strip()
        for f in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return pd.to_datetime(v, format=f)
            except ValueError:
                pass
        raise ValueError(v)
    return pd.Timestamp(v)


def _std(d, cols):
    d = d.rename(columns=cols)[list(cols.values())].copy()
    d["edb"] = d.edb.replace(ALIAS)
    d["pu"] = d.pu.astype(str).str.strip().str.lower()
    d["start"] = d.start.map(_ts)
    d["disc_yr"] = d.disc_yr.astype(int)
    dy = np.where(d.start.dt.month >= 4, d.start.dt.year + 1, d.start.dt.year)
    bad = int((dy != d.disc_yr).sum())
    assert bad <= 0.001 * len(d), f"{bad} start times outside their disclosure year"
    for c in ("saidi", "saifi", "icp_min"):
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    return d


def load():
    INT.mkdir(parents=True, exist_ok=True)
    common = {"EDB": "edb", "Disclosure year": "disc_yr", "Start date and time": "start", "SAIDI value": "saidi",
              "SAIFI value": "saifi", "ICP minutes": "icp_min"}
    d3 = pd.read_excel(COM / "dpp3_zip" / "Final model - Publication version" / "Inputs" / "DPP3 Final - EDB interruptions.xlsx",
                       dtype={"Start date and time": object})
    _std(d3, {**common, "Planned or unplanned": "pu"}).to_parquet(INT / "dpp3.parquet", index=False)
    d4 = pd.read_excel(next((COM / "dpp4_zip" / "edb_quality_dpp4" / "data-raw").glob("*.xlsx")), dtype={"Start date and time": object})
    _std(d4, {**common, "Planned_Unplanned": "pu"}).to_parquet(INT / "dpp4.parquet", index=False)
    i5 = pd.read_parquet(RAW / "EDB_ID_10a_interruptions_2025.09.1.parquet")
    i5.to_parquet(INT / "id2025_raw.parquet", index=False)
    print("loaded", len(d3), len(d4), len(i5))


def annual(d):
    u = d[d.pu == "unplanned"]
    return u.groupby(["edb", "disc_yr"]).saidi.sum()


def check():
    d3, d4 = pd.read_parquet(INT / "dpp3.parquet"), pd.read_parquet(INT / "dpp4.parquet")
    out = {}
    a3, a4 = annual(d3), annual(d4)
    a3u = a3.copy()
    # Centralines: does the DPP4 file's Unison equal Unison + Centralines of the DPP3 file in the overlap?
    yrs = range(2014, 2020)
    un3 = a3.reindex([("Unison Networks", y) for y in yrs]).to_numpy()
    ce3 = a3.reindex([("Centralines", y) for y in yrs]).fillna(0).to_numpy()
    un4 = a4.reindex([("Unison Networks", y) for y in yrs]).to_numpy()
    out["centralines"] = {"years": list(yrs), "unison_dpp3": un3.round(3).tolist(), "centralines_dpp3": ce3.round(3).tolist(),
                          "unison_dpp4": un4.round(3).tolist()}
    combine = bool(np.allclose(un4, un3 + ce3, rtol=0.05))
    out["centralines"]["dpp4_unison_equals_sum_within_5pct"] = combine
    if combine:
        a3u = a3.rename(index={"Centralines": "Unison Networks"}, level=0).groupby(level=[0, 1]).sum()
    # overlap agreement 2014-2019
    idx = [(e, y) for e in sorted(set(a4.index.get_level_values(0))) for y in yrs]
    x, y = a3u.reindex(idx), a4.reindex(idx)
    m = x.notna() & y.notna() & (y > 0)
    rel = (x[m] / y[m] - 1).abs()
    out["overlap"] = {"edb_years": int(m.sum()), "within_5pct": int((rel <= 0.05).sum()),
                      "share_within_5pct": round(float((rel <= 0.05).mean()), 4),
                      "worst": rel.sort_values(ascending=False).head(8).round(4).reset_index().astype(str).values.tolist()}
    out["overlap"]["passes"] = out["overlap"]["share_within_5pct"] >= 0.8
    # 2025: class identification
    i5 = pd.read_parquet(INT / "id2025_raw.parquet")
    out["id2025"] = {"rows": int(len(i5)), "planned_or_unplanned": i5.planned_or_unplanned.astype(str).value_counts().to_dict(),
                     "section": i5.section.astype(str).value_counts().head(10).to_dict(),
                     "cause_top": i5.cause.astype(str).value_counts().head(15).to_dict(),
                     "disc_yr": i5.disc_yr.astype(str).value_counts().to_dict(), "edbs": int(i5.edb.nunique())}
    # 2025 unplanned totals against the disclosed Class C SAIDI for 2025 (aggregate; identification check only)
    p = pd.read_parquet(RAW / "EDB_ID_Full_2026-06-01.parquet")
    cc = p[(p.section == "10(i): Interruptions") & (p.category == "SAIFI and SAIDI by class") & (p.sub_category == "SAIDI")
           & p.description.str.startswith("Class C", na=False) & (p.disc_yr == 2025)].groupby("edb").value.sum()
    un5 = i5[i5.planned_or_unplanned.astype(str).str.lower().str.startswith("unplanned")].groupby("edb").saidi_value.sum()
    j = pd.concat({"class_c_disclosed": cc, "unplanned_10a": un5}, axis=1).dropna()
    j = j[j.class_c_disclosed > 0]
    r = (j.unplanned_10a / j.class_c_disclosed - 1).abs()
    out["id2025"]["unplanned_vs_class_c"] = {"edbs": int(len(j)), "within_5pct": int((r <= 0.05).sum()),
                                             "worst": r.sort_values(ascending=False).head(6).round(4).to_dict()}
    out["id2025"]["usable"] = bool(len(j) >= 12 and (r <= 0.05).mean() >= 0.8)
    (T / "panel_checks.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


def build():
    chk = json.loads((T / "panel_checks.json").read_text())
    d3, d4 = pd.read_parquet(INT / "dpp3.parquet"), pd.read_parquet(INT / "dpp4.parquet")
    if chk["centralines"]["dpp4_unison_equals_sum_within_5pct"]:
        d3["edb"] = d3.edb.replace({"Centralines": "Unison Networks"})
    else:
        d3 = d3[d3.edb != "Centralines"]
    keep = set(d4.edb)
    parts = []
    if chk["overlap"]["passes"]:
        parts.append(d3[(d3.disc_yr <= 2013) & d3.edb.isin(keep)].assign(src="dpp3"))
    parts.append(d4[d4.disc_yr >= 2014].assign(src="dpp4"))
    if chk["id2025"]["usable"]:
        i5 = pd.read_parquet(INT / "id2025_raw.parquet")
        i5 = i5.rename(columns={"start_datetime": "start", "saidi_value": "saidi", "saifi_value": "saifi",
                                "icp_interruption_minutes": "icp_min", "planned_or_unplanned": "pu"})
        i5 = _std(i5.rename(columns={"edb": "EDB"}), {"EDB": "edb", "disc_yr": "disc_yr", "start": "start", "pu": "pu",
                                                       "saidi": "saidi", "saifi": "saifi", "icp_min": "icp_min"})
        i5["pu"] = np.where(i5.pu.str.startswith("unplanned"), "unplanned", "planned")
        parts.append(i5[i5.edb.isin(keep)].assign(src="id2025"))
    d = pd.concat(parts, ignore_index=True)
    u = d[d.pu == "unplanned"].copy()
    u.to_parquet(INT / "unplanned.parquet", index=False)
    # ICP count per distributor-year: median of ICP minutes / SAIDI over interruptions
    v = u[(u.saidi > 0) & (u.icp_min > 0)]
    icp = (v.icp_min / v.saidi).groupby([v.edb, v.disc_yr]).median().rename("icps")
    ann = pd.concat([u.groupby(["edb", "disc_yr"]).saidi.sum().rename("raw_saidi"),
                     u.groupby(["edb", "disc_yr"]).saifi.sum().rename("raw_saifi"), icp], axis=1).reset_index()
    ann.to_csv(T / "panel_annual.csv", index=False)
    print(ann.groupby("disc_yr").size().to_dict())
    print("sources", d.groupby("src").disc_yr.agg(["min", "max", "size"]).to_dict())


if __name__ == "__main__":
    {"load": load, "check": check, "build": build}[sys.argv[1]]()
