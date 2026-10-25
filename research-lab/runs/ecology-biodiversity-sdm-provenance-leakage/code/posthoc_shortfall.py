"""POST HOC (written after the H1 result): matched random removal fell short of C1's count for 13% of presences, so
the random arms removed fewer presences than C1. Removal counts by arm and source database, and the H1 contrast
restricted to species whose mean random removal is at least 90% of their C1 removal.
-> results/tables/posthoc_shortfall.json
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
R = ["C2", "C3", "C4", "C5", "C6"]
d = pd.DataFrame([json.loads(open(f).read()) for f in glob.glob(str(RUN / "data" / "work" / "rf" / "C*.json"))])
n = d.pivot(index="sp", columns="cond", values="n_pres")
rem1, remr = n["C0"] - n["C1"], n["C0"] - n[R].mean(axis=1)
auc = d.pivot(index="sp", columns="cond", values="auroc_src")
did = auc[R].mean(axis=1) - auc["C1"]
rng = np.random.default_rng(20261025)


def boot(x):
    x = x.to_numpy()
    b = [x[rng.integers(len(x), size=len(x))].mean() for _ in range(2000)]
    return [round(float(np.percentile(b, 2.5)), 5), round(float(np.percentile(b, 97.5)), 5)]


ok = remr >= 0.9 * rem1
out = {"species": int(len(did)), "mean_removed_C1": round(float(rem1.mean()), 1),
       "mean_removed_random": round(float(remr.mean()), 1),
       "matched_species": int(ok.sum()), "did_matched": round(float(did[ok].mean()), 5), "ci_matched": boot(did[ok]),
       "did_all": round(float(did.mean()), 5), "by_source_db": {}}
c0 = d[d.cond == "C0"].set_index("sp").auroc_db
for db in sorted({k for x in d.auroc_db for k in (x or {})}):
    sp = c0.map(lambda x: (x or {}).get(db)).dropna().index
    out["by_source_db"][db] = {"species": int(len(sp)), "mean_removed_C1": round(float(rem1.reindex(sp).mean()), 1),
                               "mean_removed_random": round(float(remr.reindex(sp).mean()), 1),
                               "random_to_C1_ratio": round(float(remr.reindex(sp).sum() / max(1, rem1.reindex(sp).sum())), 2)}
(T / "posthoc_shortfall.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "by_source_db"}))
