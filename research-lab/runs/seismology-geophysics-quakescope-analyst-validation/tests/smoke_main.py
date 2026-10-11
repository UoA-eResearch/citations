"""Smoke test of analysis.main() end to end on synthetic data (deviations.md D3). Runs in a scratch copy of the run
layout, so no real data or results are read or written. Plants a -inf and a NaN log_noise (as in the real covariates)
and checks that every output file is written. Bootstrap B is reduced to 4 refits for speed."""
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import analysis as A  # noqa: E402

rng = np.random.default_rng(2)
S = 140
band = rng.choice(["H", "E"], S)
noise = rng.normal(-7.5, 0.5, S)
u = 0.8 * (band == "E") - 0.6 * (noise + 7.5) + rng.normal(0, 0.35, S)
rows = []
for s in range(S):
    n = rng.poisson(60) + 30
    M = 1.5 + rng.exponential(0.6, n)
    dist = rng.uniform(1, 100, n)
    eta = 1.0 + 0.7 * M - 1.2 * np.log10(dist) + u[s]
    y = rng.random(n) < 1 / (1 + np.exp(-eta))
    for ph in ("P", "S"):
        t0 = pd.Timestamp("2019-07-01") + pd.to_timedelta(rng.integers(0, 60 * 86400, n), unit="s")
        rows.append(pd.DataFrame({
            "netsta": f"XX.S{s:03d}", "mag": M, "dist_km": dist, "phase": ph, "loaded": True, "in_stations": True,
            "matched_0.2": y & (rng.random(n) < 0.8), "matched_0.5": y, "matched_1.0": y | (rng.random(n) < 0.05),
            "onset": rng.choice(["i", "e"], n), "t_ref": t0,
            "resid_0.5": np.where(y, rng.normal(0, 0.05, n), np.nan), "cha_qs_0.5": np.where(y, band[s] + "HZ", None)}))
m = pd.concat(rows, ignore_index=True)
cov = pd.DataFrame({"netsta": [f"XX.S{s:03d}" for s in range(S)], "band": band, "instrument": "H", "read_band": [b + "H" for b in band],
                    "sample_rate": 100.0, "log_noise": noise, "noise_note": "180 windows", "network": "XX", "elevation": 0.0,
                    "latitude": rng.uniform(32, 42, S), "longitude": rng.uniform(-124, -114, S)})
cov.loc[3, "log_noise"] = -np.inf
cov.loc[7, "log_noise"] = np.nan

tmp = Path(tempfile.mkdtemp())
(tmp / "data").mkdir()
m.to_parquet(tmp / "data" / "matched.parquet", index=False)
cov.to_parquet(tmp / "data" / "covariates.parquet", index=False)
A.RUN, A.TAB = tmp, tmp / "results" / "tables"
A.MIN_H2 = 30
orig_h1 = A.h1
A.h1 = lambda d, B=4, workers=4: orig_h1(d, B=4, workers=4)
A.main()
for f in ("primary.json", "h1_bootstrap_draws.csv", "station_reliability.csv", "secondary.csv", "timing_by_band.csv"):
    assert (A.TAB / f).exists(), f
print(sorted(p.name for p in A.TAB.iterdir()))
shutil.rmtree(tmp)
print("SMOKE OK")
