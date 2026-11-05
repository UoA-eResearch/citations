"""Post hoc checks prompted by the independent review (deviations.md D1): the spread of prospective RMSE across the
five model families (finding 3), test fractions by splitter (finding 4), the lenient set's size per target
(finding 7), and whether dropped repeats fall on small targets (finding 8).

  posthoc_review.py -> results/tables/posthoc_review.json
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
L = pd.read_csv(T / "bias_long.csv")
out = {}
P = L[L.set == "primary"].drop_duplicates(["target", "model"])
spread = P.groupby("target").pros_rmse.agg(lambda x: x.max() - x.min())
out["model_spread"] = {"median_per_target_spread_pros_rmse": round(float(spread.median()), 3),
                       "median_pros_rmse_by_model": P.groupby("model").pros_rmse.median().round(3).to_dict()}
fr, drops = [], []
for f in glob.glob(str(RUN / "data" / "fits" / "*.json")):
    d = json.load(open(f))
    r = pd.DataFrame(d["retro"]); r = r[r.model == "rf"]
    for s, g in r.groupby("splitter"):
        fr.append((s, float((g.n / d["n_train"]).median())))
    drops.append((d["target"], d["n_train"], sum(1 for k, v in (d.get("notes") or {}).items() if str(v).startswith("dropped"))))
F = pd.DataFrame(fr, columns=["splitter", "test_fraction"])
out["test_fraction_median_by_splitter"] = F.groupby("splitter").test_fraction.median().round(3).to_dict()
Dd = pd.DataFrame(drops, columns=["target", "n_train", "dropped_repeats"])
out["dropped_repeats"] = {"targets_with_drops": int((Dd.dropped_repeats > 0).sum()),
                          "median_n_train_with_drops": float(Dd[Dd.dropped_repeats > 0].n_train.median()),
                          "median_n_train_without_drops": float(Dd[Dd.dropped_repeats == 0].n_train.median())}
Le = L[L.set == "lenient"].drop_duplicates("target")
out["lenient_set"] = {"targets": int(len(Le)), "rows": int(Le.pros_n.sum()), "median_compounds_per_target": float(Le.pros_n.median()),
                      "share_targets_under_20": round(float((Le.pros_n < 20).mean()), 3)}
(T / "posthoc_review.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
