"""Series structure (plan section 1, before any annual maximum): for each fetched gauge, how its records are
sampled, so the completeness rule can be fixed without looking at rainfall extremes. Reads only time stamps,
whether a record is zero, and quality codes.

  structure.py -> results/tables/series_structure.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
S, T = RUN / "data" / "series", RUN / "results" / "tables"


def describe(f):
    z = np.load(f)
    t, v, q = z["t"], z["v"], z["q"]
    server, site = f.stem.split("__", 1)
    if len(t) < 2:
        return {"server": server, "file": f.stem, "records": len(t)}
    dt = np.diff(t)
    vals, cnt = np.unique(dt, return_counts=True)
    top = vals[np.argmax(cnt)]
    codes, cc = np.unique(q, return_counts=True)
    return {"server": server, "file": f.stem, "records": len(t),
            "first": pd.Timestamp(int(t[0]), unit="m"), "last": pd.Timestamp(int(t[-1]), unit="m"),
            "modal_step_min": int(top), "share_modal_step": round(float(cnt.max() / len(dt)), 3),
            "share_zero_records": round(float((v == 0).mean()), 3),
            "gaps_over_1d": int((dt > 1440).sum()), "gaps_over_30d": int((dt > 43200).sum()),
            "quality_codes": ";".join(f"{c}:{n}" for c, n in zip(codes, cc))}


rows = [describe(f) for f in sorted(S.glob("*.npz"))]
d = pd.DataFrame(rows)
d.to_csv(T / "series_structure.csv", index=False)
d["kind"] = np.where(d.share_zero_records > 0.5, "regular with zeros", "event or totals-only")
print(d.groupby(["server", "kind"]).size().unstack(fill_value=0))
print(d.groupby("server")[["modal_step_min", "share_modal_step", "share_zero_records", "gaps_over_1d"]].median())
print("quality codes by server:")
for s, g in d.groupby("server"):
    allc = {}
    for x in g.quality_codes.dropna():
        for kv in x.split(";"):
            k, n = kv.split(":"); allc[k] = allc.get(k, 0) + int(n)
    print(" ", s, dict(sorted(allc.items(), key=lambda kv: -kv[1])[:8]))
