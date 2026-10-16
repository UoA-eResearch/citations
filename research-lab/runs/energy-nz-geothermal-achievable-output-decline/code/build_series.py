"""Monthly achievable-output series for every New Zealand geothermal plant and field, from EMI Generation_MD.

Generation_MD gives half-hourly metered generation (kWh per trading period) by plant, with fuel codes, from 2000.
Each half-hour value is converted to average MW (kWh x 2 / 1000).

  plant series   one per (POC_Code, Gen_Code); Gen_Code is compared case-insensitively, so "Te_Mihi" (2013-19) and
                 "te_mihi" (2020-) are one plant. Different names at the same POC are different plants.
  field series   the half-hourly SUM of the field's plants that report that month. A half-hour where any of them
                 has no value is missing for the field, never zero: a plant on outage reports 0, a plant with no
                 row is unknown.
  monthly stats  P95 (the primary "achievable output": the level the field reaches or exceeds in 5% of the month's
                 half-hours, about 36 hours - robust to outages, maintenance and short dispatch flexing), P50, P99,
                 the mean, and the number of valid half-hours.

Writes data/processed/plant_monthly.csv, field_monthly.csv, field_membership.csv (which plants report in each
month, used by analysis.py to place segment boundaries).
"""
import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, PROC = RUN / "data" / "raw" / "emi_gmd", RUN / "data" / "processed"
TP = [f"TP{i}" for i in range(1, 51)]

# (POC, Gen_Code lower-case) -> field. The eight developed fields; plants on a shared fluid take are on one field.
FIELD = {
    ("WRK2201", "wairakei"): "Wairakei", ("PPI2201", "poihipi"): "Wairakei", ("THI2201", "te_mihi"): "Wairakei",
    ("WRK0331", "tehuka"): "Tauhara", ("TAB2201", "tauhara"): "Tauhara", ("TAB0331", "te_huka_3"): "Tauhara",
    ("WRK0331", "rotokawa"): "Rotokawa", ("NAP2201", "nap"): "Rotokawa",
    ("NAP2202", "ngatamariki"): "Ngatamariki",
    ("OKI2201", "ohaaki"): "Ohaaki",
    ("WKM2201", "mokai"): "Mokai",
    ("KAW0111", "kawerau_geo"): "Kawerau", ("KAW0111", "kawerau"): "Kawerau", ("KAW0112", "norskeskog"): "Kawerau",
    ("KAW1101", "kawerau_new"): "Kawerau", ("KAW2201", "kawerau_(topp2)"): "Kawerau",
    ("KOE0331", "ngawha"): "Ngawha", ("KOE1101", "ngawha"): "Ngawha",
}


def stats(x):
    v = x[np.isfinite(x)]
    if len(v) == 0:
        return dict(p95=np.nan, p50=np.nan, p99=np.nan, mean=np.nan, n=0)
    return dict(p95=float(np.percentile(v, 95)), p50=float(np.percentile(v, 50)), p99=float(np.percentile(v, 99)),
                mean=float(v.mean()), n=int(len(v)))


def field_sum(stack):
    """Half-hourly field total from a (plants x half-hours) array. A half-hour is valid only if every reporting
    plant has a value; TP47-50 exist only on daylight-saving days, so a half-hour missing for ALL plants is simply
    not a half-hour, while one missing for SOME is a partial (counted, and missing for the field)."""
    all_nan = np.isnan(stack).all(axis=0)
    any_nan = np.isnan(stack).any(axis=0)
    with np.errstate(invalid="ignore"):
        s = np.where(any_nan, np.nan, np.nansum(stack, axis=0))
    return s, int((any_nan & ~all_nan).sum())


def read_month(f):
    d = pd.read_csv(f, dtype=str, encoding="utf-8-sig")
    d.columns = [c.strip() for c in d.columns]
    dcol = [c for c in d.columns if c.lower() == "trading_date"][0]
    d = d[d.Fuel_Code.str.lower().str.startswith("geo", na=False)].copy()
    d["gen"] = d.Gen_Code.str.strip().str.lower()
    d["key"] = list(zip(d.POC_Code.str.strip(), d.gen))
    unknown = sorted(set(d.key) - set(FIELD))
    if unknown:
        raise RuntimeError(f"{f}: geothermal plant(s) not mapped to a field: {unknown}")
    # dates are ISO (YYYY-MM-DD) in some files and d/m/Y in others; parsing ISO with dayfirst=True swaps day and
    # month for days 1-12 (a first run lost 11-12 days of every month this way, caught by the valid-half-hour count)
    s = d[dcol].str.strip()
    iso = s.str.match(r"^\d{4}-\d{2}-\d{2}")
    d["date"] = pd.NaT
    d.loc[iso, "date"] = pd.to_datetime(s[iso], format="%Y-%m-%d")
    d.loc[~iso, "date"] = pd.to_datetime(s[~iso], dayfirst=True, format="mixed")
    d["date"] = pd.to_datetime(d["date"])
    bad = (d.date.dt.to_period("M") != pd.Period(f"{Path(f).name[:4]}-{Path(f).name[4:6]}", "M"))
    if bad.any():
        raise RuntimeError(f"{f}: {int(bad.sum())} rows dated outside the file's month")
    for c in TP:
        if c not in d:
            d[c] = np.nan
    d[TP] = d[TP].apply(pd.to_numeric, errors="coerce") * 2 / 1000.0      # kWh per half-hour -> MW
    # one row per plant-day (duplicates, if any, are summed: a plant metered on two network codes)
    d = d.groupby(["key", "date"])[TP].sum(min_count=1).reset_index()
    return d


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    plant_rows, field_rows, member_rows = [], [], []
    for f in sorted(glob.glob(str(RAW / "*.csv"))):
        ym = os.path.basename(f)[:6]
        month = pd.Period(f"{ym[:4]}-{ym[4:]}", freq="M")
        d = read_month(f)
        if d.empty:
            continue
        days = pd.date_range(month.start_time, month.end_time.normalize())
        for key, g in d.groupby("key"):
            a = g.set_index("date").reindex(days)[TP].to_numpy().ravel()
            plant_rows.append(dict(month=str(month), poc=key[0], plant=key[1], field=FIELD[key], **stats(a)))
        d["field"] = d.key.map(FIELD)
        for field, g in d.groupby("field"):
            keys = sorted(set(g.key))
            member_rows.append(dict(month=str(month), field=field, plants="|".join(f"{k[0]}:{k[1]}" for k in keys)))
            stack = np.stack([g[g.key == k].set_index("date").reindex(days)[TP].to_numpy().ravel() for k in keys])
            s, n_partial = field_sum(stack)
            r = stats(s)
            r["n_partial"] = n_partial
            field_rows.append(dict(month=str(month), field=field, n_plants=len(keys), **r))
        print(ym, len(d), flush=True)
    pd.DataFrame(plant_rows).to_csv(PROC / "plant_monthly.csv", index=False)
    pd.DataFrame(field_rows).to_csv(PROC / "field_monthly.csv", index=False)
    pd.DataFrame(member_rows).to_csv(PROC / "field_membership.csv", index=False)
    print("written", len(plant_rows), "plant-months,", len(field_rows), "field-months")


if __name__ == "__main__":
    sys.exit(main())
