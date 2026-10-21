"""Reviewer check 2: panel-level checks of matching, the price-driven class, the 'other' class, the gate, the
potential-matched floor, windows, projection and the ledger's spells."""
import sys, json
import numpy as np, pandas as pd
RUN = "/mnt/citations/research-lab/runs/energy-nz-intermittent-curtailment-ledger"
sys.path.insert(0, f"{RUN}/code")
import analysis as A
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
raw = pd.read_parquet(f"{RUN}/data/panel.parquet")
print("== (a) rows missing output by POC (dropped silently in prepare):")
m = raw[raw.G.isna()].groupby("poc").agg(n=("P", "size"), first=("date", "min"), last=("date", "max"))
print(m.to_string())
print("rows missing price by POC:", raw[raw.price.isna()].groupby("poc").size().to_dict())
d = A.prepare(raw)
d["fy"] = np.where(d.date.dt.month >= 7, d.date.dt.year + 1, d.date.dt.year)   # FY ending June
print("\n== (b) maxprice (highest offered price with MW>0) by POC, 2025/26: median, share<=0.01, share>1, share>100")
r = A.period(d, *A.RECENT)
mp = r.groupby("poc").maxprice.agg(median="median", le001=lambda v: (v <= 0.01).mean(), gt1=lambda v: (v > 1).mean(),
                                   gt100=lambda v: (v > 100).mean(), n="size").round(3)
print(mp.to_string())
print("\nshare of TPs with offered < P (plant offers less than its potential), 2025/26, by POC:")
print(r.groupby("poc").apply(lambda x: round(float((x.offered < x.P).mean()), 3)).to_string())

cr = A.calibrate(r)
cls = np.where(cr.unconstrained, "unc", np.where(cr.offered < cr.P_hat, "offlim", np.where(cr.price <= cr.maxprice.fillna(0), "price", "other")))
cr["cls"] = cls
cur = cr[cr.curtailed]
print("\n== (c) price-driven class composition, 2025/26 (curtailed energy MWh):")
pc = cur[cur.cls == "price"]
print(" price <= 0.01:", round((pc[pc.price <= 0.01].g.sum() * 0.5)), " price in (0.01, 1]:", round((pc[(pc.price > 0.01) & (pc.price <= 1)].g.sum() * 0.5)),
      " price > 1:", round((pc[pc.price > 1].g.sum() * 0.5)))
print(" price-driven MWh with price > 0.01, by POC and that POC's median maxprice in those TPs:")
t = pc[pc.price > 0.01].groupby("poc").agg(mwh=("g", lambda v: round(v.sum() * 0.5)), med_maxprice=("maxprice", "median"), med_price=("price", "median"), n=("g", "size"))
print(t.sort_values("mwh", ascending=False).head(12).to_string())
print(" curtailed energy at price exactly 0:", round(cur[cur.price <= 0].g.sum() * 0.5), " at 0<price<=0.01:", round(cur[(cur.price > 0) & (cur.price <= 0.01)].g.sum() * 0.5))
oth = cur[cur.cls == "other"]
print("\n 'other' class composition (curtailed MWh): price<1:", round(oth[oth.price < 1].g.sum() * 0.5),
      " maxprice<price<maxprice+1 (price>=1):", round(oth[(oth.price >= 1) & (oth.price < oth.maxprice.fillna(0) + 1)].g.sum() * 0.5),
      " offered<P (price>=maxprice+1):", round(oth[(oth.price >= oth.maxprice.fillna(0) + 1) & (oth.offered < oth.P)].g.sum() * 0.5), " total:", round(oth.g.sum() * 0.5))
print(" 'other' flagged TPs with price<1 by POC:", oth[oth.price < 1].groupby("poc").size().to_dict())

print("\n== (d) heteroscedasticity: mean P_hat (MW) and mean gap on flagged TPs by class, 2025/26")
print(cr.groupby("cls").agg(mean_Phat=("P_hat", "mean"), n=("g", "size")).round(1).to_string())
print(cur.groupby("cls").agg(mean_Phat_flagged=("P_hat", "mean"), mean_gap=("g", "mean"), mean_floor=("f", "mean")).round(1).to_string())
# potential-matched floor: within POC-quarter, deciles of P_hat over all TPs; floor = 95th pct of g on unconstrained TPs in the same decile
def matched_floor(c):
    c = c.copy()
    c["dec"] = c.groupby(["poc", "quarter"]).P_hat.transform(lambda v: pd.qcut(v.rank(method="first"), 10, labels=False) if v.notna().sum() >= 10 else 0)
    gq = c.g.where(c.unconstrained)
    fq = gq.groupby([c.poc, c.quarter, c.dec]).transform(lambda v: np.nanpercentile(v, 95) if v.notna().sum() >= 20 else np.nan)
    c["f_m"] = fq.fillna(c.f)
    c["curt_m"] = c.g > c.f_m
    return c
for lab, per in [("2020", A.BASE), ("2025/26", A.RECENT)]:
    c = matched_floor(A.calibrate(A.period(d, *per)))
    c["cls"] = np.where(c.unconstrained, "unc", np.where(c.offered < c.P_hat, "offlim", np.where(c.price <= c.maxprice.fillna(0), "price", "other")))
    avail = c.P_hat.sum() * 0.5
    a = c[c.curtailed].groupby("cls").g.sum() * 0.5 / avail
    b = c[c.curt_m].groupby("cls").g.sum() * 0.5 / avail
    fr = c.groupby("cls").curt_m.mean()
    print(f" {lab}: share of available by class, study floor vs potential-decile-matched floor; flag rate with matched floor")
    print(pd.concat([a.rename("study"), b.rename("matched"), fr.rename("flag_rate_matched")], axis=1).round(4).to_string())

print("\n== (e) gate: study value and variants")
gate = cr.groupby("poc").apply(lambda x: x.f.median() / x.P_hat.mean() if x.P_hat.mean() > 0 else np.nan)
print(" study:", round(gate.median(), 3), " n POCs:", gate.notna().sum())
kq = cr.groupby("poc").k.median()
print(" POC median k in 2025/26:", kq.round(2).to_dict())
g2 = gate[kq[gate.index] >= 0.5]
print(" excluding POCs with median k<0.5:", round(g2.median(), 3), "n=", len(g2))
g3 = cr.groupby("poc").apply(lambda x: x.f.median() / x.P.mean())
print(" floor over mean raw P (not P_hat):", round(g3.median(), 3))
g4 = cr[cr.fuel == "Wind"].groupby("poc").apply(lambda x: x.f.median() / x.P_hat.mean())
print(" wind only:", round(g4.median(), 3), " solar only:", round(cr[cr.fuel == "Solar"].groupby("poc").apply(lambda x: x.f.median() / x.P_hat.mean()).median(), 3))
# floor relative to potential level, by year, wind plants: 95th pct gap / mean P_hat
print("\n floor/mean P_hat by FY for the main wind plants (is the 2025 intra-period timing visible?):")
yr = {}
for fy in range(2020, 2027):
    cc = A.calibrate(d[(d.fy == fy) & (d.fuel == "Wind")])
    yr[fy] = cc.groupby("poc").apply(lambda x: x.f.median() / x.P_hat.mean() if x.P_hat.mean() > 0 else np.nan).round(2)
print(pd.DataFrame(yr).to_string())

print("\n== (g) windows: 12-month window rows and calendar 2020 price-driven")
for lo, hi in [("2020-01-01", "2020-12-31"), ("2020-07-01", "2021-06-30"), ("2020-01-01", "2021-06-30")]:
    c = A.calibrate(A.period(d, lo, hi)); c["cls"] = np.where(c.unconstrained, "unc", np.where(c.offered < c.P_hat, "offlim", np.where(c.price <= c.maxprice.fillna(0), "price", "other")))
    avail = c.P_hat.sum() * 0.5; cu = c[c.curtailed]
    print(f" {lo}..{hi}: days={c.date.nunique()} primary={cu.g.sum()*0.5/avail:.4f} price-driven={cu[cu.cls=='price'].g.sum()*0.5/avail:.5f}")

print("\n== (i) monthly price-driven curtailment from the ledger: top 10 months and share of 2025/26 price-driven in its top 3 months")
led = pd.read_csv(f"{RUN}/results/tables/ledger_monthly.csv")
mo = led.groupby("month").agg(pd_mwh=("curtailed_price-driven_mwh", "sum"), avail=("available_mwh", "sum"), curt=("curtailed_mwh", "sum"))
mo["pd_share"] = mo.pd_mwh / mo.avail
print(mo.sort_values("pd_mwh", ascending=False).head(10).round(1).to_string())
rec = mo.loc["2025-07":"2026-06"]
print(" 2025/26 price-driven MWh (ledger, whole-panel calibration):", round(rec.pd_mwh.sum()), " top-3 months share:", round(rec.pd_mwh.nlargest(3).sum() / rec.pd_mwh.sum(), 2))
print(" by POC 2025/26 price-driven MWh:", led[(led.month >= "2025-07") & (led.month <= "2026-06")].groupby("poc")["curtailed_price-driven_mwh"].sum().round(0).sort_values(ascending=False).head(8).to_dict())
