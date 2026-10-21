"""Reviewer check 6: lead time of the potential actually used (highest SubmissionOrder among latest rows) before the
trading period starts, over every fetched day, summarised by POC and financial year: median lead (min), share
submitted after the TP started, share submitted more than 2 h before, and share of unit-TPs with latest rows from
more than one submission (stale-potential cases)."""
import glob, os
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
RUN = "/mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger"
NZ, UTC = ZoneInfo("Pacific/Auckland"), ZoneInfo("UTC")
out = []
for f in sorted(glob.glob(f"{RUN}/data/offers/*.csv.gz")):
    x = pd.read_csv(f, usecols=["TradingDate", "TradingPeriod", "PointOfConnection", "Unit", "SubmissionOrder", "UTCSubmissionDate", "UTCSubmissionTime"])
    if x.empty:
        continue
    g = x.groupby(["PointOfConnection", "Unit", "TradingPeriod"])
    multi = (g.SubmissionOrder.nunique() > 1).rename("multi").reset_index()
    lat = x[x.SubmissionOrder == g.SubmissionOrder.transform("max")].drop_duplicates(["PointOfConnection", "Unit", "TradingPeriod"]).copy()
    td = pd.Timestamp(lat.TradingDate.iloc[0])
    mid = pd.Timestamp(td.year, td.month, td.day, tzinfo=NZ).astimezone(UTC).replace(tzinfo=None)   # local midnight in UTC
    start = mid + pd.to_timedelta((lat.TradingPeriod.values - 1) * 30, unit="min")               # TPs count from local midnight
    sub = pd.to_datetime(lat.UTCSubmissionDate + " " + lat.UTCSubmissionTime)
    lat["lead"] = (start - sub.values) / np.timedelta64(1, "m")
    lat = lat.merge(multi, on=["PointOfConnection", "Unit", "TradingPeriod"])
    lat["date"] = td
    out.append(lat[["date", "PointOfConnection", "Unit", "TradingPeriod", "lead", "multi"]])
a = pd.concat(out, ignore_index=True)
a.to_parquet(f"{RUN}/review/reviewer_checks/lead_times.parquet")
a["fy"] = np.where(a.date.dt.month >= 7, a.date.dt.year + 1, a.date.dt.year)
s = a.groupby(["PointOfConnection", "fy"]).agg(median_lead_min=("lead", "median"), after_start=("lead", lambda v: (v < 0).mean()),
                                               over_2h=("lead", lambda v: (v > 120).mean()), over_1d=("lead", lambda v: (v > 1440).mean()),
                                               multi_order=("multi", "mean"), n=("lead", "size")).round(3)
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 400)
print(s.to_string())
print("\nAll units, by FY:")
print(a.groupby("fy").agg(median_lead_min=("lead", "median"), after_start=("lead", lambda v: (v < 0).mean()), over_2h=("lead", lambda v: (v > 120).mean()), over_1d=("lead", lambda v: (v > 1440).mean())).round(3).to_string())
