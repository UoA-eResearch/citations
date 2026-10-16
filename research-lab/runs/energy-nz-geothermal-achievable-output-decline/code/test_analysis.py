"""Synthetic checks: known decline in, the right trend and decision out. Run before any real series is built."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402
import build_series as B  # noqa: E402

rng = np.random.default_rng(11)
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    passed += ok
    failed += not ok


def synth_halfhours(months, cap=100.0, decline=-0.02, summer_derate=0.06, outage_rate_per_yr=4.0,
                    outage_growth=0.0, flex_share=0.03):
    """Half-hourly MW for a field: capacity x (1+decline)^t x seasonal derate x noise, with an annual 3-week
    maintenance outage, Poisson forced outages of 2-10 days (rate optionally growing over time), and short
    dispatch flexing to 80%. Returns monthly stats as build_series would compute them."""
    rows = []
    for k, m in enumerate(months):
        t = k / 12
        hh = m.days_in_month * 48
        level = cap * (1 + decline) ** t * (1 - summer_derate * np.cos(2 * np.pi * (m.month - 1) / 12) ** 2
                                             * (m.month in (12, 1, 2, 3)))
        x = level * (1 + rng.normal(0, 0.01, hh))
        if m.month == 3:                                   # annual maintenance, three weeks
            x[: 21 * 48] *= 0.0
        lam = (outage_rate_per_yr / 12) * (1 + outage_growth * t)
        for _ in range(rng.poisson(lam)):
            a = rng.integers(0, hh); L = rng.integers(2 * 48, 10 * 48)
            x[a:a + L] = 0.0
        flex = rng.uniform(size=hh) < flex_share
        x[flex] *= 0.8
        rows.append(dict(month=str(m), field="F", n_plants=1, **B.stats(x)))
    return pd.DataFrame(rows)


months = pd.period_range("2005-01", "2016-12", freq="M")
mem = pd.DataFrame(dict(month=[str(m) for m in months], field="F", plants="X:a"))

# 1. P95 trend recovers a known -2%/yr through outages, maintenance, summer derating and flexing
est = []
for _ in range(25):
    fm = synth_halfhours(months)
    r = A.field_trends(fm, mem)["F"]
    est.append(A.pct(r["b"]))
check("P95 trend recovers -2%/yr", abs(np.mean(est) + 2) < 0.15 and np.std(est) < 0.3,
      f"mean {np.mean(est):+.3f}, sd {np.std(est):.3f}")

# 2. ...while the monthly MEAN is biased when forced outages become more frequent over time (aging plant)
p95s, means = [], []
for _ in range(25):
    fm = synth_halfhours(months, decline=0.0, outage_growth=0.3)
    p95s.append(A.pct(A.field_trends(fm, mem, metric="p95")["F"]["b"]))
    means.append(A.pct(A.field_trends(fm, mem, metric="mean")["F"]["b"]))
check("P95 unaffected by rising outage frequency (true trend 0)", abs(np.mean(p95s)) < 0.15, f"P95 {np.mean(p95s):+.3f}")
check("...the mean (capacity factor) is not", np.mean(means) < -0.3, f"mean {np.mean(means):+.3f}")

# 3. GLS-AR(1) intervals cover the truth for autocorrelated monthly noise (AR(1), phi 0.6)
cover = 0
for _ in range(300):
    e = np.zeros(len(months)); u = rng.normal(0, 0.02, len(months))
    for i in range(1, len(e)):
        e[i] = 0.6 * e[i - 1] + u[i]
    p = 100 * np.exp(np.log(1 - 0.01) * np.arange(len(months)) / 12 + e)
    fm = pd.DataFrame(dict(month=[str(m) for m in months], field="F", n_plants=1, p95=p, p50=p, p99=p, mean=p,
                           n=[m.days_in_month * 48 for m in months]))
    r = A.field_trends(fm, mem)["F"]
    b0 = np.log(0.99)
    cover += abs(r["b"] - b0) < 1.96 * r["se"]
check("95% interval coverage >= 0.90 (AR(1) phi 0.6, 144 months)", cover / 300 >= 0.90, f"{cover / 300:.3f}")

# 4. segments: membership change, an event window and the commissioning ramp cut where they should
months2 = pd.period_range("2000-01", "2015-12", freq="M")
plants = ["WRK2201:wairakei" if m < pd.Period("2010-01", "M") else "WRK2201:wairakei|THI2201:te_mihi" for m in months2]
mem2 = pd.DataFrame(dict(month=[str(m) for m in months2], field="Wairakei", plants=plants))
fm2 = pd.DataFrame(dict(month=[str(m) for m in months2], field="Wairakei", n_plants=1, p95=100.0, p50=100.0,
                        p99=100.0, mean=100.0, n=[m.days_in_month * 48 for m in months2]))
segs = A.segments(fm2, mem2, "Wairakei")
spans = [(str(g.m.min()), str(g.m.max())) for g in segs]
# 2000-01..2003-12 is 48 months (too short, cut by the 2004-05 binary-plant window); 2006-01..2009-12 is 48
# (too short); Te Mihi enters 2010-01 newly built -> ramp to 2010-06; 2010-07..2015-12 = 66 months
check("segments cut at event window, membership change and ramp", spans == [("2010-07", "2015-12")], str(spans))

# 5. field sum: a plant with no value makes the half-hour missing, not zero; DST slots missing for all are not partial
stack = np.array([[10.0, 10.0, np.nan, np.nan], [5.0, np.nan, 5.0, np.nan]])
s, npart = B.field_sum(stack)
check("field sum: partial -> NaN, all-missing -> not counted", np.isnan(s[1]) and np.isnan(s[2]) and s[0] == 15
      and npart == 2 and np.isnan(s[3]), f"{s}, partial {npart}")

# 6. decision rules on constructed inputs
def fake(bs):
    return {f"F{i}": dict(b=np.log(1 + p / 100), se=se, mean_mw=100.0, resid=pd.Series(dtype=float))
            for i, (p, se) in enumerate(bs)}
res = fake([(-0.5, 0.002), (-4.0, 0.005), (-5.0, 0.005), (0.3, 0.002)])
v = A.verdicts(res, A.fleet(res))
check("H1 Supported when fleet ~ -2.3%/yr? no: Refuted/Inconclusive as the interval dictates",
      v["H1"]["verdict"] in ("Refuted", "Inconclusive"), f"{v['H1']['fleet_pct_per_yr']:+.2f} {v['H1']['verdict']}")
check("H2 Supported with two fields clearly below -3%/yr", v["H2"]["verdict"] == "Supported", str(v["H2"]))
res = fake([(-0.5, 0.002), (-1.0, 0.003), (0.2, 0.002), (-0.8, 0.002)])
v = A.verdicts(res, A.fleet(res))
check("H1 Supported and H2 Refuted for a gently declining fleet", v["H1"]["verdict"] == "Supported"
      and v["H2"]["verdict"] == "Refuted", f"{v['H1']['verdict']} / {v['H2']['verdict']}")

print(f"\n{passed}/{passed + failed} passed")
sys.exit(1 if failed else 0)
