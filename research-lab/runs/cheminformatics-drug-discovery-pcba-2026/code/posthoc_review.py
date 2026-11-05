"""Post hoc checks prompted by the independent review (deviations.md D4).

1. Noise ceiling, comparable version (finding 1): for each new target and 5 random halvings, tau between a half-set
   ranking and the LIT consensus (one noisy ranking, like the H3 statistic), and tau between the two halves.
2. Memorization against ECFP4 + RF (finding 2): median EF1% in every benchmark x split arm.
3. Leakage-audit shares (finding 4): retained share by target median and pooled, actives' retention, and the hit rate
   and EF1% ceiling before and after the audit.

  posthoc_review.py -> results/tables/posthoc_review.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as A  # noqa: E402

M = pd.read_csv(A.T / "metrics.csv")
out = {}
lit = M[M["eval"] == "lit_pub"].groupby("method").ef1.median()
consensus = lit.reindex(A.METHODS).to_numpy()
S = A.load("new"); S = S[S.variant == A.PRIMARY]
rng = np.random.default_rng(20261106)
hc, hh = [], []
for t, g in S.groupby("target"):
    w = g.pivot_table(index="idx", columns="method", values="score")
    y = g.drop_duplicates("idx").set_index("idx").y.reindex(w.index).to_numpy()
    for _ in range(5):
        perm = rng.permutation(len(y)); a, b = perm[: len(y) // 2], perm[len(y) // 2:]
        va = np.array([A.ef(y[a], w[m].to_numpy()[a]) if m in w else np.nan for m in A.METHODS])
        vb = np.array([A.ef(y[b], w[m].to_numpy()[b]) if m in w else np.nan for m in A.METHODS])
        for v in (va, vb):
            if np.isfinite(v).all() and len(set(v)) > 1:
                hc.append(float(kendalltau(v, consensus).statistic))
        if np.isfinite(va).all() and np.isfinite(vb).all() and len(set(va)) > 1 and len(set(vb)) > 1:
            hh.append(float(kendalltau(va, vb).statistic))
full = pd.read_csv(A.T / "tau_h3.csv").tau
out["noise_ceiling_comparable"] = {"full_set_vs_lit_consensus": round(float(full.mean()), 3),
                                   "half_set_vs_lit_consensus": round(float(np.mean(hc)), 3),
                                   "half_vs_half": round(float(np.mean(hh)), 3), "halvings_per_target": 5}
arms = M.groupby(["eval", "variant"])
mem = {}
for (e, v), g in arms:
    med = g.groupby("method").ef1.median()
    if "nn" in med and "rf" in med:
        mem[f"{e} {v}"] = {"memorization_nn": round(float(med["nn"]), 2), "ecfp4_rf": round(float(med["rf"]), 2),
                           "difference": round(float(med["nn"] - med["rf"]), 2)}
out["memorization_vs_rf_median_ef1"] = mem
one = M[M.method == "rf"].set_index(["eval", "target", "variant"])
lk = {}
for e in ("new", "lit_cv"):
    try:
        full_v = one.xs((e, "random"), level=("eval", "variant")); aud = one.xs((e, A.PRIMARY), level=("eval", "variant"))
    except KeyError:
        continue
    j = full_v[["n", "actives", "hit_rate", "ef1_ceiling"]].join(aud[["n", "actives", "hit_rate", "ef1_ceiling"]], rsuffix="_audit", how="inner")
    lk[e] = {"targets": int(len(j)), "retained_share_median": round(float((j.n_audit / j.n).median()), 3),
             "retained_share_pooled": round(float(j.n_audit.sum() / j.n.sum()), 3),
             "actives_retained_share_median": round(float((j.actives_audit / j.actives).median()), 3),
             "hit_rate_median_before_after": [round(float(j.hit_rate.median()), 4), round(float(j.hit_rate_audit.median()), 4)],
             "ef1_ceiling_median_before_after": [round(float(j.ef1_ceiling.median()), 1), round(float(j.ef1_ceiling_audit.median()), 1)]}
out["leakage_audit"] = lk
(A.T / "posthoc_review.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
