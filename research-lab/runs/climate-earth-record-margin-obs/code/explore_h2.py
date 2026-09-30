#!/usr/bin/env python
"""EXPLORATORY (deviations.md D6; prompted by the independent review): where does the H2 shortfall come from?
R2 (observed / trend-preserving null, 2003-2025) by region, and per-year contributions to the deficit
(observed minus expected new records, summed over stations), and R2 without the largest-surplus years
(drop_years prefixed '-') or the largest-deficit years. Two-way bootstrap intervals throughout.
Output: results/tables/h2_breakdown.csv, results/tables/h2_by_year.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import E2, TAB, YEARS, pooled_twoway, stage1  # noqa: E402


def main():
    df = stage1("txx", 3, "hinge", "permute")
    us = df.station.str.startswith("US")
    rows = []
    e2 = (YEARS >= E2[0]) & (YEARS <= E2[1])
    O = np.array(df.m_obs.tolist())
    for thr in (0.0, 1.0):
        k = int(thr)
        T = np.nan_to_num(np.array(df[f"trend_py_gt{k}"].tolist()))
        D = np.where(np.isfinite(O), np.nan_to_num(O, nan=-9) > thr, 0) - T
        by_year = pd.DataFrame(dict(year=YEARS, threshold=thr, deficit_all=D.sum(0), deficit_US=D[us.values].sum(0),
                                    deficit_nonUS=D[~us.values].sum(0), expected_all=T.sum(0)))
        by_year = by_year[e2]
        if thr == 0.0:
            by_year.to_csv(TAB / "h2_by_year.csv", index=False)
        obs_y = by_year.deficit_all + by_year.expected_all
        top = obs_y.sort_values(ascending=False)
        print(f"thr {thr}: {int((by_year.deficit_all < 0).sum())} of {len(by_year)} years below expectation; top 3 years "
              f"{by_year.year.values[top.index[:3] - by_year.index[0]].tolist()} hold {top.iloc[:3].sum() / obs_y.sum():.0%} of "
              f"observed records (expected share {by_year.expected_all.loc[top.index[:3]].sum() / by_year.expected_all.sum():.0%})")
        worst = by_year.sort_values("deficit_all").year.values
        best = by_year.sort_values("deficit_all", ascending=False).year.values
        for n_drop in (1, 3):
            drop = set(best[:n_drop].tolist())
            d2 = df.copy()
            keep = ~np.isin(YEARS, list(drop))
            d2["m_obs"] = [list(np.where(keep, m, np.nan)) for m in d2.m_obs]
            r = pooled_twoway(d2, thr)["R2_obs_over_trend"]
            rows.append(dict(threshold=thr, subset="all", n=len(df), drop_years="-" + ",".join(map(str, sorted(drop))), **r))
        for label, sel in (("all", slice(None)), ("US", us.values), ("non-US", ~us.values)):
            r = pooled_twoway(df[sel], thr)["R2_obs_over_trend"]
            rows.append(dict(threshold=thr, subset=label, n=int(np.asarray(df[sel].shape[0])), drop_years="", **r))
        for n_drop in (1, 3, 5):
            drop = set(worst[:n_drop].tolist())
            d2 = df.copy()
            keep = ~np.isin(YEARS, list(drop))
            d2["m_obs"] = [list(np.where(keep, m, np.nan)) for m in d2.m_obs]
            r = pooled_twoway(d2, thr)["R2_obs_over_trend"]
            rows.append(dict(threshold=thr, subset="all", n=len(df), drop_years=",".join(map(str, sorted(drop))), **r))
        print(by_year.sort_values("deficit_all").head(6).round(1).to_string(index=False))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "h2_breakdown.csv", index=False)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
