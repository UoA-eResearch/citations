"""EXPLORATORY (not preregistered; written after the primary results; extended after review, finding 1): how much of
the absolute bias could be sampling noise? Two sources per target and splitter (RF, primary set):
  - the prospective RMSE's normal-theory SE, RMSE / sqrt(2n);
  - the retrospective estimate's SE, the standard deviation of its repeats' RMSEs / sqrt(repeats) (from data/fits).
Combined in quadrature; the expected median |bias| from noise alone is 0.6745 x the combined SE. Heavy-tailed errors
are ignored, so this remains a lower bound on noise.
  noise_check.py -> results/tables/noise_check.json
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
L = pd.read_csv(T / "bias_long.csv")
P = L[(L.set == "primary") & (L.model == "rf")]
t = P.drop_duplicates("target").set_index("target")
se_p = t.pros_rmse / np.sqrt(2 * t.pros_n)
rows = []
for f in glob.glob(str(RUN / "data" / "fits" / "*.json")):
    d = json.load(open(f))
    r = pd.DataFrame(d["retro"])
    r = r[r.model == "rf"]
    for s, g in r.groupby("splitter"):
        k = len(g)
        rows.append((d["target"], s, k, float(g.rmse.std(ddof=1) / np.sqrt(k)) if k > 1 else np.nan))
R = pd.DataFrame(rows, columns=["target", "splitter", "repeats", "se_retro"]).set_index(["target", "splitter"])
out = {"median_se_prospective_rmse": round(float(se_p.median()), 3),
       "median_abs_bias_expected_from_prospective_noise_alone": round(float((0.6745 * se_p).median()), 3), "by_splitter": {}}
for s, g in P.groupby("splitter"):
    e_p = se_p.reindex(g.target).to_numpy()
    e_r = np.array([R.se_retro.get((tg, s), np.nan) for tg in g.target])
    comb = np.sqrt(e_p ** 2 + np.nan_to_num(e_r) ** 2)
    out["by_splitter"][s] = {"observed_median_abs_bias": round(float(g.bias.abs().median()), 3),
                             "share_abs_bias_within_2se": round(float((g.bias.abs().to_numpy() < 2 * e_p).mean()), 3),
                             "median_se_retro": None if np.all(np.isnan(e_r)) else round(float(np.nanmedian(e_r)), 3),
                             "median_se_combined": round(float(np.median(comb)), 3),
                             "expected_median_abs_bias_from_noise": round(float(np.median(0.6745 * comb)), 3),
                             "share_abs_bias_within_2se_combined": round(float((g.bias.abs().to_numpy() < 2 * comb).mean()), 3),
                             "note": "one repeat: retrospective SE undefined, prospective term only" if s in ("time",) else ""}
(T / "noise_check.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
