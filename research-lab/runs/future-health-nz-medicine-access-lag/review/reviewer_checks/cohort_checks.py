import pandas as pd, numpy as np, re, sys
from pathlib import Path
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 45); pd.set_option("display.max_rows", 200)
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
c = pd.read_csv(RUN/"data/cohort.csv", parse_dates=["t0","fda_first","ema_first"])
d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t1","t2","t3"]); d = d[~d.excluded_old]
D = lambda a, b: (b - a).dt.days
# Medsafe-only share (T1->T2) among H1 substances with T1, bootstrap CI
pre = d[d.t0.dt.year <= 2023]; f = pre[pre.t3.notna()]; cl = f[f.t2.notna() & (f.t0 <= f.t2) & (f.t2 <= f.t3)]; g = cl[cl.t1.notna()].copy()
ms = lambda x: float(D(x.t1.clip(lower=x.t0), x.t2).sum() / D(x.t0, x.t3).sum())
rng = np.random.default_rng(20261020); v = [ms(g.iloc[rng.integers(0, len(g), len(g))]) for _ in range(2000)]
print(f"Medsafe-only share (T1->T2 / T0->T3, T1 clipped at T0) n={len(g)}: {ms(g):.3f} CI [{np.percentile(v,2.5):.3f}, {np.percentile(v,97.5):.3f}]")
sp = lambda x: float(D(x.t0, x.t1).clip(lower=0).sum() / D(x.t0, x.t3).sum()); v = [sp(g.iloc[rng.integers(0, len(g), len(g))]) for _ in range(2000)]
print(f"Sponsor share (clipped) n={len(g)}: {sp(g):.3f} CI [{np.percentile(v,2.5):.3f}, {np.percentile(v,97.5):.3f}]")
# random 30 cohort substances (seed 20261030) for the T0 spot check
s = c.sample(30, random_state=20261030)[["substance","t0","t0_source","fda_first","fda_name","ema_first","ema_name","fda_nme"]]
for col in ["t0","fda_first","ema_first"]: s[col] = s[col].dt.strftime("%Y-%m-%d")
print("\nrandom 30 for T0 check:"); print(s.to_string(index=False))
# Erwinaze / Xenoview / Filsuvez checks
P = pd.read_csv(RUN/"data/raw/fda/Products.txt", sep="\t", dtype=str, encoding="latin-1")
for k in ["ERWINAZE", "RYLAZE", "XENOVIEW", "FILSUVEZ", "PEPAXTO", "AMPYRA", "POTIGA", "ANDEXXA", "SEVENFACT", "VONVENDI", "COAGADEX", "OBIZUR", "RIXUBIS", "ALPROLIX", "CINRYZE", "BERINERT", "HAEGARDA", "ZALTRAP", "ELELYSO", "TECFIDERA", "BREYANZI", "ABECMA", "CARVYKTI", "HEMGENIX", "CASGEVY", "ROCTAVIAN", "ADZYNMA", "ALTUVIIIO", "LANTIDRA", "OMISIRGE"]:
    h = P[P.DrugName.str.upper().str.contains(k, na=False)]
    print(f"  Drugs@FDA {k:10s} rows={len(h):2d} {list(h.ActiveIngredient.unique())[:2]}")
# duplicates: cohort entries sharing a brand name (ema_name) -> components of one product counted several times
e = c[c.t0_source == "EMA"].groupby("ema_name").substance.apply(list); e = e[e.map(len) > 1]
print("\nEMA-first products contributing >1 cohort substance:"); print(e.to_string())
# EMA-first with ATC V10 (radiopharm) or V03/V04 not excluded
print("\nEMA ATC starting V (not J07/V01/V04/V08/V09) in cohort:", c[c.atc.fillna("").str.match(r"^V") & ~c.atc.fillna("").str.match(r"^(V01|V04|V08|V09)")][["substance","atc","ema_name"]].to_string(index=False))
# how many cohort substances have T1 < T0 overall (sponsor filed in NZ before first FDA/EMA approval)
print("\ncohort (680) with T1 < T0:", int((d.t1 < d.t0).sum()), "of", int(d.t1.notna().sum()), "with T1; with T2 < T0:", int((d.t2 < d.t0).sum()), "of", int(d.t2.notna().sum()))
