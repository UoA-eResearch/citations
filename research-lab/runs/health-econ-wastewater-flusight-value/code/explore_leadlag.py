#!/usr/bin/env python
"""EXPLORATORY (deviations.md D3): how far does the state wastewater signal lead hospital admissions?
Using final hospital data and all wastewater samples (no reporting delay), the weekly change in the state signal
(windows ending on Saturdays, i.e. aligned with the hospital epiweek) is correlated with the weekly change in
log admissions at leads -3..+4 weeks, pooled over state-weeks in the primary panel seasons (2023-10 to 2026-05),
and the same for levels after removing each state-season mean.
Output: results/tables/leadlag.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline as P  # noqa: E402
from score import TAB, panels  # noqa: E402


def main():
    h = P.load_hosp()
    loc = P.locations()
    Y = P.yweek(h[h.as_of == h.as_of.max()], loc.population)
    samples, meta = P.ww_series()
    win = P.ww_windows(samples, -3)          # lag -3 puts window ends on the round date grid R (Saturdays)
    S = P.state_signal(win, meta, pd.Timestamp("2026-09-30"))
    S = S.loc[:, S.columns.isin(Y.columns)]
    pan = panels()
    prim = pan[pan.coverage >= 0.5]
    rows = []
    for lead in range(-3, 5):
        xs, ys, xl, yl = [], [], [], []
        for _, r in prim.iterrows():
            y0, y1 = int(r.season[:4]), int(r.season[:4]) + 1
            wk = [c for c in S.columns if pd.Timestamp(f"{y0}-10-01") <= c <= pd.Timestamp(f"{y1}-05-31")]
            if r.location not in S.index:
                continue
            s = S.loc[r.location, wk]
            yy = Y.loc[r.location].reindex([c + pd.Timedelta(weeks=lead) for c in wk]).values
            ok = np.isfinite(s.values) & np.isfinite(yy)
            if ok.sum() < 10:
                continue
            ds, dy = np.diff(s.values), np.diff(yy)
            okd = np.isfinite(ds) & np.isfinite(dy)
            xs += list(ds[okd]); ys += list(dy[okd])
            xl += list(s.values[ok] - s.values[ok].mean()); yl += list(yy[ok] - yy[ok].mean())
        rows.append(dict(lead_weeks=lead, corr_changes=np.corrcoef(xs, ys)[0, 1], corr_levels=np.corrcoef(xl, yl)[0, 1], n=len(xs)))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "leadlag.csv", index=False)
    print("positive lead = wastewater week precedes the hospital week by that many weeks")
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
