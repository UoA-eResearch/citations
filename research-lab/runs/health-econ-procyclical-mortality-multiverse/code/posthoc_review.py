"""POST HOC (after independent review): summaries of the existing specification tables that the review's findings
rest on. No re-estimation.
  1. long windows (1976-2017/2019/2023) vs sub-periods: share negative and WCR-significant;
  2. long windows, by measure x controls x outcome (the employment-to-population ageing confound);
  3. canonical-type H2 and pre-2011 drug specifications (log drug rate, unemployment, population weights, no trend,
     contemporaneous, TWFE, demographic controls) with CR1 95% intervals;
  4. FD specifications with the cumulative lag in windows starting 1976 (1977 dropped: LAUS starts in 1976);
  5. 2006-2017 shares by trend option.
-> results/tables/posthoc_review.json
"""
import json
from pathlib import Path

import pandas as pd
from scipy.stats import t as tdist

T = Path(__file__).resolve().parents[1] / "results" / "tables"
h1 = pd.read_csv(T / "specs_h1.csv")
h2 = pd.read_csv(T / "specs_h2.csv")
pre = pd.read_csv(T / "specs_drug_pre2011.csv")
ns = lambda d: round(float(((d.beta < 0) & (d.p_wcr < 0.05)).mean()), 4)
LONG = ["1976-2017", "1976-2019", "1976-2023"]
lg, sub = h1[h1.window.isin(LONG)], h1[~h1.window.isin(LONG)]
out = {"long_windows": {"specs": int(len(lg)), "share_neg_sig": ns(lg)}, "sub_periods": {"specs": int(len(sub)), "share_neg_sig": ns(sub)}}
out["long_by_measure_controls_outcome"] = {f"{m}|{c}": {o: ns(g[g.outcome == o]) for o in sorted(g.outcome.unique())}
                                           for (m, c), g in lg.groupby(["treat", "controls"])}
crit = tdist.ppf(0.975, 50)
def canon(d):
    q = d[(d.outcome == "log_drug") & (d.treat == "ur") & (d.weight == "pop") & (d.trend == "none") & (d.lag == "contemp") &
          (d.estimator == "twfe") & (d.controls == "demog")]
    return {r.window: {"beta_pct_per_point": round(100 * r.beta, 2), "ci95": [round(100 * (r.beta - crit * r.se), 2), round(100 * (r.beta + crit * r.se), 2)],
                       "p_wcr": round(r.p_wcr, 4)} for r in q.itertuples()}
out["h2_canonical"] = canon(h2)
out["pre2011_canonical"] = canon(pre)
ld = h2[h2.outcome == "log_drug"]
out["h2_log_drug_median_ci_halfwidth_pct"] = round(float(100 * crit * ld.se.median()), 2)
negsig = h2[(h2.beta < 0) & (h2.p_wcr < 0.05)]
out["h2_negative_significant"] = {"specs": int(len(negsig)), "unweighted": int((negsig.weight == "none").sum()),
                                  "crude_level": int((negsig.outcome == "drug").sum()), "epop": int((negsig.treat == "epop_neg").sum())}
fd = h1[h1.window.str.startswith("1976") & (h1.estimator == "fd") & (h1.lag == "cumulative")]
ref = h1[h1.window.str.startswith("1976") & (h1.estimator == "fd") & (h1.lag == "contemp")]
out["fd_cumulative_1976_windows"] = {"specs": int(len(fd)), "n_by_window": fd.groupby("window").n.first().to_dict(),
                                     "n_contemp_by_window": ref.groupby("window").n.first().to_dict()}
w = h1[h1.window == "2006-2017"]
out["window_2006_2017_by_trend"] = {k: ns(g) for k, g in w.groupby("trend")}
out["specs_k_over_n_gt_0_3"] = int((h1.k / h1.n > 0.3).sum())
(T / "posthoc_review.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
