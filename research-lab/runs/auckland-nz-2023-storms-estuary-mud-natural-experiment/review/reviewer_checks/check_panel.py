"""Reviewer check 1: panel structure, tercile construction, site composition by year, and the post-hoc 2023 pulse.

Read-only on the study. Writes review/reviewer_checks/check_panel.out (via stdout redirect).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path("/mnt/citations/research-lab/runs/auckland-nz-2023-storms-estuary-mud-natural-experiment")
T = RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import analysis as A  # noqa: E402

pd.set_option("display.width", 200, "display.max_columns", 30, "display.max_rows", 200)

raw = pd.read_excel(RUN / "data" / "raw" / "lawa_estuary_2025v2.xlsx", sheet_name="Data")
print("sheets:", pd.ExcelFile(RUN / "data" / "raw" / "lawa_estuary_2025v2.xlsx").sheet_names)
print("columns:", list(raw.columns))
ak = raw[(raw["Council/Agency"] == "Auckland Council") & (raw.Indicator == "Mud_content")].copy()
ak["dt"] = pd.to_datetime(ak["Date sampled (YYYY/MM/DD)"])
ak["year"] = ak.dt.dt.year
ak["y"] = pd.to_numeric(ak["Indicator value"], errors="coerce")
sites = pd.read_csv(T / "sites.csv")
ex = pd.read_csv(T / "exposure.csv")
a56 = ak[ak["LAWA Site ID"].isin(sites.site_id)]

print("\n== 1. one row per site-year? ==")
dup = a56.groupby(["LAWA Site ID", "year"]).size()
print("site-years with >1 row:", int((dup > 1).sum()), "; NaN values:", int(a56.y.isna().sum()))
print("rows 2010-2024:", int(a56.year.between(2010, 2024).sum()), "(primary.json panel rows = 712)")
print("rows outside 2010-2024 at these sites:", a56[~a56.year.between(2010, 2024)].year.value_counts().sort_index().to_dict())
yo = a56[(a56.dt.dt.month == 1) & (a56.dt.dt.day == 1)]
print("year-only (1 Jan) rows by year:", yo.year.value_counts().sort_index().to_dict())
print("month of sampling by year (counts):")
print(pd.crosstab(a56.year, a56.dt.dt.month))

print("\n== 2. design matrix rank ==")
d = A.load()
for name, fn in (("H1", lambda: A.h1), ("H2", None)):
    pass
x = d[d.tercile.isin(["top", "bottom"])].copy()
x["top"] = (x.tercile == "top").astype(float)
x["top_2023"] = x.top * (x.year == 2023)
x["top_2024"] = x.top * (x.year == 2024)
X, names = A.design(x, ["top_2023", "top_2024"])
print("H1: n =", X.shape[0], "k =", X.shape[1], "rank =", np.linalg.matrix_rank(X))
x2 = d.copy()
x2["E_2023"] = x2.E_route_5 * (x2.year == 2023)
x2["E_2024"] = x2.E_route_5 * (x2.year == 2024)
X2, names2 = A.design(x2, ["E_2023", "E_2024"])
print("H2: n =", X2.shape[0], "k =", X2.shape[1], "rank =", np.linalg.matrix_rank(X2))

print("\n== 3. terciles: built from exposure only? ==")
t_re = A.terciles(ex.set_index("site_id").E_route_5)
print("terciles() in analysis.py reproduces exposure.csv tercile:", bool((t_re.values == ex.tercile.values).all()))
print("tercile counts:", ex.tercile.value_counts().to_dict())
print("tercile by harbour (sites):")
print(pd.crosstab(sites.set_index("site_id").estuary, ex.set_index("site_id").tercile))

print("\n== 4. site composition by year and tercile ==")
d2 = d.merge(sites[["site_id", "pre_years", "has_2024"]], on="site_id")
print(pd.crosstab(d2.year, d2.tercile, margins=True))
print("\nsites with exactly 5-6 pre-2023 years: their sampled years")
few = sites[sites.pre_years <= 6].site_id
for s in few:
    yrs = sorted(d[d.site_id == s].year.tolist())
    print(f"  {s} {sites.set_index('site_id').site_name[s]:<22} {sites.set_index('site_id').estuary[s]:<30} tercile={ex.set_index('site_id').tercile[s]:<7} years={yrs}")
print("\nlast pre-2023 sampling year per site (counts):")
last = d[d.year <= 2022].groupby("site_id").year.max()
print(last.value_counts().sort_index().to_dict())

print("\n== 5. the post-hoc 2023 pulse: composition ==")
base = d[d.year <= 2022].groupby("site_id").y.mean()
d["dev"] = d.y - d.site_id.map(base)
d["last_pre"] = d.site_id.map(last)
d["gap"] = d.year - d.last_pre
d23 = d[d.year == 2023]
print("all 56: mean dev 2023 =", round(d23.dev.mean(), 3), " median =", round(d23.dev.median(), 3))
cont = d23[d23.last_pre >= 2021]
ret = d23[d23.last_pre < 2021]
print(f"sites last sampled 2021-22 (n={len(cont)}): mean dev 2023 = {cont.dev.mean():.3f}, median {cont.dev.median():.3f}, share up {(cont.dev > 0).mean():.2f}")
print(f"sites returning after a gap (last pre year < 2021; n={len(ret)}): mean dev 2023 = {ret.dev.mean():.3f}, median {ret.dev.median():.3f}")
print(ret[["site_id", "estuary", "tercile", "last_pre", "gap", "y", "dev"]].assign(base=lambda z: z.site_id.map(base)).round(2).to_string(index=False))
print("\n2023 mean dev by tercile, continuous sites only:")
print(cont.groupby("tercile").dev.agg(["mean", "median", "count"]).round(2))
print("2023 mean dev by tercile, all:")
print(d23.groupby("tercile").dev.agg(["mean", "median", "count"]).round(2))
print("\n2023 mean dev by harbour:")
print(d23.groupby("estuary").dev.agg(["mean", "median", "count"]).round(2).sort_values("mean"))
print("\n2024: sites with 2024 =", int((d.year == 2024).sum()), "; their 2023 mean dev =",
      round(d23[d23.site_id.isin(d[d.year == 2024].site_id)].dev.mean(), 3),
      "; their 2024 mean dev =", round(d[d.year == 2024].dev.mean(), 3))
print("sites without 2024: their 2023 mean dev =", round(d23[~d23.site_id.isin(d[d.year == 2024].site_id)].dev.mean(), 3),
      "n =", int((~d23.site_id.isin(d[d.year == 2024].site_id)).sum()))

print("\n== 6. yearly mean deviation, leave-that-year-out baseline (fair comparison for 'largest since 2010') ==")
rows = []
for yr in range(2010, 2025):
    b = d[(d.year <= 2022) & (d.year != yr)].groupby("site_id").y.mean()
    z = d[d.year == yr]
    dv = z.y - z.site_id.map(b)
    rows.append({"year": yr, "n": len(z), "mean_dev_loo": round(dv.mean(), 2), "median_dev_loo": round(dv.median(), 2),
                 "mean_dev_in_baseline": round(z.dev.mean(), 2)})
print(pd.DataFrame(rows).to_string(index=False))

print("\n== 7. harbour-cluster bootstrap for the 2023 pulse (site bootstrap in the report) ==")
rng = np.random.default_rng(1)
harb = d23.estuary.unique()
by = {h: g.dev.to_numpy() for h, g in d23.groupby("estuary")}
bt = [np.concatenate([by[h] for h in rng.choice(harb, len(harb))]).mean() for _ in range(4000)]
print("harbour-cluster bootstrap 95%:", np.round(np.percentile(bt, [2.5, 97.5]), 2), "(report: site bootstrap 2.26 to 6.30)")
byc = {h: g.dev.to_numpy() for h, g in cont.groupby("estuary")}
hc = list(byc)
bt2 = [np.concatenate([byc[h] for h in rng.choice(hc, len(hc))]).mean() for _ in range(4000)]
print("continuous sites only, harbour-cluster bootstrap 95%:", np.round(np.percentile(bt2, [2.5, 97.5]), 2))
pre_yr = d[d.year <= 2022].groupby("year").dev.mean()
print("SD of pre-2023 yearly means (in-baseline):", round(pre_yr.std(), 2))

print("\n== 8. value precision by year (a laboratory/reporting change would show here) ==")
def decimals(v):
    s = f"{v:.6f}".rstrip("0").split(".")
    return len(s[1]) if len(s) > 1 else 0
a56 = a56.assign(dec=a56.y.map(decimals))
print(pd.crosstab(a56.year, a56.dec))
print("share of values that are whole numbers, by year:")
print(a56.groupby("year").dec.apply(lambda s: round((s == 0).mean(), 2)).to_dict())

print("\n== 9. event study: pre-period variability of top-minus-bottom ==")
es = pd.read_csv(T / "event_study.csv").set_index("year")
pre = es.loc[2010:2021, "top_minus_bottom"]
print("2010-2021 top-bottom: mean", round(pre.mean(), 2), "SD", round(pre.std(), 2), "; 2022 =", es.loc[2022, "top_minus_bottom"],
      "; 2023 =", es.loc[2023, "top_minus_bottom"], f"({(es.loc[2023, 'top_minus_bottom'] - pre.mean()) / pre.std():.1f} SD)")
# FE placebo for 2022 and a linear pre-trend
pre_d = d[(d.year <= 2022) & d.tercile.isin(["top", "bottom"])].copy()
pre_d["top_P"] = (pre_d.tercile == "top").astype(float) * (pre_d.year == 2022)
Xp, np_ = A.design(pre_d, ["top_P"])
_, bp = A.ols(Xp, pre_d.y.to_numpy(float))
print("FE placebo beta for 2022 (pre-2023 data):", round(float(bp[np_.index("top_P")]), 3))
pre_d["top_trend"] = (pre_d.tercile == "top").astype(float) * (pre_d.year - 2016)
Xt, nt = A.design(pre_d, ["top_trend"])
_, bt_ = A.ols(Xt, pre_d.y.to_numpy(float))
print("FE linear differential pre-trend (pp per year, top vs bottom, 2010-2022):", round(float(bt_[nt.index("top_trend")]), 3))

print("\n== 10. other outcomes: macrofauna values and metadata ==")
mac = raw[(raw["Council/Agency"] == "Auckland Council") & (raw.Indicator == "Macrofauna")]
print("Macrofauna value range:", pd.to_numeric(mac["Indicator value"], errors="coerce").describe().round(2).to_dict())
for c in raw.columns:
    if raw[c].dtype == object and raw[c].nunique() < 40 and c not in ("Indicator value",):
        print(f"  {c}: {raw[c].dropna().unique()[:40].tolist()}")
print("Indicators:", raw.Indicator.unique().tolist())
# other sheets
xl = pd.ExcelFile(RUN / "data" / "raw" / "lawa_estuary_2025v2.xlsx")
for sh in xl.sheet_names:
    if sh != "Data":
        s = xl.parse(sh, header=None)
        print(f"--- sheet {sh}: shape {s.shape}")
        print(s.head(60).to_string())

print("\n== 11. Waikato 2023 sites (report: 'mostly Coromandel') ==")
w = raw[(raw.Region.astype(str).str.strip() == "Waikato") & (raw.Indicator == "Mud_content")].copy()
w["year"] = pd.to_datetime(w["Date sampled (YYYY/MM/DD)"], errors="coerce").dt.year
print(w[w.year == 2023][["LAWA Site ID", "Site name", "Estuary name"]].drop_duplicates().to_string(index=False))
