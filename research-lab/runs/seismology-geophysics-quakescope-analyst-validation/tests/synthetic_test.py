"""Synthetic check of match.py and analysis.py (plan section 8, step 4): known station SD and covariate effects."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import analysis as A  # noqa: E402
import match as Mt  # noqa: E402

rng = np.random.default_rng(1)
# 1. greedy matching
ref = np.array([0, 1_000_000_000, 2_000_000_000], dtype=np.int64)
pk = np.array([300_000_000, 1_100_000_000, 1_200_000_000, 5_000_000_000], dtype=np.int64)
assert list(Mt.greedy_match(ref, pk, 0.5)) == [0, 1, -1], Mt.greedy_match(ref, pk, 0.5)
assert list(Mt.greedy_match(ref, pk, 0.2)) == [-1, 1, -1]
# a catalogue pick closer to the second reference pick goes to it, not to the first
assert list(Mt.greedy_match(np.array([0, 400_000_000]), np.array([350_000_000]), 0.5)) == [-1, 0]
print("matching ok")

# 2. H1/H2 recovery: 300 stations; station effect = 0.8*(band=='E') - 0.6*log_noise_z + noise
S = 300
band = rng.choice(["H", "E", "B"], S)
noise = rng.normal(0, 1, S)
u = 0.8 * (band == "E") - 0.6 * noise + rng.normal(0, 0.35, S)
u = u - u.mean()
rows = []
for s in range(S):
    n = rng.poisson(80) + 30
    M = 1.5 + rng.exponential(0.6, n)
    dist = rng.uniform(1, 100, n)
    eta = 1.0 + 0.7 * M - 1.2 * np.log10(dist) + u[s]
    y = rng.random(n) < 1 / (1 + np.exp(-eta))
    rows.append(pd.DataFrame({"netsta": f"XX.S{s:03d}", "mag": M, "dist_km": dist, "matched_0.5": y, "loaded": True,
                              "in_stations": True, "phase": "P"}))
d = A.prepare(pd.concat(rows, ignore_index=True))
true_sdp = A.sd_p({"Intercept": 1.0, "M": 0.7, "logd": -1.2}, float(np.std(u)))
f = A.fit(d)
est = A.sd_p(f["beta"], f["s_u"])
print("true SD_p", round(true_sdp, 4), "estimated", round(est, 4), "beta", {k: round(v, 3) for k, v in f["beta"].items()},
      "s_u", round(f["s_u"], 3), "true sd(u)", round(float(np.std(u)), 3), "converged", f["converged"], "levels", (f["levels"] or [])[:3])
eff = A.station_effects(f, d)
print("corr(u_hat, u) =", round(float(np.corrcoef(eff.u.values, u)[0, 1]), 3))
cov = pd.DataFrame({"netsta": [f"XX.S{s:03d}" for s in range(S)], "band": band, "instrument": "H", "sample_rate": 100.0,
                    "log_noise": noise, "network": "XX", "elevation": 0.0, "latitude": rng.uniform(32, 42, S),
                    "longitude": rng.uniform(-124, -114, S)}).set_index("netsta")
r2, sec, _ = A.h2(f, d, cov)
print("H2", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r2.items()}, "linear R2", round(sec["linear"]["R2"], 3))
assert abs(est - true_sdp) < 0.03 and r2["R2"] > 0.5
r1 = A.h1(d, B=8, workers=8)[1]
print("H1 (8 bootstrap refits)", {k: v for k, v in r1.items() if k != "beta"})
print("SYNTHETIC OK")
