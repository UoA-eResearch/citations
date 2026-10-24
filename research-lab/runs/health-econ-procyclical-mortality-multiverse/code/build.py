"""Build the state-year panel (plan section 1) -> data/interim/panel.parquet and results/tables/splice_validation.json.

  build.py nber     count NBER MCD deaths by state of residence x NCHS age group, 1976-2004 -> data/interim/nber_deaths.parquet
  build.py panel    SEER, CDC, FRED, splice and assemble -> data/interim/panel.parquet
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pcsv

RUN = Path(__file__).resolve().parents[1]
RAW, INT, TAB = RUN / "data" / "raw", RUN / "data" / "interim", RUN / "results" / "tables"
INT.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

POSTAL = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA",
          "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR",
          "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]          # NCHS alphabetical 01-51
FIPS = {"AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10", "DC": "11", "FL": "12",
        "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23",
        "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
        "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
        "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55",
        "WY": "56"}
NAME = {"Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
        "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
        "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
        "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
        "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
        "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
        "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
        "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
        "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY", "New York City": "NY"}
DIVISION = {"CT": 1, "ME": 1, "MA": 1, "NH": 1, "RI": 1, "VT": 1, "NJ": 2, "NY": 2, "PA": 2, "IL": 3, "IN": 3, "MI": 3, "OH": 3,
            "WI": 3, "IA": 4, "KS": 4, "MN": 4, "MO": 4, "NE": 4, "ND": 4, "SD": 4, "DE": 5, "DC": 5, "FL": 5, "GA": 5, "MD": 5,
            "NC": 5, "SC": 5, "VA": 5, "WV": 5, "AL": 6, "KY": 6, "MS": 6, "TN": 6, "AR": 7, "LA": 7, "OK": 7, "TX": 7, "AZ": 8,
            "CO": 8, "ID": 8, "MT": 8, "NV": 8, "NM": 8, "UT": 8, "WY": 8, "AK": 9, "CA": 9, "HI": 9, "OR": 9, "WA": 9}
STD2000 = np.array([13818, 55317, 145565, 138646, 135573, 162613, 134834, 87247, 66037, 44842, 15508]) / 1e6   # 11 NCHS groups
SEER_TO_11 = [0, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10]                 # SEER 20 groups (18 = 85-89, 19 = 90+) -> NCHS 11


def state_code(v):
    v = str(v).strip().strip('"')
    if v.isdigit() and 1 <= int(v) <= 51:
        return POSTAL[int(v) - 1]
    return v if v in FIPS else None


def nber():
    rows = []
    for y in range(1976, 2005):
        z = RAW / "nber" / f"mort{y}.csv.zip"
        with zipfile.ZipFile(z) as zf:
            name = [n for n in zf.namelist() if n.endswith(".csv")][0]
            with zf.open(name) as fh:
                head = fh.readline().decode().strip().replace('"', "").split(",")
            cols = [c for c in ("restatus", "staters", "stateres", "ager12") if c in head]
            with zf.open(name) as fh:
                t = pcsv.read_csv(fh, convert_options=pcsv.ConvertOptions(
                    include_columns=cols, column_types={c: pa.string() for c in cols}))
        d = t.to_pandas()
        st = "staters" if "staters" in d else "stateres"
        n0 = len(d)
        d = d[d.restatus.astype(str).str.strip() != "4"]
        d["state"] = d[st].map(state_code)
        d["age11"] = pd.to_numeric(d.ager12, errors="coerce")
        lost = int(d.state.isna().sum())
        d = d.dropna(subset=["state"])
        g = d.groupby(["state", "age11"], dropna=False).size().rename("deaths").reset_index()
        g["year"] = y
        rows.append(g)
        print(y, "records", n0, "foreign", n0 - len(d) - lost, "no state", lost, "age not stated",
              int(d.age11.isna().sum() + (d.age11 == 12).sum()), flush=True)
    out = pd.concat(rows)
    out.to_parquet(INT / "nber_deaths.parquet", index=False)


def seer():
    cache = INT / "seer_state.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    widths = [4, 2, 2, 3, 2, 1, 1, 1, 2, 8]
    names = ["year", "state", "fips", "county", "reg", "race", "origin", "sex", "age", "pop"]
    d = pd.read_fwf(RAW / "seer" / "us.1969_2024.20ages.adjusted.txt.gz", widths=widths, names=names,
                    dtype={"state": str, "fips": str, "county": str, "race": str, "age": int, "pop": np.int64}, compression="gzip")
    d = d[d.state.isin(FIPS)]
    d["age11"] = d.age.map(lambda a: SEER_TO_11[a])
    tot = d.groupby(["state", "year"]).pop.sum().rename("pop")
    by11 = d.groupby(["state", "year", "age11"]).pop.sum().unstack("age11").fillna(0)
    by11.columns = [f"pop_a{int(c)}" for c in by11.columns]
    a = d.groupby(["state", "year", "age"]).pop.sum().unstack("age").fillna(0)
    sh = pd.DataFrame({"sh_u5": (a[0] + a[1]) / a.sum(1), "sh_65": a[list(range(14, 20))].sum(1) / a.sum(1),
                       "sh_85": (a[18] + a[19]) / a.sum(1), "pop15": a[list(range(4, 20))].sum(1)})
    sh["sh_black"] = d[d.race == "2"].groupby(["state", "year"]).pop.sum() / tot
    out = pd.concat([tot, by11, sh], axis=1).reset_index()
    out.to_parquet(cache, index=False)
    return out


def weekly_calendar():
    """CDC weekly all-cause counts by jurisdiction of occurrence -> calendar years by day-share apportionment."""
    a = pd.read_csv(RAW / "cdc" / "3yf8-kanr.csv")
    b = pd.read_csv(RAW / "cdc" / "muzy-jte6.csv")
    a = a.rename(columns={"All  Cause": "deaths"})[["Jurisdiction of Occurrence", "Week Ending Date", "deaths"]]
    b = b.rename(columns={"All Cause": "deaths"})[["Jurisdiction of Occurrence", "Week Ending Date", "deaths"]]
    w = pd.concat([a, b])
    w["state"] = w["Jurisdiction of Occurrence"].map(NAME)
    w = w.dropna(subset=["state"])
    w["end"] = pd.to_datetime(w["Week Ending Date"], format="mixed")        # 2014-2019 file m/d/Y, 2020-2023 ISO
    w = w.groupby(["state", "end"]).deaths.sum().reset_index()         # NYC added to NY
    rec = []
    for _, r in w.iterrows():
        days = pd.date_range(r.end - pd.Timedelta(days=6), r.end)
        for yr, n in pd.Series(days.year).value_counts().items():
            rec.append((r.state, yr, r.deaths * n / 7.0, n))
    c = pd.DataFrame(rec, columns=["state", "year", "deaths", "days"]).groupby(["state", "year"]).sum().reset_index()
    c["ndays"] = np.where(pd.to_datetime(c.year.astype(str) + "-12-31").dt.dayofyear == 366, 366, 365)
    c["deaths_weekly"] = c.deaths * c.ndays / c.days                  # scale years not fully covered by weeks
    return c[["state", "year", "deaths_weekly", "days", "ndays"]]


def fred():
    rec = []
    for st, f in FIPS.items():
        u = pd.read_csv(RAW / "fred" / f"LAUST{f}0000000000003A.csv")
        e = pd.read_csv(RAW / "fred" / f"LAUST{f}0000000000005A.csv")
        u.columns, e.columns = ["date", "ur"], ["date", "emp"]
        m = u.merge(e, on="date")
        m["year"] = pd.to_datetime(m.date).dt.year
        m["state"] = st
        rec.append(m[["state", "year", "ur", "emp"]])
    return pd.concat(rec)


def panel():
    nb = pd.read_parquet(INT / "nber_deaths.parquet")
    pop = seer()
    val = {}
    # NBER totals and age-adjusted rates (age not stated: excluded from the age-specific rates, kept in the total)
    tot = nb.groupby(["state", "year"]).deaths.sum().rename("deaths_nber").reset_index()
    ag = nb[nb.age11.between(1, 11)].copy()
    ag["a"] = ag.age11.astype(int) - 1
    ag = ag.merge(pop.melt(id_vars=["state", "year"], value_vars=[f"pop_a{i}" for i in range(11)], var_name="v", value_name="p")
                  .assign(a=lambda x: x.v.str[5:].astype(int)), on=["state", "year", "a"])
    ag["w"] = ag.deaths / ag.p * 1e5 * STD2000[ag.a]
    aadr = ag.groupby(["state", "year"]).w.sum().rename("aadr_nber").reset_index()
    nbt = tot.merge(aadr, on=["state", "year"])
    # CDC Leading Causes, all causes, 1999-2017
    lc = pd.read_csv(RAW / "cdc" / "bi63-dtpu.csv")
    lc = lc[lc["Cause Name"] == "All causes"].copy()
    lc["state"] = lc.State.map(NAME)
    lc = lc.dropna(subset=["state"]).rename(columns={"Year": "year", "Deaths": "deaths_lc", "Age-adjusted Death Rate": "aadr_lc"})
    lc = lc[["state", "year", "deaths_lc", "aadr_lc"]]
    lc["deaths_lc"] = pd.to_numeric(lc.deaths_lc.astype(str).str.replace(",", ""))
    # weekly, calibrated on 2014-2017
    wk = weekly_calendar()
    cal = wk.merge(lc, on=["state", "year"])
    cal = cal[cal.year.between(2014, 2017)]
    cal["lr"] = np.log(cal.deaths_lc / cal.deaths_weekly)
    fac = cal.groupby("state").lr.mean()
    wk["deaths_wk_cal"] = wk.deaths_weekly * np.exp(wk.state.map(fac))
    v = cal.groupby("state").lr.agg(["mean", "std"])
    val["weekly_vs_lc_2014_2017"] = {"median_abs_log_ratio_raw": round(float(cal.lr.abs().median()), 5),
                                     "max_abs_state_mean": round(float(v["mean"].abs().max()), 5),
                                     "median_within_state_sd": round(float(v["std"].median()), 5),
                                     "state_max_mean": v["mean"].abs().idxmax()}
    ov = nbt.merge(lc, on=["state", "year"])
    ov = ov[ov.year.between(1999, 2004)]
    val["nber_vs_lc_1999_2004"] = {"n": int(len(ov)),
                                   "median_abs_log_ratio_deaths": round(float(np.log(ov.deaths_nber / ov.deaths_lc).abs().median()), 5),
                                   "max_abs_log_ratio_deaths": round(float(np.log(ov.deaths_nber / ov.deaths_lc).abs().max()), 5),
                                   "median_abs_log_ratio_aadr": round(float(np.log(ov.aadr_nber / ov.aadr_lc).abs().median()), 5),
                                   "max_abs_log_ratio_aadr": round(float(np.log(ov.aadr_nber / ov.aadr_lc).abs().max()), 5)}
    # drug poisoning
    dp = pd.read_csv(RAW / "cdc" / "44rk-q6r2.csv")
    dp = dp[(dp.Sex == "Both Sexes") & (dp["Age Group"] == "All Ages") & (dp["Race and Hispanic Origin"] == "All Races-All Origins")].copy()
    dp["state"] = dp.State.map(NAME)
    dp = dp.dropna(subset=["state"]).rename(columns={"Year": "year", "Deaths": "drug_nchs", "Age-adjusted Rate": "drug_aadr"})
    dp = dp[["state", "year", "drug_nchs", "drug_aadr"]]
    vs = pd.read_csv(RAW / "cdc" / "xkb8-kh2a.csv")
    vs = vs[(vs.Indicator == "Number of Drug Overdose Deaths") & (vs.Period == "12 month-ending") & (vs.Month == "December")].copy()
    vs["state"] = vs["State Name"].map(NAME)
    vs = vs.dropna(subset=["state"])
    vs["drug_vsrr"] = pd.to_numeric(vs["Data Value"].astype(str).str.replace(",", ""), errors="coerce")
    vs = vs.groupby(["state", "Year"]).drug_vsrr.sum(min_count=1).reset_index().rename(columns={"Year": "year"})
    o = dp.merge(vs, on=["state", "year"])
    o = o[o.year.between(2015, 2018)].dropna()
    # D1: VSRR counts behave like occurrence counts (DC, NV high); calibrate 2019-2023 to NCHS residence counts as for the weekly series
    dfac = np.log(o.drug_nchs / o.drug_vsrr).groupby(o.state).mean()
    vs["drug_vsrr_cal"] = vs.drug_vsrr * np.exp(vs.state.map(dfac))
    val["vsrr_calibration_factor"] = {"min": round(float(np.exp(dfac.min())), 4), "max": round(float(np.exp(dfac.max())), 4),
                                      "median": round(float(np.exp(dfac.median())), 4), "state_min": dfac.idxmin()}
    val["vsrr_vs_nchs_2015_2018"] = {"n": int(len(o)), "median_abs_log_ratio": round(float(np.log(o.drug_vsrr / o.drug_nchs).abs().median()), 5),
                                     "max_abs_log_ratio": round(float(np.log(o.drug_vsrr / o.drug_nchs).abs().max()), 5)}
    # assemble
    P = pop.merge(fred(), on=["state", "year"], how="left")
    P = P[P.year.between(1975, 2023)]
    P = P.merge(nbt, on=["state", "year"], how="left").merge(lc, on=["state", "year"], how="left") \
         .merge(wk[["state", "year", "deaths_wk_cal"]], on=["state", "year"], how="left") \
         .merge(dp, on=["state", "year"], how="left").merge(vs[["state", "year", "drug_vsrr", "drug_vsrr_cal"]], on=["state", "year"], how="left")
    # D1: the 2020-2023 weekly file ends in September 2023, so 2023 uses the VSRR quarterly all-cause crude rate (12 months
    # ending 2023 Q4, residence) x SEER population
    q = pd.read_csv(RAW / "cdc" / "489q-934x.csv")
    q = q[(q["Cause of Death"] == "All causes") & (q["Year and Quarter"] == "2023 Q4") & (q["Time Period"] == "12 months ending with quarter")
          & (q["Rate Type"] == "Crude")]
    assert len(q) == 1
    q23 = pd.DataFrame([{"state": NAME[c[5:]], "year": 2023, "rate_q23": float(q.iloc[0][c])} for c in q.columns
                        if c.startswith("Rate ") and c[5:] in NAME and c[5:] != "New York City"])
    P = P.merge(q23, on=["state", "year"], how="left")
    P["deaths_q23"] = P.rate_q23 * P["pop"] / 1e5
    c23 = P[P.year == 2023]
    val["year2023_quarterly_vs_weekly_dayscaled"] = {"median_abs_log_ratio": round(float(np.log(c23.deaths_q23 / c23.deaths_wk_cal).abs().median()), 5),
                                                     "max_abs_log_ratio": round(float(np.log(c23.deaths_q23 / c23.deaths_wk_cal).abs().max()), 5),
                                                     "weekly_days_covered_2023": int(wk[wk.year == 2023].days.max())}
    P["deaths"] = np.where(P.year <= 1998, P.deaths_nber, np.where(P.year <= 2017, P.deaths_lc,
                           np.where(P.year <= 2022, P.deaths_wk_cal, P.deaths_q23)))
    P["source"] = np.where(P.year <= 1998, "nber", np.where(P.year <= 2017, "leading_causes",
                           np.where(P.year <= 2022, "weekly_calibrated", "vsrr_quarterly_rate")))
    P["aadr"] = np.where(P.year <= 1998, P.aadr_nber, np.where(P.year <= 2017, P.aadr_lc, np.nan))
    P["drug"] = np.where(P.year <= 2018, P.drug_nchs, P.drug_vsrr_cal)
    P["crude"] = P.deaths / P["pop"] * 1e5
    P["drug_crude"] = P.drug / P["pop"] * 1e5
    P["epop_neg"] = -100 * P.emp / P.pop15
    P["division"] = P.state.map(DIVISION)
    P = P.sort_values(["state", "year"])
    P.to_parquet(INT / "panel.parquet", index=False)
    val["panel"] = {"states": int(P.state.nunique()), "years": [int(P.year.min()), int(P.year.max())],
                    "missing_deaths_1976_2023": int(P[P.year >= 1976].deaths.isna().sum()),
                    "missing_drug_1999_2023": int(P[P.year >= 1999].drug.isna().sum()),
                    "zero_drug_1999_2023": int((P[P.year >= 1999].drug == 0).sum()),
                    "missing_ur": int(P[P.year >= 1976].ur.isna().sum())}
    (TAB / "splice_validation.json").write_text(json.dumps(val, indent=1) + "\n")
    print(json.dumps(val, indent=1))


if __name__ == "__main__":
    {"nber": nber, "panel": panel}[sys.argv[1]]()
