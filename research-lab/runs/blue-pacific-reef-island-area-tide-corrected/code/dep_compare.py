"""Secondary (plan section 4): Digital Earth Pacific Coastlines against this study's Sentinel-2 epoch rates.

DEP's per-point annual shoreline distances near each islet (dep_audit.py) give an areal rate:
100 x (mean seaward rate, m/yr) x perimeter / OSM area, in %/yr of the OSM area (the D3 reference).
- Full record: DEP's own rate_time (1999-2023).
- Late: least-squares slope of DEP's annual distances over 2016-2023, the window that overlaps Sentinel-2.

Compared, over retained non-engineered islets with at least 5 DEP points, against the corrected and uncorrected
Sentinel-2 rates: Pearson and Spearman correlation, mean difference, and mean absolute difference.

Writes results/tables/dep_compare.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"


def main():
    dep = pd.read_csv(T / "dep_audit_islets.csv")
    dep = dep[dep.dep_points >= 5].copy()
    dep["dep_late_pct"] = 100 * dep.dep_late_m_yr * dep.perimeter_m / dep.area_m2
    r = pd.read_csv(T / "islet_rates.csv")
    r = r[(r.family == "E2") & (r.series == "area_otsu") & (r.robust_slope == 0) & (r.engineered == 0)
          & (r.possible_loss == 0)]
    x = r.merge(dep[["islet", "dep_points", "dep_area_rate_pct", "dep_late_pct"]], on="islet")
    out = {"islets": int(len(x)), "atolls": int(x.atoll.nunique())}
    for dcol in ("dep_late_pct", "dep_area_rate_pct"):
        for ocol in ("rate_corr", "rate_uncorr"):
            z = x[[dcol, ocol]].dropna()
            out[f"{dcol}_vs_{ocol}"] = {
                "n": int(len(z)), "pearson": round(float(stats.pearsonr(z[dcol], z[ocol])[0]), 3),
                "spearman": round(float(stats.spearmanr(z[dcol], z[ocol])[0]), 3),
                "mean_diff_ours_minus_dep": round(float((z[ocol] - z[dcol]).mean()), 3),
                "mean_abs_diff": round(float((z[ocol] - z[dcol]).abs().mean()), 3)}
    out["by_atoll_late"] = {k: {"islets": int(len(g)), "dep_late_mean": round(float(g.dep_late_pct.mean()), 3),
                                "ours_corr_mean": round(float(g.rate_corr.mean()), 3),
                                "ours_uncorr_mean": round(float(g.rate_uncorr.mean()), 3)}
                            for k, g in x.groupby("atoll")}
    json.dump(out, open(T / "dep_compare.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
