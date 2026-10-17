import pandas as pd, numpy as np, json, re
from pathlib import Path
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
c = pd.read_csv(RUN/"data/cohort.csv", parse_dates=["t0","fda_first","ema_first"])
d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t1","t2","t3b","t3h","t3","t3_au","consent_ended","t_app","t_dec","t_tga"])
print("cohort n", len(c), c.t0_source.value_counts().to_dict())
print("linked n", len(d), "excluded_old", d.excluded_old.sum())
print("by t0 year", c.t0.dt.year.value_counts().sort_index().to_dict())
mw = c[c.substance.str.contains(" ")]
print("\nmulti-word substances:", len(mw))
for s, src in zip(mw.substance, mw.t0_source): print("  ", src, "|", s)
print("\nEMA-first substances:", (c.t0_source=="EMA").sum())
for r in c[c.t0_source=="EMA"].itertuples(): print("  ", r.t0.date(), "|", r.substance, "|", r.ema_name, "|", r.atc)
