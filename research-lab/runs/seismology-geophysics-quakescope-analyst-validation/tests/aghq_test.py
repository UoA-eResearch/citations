"""AGHQ maximum-likelihood check on synthetic data with a known station SD (deviations.md D4)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import checks as C  # noqa: E402

rng = np.random.default_rng(5)
S, s_true = int(sys.argv[1]) if len(sys.argv) > 1 else 400, 1.1
u = rng.normal(0, s_true, S)
rows = []
for s in range(S):
    n = rng.poisson(80) + 10
    M = 1.5 + rng.exponential(0.6, n)
    ld = np.log10(rng.uniform(1, 100, n))
    eta = 2.6 + 0.6 * M - 0.9 * ld + u[s]
    rows.append(pd.DataFrame({"netsta": f"S{s:03d}", "M": M, "logd": ld, "y": (rng.random(n) < 1 / (1 + np.exp(-eta))).astype(float)}))
d = pd.concat(rows, ignore_index=True)
for K in (1, 15):
    g = C.AGHQ(d, K)
    r = minimize(g.negll, np.zeros(4), method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-4, "maxiter": 4000, "maxfev": 8000})
    print(K, np.round(r.x[:3], 3), "sigma", round(float(np.exp(r.x[3])), 3), "true 1.1 (sample SD %.3f)" % u.std())
