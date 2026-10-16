"""Post-hoc, descriptive checks written after the preregistered results were seen (deviations D3). None changes a
verdict.

The preregistered trend is linear within each segment. A field whose output was lifted by make-up drilling and then
ran down would show a small linear trend over the whole segment while running down fast between campaigns -
Ohaaki's annual median P95 went 35-40 MW (2000-07), 66 MW (2008), back to ~40 MW (2013) and flat since.

  R1  rolling 60-month trend for every field (deseasonalised log P95, OLS slope; descriptive, no intervals)
  R2  steps: consecutive calendar years whose median P95 differs by >= 15%, inside a preregistered segment
  R3  the run-down after each upward step: the same GLS-AR(1) trend model fitted from the step year to the end of
      the decline (the first later year at or below the pre-step level, or the segment end), exploratory
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def deseason(g):
    d = g[g.ok].copy()
    y = np.log(d.p95.to_numpy(float))
    X = sm.add_constant(pd.get_dummies(d.m.dt.month, drop_first=True).astype(float).to_numpy())
    d["ly"] = y - X @ sm.OLS(y, X).fit().params + y.mean()
    d["t"] = d.m.dt.year + (d.m.dt.month - 0.5) / 12
    return d


def main():
    fm = pd.read_csv(TAB / "field_monthly.csv")
    mem = pd.read_csv(TAB / "field_membership.csv")
    roll, steps, rundowns = [], [], []
    for field in sorted(fm.field.unique()):
        for g in A.segments(fm, mem, field):
            d = deseason(g).reset_index(drop=True)
            for i in range(60, len(d) + 1):
                w = d.iloc[i - 60:i]
                b = np.polyfit(w.t, w.ly, 1)[0]
                roll.append(dict(field=field, end=str(w.m.iloc[-1]), pct_per_yr=A.pct(b)))
            ann = d.groupby(d.m.dt.year).p95.median()
            for y0, y1 in zip(ann.index[:-1], ann.index[1:]):
                ch = ann[y1] / ann[y0] - 1
                if abs(ch) >= 0.15:
                    steps.append(dict(field=field, from_year=int(y0), to_year=int(y1), change_pct=100 * ch,
                                      mw_from=float(ann[y0]), mw_to=float(ann[y1])))
                    if ch > 0:
                        later = ann[ann.index > y1]
                        back = later[later <= ann[y0]]
                        end = int(back.index[0]) if len(back) else int(ann.index[-1])
                        sub = g[(g.m.dt.year >= y1) & (g.m.dt.year <= end)].copy()
                        if sub.ok.sum() >= 36:
                            r = A.seg_trend(sub)
                            rundowns.append(dict(field=field, start_year=int(y1), end_year=end, months=r["n"],
                                                 pct_per_yr=A.pct(r["b"]),
                                                 ci=[A.pct(r["b"] - 1.96 * r["se"]), A.pct(r["b"] + 1.96 * r["se"])]))
    pd.DataFrame(roll).to_csv(TAB / "rolling_60m_trend.csv", index=False)
    out = dict(steps=steps, rundowns_after_upward_steps=rundowns,
               rolling_60m_range={f: [float(g.pct_per_yr.min()), float(g.pct_per_yr.max())]
                                  for f, g in pd.DataFrame(roll).groupby("field")})
    json.dump(out, open(TAB / "supplementary.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    sys.exit(main())
