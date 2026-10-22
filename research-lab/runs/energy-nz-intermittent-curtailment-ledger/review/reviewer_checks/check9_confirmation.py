"""Confirmation pass: verify the revised report's lead-time and solar-staleness statements against
sensitivity_post_review.json, and test the report's 'post-period potentials can hide a turn-down' claim: flag rate
among half-hours at or below the plant's own offer, by wind plant, FY2025 vs FY2026, split by whether the plant moved
to post-period submission."""
import sys, json
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger"
sys.path.insert(0, f"{RUN}/code"); import analysis as A
J = json.load(open(f"{RUN}/results/tables/sensitivity_post_review.json"))
wind = ["BPE0331","GOR0331","HRP2201","KIW2201","LTN0331","LTN2201","MPE1101","NMA0331","TWC2201","TWH0331","WDV1101","WIL0331","WVY1101","WWD1102","WWD1103"]
solar = ["ASB0661","DVK0111","EDG0331","ISL0661","KOE1101","KPU0661","MTO0331","TMK0331","WAI0331","WHU1101"]
lm, af = J["lead_minutes_median"], J["share_submitted_after_period_start"]
print("wind plants FY2026: median lead (min), share after start")
for p in wind:
    print(f"  {p}: lead {lm[p].get('2026')}  after {af[p].get('2026')}   (FY2025 lead {lm[p].get('2025')}, after {af[p].get('2025')})")
print("wind FY2021-FY2025 median leads range:", min(v for p in wind for k, v in lm[p].items() if k in ('2021','2022','2023','2024','2025') and v == v), "to", max(v for p in wind for k, v in lm[p].items() if k in ('2021','2022','2023','2024','2025') and v == v))
print("solar median leads (days) by FY:")
for p in solar:
    print(f"  {p}: " + ", ".join(f"FY{k}: {v/1440:.2f}" for k, v in lm[p].items() if v == v))
# hide test
d = A.prepare(pd.read_parquet(f"{RUN}/data/panel.parquet"))
rows = []
for lab, per in [("FY2025", ("2024-07-01", "2025-06-30")), ("FY2026", A.RECENT)]:
    c = A.calibrate(A.period(d, *per)); c = c[c.fuel == "Wind"]
    at = c[~c.unconstrained & (c.offered >= c.P_hat) & (c.price <= c.maxprice.fillna(0))]
    s = at.groupby("poc").agg(n_at_or_below=("g", "size"), flag_rate=("curtailed", "mean"), mean_gap_flagged=("g", lambda v: v[at.loc[v.index, "curtailed"]].mean()))
    s["fy"] = lab; rows.append(s.reset_index())
t = pd.concat(rows).pivot(index="poc", columns="fy")
t["post_period_FY2026"] = [af[p].get("2026", np.nan) for p in t.index]
pd.set_option("display.width", 200)
print(t.round(3).to_string())
