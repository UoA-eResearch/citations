"""Reviewer check 4: detectability for PARTIAL reductions (calls thinned to 50% or 25%) rather than complete closures,
run through recovery.one_event exactly as detectability.py does (own-history model). 60 reps per cell."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import recovery as R
MUS = (0.5, 1.0, 2.0, 4.0); ALPHAS = (0.25, 1.0); LENGTHS = (7, 14, 28); KEEP = (0.5, 0.25, 0.0); REPS = 60

def cell(args):
    mu, alpha, L, keep, k = args
    rng = np.random.default_rng([99, k])
    d0 = pd.Timestamp("2022-06-01")
    dates = pd.date_range(d0 - pd.Timedelta(days=R.FIT_BACK), d0 + pd.Timedelta(days=R.HORIZON + 2 * R.MAX_K))
    n = 1.0 / alpha; day = (dates - d0).days.to_numpy()
    det, Ts, n_ok = 0, [], 0
    for _ in range(REPS):
        y = rng.negative_binomial(n, n / (n + mu), size=len(dates)).astype(float)
        m = (day >= 0) & (day < L)
        y[m] = rng.binomial(y[m].astype(int), keep) if keep > 0 else 0.0
        res = R.one_event(pd.Series(y, index=dates), None, d0, rng, use_index=False)
        if res.get("status") != "ok": continue
        n_ok += 1; det += res["disrupted"]
        if res["disrupted"]: Ts.append(res["T"])
    return dict(mu=mu, alpha=alpha, L=L, keep=keep, p_detect=det / n_ok, n_ok=n_ok,
                median_T=float(np.median(Ts)) if Ts else None)

if __name__ == "__main__":
    from multiprocessing import Pool
    combos = [(m, a, l, kp) for m in MUS for a in ALPHAS for l in LENGTHS for kp in KEEP]
    with Pool(20) as pool:
        rows = pool.map(cell, [(m, a, l, kp, i) for i, (m, a, l, kp) in enumerate(combos)])
    t = pd.DataFrame(rows)
    print(t.pivot_table(index=["mu", "alpha", "L"], columns="keep", values="p_detect").round(2).to_string())
    t.to_csv(Path(__file__).parent / "partial_sim.csv", index=False)
