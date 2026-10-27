"""G3 traces: for three targets (smallest, median and a large one by training size), recompute the primary model's
prospective RMSE independently of run.py's loop and compare it with data/fits/<target>.json.
  plausibility_check.py -> results/tables/plausibility_traces.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
from run import SEED, featurise  # noqa: E402

D, T = RUN / "data", RUN / "results" / "tables"
tr, ps = pd.read_parquet(D / "train.parquet"), pd.read_parquet(D / "prospective.parquet")
sizes = tr.groupby("target").size().sort_values()
picks = [sizes.index[0], sizes.index[len(sizes) // 2], sizes.index[int(len(sizes) * 0.9)]]
out = []
for t in picks:
    from sklearn.ensemble import RandomForestRegressor
    g = tr[tr.target == t].reset_index(drop=True)
    p = ps[(ps.target == t) & (ps.set == "primary")].reset_index(drop=True)
    f, _, ok, _ = featurise(g.smiles); X = np.stack([a for a, k in zip(f, ok) if k]); y = g.pchembl.to_numpy(float)[ok]
    fp, _, okp, _ = featurise(p.smiles); Xp = np.stack([a for a, k in zip(fp, okp) if k]); yp = p.pchembl.to_numpy(float)[okp]
    pred = RandomForestRegressor(n_estimators=500, n_jobs=1, random_state=SEED).fit(X, y).predict(Xp)
    rmse = float(np.sqrt(np.mean((pred - yp) ** 2)))
    fit = json.loads((D / "fits" / f"{t}.json").read_text())
    stored = next(x["rmse"] for x in fit["pros"] if x["set"] == "primary" and x["model"] == "rf")
    retro = {s: round(float(np.mean([x["rmse"] for x in fit["retro"] if x["splitter"] == s and x["model"] == "rf"])), 4)
             for s in ("random", "scaffold", "document", "time")}
    out.append({"target": t, "train_compounds": int(len(y)), "prospective_compounds": int(len(yp)), "label_sd_train": round(float(y.std()), 3),
                "label_sd_prospective": round(float(yp.std()), 3), "rf_prospective_rmse_recomputed": round(rmse, 4),
                "rf_prospective_rmse_stored": round(float(stored), 4), "rf_retro_rmse_by_splitter": retro, "notes": fit["notes"]})
    print(out[-1], flush=True)
(T / "plausibility_traces.json").write_text(json.dumps(out, indent=1))
