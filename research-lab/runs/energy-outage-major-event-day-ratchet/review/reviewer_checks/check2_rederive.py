"""Reviewer check 2: independent re-derivation of daily state SAIDI for eight states (DC, FL, IA, IL, LA, MI, NV, VT) for all of
2015-2025 from the raw rows cached by check1 (selected on the raw 'state' column, not on the FIPS prefix), with my own
time-zone handling, compared with data/daily.csv. Also: (i) the UTC hour-of-day profile of customers out, to confirm the
timestamps are UTC (outage restoration peaks in local daytime); (ii) how much of the first and last local day of the
study window is missing because the 2014 and 2026 files are absent; (iii) what the within-slot duplicates and the
blank customers_out rows amount to per state-year; (iv) a count-weighted check of the 15-minute assumption per state-year
(customer-minutes under 'x 15' vs under 'x actual gap to the next snapshot', capped at 60 minutes).
Writes check2_rederive.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
CACHE = HERE / "cache"
TZ = {"District of Columbia": "America/New_York", "Florida": "America/New_York", "Vermont": "America/New_York", "Michigan": "America/New_York",
      "Iowa": "America/Chicago", "Illinois": "America/Chicago", "Louisiana": "America/Chicago", "Nevada": "America/Los_Angeles"}
ABBR = {"District of Columbia": "DC", "Florida": "FL", "Vermont": "VT", "Iowa": "IA", "Illinois": "IL", "Louisiana": "LA", "Nevada": "NV", "Michigan": "MI"}
out = {}

sub = pd.concat([pd.read_parquet(CACHE / f"subset_{y}.parquet") for y in range(2015, 2026)], ignore_index=True)
sub["t"] = pd.to_datetime(sub.t)
mcc = pd.read_csv(RUN / "data" / "raw" / "MCC.csv", encoding="utf-8-sig")
mcc["stfips"] = (pd.to_numeric(mcc.County_FIPS, errors="coerce") // 1000)
cust = mcc.groupby("stfips").Customers.sum()
daily = pd.read_csv(RUN / "data" / "daily.csv")
daily["year"] = daily.date.str[:4].astype(int)

res = {}
for name, tz in TZ.items():
    g = sub[sub.state == name].copy()
    stf = int(g.fips.iloc[0] // 1000); assert (g.fips // 1000 == stf).all()
    tl = g.t.dt.tz_localize("UTC").dt.tz_convert(tz)
    g["date"] = tl.dt.strftime("%Y-%m-%d")
    g["hour_utc"] = g.t.dt.hour; g["hour_local"] = tl.dt.hour
    c = g.cust.fillna(0.0)
    mine = (c * 15.0).groupby(g.date).sum() / cust[stf]
    th = daily[daily.st == ABBR[name]].set_index("date").saidi
    cmp = pd.concat([mine.rename("mine"), th.rename("theirs")], axis=1).fillna(0.0)
    cmp = cmp[(cmp.index >= "2015-01-01") & (cmp.index <= "2025-12-31")]
    diff = (cmp.mine - cmp.theirs).abs()
    r = dict(n_days=int(len(cmp)), max_abs_diff=float(diff.max()), n_days_diff_gt_1e9=int((diff > 1e-9).sum()),
             annual_mine=cmp.groupby(cmp.index.str[:4]).mine.sum().round(3).to_dict(),
             annual_theirs=cmp.groupby(cmp.index.str[:4]).theirs.sum().round(3).to_dict())
    # (i) UTC vs local hour profile of customers out (share of customer-snapshots by hour)
    hp = c.groupby(g.hour_utc).sum(); hp = hp / hp.sum()
    r["peak_hour_utc"] = int(hp.idxmax()); r["peak_hour_local"] = int((c.groupby(g.hour_local).sum()).idxmax())
    # (iii) blanks and within-slot duplicates
    r["n_rows_blank_cust"] = int(g.cust.isna().sum())
    slot = g.t.dt.floor("15min")
    dup = g.duplicated(subset=["fips"], keep=False) & g.assign(slot=slot).duplicated(subset=["fips", "slot"], keep=False)
    r["n_rows_within_slot_dup"] = int(dup.sum()); r["cust_minutes_in_dup_rows_share"] = float(c[dup].sum() / max(c.sum(), 1))
    # (iv) the 15-minute assumption: per county, the gap to the next snapshot of the same county
    g = g.sort_values(["fips", "t"])
    nxt = g.groupby("fips").t.shift(-1)
    gap = ((nxt - g.t).dt.total_seconds() / 60).fillna(15.0).clip(upper=60)
    alt = (c * gap).groupby(g.date).sum() / cust[stf]
    ratio = alt.groupby(alt.index.str[:4]).sum() / cmp.mine.groupby(cmp.index.str[:4]).sum()
    r["annual_ratio_gapweighted_over_x15"] = ratio.round(4).to_dict()
    r["share_of_snapshots_gap_eq_15"] = float((gap == 15).mean())
    r["share_of_snapshots_gap_gt_15"] = float((gap > 15).mean())
    res[ABBR[name]] = r
    print(ABBR[name], {k: v for k, v in r.items() if not isinstance(v, dict)}, flush=True)
out["states"] = res
# (ii) window edges: how many hours of the first local day are before the first UTC row in the 2015 file,
# and how many hours of the last local day are after the last UTC row in the 2025 file
first = pd.Timestamp(sub.t.min()).tz_localize("UTC"); last = pd.Timestamp(sub.t.max()).tz_localize("UTC")
out["window_edges"] = {n: dict(first_local=str(first.tz_convert(tz)), last_local=str(last.tz_convert(tz))) for n, tz in TZ.items()}
json.dump(out, open(HERE / "check2_rederive.json", "w"), indent=1, default=float)
print(json.dumps(out["window_edges"], indent=1))
