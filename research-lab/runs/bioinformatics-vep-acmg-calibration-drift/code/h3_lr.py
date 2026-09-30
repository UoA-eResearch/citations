#!/usr/bin/env python
"""H3, second part (plan.md sec 5): interval LRs on ClinGen VCEP missense labels -- all labels vs tool-independent
labels (those that stay P/LP or B/LB when their PP3/BP4 points are removed). Also the tool-dependent fraction by
approval year for missense variants, with Wilson 95% intervals, and a logistic trend test.

Outputs: results/tables/h3_lr.csv, results/tables/h3_missense_by_year.csv, results/tables/h3_trend.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calib import TOOLS, assign_points  # noqa: E402
from analyze import lr_table, pooled  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
GROUP = {"P": "P", "LP": "P", "VUS": "VUS", "LB": "B", "B": "B"}


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    den = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return c - h, c + h


def main():
    v = pd.read_parquet(PROC / "vcep_recount.parquet")
    v = v[v.confident & v.agrees & v.variation_id.notna()].copy()
    v["variation_id"] = v.variation_id.astype(np.int64)
    v["vlabel"] = v.assertion.map(GROUP)
    at = pd.read_parquet(PROC / "analysis_table.parquet")
    sc = at.drop_duplicates("variation_id")[["variation_id", "gene", "rare"] + list(TOOLS)]
    m = v.merge(sc, on="variation_id", how="inner", suffixes=("_erepo", ""))
    m = m[m.rare].copy()
    m["label"] = m.vlabel
    for t in TOOLS:
        m[f"pts_{t}"] = assign_points(t, m[t].values)
    print(f"VCEP missense (rare, recount agrees, scored): {len(m):,}  P {int((m.label == 'P').sum())}  B {int((m.label == 'B').sum())}")
    # tool-dependent fraction by year, missense only
    rows = []
    for (y, side), g in m.groupby(["year", "label"]):
        k, n = int(g.tool_dependent.sum()), len(g)
        lo, hi = wilson(k, n)
        rows.append(dict(year=int(y), side=side, n=n, n_tool_dependent=k, frac=k / n, lo95=lo, hi95=hi,
                         frac_uses_pp3_bp4=float(g.uses_comp.mean())))
    by = pd.DataFrame(rows)
    by.to_csv(TAB / "h3_missense_by_year.csv", index=False)
    print(by.round(3).to_string(index=False))
    # trend: logistic regression of tool_dependent on approval year, per side (Wald test on the slope)
    trend = {}
    for side, g in m.groupby("label"):
        x = g.year.values.astype(float) - 2020
        yv = g.tool_dependent.values.astype(float)
        X = np.column_stack([np.ones_like(x), x])
        beta = np.zeros(2)
        for _ in range(50):                                   # Newton-Raphson
            p = 1 / (1 + np.exp(-X @ beta))
            W = p * (1 - p)
            H = X.T @ (X * W[:, None])
            beta = beta + np.linalg.solve(H, X.T @ (yv - p))
        se = np.sqrt(np.diag(np.linalg.inv(H)))
        z = beta[1] / se[1]
        trend[side] = dict(n=int(len(g)), odds_ratio_per_year=float(np.exp(beta[1])),
                           or_lo95=float(np.exp(beta[1] - 1.96 * se[1])), or_hi95=float(np.exp(beta[1] + 1.96 * se[1])),
                           p_two_sided=float(2 * stats.norm.sf(abs(z))))
    json.dump(trend, open(TAB / "h3_trend.json", "w"), indent=2)
    print("trend:", json.dumps(trend))
    # interval LRs: all VCEP labels vs tool-independent labels
    out = []
    for t in ("revel", "am", "esm1b", "bayesdel"):
        for sub, d in (("all_vcep", m), ("tool_independent", m[~m.tool_dependent])):
            out += lr_table(d, t, "VCEP", seed=41, extra={"subset": sub})
            dp = pooled(d, t)
            dp[f"pts_{t}"] = dp.pts_pool
            for r in lr_table(dp, t, "VCEP", seed=42, extra={"subset": sub}):
                if r["points"] in (-3, 3):
                    r["points"] = "<= -3" if r["points"] == -3 else ">= +3"
                    out.append(r)
    h3 = pd.DataFrame(out)
    h3.to_csv(TAB / "h3_lr.csv", index=False)
    print(h3[h3.points.astype(str).str.contains("=")][["tool", "subset", "points", "n_P", "n_B", "lr", "lr_lo5", "lr_hi95"]].round(3).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
