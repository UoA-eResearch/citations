#!/usr/bin/env python
"""EXPLORATORY (deviations.md D3): forecast value of wastewater as a function of its reporting lag.
Relative WIS (with / without wastewater) for availability lags 0, 2, 5, 7, 10 (primary) and 17 days, overall and by
horizon, primary and secondary panels. At lag 0 the latest wastewater window ends on the due date (Wednesday), four days
into the horizon-0 target week; that is a best-case bound, not a realistic reporting delay.
Output: results/tables/timeliness.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import FC, TAB, attach_scores, paired, panels, rel_wis, truth  # noqa: E402


def main():
    tr, pan = truth(), panels()
    rows = []
    for lag in (0, 2, 5, 7, 10, 17):
        sc = attach_scores(pd.read_parquet(FC / f"main_lag{lag}.parquet"), tr).merge(pan, on=["season", "location"], how="left")
        for panel, thr in (("primary", 0.5), ("secondary", 0.2)):
            d = sc[sc.coverage >= thr]
            m = paired(d[d.model == "ww"], d[d.model == "base"])
            for hz in ("all", 0, 1, 2, 3):
                mm = m if hz == "all" else m[m.horizon == hz]
                r = rel_wis(mm, nboot=2000)
                r.update(lag_days=lag, panel=panel, horizon=hz)
                rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "timeliness.csv", index=False)
    print(out.pivot_table(index=["panel", "horizon"], columns="lag_days", values="rel_wis").round(3).to_string())
    print(out[out.horizon == "all"][["panel", "lag_days", "rel_wis", "lo", "hi"]].round(3).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
