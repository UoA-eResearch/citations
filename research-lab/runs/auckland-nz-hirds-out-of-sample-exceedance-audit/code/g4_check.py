"""G4 (plan section 5): 30 randomly sampled qualifying 6-hour annual maxima, recomputed independently from the raw
records and compared with maxima.py.

Independent method: the cumulative rain curve is piecewise linear between records, so the largest d-hour total is
reached with a window edge on a record time. Evaluate C(end) - C(end - d) for every end in {t_i, t_i + d} inside the
water year, directly from the records (no 5-minute grid). maxima.py's grid maximum must not exceed it and should be
within a few per cent of it.

  g4_check.py -> results/tables/g4_check.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import maxima as MX  # noqa: E402  (load() and bad_quality() only: the record reader and the quality rule)

D, T, d = RUN / "data", RUN / "results" / "tables", 6


def exact_max(f, y):
    t, v, q = MX.load(MX.S / f"{f}.npz")
    rain = np.where(MX.bad_quality(q, "primary"), 0.0, v)
    C = np.r_[0.0, np.cumsum(rain[1:])]                    # cumulative at record times; record 0 opens the series
    a, b = MX.wy_start(y), MX.wy_start(y + 1)
    ends = np.unique(np.r_[t, t + d * 60])
    ends = ends[(ends > a) & (ends <= b)]
    win = np.interp(ends, t, C) - np.interp(ends - d * 60, t, C)
    return float(win.max()) if len(win) else np.nan


def main():
    M = pd.read_parquet(D / "maxima.parquet")
    m = M[(M.d == d) & (M.variant == "primary") & (M.known_frac >= 0.9) & (M.wet_median_min <= 15)]
    s = m.sample(30, random_state=20261028)
    s = s.assign(exact=[exact_max(r.file, r.wy) for r in s.itertuples()])
    s["grid_over_exact"] = s.max_point / s.exact
    s[["file", "wy", "max_point", "exact", "grid_over_exact"]].to_csv(T / "g4_check.csv", index=False)
    print(s[["file", "wy", "max_point", "exact", "grid_over_exact"]].round(3).to_string(index=False))
    print("grid never above exact:", bool((s.max_point <= s.exact + 1e-6).all()),
          "| min ratio", round(float(s.grid_over_exact.min()), 4), "| median", round(float(s.grid_over_exact.median()), 4))


if __name__ == "__main__":
    main()
