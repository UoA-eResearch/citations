#!/usr/bin/env python
"""Validation of analysis.att_es on synthetic data (report sec 3): 32 wikis in four staggered waves, wiki and month
effects, noise, and a known +2-point effect after the switch. Output: results/tables/estimator_validation.csv"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402


def main():
    rng = np.random.default_rng(1)
    months = pd.period_range("2024-01", "2026-06", freq="M")
    cohorts = [pd.Period(x, "M") for x in ("2024-11", "2025-03", "2025-06", "2025-11")]
    rows = []
    for i in range(32):
        g, a = cohorts[i % 4], rng.normal(0, 0.02)
        for k, m in enumerate(months):
            if m != g:
                rows.append(dict(wiki=f"w{i}", month=m, g=g, Y_LO=0.10 + a + 0.001 * k + rng.normal(0, 0.003) + (0.02 if m > g else 0)))
    Y, gidx, ms = A.matrices(pd.DataFrame(rows), "Y_LO")
    es, ov, pm = A.att_es(Y, gidx, ms)
    b, _, _ = A.bootstrap(Y, gidx, ms, 200)
    out = pd.DataFrame([dict(true_effect=0.02, estimate=ov, lo=np.percentile(b, 2.5), hi=np.percentile(b, 97.5),
                             mean_lead=float(es[es.index < 0].mean()))])
    out.to_csv(Path(__file__).resolve().parents[1] / "results" / "tables" / "estimator_validation.csv", index=False)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
