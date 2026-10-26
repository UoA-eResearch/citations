"""Per-trigger spread (plan section 6, expected false positives by trigger): observed significant pairs minus expected
(sum of station p0) per trigger, against the binomial variance sum p0 (1 - p0) that independent station outcomes would
give. -> results/tables/trigger_dispersion.json"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

T = Path(__file__).resolve().parents[1] / "results" / "tables"
pr = pd.read_parquet(T / "pairs_primary.parquet")
pop = pr[pr.in_population].copy()
pop["var"] = pop.p0 * (1 - pop.p0)
g = pop.groupby("trigger").agg(obs=("sig", "sum"), exp=("p0", "sum"), var=("var", "sum"))
g["d"] = g.obs - g.exp
z = g.d / np.sqrt(g["var"])
out = {"triggers": int(len(g)), "dispersion_ratio": round(float((g.d ** 2).sum() / g["var"].sum()), 2),
       "share_obs_above_exp": round(float((g.d > 0).mean()), 3), "median_obs_minus_exp": round(float(g.d.median()), 2),
       "triggers_z_gt_3": int((z > 3).sum()), "triggers_z_lt_minus3": int((z < -3).sum())}
(T / "trigger_dispersion.json").write_text(json.dumps(out, indent=1))
print(out)
