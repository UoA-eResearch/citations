"""Trends in achievable output, field by field and fleet-wide, exactly as preregistered in plan.md.

Achievable output = the field's monthly P95 of half-hourly generation (build_series.py).

  segments   A field's record is cut wherever (a) the set of plants reporting changes, or (b) a documented capacity
             change of a reporting plant occurs (EVENTS, with sources; the event window is excluded). A newly built
             plant's first 6 months after it enters are excluded as commissioning ramp. Segments shorter than 60
             months are not used. Months with fewer than 80% of their half-hours valid, or with P95 below 20% of the
             segment median (the field off for most of the month, i.e. a whole-month outage, not lost capability),
             are dropped from the regression but do not cut the segment.
  trend      Within a segment: log(P95) ~ month-of-year dummies (ambient temperature: binary plants lose output in
             summer) + a linear trend in years, fitted by GLS with AR(1) errors (Newey-West is a sensitivity). A
             field's trend is the inverse-variance weighted mean of its segment trends.
  fleet      The capacity-weighted mean of field trends, weights = the field's mean P95 (MW) over its segment
             months. Its variance uses the correlation of the fields' monthly residuals over common months (pairs
             with < 36 common months get 0); the bound under perfect correlation is reported too.
  units      %/yr = 100 (exp(b) - 1).

  H1  fleet decline is less than 1.5%/yr (half MBIE's 3%/yr). Supported if the 95% interval's lower end is above
      -1.5%/yr; Refuted if its upper end is below -1.5%/yr; Inconclusive otherwise.
  H2  at least two fields decline faster than 3%/yr. Supported if >= 2 fields have a point estimate below -3%/yr
      with the interval's upper end below 0; Refuted if fewer than 2 fields have an interval reaching below
      -3%/yr; Inconclusive otherwise.
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"
MIN_MONTHS, RAMP, MIN_VALID, OUTAGE_FRAC, HAC_LAGS, MIN_COMMON = 60, 6, 0.8, 0.2, 12, 36
H1_LINE, H2_LINE = -1.5, -3.0
SE_METHOD = "glsar"     # "nw" (Newey-West) is a sensitivity

# Documented capacity changes of plants that report in Generation_MD, fixed before any output series was built.
# (field, first month excluded, last month excluded, what, source)
EVENTS = [
    ("Wairakei", "2004-01", "2005-12", "Wairakei binary bottoming plant (14 MW), 2004-2005", "MBIE FGGS 2020, Table 2"),
    ("Mokai", "2005-01", "2005-12", "Mokai stage 2, 2005", "MBIE FGGS 2020, Table 2"),
    ("Mokai", "2007-01", "2007-12", "Mokai stage 1A, 2007 (total 112 MW)", "MBIE FGGS 2020, Table 2"),
    ("Kawerau", "2017-01", "2017-12", "Kawerau (KGL) rerated 100 -> 117 MW, 2017", "MBIE FGGS 2020, s. Kawerau"),
    ("Kawerau", "2018-01", "2018-12", "Te Ahi O Maui (25 MW), 2018", "MBIE FGGS 2020, Table 2"),
    ("Ngawha", "2020-01", "2021-12", "Ngawha OEC4 / Ngawha B (31.5 MW); register 2020, MBIE expected mid-2021",
     "EMI plant register 2026-07-02; MBIE FGGS 2020"),
    ("Ngatamariki", "2026-01", "2026-12", "Nga Tamariki OEC5 (+46 MW), January-March 2026", "Mercury NZX, Jan 2026"),
]
# plants that were newly BUILT when they first appear (commissioning ramp excluded); other first appearances are
# reporting changes of existing plant (a segment boundary, no ramp)
NEW_AT_ENTRY = {"THI2201:te_mihi", "NAP2201:nap", "WRK0331:tehuka", "NAP2202:ngatamariki", "KAW1101:kawerau_new",
                "TAB2201:tauhara", "TAB0331:te_huka_3", "KAW2201:kawerau_(topp2)"}


def segments(fm, members, field, metric="p95", window=None):
    """Return a list of DataFrames, one per usable segment of `field`."""
    f = fm[fm.field == field].copy()
    f["m"] = pd.PeriodIndex(f.month, freq="M")
    mem = members[members.field == field].set_index("month").plants
    f["plants"] = f.month.map(mem)
    f = f.sort_values("m").reset_index(drop=True)
    excl = pd.Series(False, index=f.index)
    for fld, a, b, *_ in EVENTS:
        if fld == field:
            excl |= (f.m >= pd.Period(a, "M")) & (f.m <= pd.Period(b, "M"))
    # commissioning ramp after a newly built plant enters
    seen = set()
    for i, row in f.iterrows():
        now = set(row.plants.split("|"))
        for p in now - seen:
            if p in NEW_AT_ENTRY:
                excl |= (f.m >= row.m) & (f.m < row.m + RAMP)
        seen |= now
    if window is not None:
        excl |= (f.m < pd.Period(window[0], "M")) | (f.m > pd.Period(window[1], "M"))
    # segment id: new segment at every membership change, every excluded gap, and every calendar gap
    seg, sid, prev = [], 0, None
    for i, row in f.iterrows():
        if excl[i]:
            seg.append(-1); prev = None; continue
        if prev is None or row.plants != prev.plants or row.m != prev.m + 1:
            sid += 1
        seg.append(sid); prev = row
    f["seg"] = seg
    out = []
    for s, g in f[f.seg > 0].groupby("seg"):
        if len(g) < MIN_MONTHS:
            continue
        g = g.copy()
        hh = g.m.map(lambda p: p.days_in_month * 48)
        g["ok"] = (g.n >= MIN_VALID * hh) & (g[metric] > OUTAGE_FRAC * g[metric].median()) & (g[metric] > 0)
        out.append(g)
    return out


def seg_trend(g, metric="p95"):
    d = g[g.ok]
    t = (d.m.dt.year + (d.m.dt.month - 0.5) / 12).to_numpy(float)
    X = pd.get_dummies(d.m.dt.month, prefix="mo", drop_first=True).astype(float)
    X.insert(0, "trend", t - t.mean())
    X = sm.add_constant(X)
    y = np.log(d[metric].to_numpy(float))
    if SE_METHOD == "nw":
        r = sm.OLS(y, X.to_numpy()).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    else:
        # GLS with AR(1) errors: in synthetic tests Newey-West intervals covered only 0.67-0.88 for 60-144 month
        # segments with AR(1) noise; GLS-AR(1) covered 0.87-0.95 (plan section 6)
        r = sm.GLSAR(y, X.to_numpy(), rho=1).iterative_fit(maxiter=20)
    return dict(b=float(r.params[1]), se=float(r.bse[1]), n=int(len(d)), n_dropped=int((~g.ok).sum()),
                start=str(g.m.min()), end=str(g.m.max()), mean_mw=float(d[metric].mean()),
                resid=pd.Series(r.resid, index=d.m.astype(str).to_numpy()))


def pct(b):
    return 100.0 * (np.exp(b) - 1.0)


def field_trends(fm, members, metric="p95", window=None, fields=None):
    res = {}
    for field in sorted(fields or fm.field.unique()):
        segs = [seg_trend(g, metric) for g in segments(fm, members, field, metric, window)]
        if not segs:
            continue
        w = np.array([1 / s["se"] ** 2 for s in segs])
        b = float(np.sum(w * [s["b"] for s in segs]) / w.sum())
        se = float(1 / np.sqrt(w.sum()))
        months = sum(s["n"] for s in segs)
        mean_mw = float(sum(s["mean_mw"] * s["n"] for s in segs) / months)
        res[field] = dict(b=b, se=se, mean_mw=mean_mw, months=months, segments=segs,
                          resid=pd.concat([s["resid"] for s in segs]))
    return res


def fleet(res, weights="capacity"):
    fields = list(res)
    w = np.array([res[f]["mean_mw"] if weights == "capacity" else 1.0 for f in fields])
    w = w / w.sum()
    b = np.array([res[f]["b"] for f in fields])
    se = np.array([res[f]["se"] for f in fields])
    R = np.eye(len(fields))
    for i in range(len(fields)):
        for j in range(i + 1, len(fields)):
            a, c = res[fields[i]]["resid"], res[fields[j]]["resid"]
            common = a.index.intersection(c.index)
            if len(common) >= MIN_COMMON:
                R[i, j] = R[j, i] = float(np.corrcoef(a[common], c[common])[0, 1])
    est = float(w @ b)
    sd = float(np.sqrt(w @ (np.outer(se, se) * R) @ w))
    sd_max = float(w @ se)
    return dict(b=est, se=sd, se_perfect_corr=sd_max, weights=dict(zip(fields, w.tolist())),
                corr=pd.DataFrame(R, index=fields, columns=fields).round(3).to_dict())


def verdicts(res, fl):
    lo, hi = pct(fl["b"] - 1.96 * fl["se"]), pct(fl["b"] + 1.96 * fl["se"])
    h1 = "Supported" if lo > H1_LINE else ("Refuted" if hi < H1_LINE else "Inconclusive")
    fast = [f for f, r in res.items() if pct(r["b"]) < H2_LINE and pct(r["b"] + 1.96 * r["se"]) < 0]
    reach = [f for f, r in res.items() if pct(r["b"] - 1.96 * r["se"]) < H2_LINE]
    h2 = "Supported" if len(fast) >= 2 else ("Refuted" if len(reach) < 2 else "Inconclusive")
    return dict(H1=dict(verdict=h1, fleet_pct_per_yr=pct(fl["b"]), ci=[lo, hi],
                        ci_perfect_corr=[pct(fl["b"] - 1.96 * fl["se_perfect_corr"]),
                                         pct(fl["b"] + 1.96 * fl["se_perfect_corr"])]),
                H2=dict(verdict=h2, fields_faster_than_3pct=fast, fields_whose_ci_reaches_3pct=reach))


def summarise(res):
    return {f: dict(pct_per_yr=pct(r["b"]), ci=[pct(r["b"] - 1.96 * r["se"]), pct(r["b"] + 1.96 * r["se"])],
                    mean_mw=r["mean_mw"], months=r["months"],
                    segments=[dict(start=s["start"], end=s["end"], n=s["n"], n_dropped=s["n_dropped"],
                                   pct_per_yr=pct(s["b"]),
                                   ci=[pct(s["b"] - 1.96 * s["se"]), pct(s["b"] + 1.96 * s["se"])],
                                   mean_mw=s["mean_mw"]) for s in r["segments"]])
            for f, r in res.items()}


def run(fm, members, **kw):
    weights = kw.pop("weights", "capacity")
    res = field_trends(fm, members, **kw)
    fl = fleet(res, weights)
    return dict(fields=summarise(res), fleet=dict(pct_per_yr=pct(fl["b"]), weights=fl["weights"],
                                                   residual_corr=fl["corr"]), **verdicts(res, fl))


def main():
    fm = pd.read_csv(PROC / "field_monthly.csv")
    members = pd.read_csv(PROC / "field_membership.csv")
    out = dict(primary=run(fm, members))
    sens = {}
    for name, kw in (("metric_p50", dict(metric="p50")), ("metric_p99", dict(metric="p99")),
                     ("metric_mean", dict(metric="mean")), ("equal_weights", dict(weights="equal")),
                     ("last_10_years", dict(window=("2016-10", "2026-09"))),
                     ("excluding_wairakei", dict(fields=[f for f in fm.field.unique() if f != "Wairakei"]))):
        try:
            sens[name] = run(fm, members, **kw)
        except Exception as e:
            sens[name] = dict(error=str(e))
    global SE_METHOD
    SE_METHOD = "nw"
    try:
        sens["newey_west_se"] = run(fm, members)
    finally:
        SE_METHOD = "glsar"
    out["sensitivity"] = sens
    out["events"] = [dict(field=e[0], start=e[1], end=e[2], what=e[3], source=e[4]) for e in EVENTS]
    TAB.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(TAB / "primary.json", "w"), indent=1, default=float)
    p = out["primary"]
    print("H1:", p["H1"]); print("H2:", p["H2"])
    for f, r in p["fields"].items():
        print(f"  {f:12s} {r['pct_per_yr']:+6.2f}%/yr ({r['ci'][0]:+.2f}, {r['ci'][1]:+.2f})  {r['mean_mw']:6.1f} MW  "
              f"{r['months']} months in {len(r['segments'])} segment(s)")


if __name__ == "__main__":
    sys.exit(main())
