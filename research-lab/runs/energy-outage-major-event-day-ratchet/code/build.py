"""Daily state SAIDI from EAGLE-I (plan section 1). For each state and local day (the state's predominant time zone):
customer-minutes interrupted = sum over its counties' 15-minute snapshots of customers_out x 15; daily SAIDI = that /
the state's MCC 2022 customers. Days with no record are 0. Also counts, per state and year, the distinct counties that
reported any outage (for the coverage-stability rule). Writes data/daily.csv and data/county_reporting.csv."""
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
        "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
        "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
        "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
        "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
        "56": "WY"}
TZ = {**{s: "America/New_York" for s in "CT DE DC FL GA IN KY ME MD MA MI NH NJ NY NC OH PA RI SC VT VA WV".split()},
      **{s: "America/Chicago" for s in "AL AR IL IA KS LA MN MS MO NE ND OK SD TN TX WI".split()},
      **{s: "America/Denver" for s in "CO MT NM UT WY".split()}, "AZ": "America/Phoenix", "ID": "America/Boise",
      **{s: "America/Los_Angeles" for s in "CA NV OR WA".split()}, "AK": "America/Anchorage", "HI": "Pacific/Honolulu"}


def main():
    mcc = pd.read_csv(RAW / "MCC.csv", encoding="utf-8-sig", dtype={"County_FIPS": str})
    mcc["st"] = mcc.County_FIPS.str.zfill(5).str[:2].map(FIPS)
    cust = mcc.dropna(subset=["st"]).groupby("st").Customers.sum()
    daily, counties = [], []
    for y in range(2015, 2026):
        f = RAW / f"eaglei_outages_{y}.csv"
        parts, cty = [], []
        for ch in pd.read_csv(f, usecols=["fips_code", "customers_out", "run_start_time"], dtype={"fips_code": str},
                              chunksize=5_000_000):
            ch["st"] = ch.fips_code.str.zfill(5).str[:2].map(FIPS)
            ch = ch.dropna(subset=["st", "customers_out"])
            t = pd.to_datetime(ch.run_start_time, utc=True, errors="coerce")
            ch = ch[t.notna()]; t = t[t.notna()]
            ch["date"] = ""
            for st, idx in ch.groupby("st").groups.items():
                ch.loc[idx, "date"] = t.loc[idx].dt.tz_convert(TZ[st]).dt.strftime("%Y-%m-%d").values
            ch["cmi"] = ch.customers_out.astype(float) * 15.0
            parts.append(ch.groupby(["st", "date"]).cmi.sum())
            cty.append(ch[ch.customers_out > 0].groupby("st").fips_code.unique().explode().reset_index())
        d = pd.concat(parts).groupby(level=[0, 1]).sum().reset_index()
        daily.append(d)
        c = pd.concat(cty).drop_duplicates()
        counties.append(c.groupby("st").fips_code.nunique().rename("n_counties").reset_index().assign(year=y))
        print(y, len(d), "state-days", flush=True)
    d = pd.concat(daily).groupby(["st", "date"]).cmi.sum().reset_index()
    # fill every state-day 2015-01-01 .. 2025-12-31 (local), zeros where nothing was recorded
    days = pd.date_range("2015-01-01", "2025-12-31").strftime("%Y-%m-%d")
    full = pd.MultiIndex.from_product([sorted(cust.index), days], names=["st", "date"])
    d = d.set_index(["st", "date"]).reindex(full, fill_value=0.0).reset_index()
    d["customers"] = d.st.map(cust)
    d["saidi"] = d.cmi / d.customers
    d.to_csv(RUN / "data" / "daily.csv", index=False)
    pd.concat(counties).to_csv(RUN / "data" / "county_reporting.csv", index=False)
    print(len(d), "state-days written")


if __name__ == "__main__":
    main()
