#!/usr/bin/env python
"""EXPLORATORY (deviations.md D6; prompted by the independent review): is the hinge's "flat until 1980" assumption met?
Mean residual (degC) of the hinge and of the 3-parameter piecewise-linear trend, by 5-year period, for US and other
stations (TXx, qualifying stations).
Output: results/tables/baseline_residuals.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import PROC, TAB, YEARS, detrend, stage1  # noqa: E402


def main():
    ids = set(stage1("txx", 3, "hinge", "permute").station)
    ex = pd.read_parquet(PROC / "extremes.parquet")
    ex = ex[ex.station.isin(ids)]
    rows = []
    for sid, g in ex.groupby("station"):
        g = g.set_index("year").reindex(YEARS)
        v = g.valid.fillna(False).values.astype(bool) & np.isfinite(g.txx.values)
        for m in ("hinge", "pw"):
            tr, _ = detrend(YEARS[v], g.txx.values[v], m)
            r = np.where(v, g.txx.values - tr, np.nan)
            rows.append(pd.DataFrame(dict(station=sid, method=m, year=YEARS, resid=r)))
    d = pd.concat(rows)
    d["region"] = np.where(d.station.str.startswith("US"), "US", "non-US")
    d["period"] = (d.year - 1951) // 5 * 5 + 1951
    out = d.groupby(["method", "region", "period"]).resid.mean().unstack("period").round(2)
    out.to_csv(TAB / "baseline_residuals.csv")
    print(out.to_string())


if __name__ == "__main__":
    sys.exit(main())
