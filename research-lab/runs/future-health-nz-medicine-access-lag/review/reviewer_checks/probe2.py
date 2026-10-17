import pandas as pd, numpy as np, json, re
from pathlib import Path
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
L = pd.read_csv(RUN/"data/pharmac_listings.csv", usecols=["edition","source","section"], dtype=str)
print("sections by source:"); print(L.groupby(["source","section"]).size())
eds = sorted(L[L.source=="schedule"].edition.unique()); print("\nschedule editions", len(eds), eds[:3], eds[-3:])
allm = pd.period_range("2006-09", "2026-10", freq="M").strftime("%Y-%m-01")
print("missing schedule months:", [m for m in allm if m not in set(eds)])
hed = sorted(L[L.source=="HML"].edition.unique()); print("\nHML editions", len(hed), hed[:3], hed[-3:])
allh = pd.period_range("2013-10", "2026-10", freq="M").strftime("%Y-%m-01")
print("missing HML months:", [m for m in allh if m not in set(hed)])
d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t1","t2","t3b","t3h","t3","t3_au","consent_ended","t_app","t_dec","t_tga"])
d = d[~d.excluded_old]
print("\nt3h == first HML edition (2013-10-01):", (d.t3h=="2013-10-01").sum(), list(d[d.t3h=="2013-10-01"].substance))
print("t3 == 2013-10-01 (and t3b later or absent):", list(d[(d.t3=="2013-10-01")][["substance","t0","t2","t3b","t3h"]].itertuples(index=False)))
print("\nt3b at a post-gap edition (2018-02-01, 2026-01-01):", d[d.t3b.isin(["2018-02-01","2026-01-01"])][["substance","t3b","t3h","t3"]].to_string())
print("\nt3b inside gap windows (from SU):", d[((d.t3b>="2018-01-01")&(d.t3b<"2018-02-01"))|((d.t3b>="2024-06-01")&(d.t3b<"2026-01-01"))][["substance","t0","t2","t3b","t3h","t3"]].to_string())
# funded with t1 < t0
f = d[d.t3.notna()]
print("\nfunded n", len(f), "; t1<t0 among funded:", (f.t1<f.t0).sum(), list(f[f.t1<f.t0][["substance","t0","t1","t2","t3"]].itertuples(index=False)))
print("funded with t1 missing but t2 present:", ((f.t1.isna())&(f.t2.notna())).sum())
print("funded, t2 present, t1 present, t0<=t1<=t2<=t3:", ((f.t2.notna())&(f.t1.notna())&(f.t0<=f.t1)&(f.t1<=f.t2)&(f.t2<=f.t3)).sum())
SU = pd.read_csv(RUN/"data/su_listings.csv", dtype=str)
print("\nSU rows effective >= 2026-10-01:"); print(SU[SU.effective>="2026-10-01"].to_string())
fc = pd.read_csv(RUN/"results/forecast_2026.csv")
print("\nforecast head"); print(fc.head(8).to_string())
