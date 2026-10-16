"""Checks prompted by the adversarial review (review/review.md), in the study's own code (deviations D4). Post hoc;
none changes a preregistered verdict. analysis.py is imported, not modified.

  V1  alternative segmentations (review A1): Wairakei 2014- segment from 2015-01 (Te Mihi's ramp outlasted 6 months);
      Ngatamariki from 2014-10 (its 2014 low); Wairakei 2006-13 dropped (Poihipi connected to the Wairakei steamfield
      2006, full capacity 2011 - a documented capacity change the plan missed); applied cumulatively, as the review did
  V2  a rule-based version of the same idea, decided without reference to the series: 12-month commissioning ramps,
      the Poihipi connection cut 2006-01..2011-12, Kawerau as KGL alone (its 2000-08 segment is a 5.5 MW plant and
      its 2020-25 segment includes net-injection series of uncertain identity; review A3)
  V3  segments combined by capacity (mean P95) rather than inverse variance (review B2)
  V4  AR(2) errors instead of AR(1) (review B1): every segment refit with statsmodels SARIMAX, AR(2) + month dummies
  V5  months with P95 below 85% of a centred 13-month rolling median dropped (multi-month single-unit outages, B4)
  V6  the Ohaaki run-down slope for other windows (review A4)
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
fm = pd.read_csv(TAB / "field_monthly.csv")
mem = pd.read_csv(TAB / "field_membership.csv")


def trends_from(segs_by_field, combine="ivw", fitter=A.seg_trend):
    res = {}
    for field, segs in segs_by_field.items():
        fits = [fitter(g) for g in segs if g.ok.sum() >= 24]
        if not fits:
            continue
        if combine == "ivw":
            w = np.array([1 / s["se"] ** 2 for s in fits])
        else:
            w = np.array([s["mean_mw"] * s["n"] for s in fits])
        b = float(np.sum(w * [s["b"] for s in fits]) / w.sum())
        se = float(np.sqrt(np.sum((w / w.sum()) ** 2 * np.array([s["se"] for s in fits]) ** 2)))
        months = sum(s["n"] for s in fits)
        res[field] = dict(b=b, se=se, months=months, mean_mw=float(sum(s["mean_mw"] * s["n"] for s in fits) / months),
                          segments=fits, resid=pd.concat([s["resid"] for s in fits]))
    return res


def summary(res):
    fl = A.fleet(res)
    v = A.verdicts(res, fl)
    return dict(fleet=v["H1"]["fleet_pct_per_yr"], ci=v["H1"]["ci"], H1=v["H1"]["verdict"], H2=v["H2"]["verdict"],
                fields={f: round(A.pct(r["b"]), 3) for f, r in res.items()})


def base_segments():
    return {f: A.segments(fm, mem, f) for f in sorted(fm.field.unique())}


def trim(g, start=None, end=None):
    g = g.copy()
    if start:
        g = g[g.m >= pd.Period(start, "M")]
    if end:
        g = g[g.m <= pd.Period(end, "M")]
    return g


def sarimax_ar2(g, metric="p95"):
    d = g[g.ok]
    t = (d.m.dt.year + (d.m.dt.month - 0.5) / 12).to_numpy(float)
    X = pd.get_dummies(d.m.dt.month, prefix="mo", drop_first=True).astype(float)
    X.insert(0, "trend", t - t.mean())
    X = sm.add_constant(X).to_numpy()
    y = np.log(d[metric].to_numpy(float))
    r = sm.tsa.SARIMAX(y, exog=X, order=(2, 0, 0), trend="n").fit(disp=False, maxiter=200)
    return dict(b=float(r.params[1]), se=float(r.bse[1]), n=int(len(d)), n_dropped=int((~g.ok).sum()),
                start=str(g.m.min()), end=str(g.m.max()), mean_mw=float(d[metric].mean()),
                resid=pd.Series(np.asarray(r.resid), index=d.m.astype(str).to_numpy()))


def main():
    out = {}
    base = base_segments()
    out["preregistered"] = summary(trends_from(base))

    # V1, cumulative as in the review
    s1 = {f: list(v) for f, v in base.items()}
    s1["Wairakei"] = [s1["Wairakei"][0], trim(s1["Wairakei"][1], start="2015-01")]
    out["V1a_wairakei_from_2015"] = summary(trends_from(s1))
    s1["Ngatamariki"] = [trim(s1["Ngatamariki"][0], start="2014-10")]
    out["V1b_plus_ngatamariki_from_2014_10"] = summary(trends_from(s1))
    s1["Wairakei"] = [s1["Wairakei"][1]]
    out["V1c_plus_drop_wairakei_2006_13"] = summary(trends_from(s1))

    # V2 rule-based: 12-month ramps, Poihipi connection window, Kawerau = KGL only
    old_ramp, old_events = A.RAMP, list(A.EVENTS)
    try:
        A.RAMP = 12
        A.EVENTS = old_events + [("Wairakei", "2006-01", "2011-12", "Poihipi connected to the Wairakei steamfield 2006, "
                                  "full capacity 2011", "NZGA Wairakei field page")]
        s2 = {f: A.segments(fm, mem, f) for f in sorted(fm.field.unique())}
    finally:
        A.RAMP, A.EVENTS = old_ramp, old_events
    s2["Kawerau"] = [g for g in s2["Kawerau"] if g.plants.iloc[0] == "KAW1101:kawerau_new"]
    r2 = trends_from(s2)
    out["V2_rule_based"] = summary(r2)
    out["V2_rule_based"]["segments"] = {f: [(s["start"], s["end"], round(A.pct(s["b"]), 3)) for s in r["segments"]]
                                        for f, r in r2.items()}

    # V3 capacity-weighted segment combination
    out["V3_capacity_weighted_segments"] = summary(trends_from(base, combine="capacity"))
    # V4 AR(2) errors
    out["V4_ar2_errors"] = summary(trends_from(base, fitter=sarimax_ar2))
    # V5 rolling-median outage filter
    s5 = {}
    for f, segs in base.items():
        s5[f] = []
        for g in segs:
            g = g.copy()
            rm = g.p95.rolling(13, center=True, min_periods=7).median()
            g["ok"] = g.ok & (g.p95 >= 0.85 * rm)
            s5[f].append(g)
    r5 = trends_from(s5)
    out["V5_rolling_outage_filter"] = summary(r5)
    out["V5_rolling_outage_filter"]["months_dropped"] = int(sum((~g.ok).sum() for v in s5.values() for g in v))

    # V6 Ohaaki windows
    oh = base["Ohaaki"][0]
    v6 = {}
    for a, b in (("2008-01", "2013-12"), ("2008-01", "2012-12"), ("2009-01", "2013-12"), ("2008-01", "2016-12"),
                 ("2008-01", "2026-09"), ("2000-01", "2007-10")):
        r = A.seg_trend(trim(oh, a, b))
        v6[f"{a}..{b}"] = [round(A.pct(r["b"]), 2), round(A.pct(r["b"] - 1.96 * r["se"]), 2),
                           round(A.pct(r["b"] + 1.96 * r["se"]), 2)]
    out["V6_ohaaki_windows"] = v6
    json.dump(out, open(TAB / "review_response.json", "w"), indent=1, default=float)
    for k, v in out.items():
        print(k, json.dumps(v, default=float)[:400])


if __name__ == "__main__":
    sys.exit(main())
