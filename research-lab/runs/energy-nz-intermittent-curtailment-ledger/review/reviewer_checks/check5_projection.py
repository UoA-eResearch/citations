"""Reviewer check 5: the frozen 2026/27 projection: which plants are annualised, from how many months, and what the
rule in plan section 4 implies."""
import sys
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger"
sys.path.insert(0, f"{RUN}/code")
import analysis as A
d = A.prepare(pd.read_parquet(f"{RUN}/data/panel.parquet"))
rec = A.calibrate(A.period(d, *A.RECENT)); a_rec = rec.groupby("poc").P_hat.sum() * 0.5
first = d.groupby("poc").date.min(); last = d.groupby("poc").date.max()
lcal = A.calibrate(d[d.date <= "2026-09-30"]); lcal["month"] = lcal.date.dt.to_period("M")
monthly = lcal.groupby(["poc", "month"]).P_hat.sum() * 0.5
rows = []
for p in first.index:
    if first[p] <= pd.Timestamp(A.RECENT[0]) and p in a_rec:
        rows.append((p, "2025/26 actual", str(first[p].date()), str(last[p].date()), int(rec[rec.poc == p].date.nunique()), round(float(a_rec[p]))))
    elif p in monthly.index.get_level_values(0):
        m = monthly.loc[p]
        rows.append((p, f"annualised from {len(m)} months (mean x 12)", str(first[p].date()), str(last[p].date()), len(m), round(float(m.mean() * 12))))
t = pd.DataFrame(rows, columns=["poc", "basis", "first", "last", "days_or_months", "projected_available_mwh"])
pd.set_option("display.width", 200); print(t.to_string(index=False))
print("sum projected:", round(t.projected_available_mwh.sum()), " 2025/26 available:", round(float(a_rec.sum())))
print("plants in 2025/26 with fewer than 300 days (partial year, not annualised by the code):", t[(t.basis == "2025/26 actual") & (t.days_or_months < 300)].poc.tolist())
print("fraction of the 2025/26 available energy from k<0.5 plant-quarters:", round(float(rec[rec.k < 0.5].P_hat.sum() / rec.P_hat.sum()), 4))
