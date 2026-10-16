"""How long must a closure be before this method can see it, at a given level of port traffic?

Pure simulation - no port data - so it runs before plan.md. Most Pacific island ports average under one call
a day (12 of 62 reach 0.5), and at that traffic a short closure is indistinguishable from an ordinary quiet
week. Without this, a recovery time of zero at a quiet port would read as resilience when it is blindness.

For each traffic level mu (calls/day), dispersion alpha and closure length L: simulate 730 days of NB history
plus 135 days after, set calls to zero for days 0..L-1, run recovery.one_event exactly as on real data (with
the own-history model, no reference index), and record whether a disruption was detected and the recovery
time it reported. Writes results/tables/detectability.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recovery as R  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
MUS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
ALPHAS = (0.25, 1.0)
LENGTHS = (0, 2, 4, 7, 10, 14, 21, 28)
REPS = 120


def cell(args):
    """One (mu, alpha, closure length) cell, seeded per cell so the grid reproduces in any order."""
    mu, alpha, L, k = args
    rng = np.random.default_rng([R.SEED + 1, k])
    d0 = pd.Timestamp("2022-06-01")
    # long enough for the widest traffic-scaled window: an earlier version stopped at HORIZON + 14 days, so quiet
    # ports came back "short_followup" and were silently scored as undetected
    dates = pd.date_range(d0 - pd.Timedelta(days=R.FIT_BACK), d0 + pd.Timedelta(days=R.HORIZON + 2 * R.MAX_K))
    n = 1.0 / alpha
    day = (dates - d0).days.to_numpy()
    det, n_ok, Ts = 0, 0, []
    for _ in range(REPS):
        y = rng.negative_binomial(n, n / (n + mu), size=len(dates)).astype(float)
        y[(day >= 0) & (day < L)] = 0.0
        res = R.one_event(pd.Series(y, index=dates), None, d0, rng, use_index=False)
        if res.get("status") != "ok":
            continue
        n_ok += 1
        det += res["disrupted"]
        if res["disrupted"]:
            Ts.append(res["T"])
    if n_ok < REPS:
        raise RuntimeError(f"cell mu={mu} alpha={alpha} L={L}: only {n_ok}/{REPS} runs valid")
    return dict(mu=mu, alpha=alpha, closure_days=L, p_detect=det / n_ok, n_ok=n_ok,
                median_T_if_detected=float(np.median(Ts)) if Ts else None)


def main():
    # parallel over cells: one core took ~100 s a cell, ~2.7 h for the grid
    from multiprocessing import Pool
    combos = [(m, a, l) for m in MUS for a in ALPHAS for l in LENGTHS]
    with Pool(28) as pool:
        rows = pool.map(cell, [(m, a, l, k) for k, (m, a, l) in enumerate(combos)])
    for r in rows:
        print(f"mu {r['mu']:4.2f} alpha {r['alpha']:.2f} L {r['closure_days']:2d}: detect {r['p_detect']:.2f}"
              + (f", median T {r['median_T_if_detected']:.0f}" if r["median_T_if_detected"] is not None else ""))
    t = pd.DataFrame(rows)
    l80 = {}
    for (mu, alpha), g in t[t.closure_days > 0].groupby(["mu", "alpha"]):
        hit = g[g.p_detect >= 0.8]
        l80[f"mu={mu},alpha={alpha}"] = int(hit.closure_days.min()) if len(hit) else None
    json.dump(dict(grid=rows, shortest_closure_detected_80pct=l80,
                   false_alarm_rate_by_mu={str(m): float(t[(t.mu == m) & (t.closure_days == 0)].p_detect.mean()) for m in MUS}),
              open(TAB / "detectability.json", "w"), indent=1)
    print("\nshortest closure detected 80% of the time:", l80)


if __name__ == "__main__":
    sys.exit(main())
