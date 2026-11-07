"""Post hoc (D3): where the effort surface sits in each period. Thinned species x 5-arcmin-cell units per period,
as velocity.load builds them; effort-weighted mean |latitude| and band shares. -> results/tables/effort_surface.json"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RUN = Path(__file__).resolve().parents[1]
t = pq.read_table(RUN / "data" / "clean.parquet", columns=["specieskey", "lat", "lon", "period"]).to_pandas()
f = 12
t["cy"], t["cx"] = np.floor(t.lat * f).astype(np.int64), np.floor(t.lon * f).astype(np.int64)
u = t[["specieskey", "cy", "cx", "period"]].drop_duplicates()
u["alat"] = ((u.cy + 0.5) / f).abs()
out = {}
for p, g in u.groupby("period"):
    out[f"P{p}"] = {"units": int(len(g)), "mean_abs_lat": round(float(g.alat.mean()), 2),
                    "tropical_share": round(float((g.alat < 23.5).mean()), 3), "temperate_share": round(float(((g.alat >= 23.5) & (g.alat < 50)).mean()), 3),
                    "boreal_share": round(float((g.alat >= 50).mean()), 3)}
(RUN / "results" / "tables" / "effort_surface.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out))
