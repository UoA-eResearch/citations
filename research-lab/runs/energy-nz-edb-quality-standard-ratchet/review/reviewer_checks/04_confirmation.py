"""Confirmation pass (D3): checks on what including 2025 introduced.

1. Timestamp basis of the 2025 disclosure (UTC-labelled) against the model files (naive NZ local).
2. Composition effect of Top Energy's missing 2025 on the national index and the raw trend (impute its disclosed
   Class C 2025 total, re-run the study's h12()).
3. The preregistered sensitivity "trend windows ending in 2024" (plan section 4), absent from primary.json.
4. Per-distributor detail of the 2024-vs-2025 recording-basis check.
5. validation.json: the Stata comparison.
Writes 04_confirmation.json next to this script. Read-only on the study.
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
import rules as R  # noqa: E402

T = RUN / "results" / "tables"
pd.set_option("display.width", 250)
out = {}

# ---- 1. timestamp basis --------------------------------------------------------------------------------------------
U = pd.read_parquet(R.INT / "unplanned.parquet")
print("unplanned.parquet start dtype:", U.start.dtype, "| src counts:", U.src.value_counts().to_dict())
raw5 = pd.read_parquet(R.INT / "id2025_raw.parquet")
r5 = raw5[raw5.planned_or_unplanned.astype(str).str.lower().str.startswith("unplanned")]
u25 = U[U.src == "id2025"]
print("2025 rows in panel:", len(u25), "| first/last start:", u25.start.min(), u25.start.max())
print("raw 10a(i) unplanned first/last start_datetime:", r5.start_datetime.min(), r5.start_datetime.max())
# are the stored 2025 starts the UTC clock values (tz dropped) or converted to NZ local?
sample = r5.sort_values("start_datetime").head(3)[["edb", "start_datetime", "saidi_value"]]
print(sample.to_string(index=False))
panel_same = u25.merge(sample.rename(columns={"saidi_value": "saidi"}), on=["edb", "saidi"], how="inner")[["edb", "start", "start_datetime"]]
print(panel_same.head(3).to_string(index=False))
# rows of the 2025 file that the code's disc_year puts in 2024 (i.e. before 2024-04-01 on the stored clock)
n_before = int((u25.start < "2024-04-01").sum())
dy25 = R.disc_year(u25.start)
print("2025-file rows with stored start before 2024-04-01:", n_before, "| disc_year != 2025:", int((dy25 != 2025).sum()), "of", len(u25))
# hour-of-day profile, unplanned interruptions, SAIDI-weighted: model file 2024 vs 2025 file
def hour_profile(df):
    h = df.start.dt.hour
    return df.groupby(h).saidi.sum().reindex(range(24), fill_value=0.0) / df.saidi.sum()
p24 = hour_profile(U[(U.src == "dpp4") & (U.disc_yr == 2024)])
p23 = hour_profile(U[(U.src == "dpp4") & (U.disc_yr == 2023)])
p25 = hour_profile(u25)
prof = pd.DataFrame({"2023_model": p23, "2024_model": p24, "2025_file": p25}).round(3)
print("SAIDI-weighted hour-of-day share of unplanned interruptions (stored clock):")
print(prof.T.to_string())
# best circular lag of the 2025 profile against 2024
lags = {k: float(np.corrcoef(np.roll(p25.to_numpy(), -k), p24.to_numpy())[0, 1]) for k in range(24)}
best = max(lags, key=lags.get)
print("correlation of 2025 profile with 2024 by shift (hours):", {k: round(v, 2) for k, v in lags.items()})
print("best shift:", best, "h (0 = same clock basis; ~12-13 = 2025 stored in UTC)")
out["timestamps"] = {"panel_start_dtype": str(U.start.dtype), "rows_2025_file_before_2024_04_01": n_before,
                     "rows_2025_file_disc_year_ne_2025": int((dy25 != 2025).sum()), "n_2025_rows": int(len(u25)),
                     "hour_profile": prof.to_dict(), "best_shift_hours": best, "corr_by_shift": lags,
                     "corr_2023_vs_2024_model_shift0": float(np.corrcoef(p23, p24)[0, 1])}

# ---- 2. composition: Top Energy missing in 2025 -----------------------------------------------------------------------
a = pd.read_csv(T / "annual_rules.csv")
W = pd.read_csv(T / "panel_annual.csv")[["edb", "disc_yr", "icps"]]
p = json.loads((T / "primary.json").read_text())
P = A.pivots(a, W)
wt = P["icps"]
print("\nTop Energy 2025 in annual_rules:", int(((a.edb == "Top Energy") & (a.disc_yr == 2025)).sum()))
top_cc_2025 = 258.06   # disclosed Class C unplanned SAIDI 2025, "All" row (review check 3)
a_imp = pd.concat([a, pd.DataFrame([{"edb": "Top Energy", "disc_yr": 2025, "raw": top_cc_2025, "excl_rolling": np.nan,
                                     "excl_frozen": np.nan, "med_rolling": np.nan, "med_frozen": np.nan,
                                     "thr_rolling": np.nan, "thr_frozen": np.nan}])], ignore_index=True)
nat_study = A.national(P, "raw")
nat_imp = A.national(A.pivots(a_imp, W), "raw")
print("national raw 2025: study (Top missing)", round(float(nat_study[2025]), 2), "| Top imputed at Class C 258.06:", round(float(nat_imp[2025]), 2))
res_imp = A.h12(a_imp, W, "Top 2025 imputed")
res_study = p["H1_H2"]
print("raw trend: study", res_study["trend_pct_per_yr"]["raw"], res_study["cluster"]["raw_ci"],
      "| Top imputed", res_imp["trend_pct_per_yr"]["raw"], res_imp["cluster"]["raw_ci"], "years", res_imp["years_bootstrap"]["raw_ci"], "| H1", res_imp["H1"])
out["top_2025_composition"] = {"national_raw_2025_study": float(nat_study[2025]), "national_raw_2025_top_imputed": float(nat_imp[2025]),
                               "top_weight_share_2024": float(wt.loc["Top Energy", 2024] / wt[2024].sum()),
                               "h12_top_imputed": res_imp}

# ---- 3. preregistered sensitivity: window ending 2024 ------------------------------------------------------------
af = pd.read_csv(T / "annual_rules_saifi.csv")
r24 = A.h12(a[a.disc_yr <= 2024], W, "2014-2024")
r24f = A.h12(af[af.disc_yr <= 2024], W, "2014-2024 SAIFI")
for lab, r in (("SAIDI 2014-2024", r24), ("SAIFI 2014-2024", r24f)):
    c = r["cluster"]
    print(f"{lab}: raw {r['trend_pct_per_yr']['raw']:+.2f} ({c['raw_ci'][0]:+.2f},{c['raw_ci'][1]:+.2f}) excl_roll {r['trend_pct_per_yr']['excl_rolling']:+.2f} "
          f"({c['excl_rolling_ci'][0]:+.2f},{c['excl_rolling_ci'][1]:+.2f}) ratio {r['ratio']} ({c['ratio_ci'][0]:+.2f},{c['ratio_ci'][1]:+.2f}) "
          f"diff {r['diff_pp']:+.3f} ({c['diff_ci'][0]:+.3f},{c['diff_ci'][1]:+.3f}) | {r['H1']} | H2 {r['H2']}")
out["window_ending_2024"] = {"saidi": r24, "saifi": r24f}
# leverage of 2025: trend on 2014-2025 with 2025 dropped vs with 2025 present (point estimates)
yrs_all = sorted(a.disc_yr.unique())
print("national raw by year:", {int(y): round(float(v), 1) for y, v in nat_study.items()})

# ---- 4. recording-basis detail ----------------------------------------------------------------------------------------
chk = json.loads((T / "panel_checks.json").read_text())
b = pd.DataFrame(chk["id2025"]["basis_2024_vs_2025"]["by_edb"]).T
b["count_ratio"] = (b.n2025 / b.n2024).round(2)
b["saidi_per_int_ratio"] = (b.saidi_per_int_2025 / b.saidi_per_int_2024).round(2)
print("\nrecording-basis check by distributor:")
print(b[["n2024", "n2025", "count_ratio", "saidi_per_int_ratio"]].to_string())
flag = b[(b.count_ratio < 0.67) | (b.count_ratio > 1.5) | (b.saidi_per_int_ratio < 0.67) | (b.saidi_per_int_ratio > 1.5)]
print("distributors with a 2024->2025 change beyond 1.5x in count or SAIDI per row:", flag.index.tolist())
print("10a(i) 2025 rows per interruption_identifier (study distributors):",
      round(float(r5.groupby(["edb", "interruption_identifier"]).size().mean()), 2))
out["basis_detail"] = {"flagged": flag.index.tolist(), "rows_per_identifier_2025": float(r5.groupby(["edb", "interruption_identifier"]).size().mean())}

# ---- 5. validation.json Stata comparison -------------------------------------------------------------------------------
v = json.loads((T / "validation.json").read_text())
print("\nvalidation dpp3_vs_stata:", v["dpp3_vs_stata"])
out["validation_dpp3_vs_stata"] = v["dpp3_vs_stata"]
(HERE / "04_confirmation.json").write_text(json.dumps(out, indent=1, default=float))
print("written", HERE / "04_confirmation.json")
