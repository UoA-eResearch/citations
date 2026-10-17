import pandas as pd, numpy as np
from pathlib import Path
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 40); pd.set_option("display.max_rows", 200)
RUN = Path("/mnt/citations/research-lab/runs/future-health-nz-medicine-access-lag")
d = pd.read_csv(RUN/"data/linked.csv", parse_dates=["t0","t1","t2","t3b","t3h","t3","t3_au","consent_ended","t_app","t_dec","t_tga"])
c = pd.read_csv(RUN/"data/cohort.csv")
d = d.merge(c[["substance","fda_name","ema_name","fda_first","ema_first"]], on="substance")
d = d[~d.excluded_old]
f = d[d.t3.notna()].sort_values("t0")
for col in ["t0","t1","t2","t3b","t3h","t3","t_app","t_dec","t_tga"]:
    f[col] = f[col].dt.strftime("%Y-%m-%d")
print("FUNDED (not excluded_old):", len(f))
print(f[["substance","t0_source","t0","fda_first","ema_first","t1","t2","t3b","t3h","t3","t_app","fda_name","ema_name"]].to_string())
