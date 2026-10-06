"""POST-REVIEW secondary analyses (deviation D2): traceable tables for the numbers the revised report quotes. None of
them changes H1 or the frozen forecasts. Writes results/tables/post_review.json and post_review_*.csv."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backtest as BT  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def red(x, base):
    return float(1 - x.ae_M1.mean() / x[f"ae_{base}"].mean()) if len(x) else np.nan


def cover(x, lo="lo80", hi="hi80"):
    w = x.dropna(subset=[lo])
    return float(((w.actual >= w[lo]) & (w.actual <= w[hi])).mean()) if len(w) else np.nan, len(w)


def main():
    out = {}
    d = pd.read_csv(TAB / "backtest_cells.csv")
    d = d[d.M1.notna() & d.B1.notna() & d.B2.notna()]
    tot = d[(d.group == "Total") & (d.district != "National total")]
    prim = d[(d.district != "National total") & d.group.isin(BT.PRIMARY_GROUPS)]
    periods = [("2013-2019", BT.qi(2013, 1), BT.qi(2019, 4)), ("2020-2022", BT.qi(2020, 1), BT.qi(2022, 4)),
               ("2023-2026", BT.qi(2023, 1), BT.qi(2026, 2)), ("2025Q1-2026Q2", BT.qi(2025, 1), BT.qi(2026, 2))]
    rows = []
    for lab, a, b in periods:
        for h in (1, 2):
            for name, x in (("district Totals", tot), ("primary cells", prim)):
                y = x[(x.h == h) & (x.target >= a) & (x.target <= b)]
                c, n = cover(y)
                rows.append(dict(cells=name, period=lab, h=h, n=len(y), MAE_M1=y.ae_M1.mean(), MAE_B1=y.ae_B1.mean(), reduction_vs_B1=red(y, "B1"),
                                 PI80_coverage=c, PI80_n=n))
    pd.DataFrame(rows).to_csv(TAB / "post_review_short_horizon_by_period.csv", index=False)
    # D1 like-for-like: cells where both intervals exist, district Totals, 2023-2026 targets
    lf = []
    for h in (1, 2):
        y = tot[(tot.h == h) & (tot.target >= BT.qi(2023, 1))]
        both = y.dropna(subset=["lo80", "lo80r"])
        lf.append(dict(h=h, n_all=len(y), n_both=len(both), prereg_all=cover(y)[0], prereg_on_both=cover(both)[0],
                       recent_on_both=cover(both, "lo80r", "hi80r")[0], targets_2024_with_recent=int(((both.target >= BT.qi(2024, 1)) & (both.target <= BT.qi(2024, 4))).sum())))
    pd.DataFrame(lf).to_csv(TAB / "post_review_d1_like_for_like.csv", index=False)
    # interval coverage by target-cell size tertile
    sz = []
    for lab, x in (("district Totals h1-2", tot[tot.h.isin([1, 2])]), ("primary cells h4", prim[prim.h == 4])):
        x = x.dropna(subset=["lo80"]).copy()
        x["tertile"] = pd.qcut(x.n_target, 3, labels=["small", "mid", "large"])
        for t, y in x.groupby("tertile", observed=True):
            sz.append(dict(cells=lab, tertile=str(t), median_n=float(y.n_target.median()), coverage=cover(y)[0], n=len(y)))
    nat = d[(d.district == "National total") & (d.group == "Total")]
    for h in (1, 2, 4):
        sz.append(dict(cells=f"national Total h{h}", tertile="national", median_n=float(nat[nat.h == h].n_target.median()), coverage=cover(nat[nat.h == h])[0], n=cover(nat[nat.h == h])[1]))
    pd.DataFrame(sz).to_csv(TAB / "post_review_coverage_by_size.csv", index=False)
    # M2 against M1 and persistence on common cells; eligible-weighted reduction at h = 4
    a = pd.read_csv(TAB / "backtest_cells.csv")
    c = a[(a.h == 4) & (a.district != "National total") & a.group.isin(BT.PRIMARY_GROUPS) & a.M1.notna() & a.M2.notna() & a.B1.notna()]
    out["M2_common"] = dict(n=len(c), MAE_M1=c.ae_M1.mean(), MAE_M2=c.ae_M2.mean(), MAE_B1=c.ae_B1.mean(), reduction_M2_vs_B1=float(1 - c.ae_M2.mean() / c.ae_B1.mean()))
    h4 = prim[prim.h == 4]
    w = h4.n_target
    out["h4_eligible_weighted_reduction_vs_B1"] = float(1 - np.average(h4.ae_M1, weights=w) / np.average(h4.ae_B1, weights=w))
    out["h4_PI80_cells_with_interval"] = int(h4.lo80.notna().sum())
    out["h4_cells"] = len(h4)
    # binomial noise floor at the target cell: E|p_hat - p| ~ sqrt(2 p (1-p) / (pi n)), mean over cells, by period
    nf = []
    for lab, a_, b_ in periods[:3]:
        for g in ("all", "Pacific"):
            y = h4[(h4.target >= a_) & (h4.target <= b_)]
            y = y if g == "all" else y[y.group == "Pacific"]
            nf.append(dict(period=lab, group=g, MAE_B1=y.ae_B1.mean(), bar_30pct=0.7 * y.ae_B1.mean(),
                           noise_floor_target_only=float(np.mean(100 * np.sqrt(2 * y.actual * (1 - y.actual) / (np.pi * y.n_target)))),
                           median_n=float(y.n_target.median())))
    pd.DataFrame(nf).to_csv(TAB / "post_review_noise_floor.csv", index=False)
    # national milestones around the October 2020 schedule change; the 12-to-24 cohort gap; AIR denominator ratios
    cov = pd.read_parquet(RUN / "data" / "coverage.parquet")
    n = cov[(cov.district == "National total") & (cov.group == "Total")].copy()
    n["qi"] = [BT.qi(t.year, (t.month - 1) // 3 + 1) for t in pd.to_datetime(n.quarter_end)]
    n["c"] = 100 * n.immunised / n.eligible
    pv = n.pivot_table(index="qi", columns="milestone", values="c")
    ev = n.pivot_table(index="qi", columns="milestone", values="eligible")
    ch = pv[[12, 18, 24]].diff()
    sched = ch.loc[BT.qi(2020, 3):BT.qi(2021, 3)].round(2)
    sched.index = [BT.qlabel(i) for i in sched.index]
    sched.to_csv(TAB / "post_review_schedule_change_milestones.csv")
    gap = pd.DataFrame({"gap_24_minus_12_cohort_pp": [pv[24].get(t, np.nan) - pv[12].get(t - 4, np.nan) for t in pv.index],
                        "denominator_ratio_n24_over_n12": [ev[24].get(t, np.nan) / ev[12].get(t - 4, np.nan) for t in ev.index]}, index=[BT.qlabel(i) for i in pv.index])
    gap.round(4).to_csv(TAB / "post_review_cohort_gap_and_denominators.csv")
    # effect of including the national total in the interval pool (plan says districts only)
    P = BT.load()
    districts = sorted({k[0] for k in P if k[0] != "National total"})
    dd, _ = BT.run_backtest(P, districts, BT.PRIMARY_GROUPS, [1, 4])
    dd = dd[dd.M1.notna() & dd.B1.notna() & dd.B2.notna()]  # like-for-like with the committed cells (confirmation N2)
    out["interval_pool_without_national"] = {f"h{h}_primary_coverage": cover(dd[dd.h == h])[0] for h in (1, 4)}
    out["interval_pool_with_national"] = {f"h{h}_primary_coverage": cover(prim[prim.h == h])[0] for h in (1, 4)}
    json.dump(out, open(TAB / "post_review.json", "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))
    print(pd.DataFrame(rows).round(3).to_string()); print(pd.DataFrame(lf).round(3).to_string()); print(pd.DataFrame(sz).round(3).to_string())
    print(pd.DataFrame(nf).round(3).to_string()); print(sched.to_string()); print(gap.loc["2023Q1":"2025Q4"].round(3).to_string())


if __name__ == "__main__":
    main()
