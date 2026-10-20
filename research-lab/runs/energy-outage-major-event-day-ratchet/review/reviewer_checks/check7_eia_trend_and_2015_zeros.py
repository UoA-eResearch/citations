"""Reviewer check 7: (a) which included state has ~46% zero days in 2015 and when those zeros fall (coverage start);
(b) on the same state-years, the pooled FE trend with state-cluster bootstrap intervals of the utilities' own EIA-861
SAIDI (IEEE-method utilities, customer-weighted) with and without MEDs, against the EAGLE-I all-events and rolling
MED-excluded indices, for 2020-2024 and, where EIA 2025 exists, 2020-2025. Writes check7.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
T = RUN / "results" / "tables"
out = {}
d = pd.read_csv(RUN / "data" / "daily.csv"); d["year"] = d.date.str[:4].astype(int); d["month"] = d.date.str[5:7].astype(int)
incl = json.load(open(T / "primary.json"))["included"]
d = d[d.st.isin(incl)]
z = d[d.year == 2015].assign(z=lambda x: x.saidi == 0).groupby("st").z.mean().sort_values(ascending=False)
out["zero_share_2015_top"] = z.head(5).round(3).to_dict()
top = z.index[0]
out["zero_share_2015_by_month_" + top] = d[(d.st == top) & (d.year == 2015)].assign(z=lambda x: x.saidi == 0).groupby("month").z.mean().round(2).to_dict()
out["zero_share_by_year_" + top] = d[d.st == top].assign(z=lambda x: x.saidi == 0).groupby("year").z.mean().round(3).to_dict()
out["annual_saidi_" + top] = d[d.st == top].groupby("year").saidi.sum().round(1).to_dict()
out["n_counties_reporting_" + top] = pd.read_csv(RUN / "data" / "county_reporting.csv").query("st == @top").set_index("year").n_counties.to_dict()


def fe_trend(df, col):
    y = np.log(df[col].values + 1.0); x = df.year.values.astype(float); g = df.st.values
    yd = y - pd.Series(y).groupby(g).transform("mean").values; xd = x - pd.Series(x).groupby(g).transform("mean").values
    return 100 * (np.exp((xd @ yd) / (xd @ xd)) - 1)


def cboot(df, f, B=2000, seed=20261018):
    rng = np.random.default_rng(seed); sts = df.st.unique(); grp = {s: x for s, x in df.groupby("st")}; v = []
    for _ in range(B):
        pick = rng.choice(sts, len(sts)); v.append(f(pd.concat([grp[s].assign(st=f"{s}_{k}") for k, s in enumerate(pick)])))
    return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]


e = pd.read_parquet(RUN / "data" / "raw" / "core_eia861__yearly_reliability.parquet")
e["year"] = pd.to_datetime(e.report_date).dt.year
e = e[(e.standard == "ieee_standard") & (e.customers > 0)]
w = lambda col: e[e[col].notna()].groupby(["state", "year"]).apply(lambda x: np.average(x[col], weights=x.customers), include_groups=False)
ew = w("saidi_w_major_event_days_minutes").rename("eia_all"); ewo = w("saidi_wo_major_event_days_minutes").rename("eia_noMED")
ew.index.names = ewo.index.names = ["st", "year"]
sy = pd.read_csv(T / "state_year.csv").set_index(["st", "year"])[["all", "noMED_roll", "noMED_frozen"]]
ea = d.groupby(["st", "year"]).saidi.sum().rename("eaglei_all")
j = pd.concat([ea, sy, ew, ewo], axis=1, join="inner").reset_index()
out["eia_years_available_for_included_states"] = sorted(j.year.unique().tolist())
for lo, hi in ((2020, 2024), (2020, 2025)):
    k = j[j.year.between(lo, hi)].dropna()
    if k.year.nunique() < hi - lo + 1:
        continue
    r = dict(n=int(len(k)), n_states=int(k.st.nunique()))
    for col in ["eaglei_all", "eia_all", "noMED_roll", "noMED_frozen", "eia_noMED"]:
        r[col] = dict(trend=fe_trend(k, col), ci=cboot(k, lambda x, c=col: fe_trend(x, c)))
    diff = lambda x: fe_trend(x, "noMED_roll") - fe_trend(x, "eia_noMED")
    r["roll_minus_eia_noMED"] = dict(diff=diff(k), ci=cboot(k, diff))
    diff2 = lambda x: fe_trend(x, "eaglei_all") - fe_trend(x, "eia_all")
    r["eaglei_all_minus_eia_all"] = dict(diff=diff2(k), ci=cboot(k, diff2))
    # the utilities' own masking: EIA noMED trend / EIA all trend, and MED share of SAIDI
    r["eia_MED_share_of_saidi_by_year"] = (1 - k.groupby("year").eia_noMED.mean() / k.groupby("year").eia_all.mean()).round(3).to_dict()
    r["eaglei_MED_share_of_saidi_by_year"] = (1 - k.groupby("year").noMED_roll.mean() / k.groupby("year").eaglei_all.mean()).round(3).to_dict()
    out[f"{lo}_{hi}"] = r
json.dump(out, open(HERE / "check7.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
