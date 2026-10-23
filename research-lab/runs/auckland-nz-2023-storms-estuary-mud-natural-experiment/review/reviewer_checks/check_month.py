"""Reviewer check 6: do the 2023 rises track the sampling month (15 November rows in 2023 vs 4 in other years), and
which sites carry the year-only (1 Jan) dates? stdout -> check_month.out."""
import sys
from pathlib import Path
import pandas as pd
RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-2023-storms-estuary-mud-natural-experiment")
sys.path.insert(0, str(RUN / "code"))
import analysis as A
raw = pd.read_excel(RUN / "data" / "raw" / "lawa_estuary_2025v2.xlsx", sheet_name="Data")
ak = raw[(raw["Council/Agency"] == "Auckland Council") & (raw.Indicator == "Mud_content")].copy()
ak["dt"] = pd.to_datetime(ak["Date sampled (YYYY/MM/DD)"]); ak["year"] = ak.dt.dt.year; ak["month"] = ak.dt.dt.month
ak = ak.rename(columns={"LAWA Site ID": "site_id"})[["site_id", "year", "month", "dt"]]
d = A.load().merge(ak, on=["site_id", "year"])
base = d[d.year <= 2022].groupby("site_id").y.mean(); d["dev"] = d.y - d.site_id.map(base)
d23 = d[d.year == 2023]
print("2023 deviation by sampling month:"); print(d23.groupby("month").dev.agg(["mean", "median", "count"]).round(2))
print("2023 November sites:", d23[d23.month == 11][["site_id", "estuary", "dt", "dev"]].sort_values("dev").round(1).to_string(index=False))
print("\n2023 sampling dates (distinct):", sorted(d23.dt.dt.strftime("%Y-%m-%d").unique().tolist()))
print("usual month of each November-2023 site in 2015-2022:")
nov = d23[d23.month == 11].site_id
print(d[d.site_id.isin(nov) & d.year.between(2015, 2022)].groupby("site_id").month.agg(lambda s: sorted(s.unique().tolist())).to_dict())
print("\nyear-only (1 Jan) rows: sites and years")
yo = d[(d.month == 1)]
print(yo.groupby("site_id").year.agg(list).to_dict())
