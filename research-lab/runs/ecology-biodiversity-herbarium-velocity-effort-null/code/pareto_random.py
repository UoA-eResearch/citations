"""Post hoc (D4, after the confirmation pass): the Pareto inclusion check of absorption_test.py on a seeded random
150 primary species with fewer than 100 records, instead of the 5 smallest. -> results/tables/pareto_random.json"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import velocity as V  # noqa: E402

T = RUN / "results" / "tables"
V.D, V.T = RUN / "data", T
V.load("clean.parquet", 12, 1.0)
nu = pd.read_parquet(T / "nulls_primary.parquet")
small = nu[(nu.n1 + nu.n2) < 100].sample(150, random_state=20261109)
idx_of = {int(V.G["sp"][V.G["starts"][i]]): i for i in range(len(V.G["starts"]))}
rows = []
for key in small.specieskey:
    cy, cx, per, cidx, k, clat, clon, xyz, uy, ux = V.species_arrays(idx_of[int(key)])
    n, n1 = len(per), int((per == 1).sum())
    w, _ = V.weights(cy, cx, per, uy, ux, cidx)
    with np.errstate(divide="ignore", invalid="ignore"):
        target = np.where(np.isinf(w), 1.0, n1 * w / (n1 * w + (n - n1)))
    rng = np.random.default_rng(20261109)
    hits = np.zeros(n)
    for _ in range(50):
        u = rng.random((100, n))
        with np.errstate(divide="ignore", invalid="ignore"):
            keys = np.nan_to_num((u / (1 - u)) / w[None, :], nan=np.inf, posinf=np.inf)
        np.add.at(hits, np.argpartition(keys, n1 - 1, axis=1)[:, :n1].ravel(), 1)
    emp = hits / 5000
    rows.append({"max_abs_dev": float(np.abs(emp - target).max()), "target_sum_rel_err": float(abs(target.sum() - n1) / n1),
                 "corr": float(np.corrcoef(emp, target)[0, 1]) if target.std() > 0 and emp.std() > 0 else None})
d = pd.DataFrame(rows)
out = {"species": len(d), "max_abs_dev_median": round(float(d.max_abs_dev.median()), 3), "max_abs_dev_max": round(float(d.max_abs_dev.max()), 3),
       "target_sum_rel_err_median": round(float(d.target_sum_rel_err.median()), 3), "corr_median": round(float(d["corr"].median()), 4)}
(T / "pareto_random.json").write_text(json.dumps(out, indent=1) + "\n")
print(out)
