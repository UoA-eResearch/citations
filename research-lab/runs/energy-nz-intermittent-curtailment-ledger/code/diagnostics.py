"""Post hoc diagnostics of the preregistered measure (deviations D2). Descriptive; no verdict changes.

The preregistered rule flags a TP as curtailed when its gap exceeds the 95th percentile of gaps on unconstrained TPs,
and it counts every TP, including the unconstrained ones. By construction about 5% of unconstrained TPs are then
flagged, so forecast error alone produces a positive "curtailment" share. This script splits the curtailed energy by
the kind of TP it falls in and tracks the clearest real signal, curtailment when the node price is at or below the
unit's own offer price, by 12-month window.

Writes results/tables/diagnostics.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

TAB = A.TAB


def classify(c):
    return np.where(c.unconstrained, "unconstrained (noise by construction)",
                    np.where(c.offered < c.P_hat, "offer-limited",
                             np.where(c.price <= c.maxprice.fillna(0), "price-driven", "other")))


def split(cal):
    c = cal.copy()
    c["cls"] = classify(c)
    avail = c.P_hat.sum() * 0.5
    cur = c[c.curtailed]
    by = (cur.g * 0.5).groupby(cur.cls).sum()
    tps = c.groupby("cls").size()
    flagged = cur.groupby("cls").size()
    return {"available_mwh": round(float(avail), 1),
            "curtailed_mwh_by_class": by.round(1).to_dict(),
            "share_of_available_by_class": (by / avail).round(5).to_dict(),
            "tps_by_class": tps.to_dict(),
            "flag_rate_by_class": (flagged / tps).round(4).fillna(0).to_dict()}


def main():
    d = A.prepare(pd.read_parquet(A.DATA / "panel.parquet"))
    out = {"baseline_2020": split(A.calibrate(A.period(d, *A.BASE))),
           "recent_2025_26": split(A.calibrate(A.period(d, *A.RECENT)))}
    windows = {}
    for y in range(2020, 2026):
        lo, hi = f"{y}-07-01", f"{y + 1}-06-30"
        if y == 2020:
            lo = "2020-01-01"
        cal = A.calibrate(A.period(d, lo, hi))
        cal["cls"] = classify(cal)
        avail = cal.P_hat.sum() * 0.5
        cur = cal[cal.curtailed]
        price = cur[cur.cls == "price-driven"]
        windows[f"{lo[:7]}..{hi[:7]}"] = {
            "primary_share": round(float(cur.g.sum() * 0.5 / avail), 5),
            "price_driven_share": round(float(price.g.sum() * 0.5 / avail), 5),
            "share_of_tps_at_or_below_offer_price": round(float((cal.cls == "price-driven").mean()), 4),
            "available_gwh": round(float(avail / 1000), 1)}
    out["by_12_month_window"] = windows
    json.dump(out, open(TAB / "diagnostics.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
