"""Preregistered outcome variant (plan section 2): emergence as the FIRST observation of a pair by any isolate,
instead of the two-BioProject rule. Under the primary rule 705 of 847 test "emergences" are second-BioProject
confirmations of pairs already seen once, so this variant tests the first-appearance reading directly.

  variant_any.py -> results/tables/variant_any.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as A  # noqa: E402


def main():
    tr = pd.read_parquet(A.D / "task_train_any.parquet")
    te = pd.read_parquet(A.D / "task_test_any.parquet")
    y = te.y.to_numpy(); p_null = te.null_p.to_numpy()
    out = {"train_positives": int(tr.y.sum()), "test_candidates": len(te), "test_positives": int(y.sum())}
    for nm, feats in (("full", A.FULL), ("no_embedding", A.EFFORT + A.COOC + A.TAX)):
        p, _, _ = A.fit_predict(tr, te, feats)
        rng = np.random.default_rng(A.SEED + 11)
        pm, pn = A.precision_at(p, y, 100), A.precision_at(p_null, y, 100)
        ratios = []
        for idx in A.boot_indices(te.gene.to_numpy(), rng, A.B):
            a_, b_ = A.precision_at(p[idx], y[idx], 100), A.precision_at(p_null[idx], y[idx], 100)
            ratios.append(a_ / b_ if b_ > 0 else np.nan)
        ratios = np.array(ratios, float)
        out[nm] = {"precision_at_100": pm, "null_precision_at_100": pn,
                   "ratio": round(pm / pn, 3) if pn else None,
                   "ratio_ci": [float(np.nanpercentile(ratios, 2.5)), float(np.nanpercentile(ratios, 97.5))]}
    (A.T / "variant_any.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
