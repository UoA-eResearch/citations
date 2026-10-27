"""EXPLORATORY (not preregistered; written after the primary results): how much of the absolute bias could be sampling
noise in each target's prospective RMSE? Normal-theory SE of an RMSE from n compounds: RMSE / sqrt(2n). Ignores the
retrospective repeats' own noise and heavy-tailed errors, so it is a rough lower bound on noise.
  noise_check.py -> results/tables/noise_check.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

T = Path(__file__).resolve().parents[1] / "results" / "tables"
L = pd.read_csv(T / "bias_long.csv")
P = L[(L.set == "primary") & (L.model == "rf")]
t = P.drop_duplicates("target").set_index("target")
se = t.pros_rmse / np.sqrt(2 * t.pros_n)
out = {"median_se_prospective_rmse": round(float(se.median()), 3),
       "median_abs_bias_expected_from_prospective_noise_alone": round(float((0.6745 * se).median()), 3), "by_splitter": {}}
for s, g in P.groupby("splitter"):
    e = se.reindex(g.target).to_numpy()
    out["by_splitter"][s] = {"observed_median_abs_bias": round(float(g.bias.abs().median()), 3),
                             "share_abs_bias_within_2se": round(float((g.bias.abs().to_numpy() < 2 * e).mean()), 3)}
(T / "noise_check.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
