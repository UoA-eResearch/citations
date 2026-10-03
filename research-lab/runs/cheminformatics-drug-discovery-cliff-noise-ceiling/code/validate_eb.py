#!/usr/bin/env python
"""Synthetic calibration check of the empirical-Bayes cliff confidence (plan.md sec 7), run before real data.

True differences from a heavy-tailed known prior (Laplace, scale 0.45, i.e. most similar pairs differ little but some
differ a lot), noise SD s drawn from {0.35, 0.5, 0.7} / sqrt(n) with n in {1, 2, 3}; 20,000 pairs. Fit the NPMLE on the
observed differences, then check: among pairs with confidence in [0.7, 0.9], the fraction that are true |diff| > 1
cliffs must be 70-90%; and overall reliability by confidence decile.
Output: results/tables/validation_eb.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import noise_eb as NE  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def main():
    rng = np.random.default_rng(11)
    n = 20000
    delta = rng.laplace(0, 0.45, n)
    s = rng.choice([0.35, 0.5, 0.7], n) * np.sqrt(1 / rng.choice([1, 2, 3], n) + 1 / rng.choice([1, 2, 3], n))
    d = delta + rng.normal(0, s)
    w = NE.npmle(d, s)
    c = NE.confidence(d, s, w)
    true = np.abs(delta) > 1
    band = (c >= 0.7) & (c <= 0.9)
    rows = []
    for lo in np.arange(0, 1, 0.1):
        m = (c >= lo) & (c < lo + 0.1 + (lo >= 0.9) * 0.01)
        rows.append(dict(bin=f"{lo:.1f}-{lo + 0.1:.1f}", n=int(m.sum()), mean_conf=float(c[m].mean()) if m.any() else np.nan,
                         true_rate=float(true[m].mean()) if m.any() else np.nan))
    r = pd.DataFrame(rows)
    r.to_csv(RUN / "results" / "tables" / "validation_eb.csv", index=False)
    print(r.round(3).to_string(index=False))
    rate = true[band].mean()
    print(f"band [0.7, 0.9]: {band.sum()} pairs, true-cliff rate {rate:.3f} -> {'PASS' if 0.7 <= rate <= 0.9 else 'FAIL'}")
    obs_cliff = np.abs(d) > 1
    print(f"observed cliffs {obs_cliff.sum()}, of which truly > 1: {true[obs_cliff].mean():.3f}; mean confidence {c[obs_cliff].mean():.3f}")


if __name__ == "__main__":
    main()
