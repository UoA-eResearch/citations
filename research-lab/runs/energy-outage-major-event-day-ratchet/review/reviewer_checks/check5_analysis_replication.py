"""Reviewer check 5: independent re-implementation of analysis.py from data/daily.csv (nothing imported from code/).
  (a) inclusion rule as preregistered; (b) thresholds, indices and MED counts vs results/tables/state_year.csv;
  (c) FE trends and state-cluster bootstrap vs primary.json; H1/H2 rules; (d) decomposition vs decomposition.csv and the
  plan's labelling; (e) validation: pooled Spearman as preregistered, plus within-state (temporal) Spearman and the
  Spearman of year-on-year log changes, which is what matters for trend claims; (f) baseline-window diagnostics: annual
  alpha/beta per state 2015-2019 (coverage growth in the window would depress early alpha), H2 with the frozen threshold
  from 2017-2019 and from 2018-2022, trends without 2020; (g) threshold vs the simulation's 95th-percentile tail cut-off.
Writes check5_analysis_replication.json and prints a summary."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
T = RUN / "results" / "tables"
YEARS = list(range(2020, 2026))
out = {}

d = pd.read_csv(RUN / "data" / "daily.csv")
d["year"] = d.date.str[:4].astype(int)
assert len(d) == 51 * 4018, len(d)
assert (d.groupby("st").size() == 4018).all()

# (a) inclusion
cov = pd.read_csv(RUN / "data" / "raw" / "coverage_history.csv")
cov["year"] = pd.to_datetime(cov.year, format="%m/%d/%y").dt.year
assert sorted(cov.year.unique()) == [2018, 2019, 2020, 2021, 2022]
ok_cov = cov.groupby("state").max_pct_covered.min()
ok_cov = set(ok_cov[ok_cov >= 0.80].index)
cr = pd.read_csv(RUN / "data" / "county_reporting.csv")
med = cr[cr.year.between(2018, 2022)].groupby("st").n_counties.median()
piv = cr.pivot(index="st", columns="year", values="n_counties")
dev = (piv.div(med, axis=0) - 1).abs()
stable = set(dev.index[(dev.max(axis=1) <= 0.15) & dev.notna().all(axis=1)])
incl = sorted(ok_cov & stable & set(d.st))
p = json.load(open(T / "primary.json"))
out["inclusion"] = dict(mine=incl, theirs=p["included"], match=incl == p["included"],
                        n_cov_ok_states=len(ok_cov & set(d.st)), n_cov_ok_all=len(ok_cov))
# how close to the 15% edge are the included states, and in which years
edge = dev.loc[incl].max(axis=1).sort_values(ascending=False)
out["inclusion_max_dev_included"] = edge.round(3).to_dict()
out["county_dev_2015_2016_included"] = (piv.loc[incl, [2015, 2016, 2017]].div(med[incl], axis=0) - 1).round(3).to_dict()
d = d[d.st.isin(incl)].copy()


def thr(x):
    v = np.log(x[x > 0])
    return float(np.exp(v.mean() + 2.5 * v.std(ddof=1)))


# (b) thresholds and indices
rows = []
for st, g in d.groupby("st"):
    s = g.set_index("year").saidi
    base = s.loc[2015:2019].values
    tf, q99 = thr(base), float(np.quantile(base, 0.99))
    for Y in YEARS:
        cur = s.loc[Y].values
        tr = thr(s.loc[Y - 5:Y - 1].values)
        rows.append(dict(st=st, year=Y, all=cur.sum(), t_roll=tr, t_frozen=tf, t_q99=q99, noMED_roll=cur[cur <= tr].sum(),
                         noMED_frozen=cur[cur <= tf].sum(), noMED_q99=cur[cur <= q99].sum(),
                         n_MED_roll=int((cur > tr).sum()), n_MED_frozen=int((cur > tf).sum()),
                         noMED_10y=cur[cur <= thr(s.loc[2015:2024].values)].sum() if Y == 2025 else np.nan))
idx = pd.DataFrame(rows)
sy = pd.read_csv(T / "state_year.csv")
m = idx.merge(sy, on=["st", "year"], suffixes=("", "_t"))
out["state_year_max_abs_diff"] = {c: float((m[c] - m[c + "_t"]).abs().max()) for c in
                                  ["all", "t_roll", "t_frozen", "t_q99", "noMED_roll", "noMED_frozen", "noMED_q99", "n_MED_roll", "n_MED_frozen"]}
out["noMED_10y_2025_max_abs_diff"] = float((m[m.year == 2025].noMED_10y - m[m.year == 2025].noMED_10y_t).abs().max())


# (c) trends and bootstrap
def fe_trend(df, col):
    y = np.log(df[col].values + 1.0); x = df.year.values.astype(float)
    g = df.st.values
    yd = y - pd.Series(y).groupby(g).transform("mean").values; xd = x - pd.Series(x).groupby(g).transform("mean").values
    return 100 * (np.exp((xd @ yd) / (xd @ xd)) - 1)


def cboot(df, f, B=2000, seed=20261018):
    rng = np.random.default_rng(seed)
    sts = df.st.unique(); grp = {s: x for s, x in df.groupby("st")}
    v = []
    for _ in range(B):
        pick = rng.choice(sts, len(sts), replace=True)
        v.append(f(pd.concat([grp[s].assign(st=f"{s}_{k}") for k, s in enumerate(pick)])))
    v = np.array(v)
    return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]


tr = {}
for c in ["all", "noMED_roll", "noMED_frozen", "noMED_q99"]:
    tr[c] = dict(trend=fe_trend(idx, c), ci=cboot(idx, lambda x, c=c: fe_trend(x, c)), theirs=p["trends"][c])
out["trends"] = tr
h2 = lambda x: fe_trend(x, "noMED_roll") - fe_trend(x, "noMED_frozen")
h2ci = cboot(idx, h2)
out["H2"] = dict(diff=h2(idx), ci=h2ci, verdict="Supported" if h2ci[1] < 0 else "Refuted" if h2ci[0] > 0 else "Inconclusive",
                 theirs=p["H2"])
h1 = lambda x: fe_trend(x, "noMED_roll") / fe_trend(x, "all")
out["H1"] = dict(ratio=h1(idx), ci=cboot(idx, h1), all_ci_includes_0=tr["all"]["ci"][0] <= 0 <= tr["all"]["ci"][1], theirs=p["H1"])
# per-state slopes, to see what drives the pooled trend
ps = idx.groupby("st").apply(lambda g: pd.Series({c: 100 * (np.exp(np.polyfit(g.year, np.log(g[c] + 1), 1)[0]) - 1)
                                                  for c in ["all", "noMED_roll", "noMED_frozen"]}), include_groups=False)
out["per_state_slopes"] = ps.round(2).to_dict()
out["per_state_slope_medians"] = ps.median().round(2).to_dict()
# H2 as the share of the rolling trend that is threshold effect
out["frozen_over_rolling_trend"] = tr["noMED_frozen"]["trend"] / tr["noMED_roll"]["trend"]

# (d) decomposition
dec_rows = []
for st, g in d.groupby("st"):
    s = g.set_index("year").saidi
    a20, a25 = s.loc[2020].values, s.loc[2025].values
    t20, t25 = thr(s.loc[2015:2019].values), thr(s.loc[2020:2024].values)
    N = lambda a, t: a[a <= t].sum()
    y1 = N(a25, t20) - N(a20, t20); r1 = N(a25, t25) - N(a25, t20)
    r2 = N(a20, t25) - N(a20, t20); y2 = N(a25, t25) - N(a20, t25)
    tot = a25.sum() - a20.sum()
    non, rec = (y1 + y2) / 2, (r1 + r2) / 2
    dec_rows.append(dict(st=st, total=tot, nonMED_growth=non, reclassification=rec, MED_growth=tot - non - rec,
                         MED_growth_fixed2020_class=tot - y1, nonMED_growth_fixed2020_class=y1, reclass_2025days=r1))
dec = pd.DataFrame(dec_rows)
dt = pd.read_csv(T / "decomposition.csv")
mm = dec.merge(dt, on="st", suffixes=("", "_t"))
out["decomposition_max_abs_diff"] = {c: float((mm[c] - mm[c + "_t"]).abs().max()) for c in ["total", "nonMED_growth", "reclassification", "MED_growth"]}
out["decomposition_medians"] = dec.drop(columns="st").median().round(2).to_dict()
out["decomposition_n_positive_nonMED"] = int((dec.nonMED_growth > 0).sum())
out["decomposition_sum_check"] = float((dec.nonMED_growth + dec.reclassification + dec.MED_growth - dec.total).abs().max())

# (e) validation
e = pd.read_parquet(RUN / "data" / "raw" / "core_eia861__yearly_reliability.parquet")
e["year"] = pd.to_datetime(e.report_date).dt.year
e = e[(e.standard == "ieee_standard") & (e.customers > 0) & e.saidi_w_major_event_days_minutes.notna()]
ew = e.groupby(["state", "year"]).apply(lambda x: np.average(x.saidi_w_major_event_days_minutes, weights=x.customers), include_groups=False); ew.index.names = ["st", "year"]
nut = e.groupby(["state", "year"]).size(); nut.index.names = ["st", "year"]
ecust = e.groupby(["state", "year"]).customers.sum(); ecust.index.names = ["st", "year"]
ea = d.groupby(["st", "year"]).saidi.sum()
j = pd.concat([ea.rename("eaglei"), ew.rename("eia"), nut.rename("n_utilities"), ecust.rename("eia_customers")], axis=1, join="inner").reset_index()
j = j[j.year.between(2018, 2024)]
out["validation"] = dict(n=int(len(j)), pooled_spearman=float(stats.spearmanr(j.eaglei, j.eia).statistic), theirs=p["validation"])
within = j.groupby("st").apply(lambda g: stats.spearmanr(g.eaglei, g.eia).statistic if len(g) >= 5 else np.nan, include_groups=False)
out["validation_within_state_spearman"] = dict(median=float(within.median()), mean=float(within.mean()), n_states=int(within.notna().sum()),
                                               n_negative=int((within < 0).sum()), per_state=within.round(2).to_dict())
jd = j.sort_values(["st", "year"]).copy()
jd["d_eaglei"] = jd.groupby("st").eaglei.transform(lambda s: np.log(s).diff()); jd["d_eia"] = jd.groupby("st").eia.transform(lambda s: np.log(s).diff())
jd = jd.dropna()
out["validation_yoy_log_change_spearman"] = dict(n=int(len(jd)), rho=float(stats.spearmanr(jd.d_eaglei, jd.d_eia).statistic),
                                                 pearson=float(np.corrcoef(jd.d_eaglei, jd.d_eia)[0, 1]))
jm = j.copy(); jm["eaglei_dm"] = np.log(jm.eaglei) - jm.groupby("st").eaglei.transform(lambda s: np.log(s).mean())
jm["eia_dm"] = np.log(jm.eia) - jm.groupby("st").eia.transform(lambda s: np.log(s).mean())
out["validation_within_state_demeaned_log_spearman"] = float(stats.spearmanr(jm.eaglei_dm, jm.eia_dm).statistic)
out["validation_level_ratio_eaglei_over_eia"] = dict(median=float((j.eaglei / j.eia).median()), q25=float((j.eaglei / j.eia).quantile(0.25)),
                                                     q75=float((j.eaglei / j.eia).quantile(0.75)))
# trend agreement 2018-2024: FE trend of the two all-events series on the same state-years
jt = j.rename(columns={"st": "st"})
out["validation_fe_trend_2018_2024"] = dict(eaglei=fe_trend(jt, "eaglei"), eia=fe_trend(jt, "eia"))
jt2 = jt[jt.year >= 2020]
out["validation_fe_trend_2020_2024"] = dict(eaglei=fe_trend(jt2, "eaglei"), eia=fe_trend(jt2, "eia"), n=int(len(jt2)))
# MED-excluded comparison too (EIA wo MED vs rolling noMED), 2020-2024
e2 = e[e.saidi_wo_major_event_days_minutes.notna()]
ewo = e2.groupby(["state", "year"]).apply(lambda x: np.average(x.saidi_wo_major_event_days_minutes, weights=x.customers), include_groups=False); ewo.index.names = ["st", "year"]
k = idx.set_index(["st", "year"]).noMED_roll.rename("eaglei_noMED")
k = pd.concat([k, ewo.rename("eia_noMED")], axis=1, join="inner").reset_index()
k = k[k.year.between(2020, 2024)]
out["validation_noMED_2020_2024"] = dict(n=int(len(k)), pooled_spearman=float(stats.spearmanr(k.eaglei_noMED, k.eia_noMED).statistic),
                                         fe_trend_eaglei=fe_trend(k, "eaglei_noMED"), fe_trend_eia=fe_trend(k, "eia_noMED"))
ea_all = d.groupby(["st", "year"]).saidi.sum().rename("eaglei_all").reset_index()
ea_all = ea_all[ea_all.year.between(2020, 2024)]
out["eaglei_all_events_fe_trend_2020_2024"] = fe_trend(ea_all, "eaglei_all")

# (f) baseline-window diagnostics
ab = d[d.saidi > 0].assign(l=lambda x: np.log(x.saidi)).groupby(["st", "year"]).l.agg(["mean", "std", "size"])
ab = ab.reset_index()
alpha = ab.pivot(index="st", columns="year", values="mean")
out["annual_alpha_median_across_states"] = alpha.median().round(3).to_dict()
out["annual_alpha_minus_2017_2019_mean"] = (alpha.sub(alpha[[2017, 2018, 2019]].mean(axis=1), axis=0)).median().round(3).to_dict()
zero = d.assign(z=d.saidi == 0).groupby(["st", "year"]).z.mean().unstack()
out["zero_day_share_median_by_year"] = zero.median().round(4).to_dict()
out["zero_day_share_max_by_year"] = zero.max().round(4).to_dict()
# the share of the rolling-threshold rise attributable to dropping 2015/2016 from the window:
# threshold for 2025 (window 2020-24) vs frozen on 2017-19 vs frozen on 2015-19
alt = []
for st, g in d.groupby("st"):
    s = g.set_index("year").saidi
    alt.append(dict(st=st, t_1519=thr(s.loc[2015:2019].values), t_1719=thr(s.loc[2017:2019].values), t_1822=thr(s.loc[2018:2022].values),
                    t_2024=thr(s.loc[2020:2024].values), t_1619=thr(s.loc[2016:2019].values)))
alt = pd.DataFrame(alt).set_index("st")
out["threshold_medians"] = alt.median().round(3).to_dict()
out["threshold_ratio_medians"] = dict(t1719_over_t1519=float((alt.t_1719 / alt.t_1519).median()), t2024_over_t1519=float((alt.t_2024 / alt.t_1519).median()),
                                      t2024_over_t1719=float((alt.t_2024 / alt.t_1719).median()))


def h2_alt(base_lo, base_hi):
    rows = []
    for st, g in d.groupby("st"):
        s = g.set_index("year").saidi
        tf = thr(s.loc[base_lo:base_hi].values)
        for Y in YEARS:
            cur = s.loc[Y].values; trr = thr(s.loc[Y - 5:Y - 1].values)
            rows.append(dict(st=st, year=Y, noMED_roll=cur[cur <= trr].sum(), noMED_frozen=cur[cur <= tf].sum()))
    x = pd.DataFrame(rows)
    ci = cboot(x, h2)
    return dict(frozen_window=f"{base_lo}-{base_hi}", diff=h2(x), ci=ci, frozen_trend=fe_trend(x, "noMED_frozen"),
                verdict="Supported" if ci[1] < 0 else "Refuted" if ci[0] > 0 else "Inconclusive")


out["H2_alt_frozen_windows"] = [h2_alt(2017, 2019), h2_alt(2018, 2022), h2_alt(2016, 2019)]
# trends without 2020 (the storm-heavy base year) and over 2021-2025
i2 = idx[idx.year >= 2021]
out["trends_2021_2025"] = {c: dict(trend=fe_trend(i2, c), ci=cboot(i2, lambda x, c=c: fe_trend(x, c))) for c in ["all", "noMED_roll", "noMED_frozen", "noMED_q99"]}
ci2 = cboot(i2, h2)
out["H2_2021_2025"] = dict(diff=h2(i2), ci=ci2)
# leave-one-state-out range for H2 and the rolling trend
loo = []
for s in incl:
    x = idx[idx.st != s]
    loo.append(dict(drop=s, roll=fe_trend(x, "noMED_roll"), h2=h2(x), all=fe_trend(x, "all")))
loo = pd.DataFrame(loo)
out["leave_one_out"] = dict(roll_min=float(loo.roll.min()), roll_max=float(loo.roll.max()), h2_min=float(loo.h2.min()), h2_max=float(loo.h2.max()),
                            h2_min_drop=loo.loc[loo.h2.idxmin(), "drop"], all_min=float(loo["all"].min()), all_max=float(loo["all"].max()))

# (g) threshold vs the simulation's tail cut-off (95th percentile of non-zero 2015-2019 days)
g95 = []
for st, g in d.groupby("st"):
    s = g.set_index("year").saidi.loc[2015:2019].values; nz = s[s > 0]
    u = np.quantile(nz, 0.95); tf = thr(s)
    g95.append(dict(st=st, u=u, t_frozen=tf, t_over_u=tf / u, share_nz_above_t=float((nz > tf).mean()),
                    share_tail_below_t=float(((nz > u) & (nz <= tf)).sum() / (nz > u).sum()),
                    saidi_share_tail_below_t_in_nonMED=float(nz[(nz > u) & (nz <= tf)].sum() / nz[nz <= tf].sum())))
g95 = pd.DataFrame(g95).set_index("st")
out["tail_vs_threshold"] = dict(median_t_over_u=float(g95.t_over_u.median()), median_share_nz_above_t=float(g95.share_nz_above_t.median()),
                                median_share_of_tail_days_below_t=float(g95.share_tail_below_t.median()),
                                median_saidi_share_of_nonMED_index_from_subthreshold_tail=float(g95.saidi_share_tail_below_t_in_nonMED.median()),
                                per_state=g95.round(3).to_dict())

json.dump(out, open(HERE / "check5_analysis_replication.json", "w"), indent=1, default=float)
for k in ["inclusion", "state_year_max_abs_diff", "noMED_10y_2025_max_abs_diff", "trends", "H1", "H2", "decomposition_max_abs_diff",
          "decomposition_medians", "decomposition_n_positive_nonMED", "validation", "validation_within_state_spearman",
          "validation_yoy_log_change_spearman", "validation_within_state_demeaned_log_spearman", "validation_level_ratio_eaglei_over_eia",
          "validation_fe_trend_2018_2024", "validation_fe_trend_2020_2024", "validation_noMED_2020_2024", "eaglei_all_events_fe_trend_2020_2024",
          "annual_alpha_minus_2017_2019_mean", "zero_day_share_median_by_year", "zero_day_share_max_by_year", "threshold_medians",
          "threshold_ratio_medians", "H2_alt_frozen_windows", "trends_2021_2025", "H2_2021_2025", "leave_one_out", "per_state_slope_medians",
          "frozen_over_rolling_trend", "county_dev_2015_2016_included", "inclusion_max_dev_included"]:
    v = out[k]
    if isinstance(v, dict) and "per_state" in v:
        v = {kk: vv for kk, vv in v.items() if kk != "per_state"}
    print(k, "=>", json.dumps(v, default=float)[:1500])
print("tail_vs_threshold =>", json.dumps({k: v for k, v in out["tail_vs_threshold"].items() if k != "per_state"}))
