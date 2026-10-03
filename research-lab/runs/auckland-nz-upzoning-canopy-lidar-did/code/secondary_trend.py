"""Secondary estimates (plan.md section 5) plus one post hoc long difference.
Trend-adjusted beta (preregistered secondary): beta_post - beta_pre x (post gap / pre gap), using tile capture years
(E0 2013.5; E1 north 2017.5, south 2016.75; E2 2024.6). Annualised rates (preregistered). Long difference E0 -> E2
(post hoc, D2). Output: results/tables/secondary_trend.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402


def main():
    m = pd.read_parquet(A.RUN / "data" / "units_2024_noov.parquet")  # primary data version (D4)
    m["d_post_c3"], m["d_pre_c3"], m["d_long_c3"] = m.c3_e2 - m.c3_e1, m.c3_e1 - m.c3_e0, m.c3_e2 - m.c3_e0
    post, pre = A.fit(m, "d_post_c3", "post")[0], A.fit(m, "d_pre_c3", "pre")[0]
    e1 = np.where(m.coll == "N", 2017.5, 2016.75)
    gp, gq = float(np.mean(e1 - 2013.5)), float(np.mean(2024.6 - e1))
    rows = [dict(analysis="trend-adjusted: beta_post - beta_pre x (post gap / pre gap)", est=post["est"] - pre["est"] * gq / gp,
                 note=f"pre gap {gp:.2f} y, post gap {gq:.2f} y"),
            dict(analysis="annualised post (pp per year)", est=post["est"] / gq),
            dict(analysis="annualised pre (pp per year)", est=pre["est"] / gp)]
    rows += A.fit(m, "d_long_c3", "long difference E0->E2 (post hoc)")
    pd.DataFrame(rows).to_csv(A.TAB / "secondary_trend.csv", index=False)
    print(pd.DataFrame(rows)[["analysis", "term", "est", "lo", "hi"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
