"""Reviewer check 1: is the 'latest' potential dispatch-time? Lead time of the highest-SubmissionOrder row before the
trading period starts, per POC, on sampled days; stale-potential prevalence; MaximumOutputMegawatts fill rate."""
import sys, glob
import pandas as pd, numpy as np
from zoneinfo import ZoneInfo
RUN = "/mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger"
NZ = ZoneInfo("Pacific/Auckland")
days = ["20200115","20200715","20210415","20220115","20221115","20230715","20240415","20250115","20251015","20260315","20260715"]
rows = []
for d in days:
    x = pd.read_csv(f"{RUN}/data/offers/{d}.csv.gz")
    g = x.groupby(["PointOfConnection","Unit","TradingPeriod"])
    mx = g.SubmissionOrder.transform("max")
    lat = x[x.SubmissionOrder == mx].drop_duplicates(["PointOfConnection","Unit","TradingPeriod"]).copy()
    multi = int((g.SubmissionOrder.nunique() > 1).sum())
    tdate = pd.Timestamp(lat.TradingDate.iloc[0])
    start_local = [pd.Timestamp(tdate.year, tdate.month, tdate.day, tzinfo=NZ) + pd.Timedelta(minutes=30*(tp-1)) for tp in lat.TradingPeriod]
    # local midnight + offset handles DST days approximately (wall-clock arithmetic in zoneinfo is fine for non-transition days)
    start_utc = pd.to_datetime([s.astimezone(ZoneInfo("UTC")).replace(tzinfo=None) for s in start_local])
    sub = pd.to_datetime(lat.UTCSubmissionDate + " " + lat.UTCSubmissionTime)
    lat["lead_min"] = (start_utc.values - sub.values) / np.timedelta64(1, "m")
    s = lat.groupby("PointOfConnection").lead_min.agg(["median","min","max"]).round(1)
    s["after_start_share"] = lat.groupby("PointOfConnection").lead_min.apply(lambda v: round((v < 0).mean(), 2))
    s["day"] = d; s["unitTPs_multi_order"] = multi
    s["maxout_filled"] = round(float(x.MaximumOutputMegawatts.notna().mean()), 2)
    rows.append(s.reset_index())
out = pd.concat(rows)
pd.set_option("display.width", 200)
print(out.to_string(index=False))
print("\nSummary over sampled days (all POCs): share of latest potentials submitted AFTER the TP start:")
print(out.groupby("day").after_start_share.mean().round(2).to_string())
