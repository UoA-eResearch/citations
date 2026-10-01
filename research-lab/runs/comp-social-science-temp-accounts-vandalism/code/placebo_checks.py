#!/usr/bin/env python
"""Checks requested by the independent review (deviations.md D5).
1. In-time placebo: the 2025-26 waves' treatment dates shifted back 12 months, on 2024-01..2025-05 (when none of these wikis
   had switched; the 2024-11 wave is excluded). Same estimator and bootstrap. A non-zero 'effect' measures the design's
   bias (e.g. seasonality interacting with the wave timing).
2. Size of the pre-trend tests: on the same no-treatment panel, fake treatment months are randomly reassigned across wikis
   (100 draws, 200 bootstrap draws each); rejection rates at 5% for the 11-lead and the 5-lead (-6..-2) Wald tests.
Output: results/tables/placebo_intime.csv, results/tables/pretrend_size.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

TAB = Path(__file__).resolve().parents[1] / "results" / "tables"


def wald(es, b_es, leads):
    leads = [e for e in leads if e in es.index and e in b_es.columns]
    v = es[leads].values
    cov = np.cov(b_es[leads].dropna().values, rowvar=False)
    return float(1 - chi2.cdf(float(v @ np.linalg.pinv(cov) @ v), len(leads)))


def main():
    p = pd.read_parquet(TAB / "panel_primary.parquet")
    p = p[p.g >= pd.Period("2025-01", "M")].copy()
    p["g"] = p.g - 12
    p = p[p.month <= pd.Period("2025-05", "M")]
    rows = []
    for oc in ("Y_LO", "Y_REG"):
        Y, gidx, months = A.matrices(p, oc)
        es, ov, pm = A.att_es(Y, gidx, months)
        b, br, bes = A.bootstrap(Y, gidx, months, 2000)
        lo, hi = np.nanpercentile(b, [2.5, 97.5])
        rows.append(dict(check="in-time placebo (dates shifted back 12 months)", outcome=oc, att=ov, lo=lo, hi=hi,
                         rel=ov / pm, n_wikis=Y.shape[0]))
        print(f"in-time placebo {oc}: {ov:+.4f} [{lo:+.4f}, {hi:+.4f}]  rel {ov / pm:+.3f}", flush=True)
    pd.DataFrame(rows).to_csv(TAB / "placebo_intime.csv", index=False)
    Y, gidx, months = A.matrices(p, "Y_LO")
    rng = np.random.default_rng(11)
    rej = []
    for _ in range(100):
        g2 = rng.permutation(gidx)
        es, ov, pm = A.att_es(Y, g2, months)
        _, _, bes = A.bootstrap(Y, g2, months, 200, seed=int(rng.integers(1e9)))
        rej.append((wald(es, bes, range(-12, -1)), wald(es, bes, range(-6, -1))))
    rej = np.array(rej)
    out = pd.DataFrame([dict(test="11 leads (-12..-2)", reject_5pct=float((rej[:, 0] < 0.05).mean()), reject_1pct=float((rej[:, 0] < 0.01).mean())),
                        dict(test="5 leads (-6..-2)", reject_5pct=float((rej[:, 1] < 0.05).mean()), reject_1pct=float((rej[:, 1] < 0.01).mean()))])
    out.to_csv(TAB / "pretrend_size.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
