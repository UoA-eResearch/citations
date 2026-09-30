#!/usr/bin/env python
"""Wastewater population coverage per state and FluSight season (covariate only; no hospital data).
At each FluSight reference date R (Saturday), the due date is D = R - 3 days (Wednesday) and a sample is available if
collected on or before D - LAG. A site is active if it has a sample collected in (D - LAG - 14 days, D - LAG].
Coverage = sum of population_served over unique active sites (max over sources for a site) / state population,
capped at 1; averaged over the season's reference dates.
Output: results/tables/ww_coverage.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW, PROC, TAB = RUN / "data" / "raw", RUN / "data" / "processed", RUN / "results" / "tables"
LAG = int(sys.argv[1]) if len(sys.argv) > 1 else 10


def season_of(r):
    return f"{r.year}-{str(r.year + 1)[2:]}" if r.month >= 8 else f"{r.year - 1}-{str(r.year)[2:]}"


def main():
    d = pd.read_parquet(PROC / "ww_samples.parquet")
    loc = pd.read_csv(RAW / "locations.csv", dtype={"location": str})
    pop = loc.set_index("abbreviation").population
    name2abbr = loc.set_index("location_name").abbreviation
    d["abbr"] = d.state_territory.str.upper().map(lambda s: s if s in pop.index else name2abbr.get(str(s).title()))
    print("unmapped jurisdictions:", sorted(d.loc[d.abbr.isna(), "state_territory"].unique()))
    refs = pd.to_datetime(pd.Series(open(RAW / "ensemble_reference_dates.txt").read().split()))
    rows = []
    for r in refs:
        hi = r - pd.Timedelta(days=3 + LAG)
        a = d[(d.collect > hi - pd.Timedelta(days=14)) & (d.collect <= hi)]
        cov = a.groupby(["abbr", "site"]).population_served.max().groupby("abbr").sum()
        nsite = a.groupby("abbr").site.nunique()
        for s in pop.index.drop("US"):
            rows.append(dict(reference_date=r.date(), season=season_of(r), abbr=s,
                             coverage=min(1.0, float(cov.get(s, 0)) / pop[s]), n_sites=int(nsite.get(s, 0))))
    c = pd.DataFrame(rows)
    s = c.groupby(["season", "abbr"]).agg(coverage=("coverage", "mean"), n_sites=("n_sites", "median")).reset_index()
    TAB.mkdir(parents=True, exist_ok=True)
    s.to_csv(TAB / f"ww_coverage{'' if LAG == 10 else f'_lag{LAG}'}.csv", index=False)
    for thr in (0.2, 0.3, 0.5):
        print(f"coverage >= {thr:.0%}:", s[s.coverage >= thr].groupby("season").abbr.count().to_dict())
    print(s.pivot(index="abbr", columns="season", values="coverage").round(2).to_string())


if __name__ == "__main__":
    sys.exit(main())
