#!/usr/bin/env python
"""(1) Preregistered comparison (plan.md sec 5): two-way fixed-effects event study, Y = wiki FE + month FE + event-time
dummies (-12..+6, month -1 omitted, endpoints binned), cluster bootstrap over wikis; average of +1..+6.
(2) EXPLORATORY seasonal adjustment (deviations.md D4): the Callaway-Sant'Anna estimator on year-over-year differences,
Y(m) - Y(m - 12), which removes each wiki's own seasonal cycle (school-holiday dips in the logged-out revert rate). Needs
a month 12 months earlier, so it uses 2025-01 onward and drops the 2024-11 cohort.
Output: results/tables/twfe.csv, results/tables/did_yoy.csv, results/tables/eventstudy_yoy.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def twfe(p, outcome, nboot=1000, seed=0):
    q = p.dropna(subset=[outcome]).copy()
    q["mi"] = q.month.map(lambda m: m.ordinal)
    q["gi"] = q.g.map(lambda g: g.ordinal if pd.notna(g) else np.nan)
    q["e"] = (q.mi - q.gi).clip(-12, 6)
    wikis = sorted(q.wiki.unique())
    months = sorted(q.mi.unique())
    evs = [e for e in range(-12, 7) if e not in (-1, 0)]

    def fit(qq):
        X = [np.ones(len(qq))]
        for w in wikis[1:]:
            X.append((qq.wiki == w).values.astype(float))
        for m in months[1:]:
            X.append((qq.mi == m).values.astype(float))
        for e in evs:
            X.append((qq.e == e).values.astype(float))
        X = np.column_stack(X)
        beta = np.linalg.lstsq(X, qq[outcome].values, rcond=None)[0]
        b = dict(zip(evs, beta[-len(evs):]))
        return np.mean([b[e] for e in range(1, 7)]), b
    est, b = fit(q)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        pick = rng.choice(wikis, len(wikis))
        qq = pd.concat([q[q.wiki == w].assign(wiki=w) for w in pick])
        bs.append(fit(qq)[0])
    return est, np.percentile(bs, [2.5, 97.5]), b


def main():
    p = pd.read_parquet(TAB / "panel_primary.parquet")
    p["month"] = p.month.astype("period[M]") if p.month.dtype != "period[M]" else p.month
    rows = []
    for oc in ("Y_LO", "Y_REG"):
        est, ci, b = twfe(p, oc)
        rows.append(dict(model="TWFE event study", outcome=oc, att=est, lo=ci[0], hi=ci[1]))
        print(f"TWFE {oc}: {est:+.5f} [{ci[0]:+.5f}, {ci[1]:+.5f}]", flush=True)
    pd.DataFrame(rows).to_csv(TAB / "twfe.csv", index=False)

    # exploratory year-over-year version
    q = p.copy()
    q = q.sort_values(["wiki", "month"])
    lag = q[["wiki", "month", "Y_LO", "Y_REG"]].copy()
    lag["month"] = lag.month + 12
    q = q.merge(lag, on=["wiki", "month"], how="left", suffixes=("", "_ly"))
    q["YOY_LO"] = q.Y_LO - q.Y_LO_ly
    q["YOY_REG"] = q.Y_REG - q.Y_REG_ly
    q = q[q.month >= pd.Period("2025-01", "M")]
    out, es_rows = [], []
    for oc in ("YOY_LO", "YOY_REG"):
        Y, gidx, months = A.matrices(q, oc)
        es, ov, _ = A.att_es(Y, gidx, months)
        b_ov, _, b_es = A.bootstrap(Y, gidx, months, 2000)
        lo, hi = np.nanpercentile(b_ov, [2.5, 97.5])
        base = q[(q.month < q.g) & q.g.notna()]["Y_LO" if oc == "YOY_LO" else "Y_REG"].mean()
        out.append(dict(outcome=oc, att=ov, lo=lo, hi=hi, rel=ov / base, rel_lo=lo / base, rel_hi=hi / base,
                        n_cohorts=int(len(set(gidx[(gidx >= 1) & (gidx < len(months))])))))
        for e in es.index:
            ci = np.nanpercentile(b_es[e], [2.5, 97.5])
            es_rows.append(dict(outcome=oc, e=e, att=es[e], lo=ci[0], hi=ci[1]))
        print(f"YoY {oc}: {ov:+.5f} [{lo:+.5f}, {hi:+.5f}]  rel {ov / base:+.3f} [{lo / base:+.3f}, {hi / base:+.3f}]", flush=True)
    pd.DataFrame(out).to_csv(TAB / "did_yoy.csv", index=False)
    pd.DataFrame(es_rows).to_csv(TAB / "eventstudy_yoy.csv", index=False)


if __name__ == "__main__":
    sys.exit(main())
