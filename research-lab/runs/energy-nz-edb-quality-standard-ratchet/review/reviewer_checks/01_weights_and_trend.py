"""Reviewer check 1: ICP weight anomalies and their effect on the national index, H1 and H2.

Reads the study's own tables (panel_annual.csv, annual_rules*.csv) and calls the study's h12() with corrected weights.
Writes 01_weights_and_trend.json next to this script. Nothing in the study is modified.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[1]
sys.path.insert(0, str(RUN / "code"))
import analysis as A  # noqa: E402

T = RUN / "results" / "tables"
pd.set_option("display.width", 250)

W = pd.read_csv(T / "panel_annual.csv")[["edb", "disc_yr", "icps"]]
a = pd.read_csv(T / "annual_rules.csv")
af = pd.read_csv(T / "annual_rules_saifi.csv")

# 1. anomalies: ratio of each distributor-year proxy to the distributor's median
W["med"] = W.groupby("edb").icps.transform("median")
W["ratio"] = W.icps / W.med
bad = W[(W.ratio < 0.8) | (W.ratio > 1.25) | W.icps.isna()]
print("ICP proxy anomalies (ratio to distributor median outside [0.8, 1.25] or missing):")
print(bad[["edb", "disc_yr", "icps", "med", "ratio"]].to_string(index=False))

# 2. corrected weights: mask anomalies, interpolate linearly within distributor
Wf = W.copy()
Wf.loc[bad.index, "icps"] = np.nan
Wf["icps"] = Wf.groupby("edb").icps.transform(lambda s: s.interpolate(limit_direction="both"))
Wc = W.copy()
Wc["icps"] = Wc.med  # time-invariant weights as a second sensitivity

# 3. the national index under each weighting
out = {"anomalies": bad[["edb", "disc_yr", "icps", "med", "ratio"]].round(3).to_dict(orient="records")}
nat = {}
for lab, w in (("study", W), ("interpolated", Wf), ("fixed_median", Wc)):
    P = A.pivots(a, w[["edb", "disc_yr", "icps"]])
    nat[lab] = {c: A.national(P, c).round(2).to_dict() for c in ("raw", "excl_rolling", "excl_frozen")}
    # share of the 2017 weight held by Alpine
    wt = P["icps"]
    nat[lab]["alpine_share_2017"] = round(float(wt.loc["Alpine Energy", 2017] / wt[2017].sum()), 4)
print("\nNational raw index by year:")
print(pd.DataFrame({k: v["raw"] for k, v in nat.items()}).T.to_string())
print("Alpine share of 2017 weight:", {k: v["alpine_share_2017"] for k, v in nat.items()})
out["national_raw"] = {k: v["raw"] for k, v in nat.items()}
out["national_excl_rolling"] = {k: v["excl_rolling"] for k, v in nat.items()}

# 4. H1/H2 with the study's own h12 under each weighting
res = {}
for lab, w in (("study", W), ("interpolated", Wf), ("fixed_median", Wc)):
    w = w[["edb", "disc_yr", "icps"]]
    res[lab] = {"primary": A.h12(a, w, "primary"),
                "no_2023": A.h12(a, w, "no 2023", drop_years=(2023,)),
                "no_aurora": A.h12(a, w, "no Aurora", drop_edbs=("Aurora Energy",)),
                "saifi": A.h12(af, w, "SAIFI")}
    for k, r in res[lab].items():
        c = r["cluster"]
        print(f"{lab:13s} {k:9s} raw {r['trend_pct_per_yr']['raw']:+.2f} ({c['raw_ci'][0]:+.2f},{c['raw_ci'][1]:+.2f}) "
              f"excl_roll {r['trend_pct_per_yr']['excl_rolling']:+.2f} ({c['excl_rolling_ci'][0]:+.2f},{c['excl_rolling_ci'][1]:+.2f}) "
              f"excl_frozen {r['trend_pct_per_yr']['excl_frozen']:+.2f} ratio {r['ratio']} diff {r['diff_pp']:+.3f} "
              f"({c['diff_ci'][0]:+.3f},{c['diff_ci'][1]:+.3f}) | {r['H1']} | H2 {r['H2']}")
out["h12"] = res
(HERE / "01_weights_and_trend.json").write_text(json.dumps(out, indent=1, default=float))
print("written", HERE / "01_weights_and_trend.json")
