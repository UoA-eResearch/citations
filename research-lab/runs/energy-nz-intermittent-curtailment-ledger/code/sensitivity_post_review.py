"""Post-review checks (deviations D3). Descriptive; no verdict changes.

1. Price lines: non-noise curtailment in 2025/26 split by node price <= $0.01, <= the plant's own highest offer, < $1.
2. Per-plant dispatched-down curtailment (price <= own offer) by 12-month window, and the fleet share without the two
   largest contributors.
3. Offer prices: each plant's median highest offer price ($/MWh) by financial year.
4. Lead time of the potential: minutes from the latest submission to the start of its trading period, by plant and
   financial year (median, and share submitted after the period had started).
5. Rows dropped for missing metered output, by plant and month.
6. MaximumOutputMegawatts: share of offer rows with a value, by financial year.
7. Projection variant: plants without metering projected at k = 1.

Writes results/tables/sensitivity_post_review.json.
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import diagnostics as D  # noqa: E402

TAB = A.TAB


def fy(dates):
    return dates.dt.year + (dates.dt.month >= 7)          # financial year ending June


def main():
    raw = pd.read_parquet(A.DATA / "panel.parquet")
    d = A.prepare(raw)
    out = {}
    rec = A.calibrate(A.period(d, *A.RECENT))
    rec["cls"] = D.classify(rec)
    nn = rec[rec.curtailed & ~rec.unconstrained]
    tot = float(nn.g.sum() * 0.5)
    out["nonnoise_2025_26_mwh"] = round(tot, 1)
    out["nonnoise_share_price_le_0_01"] = round(float(nn[nn.price <= 0.01].g.sum() * 0.5 / tot), 3)
    out["nonnoise_share_price_le_own_offer"] = round(float(nn[nn.price <= nn.maxprice.fillna(0)].g.sum() * 0.5 / tot), 3)
    out["nonnoise_share_price_lt_1"] = round(float(nn[nn.price < 1].g.sum() * 0.5 / tot), 3)
    # per-plant dispatched-down series
    series, wins = {}, []
    for y in range(2020, 2026):
        lo, hi = (f"{y}-07-01", f"{y + 1}-06-30") if y > 2020 else ("2020-01-01", "2021-06-30")
        cal = A.calibrate(A.period(d, lo, hi))
        cal["cls"] = D.classify(cal)
        cur = cal[cal.curtailed & (cal.cls == "price-driven")]
        by = (cur.g * 0.5).groupby(cur.poc).sum() / 1000
        avail = float(cal.P_hat.sum() * 0.5)
        key = f"{lo[:7]}..{hi[:7]}"
        series[key] = {"fleet_share": round(float(cur.g.sum() * 0.5 / avail), 5),
                       "by_plant_gwh": by.round(2).sort_values(ascending=False).head(6).to_dict()}
        top2 = by.sort_values(ascending=False).head(2).index
        rest = cal[~cal.poc.isin(top2)]
        rc = rest[rest.curtailed & (D.classify(rest) == "price-driven")]
        series[key]["fleet_share_without_top_two"] = round(float(rc.g.sum() * 0.5 / (rest.P_hat.sum() * 0.5)), 5)
        series[key]["top_two"] = list(top2)
    out["dispatched_down_series"] = series
    # offer prices by plant and financial year
    d["fy"] = fy(d.date)
    out["median_max_offer_price_by_fy"] = d.groupby(["poc", "fy"]).maxprice.median().unstack().round(3) \
        .dropna(how="all").to_dict(orient="index")
    # lead times from the filtered offers
    rows = []
    for f in sorted(glob.glob(str(A.DATA / "offers" / "*.csv.gz"))):
        x = pd.read_csv(f, usecols=["TradingDate", "TradingPeriod", "PointOfConnection", "Unit", "SubmissionOrder",
                                    "UTCSubmissionDate", "UTCSubmissionTime", "MaximumOutputMegawatts"],
                        dtype={"PointOfConnection": str})
        if x.empty:
            continue
        lt = x.loc[x.groupby(["PointOfConnection", "Unit", "TradingPeriod"]).SubmissionOrder.idxmax()].copy()
        start = (pd.to_datetime(lt.TradingDate, format="mixed").dt.tz_localize("Pacific/Auckland", ambiguous="NaT",
                                                                                 nonexistent="NaT")
                 + pd.to_timedelta((lt.TradingPeriod - 1) * 30, unit="min")).dt.tz_convert("UTC")
        sub = pd.to_datetime(lt.UTCSubmissionDate.astype(str) + " " + lt.UTCSubmissionTime.astype(str), format="mixed",
                             errors="coerce").dt.tz_localize("UTC")
        lt["lead_min"] = (start - sub).dt.total_seconds() / 60
        lt["fy"] = fy(pd.to_datetime(lt.TradingDate, format="mixed"))
        lt["maxout"] = pd.to_numeric(x.loc[lt.index, "MaximumOutputMegawatts"], errors="coerce").notna()
        rows.append(lt[["PointOfConnection", "fy", "lead_min", "maxout"]])
    L = pd.concat(rows, ignore_index=True)
    g = L.groupby(["PointOfConnection", "fy"]).lead_min
    out["lead_minutes_median"] = g.median().unstack().round(1).to_dict(orient="index")
    out["share_submitted_after_period_start"] = (L.assign(after=L.lead_min < 0).groupby(["PointOfConnection", "fy"])
                                                 .after.mean().unstack().round(3).to_dict(orient="index"))
    out["max_output_populated_share_by_fy"] = L.groupby("fy").maxout.mean().round(3).to_dict()
    # rows dropped for missing output
    miss = raw[raw.G.isna()].copy()
    miss["month"] = pd.to_datetime(miss.date).dt.to_period("M").astype(str)
    out["rows_missing_output_by_plant"] = miss.groupby("poc").month.agg(lambda m: f"{len(m)} rows, {m.min()} to {m.max()}").to_dict()
    # projection with unmetered plants at k = 1
    late = d[d.date <= "2026-09-30"].copy()
    cal = A.calibrate(late)
    cal.loc[cal.k < 0.05, "P_hat"] = cal.loc[cal.k < 0.05, "P"]
    cal["month"] = cal.date.dt.to_period("M")
    monthly = cal.groupby(["poc", "month"]).P_hat.sum() * 0.5
    r26 = A.calibrate(A.period(d, *A.RECENT))
    a_rec = r26.groupby("poc").P_hat.sum() * 0.5
    first = d.groupby("poc").date.min()
    proj = {}
    for p in first.index:
        if first[p] <= pd.Timestamp(A.RECENT[0]) and p in a_rec and a_rec[p] > 0:
            proj[p] = float(a_rec[p])
        elif p in monthly.index.get_level_values(0):
            proj[p] = float(monthly.loc[p].mean() * 12)
    prim = json.load(open(TAB / "primary.json"))["recent_2025_26"]
    out["projection_unmetered_at_k1"] = {"available_projected_mwh": round(sum(proj.values()), 1),
                                         "projected_share": round(prim["share"] * sum(proj.values()) / float(a_rec.sum()), 5)}
    json.dump(out, open(TAB / "sensitivity_post_review.json", "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items() if k not in ("median_max_offer_price_by_fy", "lead_minutes_median",
                                                                "share_submitted_after_period_start")}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
