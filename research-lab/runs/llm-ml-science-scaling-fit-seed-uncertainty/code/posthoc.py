"""Post hoc robustness (after fit.py and the late-jump finding; not preregistered).

1. W_1 over the 2,000 preregistered single-seed ladders that do not use the two 410M runs with late jumps (seeds 3, 4).
2. Ladders cut at step 64,000 (before the late rises of small models): W_1, W_3 and extrapolation error from fresh
   2,000-ladder draws with the preregistered fitting procedure.
-> results/tables/posthoc.json
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import fit as F  # noqa: E402

if __name__ == "__main__":
    out = {}
    lad, tgt = F.load()
    actual = float(tgt.loc["2.8b", "loss"])
    Nt, Dt = float(tgt.loc["2.8b", "N"]), float(tgt.loc["2.8b", "D"])
    S = pd.read_csv(F.T / "ladders_single.csv")
    s410 = S.seeds.str.split("-").str[-1].astype(int)
    keep = ~s410.isin([3, 4])
    out["W1_excluding_410m_seeds_3_4"] = {"ladders": int(keep.sum()), "W1": round(F.width(S.pred_2p8b[keep].to_numpy()), 5),
                                          "median_error": round(float(np.median(S.pred_2p8b[keep] - actual)), 5)}
    cut = lad[lad.step <= 64000]
    sbs = {s: sorted(cut[cut["size"] == s].seed.unique()) for s in F.SIZES}
    with ProcessPoolExecutor(int(os.environ.get("WORKERS", "16"))) as pool:
        res = {}
        for n in (1, 3):
            pred, par, _ = F.run_draws(cut, n, F.NLAD, Nt, Dt, np.random.default_rng(F.SEED + 10 + n), sbs, pool=pool)
            res[n] = pred
            out[f"cut64k_n{n}"] = {"W": round(F.width(pred), 5), "median_error": round(float(np.median(pred - actual)), 5),
                                   "share_overshoot": round(float((pred > actual).mean()), 4),
                                   "alpha_median": round(float(np.median(par[:, 3])), 4), "beta_median": round(float(np.median(par[:, 4])), 4)}
        out["cut64k_shrinkage_1_3"] = round(1 - out["cut64k_n3"]["W"] / out["cut64k_n1"]["W"], 4)
    (F.T / "posthoc.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
