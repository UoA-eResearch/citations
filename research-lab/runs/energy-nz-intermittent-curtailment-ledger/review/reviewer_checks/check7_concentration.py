"""Reviewer check 7: how concentrated the post hoc 'price-driven' series is (by plant), how it depends on the
definition of 'price-driven', and the plants' offer prices by financial year."""
import sys
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger"
sys.path.insert(0, f"{RUN}/code")
import analysis as A
pd.set_option("display.width", 220)
d = A.prepare(pd.read_parquet(f"{RUN}/data/panel.parquet"))
d["fy"] = np.where(d.date.dt.month >= 7, d.date.dt.year + 1, d.date.dt.year)
def cls(c):
    return np.where(c.unconstrained, "unc", np.where(c.offered < c.P_hat, "offlim", np.where(c.price <= c.maxprice.fillna(0), "price", "other")))
cr = A.calibrate(A.period(d, *A.RECENT)); cr["cls"] = cls(cr)
avail = cr.P_hat.sum() * 0.5; cur = cr[cr.curtailed]; nn = cur[cur.cls != "unc"]
print("2025/26 non-noise curtailed MWh:", round(nn.g.sum() * 0.5))
for lab, m in [("price <= 0.01 (plan's H2 line)", nn.price <= 0.01), ("price <= own offer (report's post hoc)", nn.cls == "price"),
               ("price < 1 $/MWh", nn.price < 1), ("price < 5 $/MWh", nn.price < 5)]:
    print(f"  share of non-noise curtailed energy with {lab}: {nn[m].g.sum() / nn.g.sum():.2f}")
print("\nprice-driven (post hoc) share of fleet available energy, 2025/26, leaving plants out:")
pdm = cur[cur.cls == "price"].groupby("poc").g.sum() * 0.5
ap = cr.groupby("poc").P_hat.sum() * 0.5
print(f"  all plants: {pdm.sum() / avail:.4f}")
for drop in [["LTN2201"], ["GOR0331"], ["LTN2201", "GOR0331"]]:
    print(f"  without {drop}: {(pdm.drop(drop, errors='ignore').sum()) / (avail - ap[drop].sum()):.4f}")
print("  plant's own price-driven share of its own available energy (top 6):")
print((pdm / ap).dropna().sort_values(ascending=False).head(6).round(4).to_string())
print("  share of TPs at or below own offer, by plant (top 6):", (cr.cls == "price").groupby(cr.poc).mean().sort_values(ascending=False).head(6).round(3).to_dict())
print("\nmedian highest offered price ($/MWh) by plant and FY (ending June):")
t = d.groupby(["poc", "fy"]).maxprice.median().unstack().round(2)
print(t.loc[["LTN2201", "GOR0331", "WVY1101", "HRP2201", "WWD1102", "TWH0331", "BPE0331"]].to_string())
print("\nTuritea share of TPs with maxprice > 0.01 by FY:", d[d.poc == "LTN2201"].groupby("fy").maxprice.apply(lambda v: round((v > 0.01).mean(), 2)).to_dict())
print("price-driven (post hoc) curtailed MWh by plant and FY window (window calibration):")
rows = {}
for y in range(2020, 2026):
    lo, hi = (f"{y}-07-01" if y > 2020 else "2020-01-01"), f"{y + 1}-06-30"
    c = A.calibrate(A.period(d, lo, hi)); c["cls"] = cls(c); cu = c[c.curtailed & (c.cls == "price")]
    rows[f"FY{y + 1}"] = (cu.groupby("poc").g.sum() * 0.5).round(0)
print(pd.DataFrame(rows).fillna(0).astype(int).sort_values("FY2026", ascending=False).head(8).to_string())
