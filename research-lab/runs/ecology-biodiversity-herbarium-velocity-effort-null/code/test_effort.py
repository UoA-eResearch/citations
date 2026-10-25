"""Effort-shift check: all species have fixed ranges spanning 40-50N, but P2 collecting is concentrated in the north
half. Apparent shifts should be reproduced by the effort null (LOSO) and not by the noise null."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import velocity as V

import tempfile
tmp = Path(tempfile.mkdtemp())
rng = np.random.default_rng(2)
rows = []
for s in range(1, 301):
    n = 150
    per = rng.choice([1, 2], n)
    lat = np.where(per == 1, rng.uniform(40, 50, n), np.where(rng.random(n) < 0.8, rng.uniform(45, 50, n), rng.uniform(40, 45, n)))
    rows.append(pd.DataFrame({"specieskey": s, "lat": lat, "lon": rng.uniform(0, 10, n), "period": per}))
pd.concat(rows).to_parquet(tmp / "clean.parquet", index=False)
V.D, V.T, V.NREP = tmp, tmp, 99
V.load("clean.parquet", 12, 1.0)
obs = pd.DataFrame([r for r in map(V.observed, range(len(V.G["starts"]))) if r])
res = pd.DataFrame([V.nulls(i) for i in range(60)]).merge(obs, on="specieskey")
print("observed median", round(res.v_sph.median(), 2), "noise null", round(res.noise_med.median(), 2),
      "effort null", round(res.effort_med.median(), 2), "| ratio noise", round(res.noise_med.median() / res.v_sph.median(), 2),
      "ratio effort", round(res.effort_med.median() / res.v_sph.median(), 2))
print("poleward share observed", round(float((res.pole_km > 0).mean()), 2), "effort null pole_pos", round(res.effort_pole_pos.median(), 2),
      "noise null pole_pos", round(res.noise_pole_pos.median(), 2))
