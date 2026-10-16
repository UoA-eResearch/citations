"""Checks on the estimators with synthetic data whose answers are known. Run before any real data.

Each check fails loudly. They are what stands between a coding error and a published verdict.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

rng = np.random.default_rng(1)
YEARS = np.arange(1980, 2022)
n = len(YEARS)
nino = rng.normal(0, 1, n + 1)
IDX = pd.DataFrame({"nino34": nino[1:], "nino34_lag": nino[:-1],
                    "wpe": 180 + 15 * nino[1:] + rng.normal(0, 3, n)}, index=YEARS)
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    print(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
    passed += ok
    failed += not ok


def series(trend_pp, noise_pp=1.0, enso=0.03, seed=0):
    r = np.random.default_rng(seed)
    return 0.6 + trend_pp / 100 * (YEARS - 2000) + enso * IDX.nino34.values + r.normal(0, noise_pp / 100, n)


# 1. recovers a planted trend despite a strong ENSO signal
y = series(-0.30, noise_pp=0.2)
t = A.trend_ci(y, YEARS, IDX, nboot=500)
check("recovers planted -0.30 pp/yr", abs(t["point"] + 0.30) < 0.05, f"got {t['point']:.3f}")

# 2. ENSO adjustment matters: without it, a big ENSO signal inflates the interval
t_noadj = A.trend_ci(series(0.0, 0.2, enso=0.08), YEARS, IDX, covars=(), nboot=300)
t_adj = A.trend_ci(series(0.0, 0.2, enso=0.08), YEARS, IDX, nboot=300)
check("ENSO adjustment narrows the interval", (t_adj["hi"] - t_adj["lo"]) < (t_noadj["hi"] - t_noadj["lo"]),
      f"adj width {t_adj['hi']-t_adj['lo']:.3f} vs unadj {t_noadj['hi']-t_noadj['lo']:.3f}")

# 3. interval coverage, white noise and the observed AR(1) autocorrelation (coarse: 150 reps each)
cover = 0
for s in range(150):
    tt = A.trend_ci(series(-0.10, 1.0, seed=100 + s), YEARS, IDX, nboot=200, seed=s)
    cover += tt["lo"] <= -0.10 <= tt["hi"]
check("block-bootstrap coverage roughly nominal (white noise)", 0.85 <= cover / 150 <= 0.99, f"coverage {cover/150:.2f}")
# The first version of this check used white noise only and reported 0.89, which the plan disclosed. The real
# residuals have lag-1 autocorrelation 0.56, and the review showed coverage drops to about 0.79 there. This
# check records that rather than asserting it away: it passes if coverage is measured, and prints the number.
cover_ar = 0
r = np.random.default_rng(99)
for s in range(150):
    e = np.empty(n); e[0] = r.normal(0, 1)
    for t in range(1, n):
        e[t] = 0.56 * e[t - 1] + r.normal(0, np.sqrt(1 - 0.56 ** 2))
    yy = 0.6 - 0.10 / 100 * (YEARS - 2000) + 0.03 * IDX.nino34.values + e / 100
    tt = A.trend_ci(yy, YEARS, IDX, nboot=200, seed=s)
    cover_ar += tt["lo"] <= -0.10 <= tt["hi"]
check("block-bootstrap coverage under AR(1) 0.56 is measured (expected below nominal)",
      0.6 <= cover_ar / 150 <= 0.95, f"coverage {cover_ar/150:.2f}")

# 4. the three verdict branches
check("verdict Supported", A.verdict_h1(-0.05, 0.20, -0.117) == "Supported")
check("verdict Refuted", A.verdict_h1(-0.50, -0.20, -0.117) == "Refuted")
check("verdict Inconclusive", A.verdict_h1(-0.30, 0.10, -0.117) == "Inconclusive")

# 5. H2: identical series differ by zero; a planted gap is recovered
y1 = series(0.10, 0.3, seed=7)
h = A.h2_difference(y1, y1, YEARS, IDX, nboot=300)
check("H2 identical series -> difference 0", abs(h["diff"]) < 1e-9 and h["lo"] <= 0 <= h["hi"])
h = A.h2_difference(series(0.30, 0.2, seed=8), series(-0.20, 0.2, seed=9), YEARS, IDX, nboot=300)
check("H2 recovers a planted +0.50 pp/yr gap", abs(h["diff"] - 0.50) < 0.1 and h["lo"] > 0, f"{h['diff']:.3f}")

# 6. H3: a predictor that IS the truth beats the ENSO regression out of sample
yo = series(0.0, 1.0, enso=0.0, seed=11)          # nothing for ENSO to explain
h3 = A.h3_skill(yo, yo, YEARS, IDX, nboot=300)
check("H3 perfect model beats ENSO-only", h3["d_r2"] > 0.5, f"dR2 {h3['d_r2']:.2f}")
noise_model = np.random.default_rng(12).normal(0.6, 0.01, n)
h3b = A.h3_skill(series(0.0, 0.3, enso=0.05, seed=13), noise_model, YEARS, IDX, nboot=300)
check("H3 noise model does not beat a real ENSO signal", h3b["d_r2"] < 0, f"dR2 {h3b['d_r2']:.2f}")

# 7. power: a huge decline is always found, none is found about alpha of the time
p = A.h4_power(series(0.0, 0.5, seed=14), YEARS, IDX, deltas_pp=[0.0, 1.0], nsim=300)
check("power ~ alpha at delta 0", p["curve"][0.0] <= 0.12, f"{p['curve'][0.0]:.2f}")
check("power ~ 1 at delta 1.0 pp/yr", p["curve"][1.0] >= 0.95, f"{p['curve'][1.0]:.2f}")

# 8. detection year: a steep projected decline in low noise is detected soon after 2011
d = A.h4_detection_year(np.random.default_rng(15).normal(0, 0.002, 42), tau=-0.5, nsim=200)
check("detection year early for a steep, quiet signal", d["year"] is not None and d["year"] <= 2030,
      f"year {d['year']}")
d0 = A.h4_detection_year(np.random.default_rng(16).normal(0, 0.05, 42), tau=-0.01, horizon=2040, nsim=100)
check("no detection for a tiny signal in loud noise", d0["year"] is None, f"year {d0['year']}")

print(f"\n{passed}/{passed + failed} passed")
sys.exit(1 if failed else 0)
