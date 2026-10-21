"""Reviewer check 8: is the solar plants' high floor explained by nights? Floor over mean potential on daytime TPs
(P_hat > 0) only, 2025/26; and the ledger's class columns sum to curtailed_mwh. (Run inline during the review; saved
here for reproducibility. Output: check8_solar_gate.out.)"""
import sys
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger"
sys.path.insert(0, f"{RUN}/code")
import analysis as A
d = A.prepare(pd.read_parquet(f"{RUN}/data/panel.parquet"))
cr = A.calibrate(A.period(d, *A.RECENT)); s = cr[cr.fuel == "Solar"]
g_all = s.groupby("poc").apply(lambda x: x.f.median() / x.P_hat.mean() if x.P_hat.mean() > 0 else np.nan)
g_day = s[s.P_hat > 0].groupby("poc").apply(lambda x: x.f.median() / x.P_hat.mean() if x.P_hat.mean() > 0 else np.nan)
print(pd.concat([g_all.rename("floor/mean P_hat, all TPs"), g_day.rename("daytime TPs only (P_hat>0)")], axis=1).round(2).to_string())
led = pd.read_csv(f"{RUN}/results/tables/ledger_monthly.csv")
print("ledger: max |classes - curtailed| MWh:", round(float((led[["curtailed_offer-limited_mwh", "curtailed_price-driven_mwh", "curtailed_other_mwh"]].sum(axis=1) - led.curtailed_mwh).abs().max()), 2))
