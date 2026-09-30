#!/usr/bin/env python
"""V3 (plan.md sec 6): leakage assertions. For 12 random rounds, (a) the hospital vintage used was released on or
before the due date R - 3 and its data end at R - 7 or earlier; (b) the state wastewater signal recomputed from scratch
using ONLY samples collected on or before R - 3 - lag equals the signal the pipeline uses, for every window.
Output: results/tables/leakage_checks.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline as P  # noqa: E402

TAB = Path(__file__).resolve().parents[1] / "results" / "tables"


def main():
    lag = 10
    h = P.load_hosp()
    asof = pd.DatetimeIndex(sorted(h.as_of.unique()))
    samples, meta = P.ww_series()
    win_all = P.ww_windows(samples, lag)
    refs = pd.to_datetime(open(P.RAW / "ensemble_reference_dates.txt").read().split())
    rng = np.random.default_rng(3)
    rows = []
    for R in sorted(rng.choice(refs, 12, replace=False)):
        R = pd.Timestamp(R)
        v = P.vintage_for(asof, R)
        release = v + pd.Timedelta(days=4) if v.dayofweek == 5 else v
        last = h[h.as_of == v].target_end_date.max()
        cutoff = R - pd.Timedelta(days=3 + lag)
        S_pipe = P.state_signal(win_all, meta, cutoff)
        S_scratch = P.state_signal(P.ww_windows(samples[samples.collect <= cutoff], lag), meta, cutoff)
        S_scratch = S_scratch.reindex(index=S_pipe.index, columns=S_pipe.columns)
        diff = np.nanmax(np.abs(S_pipe.values - S_scratch.values))
        same_nan = bool((S_pipe.isna().values == S_scratch.isna().values).all())
        rows.append(dict(reference_date=R.date(), vintage=v.date(), release=release.date(), data_end=last.date(),
                         release_ok=release <= R - pd.Timedelta(days=3), data_ok=last <= R - pd.Timedelta(days=7),
                         ww_max_abs_diff=float(diff), ww_same_missing=same_nan))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "leakage_checks.csv", index=False)
    print(out.to_string(index=False))
    assert out.release_ok.all() and out.data_ok.all() and (out.ww_max_abs_diff < 1e-9).all() and out.ww_same_missing.all()
    print("V3 leakage checks passed")


if __name__ == "__main__":
    sys.exit(main())
