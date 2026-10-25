"""Synthetic checks of velocity.py: shift() against a brute-force centroid computation; a fixed-range species gives
observed ~ noise null; a species that truly moves 500 km gives observed >> null."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import velocity as V

import tempfile
tmp = Path(tempfile.mkdtemp())
rng = np.random.default_rng(1)
rows = []
for s in range(1, 41):                      # 40 fixed-range species around (45, 10), 300 km scatter
    n = 200
    rows.append(pd.DataFrame({"specieskey": s, "lat": 45 + rng.normal(0, 1.5, n), "lon": 10 + rng.normal(0, 2, n),
                              "period": rng.choice([1, 2], n, p=[0.6, 0.4])}))
n = 200                                     # one species that moves 4.5 degrees north between periods
per = rng.choice([1, 2], n)
rows.append(pd.DataFrame({"specieskey": 99, "lat": 45 + rng.normal(0, 1.0, n) + 4.5 * (per == 2), "lon": 10 + rng.normal(0, 1.0, n),
                          "period": per}))
df = pd.concat(rows)
V.D, V.T = tmp, tmp
df.to_parquet(tmp / "clean.parquet", index=False)
V.load("clean.parquet", 12, 1.0)
# brute force check of shift for species index 0 with a random assignment
cy, cx, per, cidx, k, clat, clon, xyz, uy, ux = V.species_arrays(0)
P1 = rng.random(len(per)) < 0.5
vs, va, po, k1, k2, _ = V.shift(cidx, k, clat, clon, xyz, P1[None, :])
def cen(cells):
    la, lo = np.radians(clat[cells]), np.radians(clon[cells])
    v = np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)].sum(0); return v / np.linalg.norm(v)
c1, c2 = cen(np.unique(cidx[P1])), cen(np.unique(cidx[~P1]))
bf = np.arccos(np.clip(c1 @ c2, -1, 1)) * V.R_EARTH / V.YEARS
print("shift vs brute force:", round(float(vs[0]), 6), round(float(bf), 6), "k1", k1[0], len(np.unique(cidx[P1])))
V.NREP = 199
obs = pd.DataFrame([r for r in map(V.observed, range(len(V.G["starts"]))) if r])
res = pd.DataFrame([V.nulls(i) for i in range(len(V.G["starts"]))]).merge(obs, on="specieskey")
fixed = res[res.specieskey < 99]
print("fixed-range: median observed", round(fixed.v_sph.median(), 2), "noise null", round(fixed.noise_med.median(), 2),
      "effort null", round(fixed.effort_med.median(), 2), "exceed p95 share", round(float((fixed.v_sph > fixed.effort_p95).mean()), 3))
mv = res[res.specieskey == 99].iloc[0]
print("mover: observed", round(mv.v_sph, 2), "expected about", round(4.5 * V.KM_PER_DEG / 28, 2), "noise null", round(mv.noise_med, 2), "pole_km", round(mv.pole_km, 1))
