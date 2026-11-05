"""Post hoc checks prompted by the independent review (deviations.md D3): how many contrasts find no DE genes at the
matched size (finding 1), the sex-imbalance gradient in exceedance (finding 2), and the floor that 500 null draws and
BH put on the empirical p (finding 3).

  posthoc_review.py -> results/tables/posthoc_review.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
c = pd.read_csv(T / "contrasts.csv")
n = len(c)
zero = c.n_de_real == 0
ind = c.indistinguishable_nde.astype(bool)
out = {"contrasts": n,
       "zero_de_real_at_matched_size": int(zero.sum()), "share_zero_de_real": round(float(zero.mean()), 4),
       "indistinguishable_nde": int(ind.sum()), "zero_de_among_indistinguishable": int((zero & ind).sum()),
       "share_zero_among_indistinguishable": round(float((zero & ind).sum() / ind.sum()), 4),
       "share_null_median_zero": round(float((c.n_de_null_median == 0).mean()), 4),
       "share_null_q95_zero": round(float((c.n_de_null_q95 == 0).mean()), 4)}
q = pd.qcut(c.sex_imbalance.rank(method="first"), 4, labels=["lowest", "second", "third", "highest"])
g = c.assign(q=q, exceed=~ind).groupby("q", observed=True)
out["sex_imbalance_quartiles"] = {str(k): {"median_sex_imbalance": round(float(v.sex_imbalance.median()), 3),
                                           "share_exceeding_null": round(float(v.exceed.mean()), 3),
                                           "median_null_q95_nde": round(float(v.n_de_null_q95.median()), 2)} for k, v in g}
out["corr_sex_imbalance_exceed"] = round(float(np.corrcoef(c.sex_imbalance.fillna(0), (~ind).astype(float))[0, 1]), 3)
pmin = 1 / 501
out["min_attainable_p"] = round(pmin, 5)
out["contrasts_at_min_p"] = int((np.isclose(c.n_de_p, pmin)).sum())
out["ties_needed_at_min_p_for_q_below_0p05"] = int(np.ceil(pmin * n / 0.05))
(T / "posthoc_review.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
