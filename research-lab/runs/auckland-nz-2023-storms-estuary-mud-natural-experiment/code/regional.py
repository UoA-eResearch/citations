"""Post hoc (not preregistered; added after the H1/H2 results were read): the region-wide 2023 mud pulse.

1. Auckland, the 56 frozen sites: mean deviation of mud content from each site's 2010-2022 mean, by year, with a
   site-cluster bootstrap interval for 2023 (B = 2,000, seed 20261023). The fixed-effects design absorbs any shared
   2023 jump into the year effect, so H1/H2 cannot see it.
2. Every LAWA region: sites with mud content in at least 5 years from 2010 to 2022; the same deviation in 2023 and 2024,
   the range of pre-2023 yearly means, and the 2023 sampling months. Exploratory: other regions are small, sample in
   different months, and none is a clean control.

Writes results/tables/regional_2023.json and results/tables/auckland_yearly_deviation.csv.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"


def main():
    d = A.load()
    base = d[d.year <= 2022].groupby("site_id").y.mean()
    d["dev"] = d.y - d.site_id.map(base)
    yr = d.groupby("year").dev.agg(["mean", "median", "count"]).round(3)
    yr.to_csv(T / "auckland_yearly_deviation.csv")
    rng = np.random.default_rng(A.SEED)
    sites = d.site_id.unique()
    by = {s: x for s, x in d.groupby("site_id")}
    boot = []
    for _ in range(2000):
        x = pd.concat([by[s] for s in rng.choice(sites, len(sites))])
        boot.append(x[x.year == 2023].dev.mean())
    out = {"auckland": {"sites": int(len(sites)), "dev_2023": round(float(d[d.year == 2023].dev.mean()), 3),
                        "dev_2023_site_bootstrap_ci": [round(float(v), 3) for v in np.percentile(boot, [2.5, 97.5])],
                        "dev_2024": round(float(d[d.year == 2024].dev.mean()), 3),
                        "pre_year_mean_range": [round(float(yr.loc[2010:2022, "mean"].min()), 3),
                                                round(float(yr.loc[2010:2022, "mean"].max()), 3)],
                        "share_sites_up_2023": round(float((d[d.year == 2023].dev > 0).mean()), 3),
                        "dev_2023_by_tercile": d[d.year == 2023].groupby("tercile").dev.mean().round(3).to_dict()}}
    x = pd.read_excel(RUN / "data" / "raw" / "lawa_estuary_2025v2.xlsx", sheet_name="Data")
    x = x[x.Indicator == "Mud_content"].copy()
    dt = pd.to_datetime(x["Date sampled (YYYY/MM/DD)"], errors="coerce")
    x["year"], x["month"] = dt.dt.year, dt.dt.month
    x["y"] = pd.to_numeric(x["Indicator value"], errors="coerce")
    x = x.dropna(subset=["y", "year"]).groupby(["Region", "LAWA Site ID", "year"]).agg(y=("y", "mean"), month=("month", "first")).reset_index()
    pre = x[(x.year >= 2010) & (x.year <= 2022)]
    n = pre.groupby("LAWA Site ID").year.nunique()
    x = x[x["LAWA Site ID"].isin(set(n[n >= 5].index))].copy()
    x["dev"] = x.y - x["LAWA Site ID"].map(pre.groupby("LAWA Site ID").y.mean())
    reg = {}
    for r, g in x.groupby("Region"):
        g23 = g[g.year == 2023]
        if len(g23) < 3:
            continue
        pm = g[(g.year >= 2010) & (g.year <= 2022)].groupby("year").dev.mean()
        reg[r] = {"sites_2023": int(len(g23)), "dev_2023": round(float(g23.dev.mean()), 2),
                  "dev_2024": round(float(g[g.year == 2024].dev.mean()), 2) if (g.year == 2024).any() else None,
                  "pre_year_mean_range": [round(float(pm.min()), 2), round(float(pm.max()), 2)],
                  "months_2023": sorted(g23.month.dropna().astype(int).unique().tolist())}
    out["regions"] = reg
    json.dump(out, open(T / "regional_2023.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
