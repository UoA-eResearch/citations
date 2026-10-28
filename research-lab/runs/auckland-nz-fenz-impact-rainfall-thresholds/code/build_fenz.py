"""FENZ incident files -> daily suburb counts (plan section 1).

Outcome: exposures with NaturalDisasterTypeName "Flood"; V1 adds the action "Water removal: ... weather related floods";
V2 adds ICAD event types starting "NAT". StartDateTime is NZ civil time, converted to NZST (UTC+12) to match the gauges.

  build_fenz.py -> data/fenz_daily.parquet (suburb, tla, region, day [NZST date], flood, v1, v2, nonflood),
                   results/tables/fenz_rows.json (row counts per file and step)
"""
import json
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, D, T = RUN / "data" / "raw", RUN / "data", RUN / "results" / "tables"
COLS = ["ExposureID", "StartDateTime", "RegionalCouncilName", "Suburb", "TLA", "NaturalDisasterTypeName",
        "ICADEventType", "ActionTakenName"]


def one(f):
    try:
        d = pd.read_csv(f, encoding="utf-8-sig", usecols=lambda c: c in COLS, dtype=str, low_memory=False)
        enc = "utf-8"
    except UnicodeDecodeError:                             # one year's export is Windows-1252
        d = pd.read_csv(f, encoding="cp1252", usecols=lambda c: c.lstrip("\ufeff\xef\xbb\xbf") in COLS, dtype=str, low_memory=False)
        d.columns = [c.lstrip("\ufeff").replace("ï»¿", "") for c in d.columns]
        enc = "cp1252"
    st = d.StartDateTime.fillna("")
    slash = st.str.contains("/")                          # 2024/25 writes day-first d/mm/yyyy H:MM; never let pandas guess
    t = pd.Series(pd.NaT, index=d.index, dtype="datetime64[ns]")
    t[slash] = pd.to_datetime(st[slash], format="%d/%m/%Y %H:%M", errors="coerce")
    t[~slash] = pd.to_datetime(st[~slash], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce")
    local = t.dt.tz_localize("Pacific/Auckland", ambiguous="NaT", nonexistent="NaT")
    nzst = (local.dt.tz_convert("UTC") + pd.Timedelta(hours=12)).dt.tz_localize(None)
    act = d.ActionTakenName.fillna("").str.lower()
    out = pd.DataFrame({
        "suburb": d.Suburb.fillna("").str.strip(), "tla": d.TLA.fillna("").str.strip(),
        "region": d.RegionalCouncilName.fillna("").str.strip(), "day": nzst.dt.normalize(),
        "flood": d.NaturalDisasterTypeName.fillna("").str.strip().eq("Flood"),
        "v1x": act.str.contains("water removal") & act.str.contains("weather related flood"),
        "v2x": d.ICADEventType.fillna("").str.upper().str.startswith("NAT")})
    stats = {"encoding": enc, "rows": len(d), "time_unparsed_or_dst_gap": int(out.day.isna().sum()), "no_suburb": int((out.suburb == "").sum()),
             "flood": int(out.flood.sum()), "v1_extra": int((out.v1x & ~out.flood).sum()), "v2_extra": int((out.v2x & ~out.flood).sum())}
    return out, stats


def main():
    parts, stats = [], {}
    for f in sorted(RAW.glob("*.csv")):
        o, s = one(f)
        parts.append(o); stats[f.name] = s
        print(f.name, s, flush=True)
    x = pd.concat(parts)
    x = x[x.day.notna() & (x.suburb != "")]
    # a suburb's region is its most frequent non-empty RegionalCouncilName (2018/19 often leaves it blank; D1)
    reg = x[x.region != ""].groupby(["suburb", "tla"]).region.agg(lambda r: r.value_counts().index[0])
    x["region"] = pd.MultiIndex.from_frame(x[["suburb", "tla"]]).map(reg).fillna("").to_numpy()
    x["v1"] = x.flood | x.v1x
    x["v2"] = x.flood | x.v2x
    x["nonflood"] = ~x.v1                                  # activity: exposures that are not flood-related in any variant
    g = x.groupby(["suburb", "tla", "region", "day"]).agg(flood=("flood", "sum"), v1=("v1", "sum"), v2=("v2", "sum"),
                                                         nonflood=("nonflood", "sum")).reset_index()
    g.to_parquet(D / "fenz_daily.parquet")
    stats["kept_rows"] = len(x); stats["suburb_days_with_any_exposure"] = len(g)
    stats["suburbs"] = int(g[["suburb", "tla"]].drop_duplicates().shape[0])
    (T / "fenz_rows.json").write_text(json.dumps(stats, indent=1) + "\n")
    print(json.dumps({k: v for k, v in stats.items() if not k.endswith(".csv")}, indent=1))


if __name__ == "__main__":
    main()
