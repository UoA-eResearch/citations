"""Reviewer check 5: loose report numbers. (a) Waikato 2023 site set behind 'mostly Coromandel'; (b) why
regional_2023.json carries two different Auckland 2024 numbers (1.10 vs 2.26); (c) 2024 composition by tercile for the
H1 persistence term; (d) H1 top vs bottom tercile = which harbours (spatial confounding). stdout -> check_misc.out."""
import sys
from pathlib import Path

import pandas as pd

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-2023-storms-estuary-mud-natural-experiment")
T = RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import analysis as A  # noqa: E402

raw = pd.read_excel(RUN / "data" / "raw" / "lawa_estuary_2025v2.xlsx", sheet_name="Data")
x = raw[raw.Indicator == "Mud_content"].copy()
dt = pd.to_datetime(x["Date sampled (YYYY/MM/DD)"], errors="coerce")
x["year"], x["month"] = dt.dt.year, dt.dt.month
x["y"] = pd.to_numeric(x["Indicator value"], errors="coerce")
x = x.dropna(subset=["y", "year"]).groupby(["Region", "LAWA Site ID", "Site name", "Estuary name", "year"]).agg(y=("y", "mean"), month=("month", "first")).reset_index()
pre = x[(x.year >= 2010) & (x.year <= 2022)]
n = pre.groupby("LAWA Site ID").year.nunique()
x = x[x["LAWA Site ID"].isin(set(n[n >= 5].index))].copy()
x["dev"] = x.y - x["LAWA Site ID"].map(pre.groupby("LAWA Site ID").y.mean())

print("== (a) Waikato sites with >= 5 pre-2023 years and a 2023 value ==")
w = x[(x.Region.str.strip() == "Waikato") & (x.year == 2023)]
print(w[["Site name", "Estuary name", "month", "dev"]].round(2).to_string(index=False))

print("\n== (b) regional_2023.json 'regions.Auckland' vs 'auckland' ==")
ak = x[x.Region.str.strip() == "Auckland"]
sites56 = set(pd.read_csv(T / "sites.csv").site_id)
print("Auckland sites with >=5 pre years (regions block):", ak["LAWA Site ID"].nunique(), "; with 2023:", ak[ak.year == 2023]["LAWA Site ID"].nunique(),
      "; with 2024:", ak[ak.year == 2024]["LAWA Site ID"].nunique(), "of which in the 56:", ak[(ak.year == 2024) & ak["LAWA Site ID"].isin(sites56)]["LAWA Site ID"].nunique())
a24 = ak[ak.year == 2024]
print("2024 mean dev, regions-block set:", round(a24.dev.mean(), 2), "; restricted to the 56:", round(a24[a24["LAWA Site ID"].isin(sites56)].dev.mean(), 2),
      "; the extra sites (not among the 56, no 2023 survey):", round(a24[~a24["LAWA Site ID"].isin(sites56)].dev.mean(), 2), "n =", int((~a24["LAWA Site ID"].isin(sites56)).sum()))
print("extra 2024 sites:", a24[~a24["LAWA Site ID"].isin(sites56)][["Site name", "Estuary name", "dev"]].round(1).to_string(index=False))

print("\n== (c) 2024 rows by tercile (H1 persistence term) ==")
d = A.load()
print(pd.crosstab(d[d.year.isin([2023, 2024])].year, d[d.year.isin([2023, 2024])].tercile))

print("\n== (d) H1 contrast = which harbours ==")
s = pd.read_csv(T / "sites.csv").merge(pd.read_csv(T / "exposure.csv")[["site_id", "tercile"]], on="site_id")
for t in ("top", "bottom"):
    print(t, s[s.tercile == t].estuary.value_counts().to_dict())
