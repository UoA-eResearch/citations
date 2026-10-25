"""Edge turnover between snapshots (descriptive; the generating code for the 26-42% figure in deviations.md, added at
the pre-review gate): share of v0.6 species pairs, by class, absent from v0.11. -> results/tables/turnover.json"""
import json
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
a = pd.read_parquet(RUN / "data" / "interim" / "edges_v0.6.parquet", columns=["s", "t", "cls"]).drop_duplicates()
b = pd.read_parquet(RUN / "data" / "interim" / "edges_v0.11.parquet", columns=["s", "t", "cls"]).drop_duplicates()
out = {}
for cls, g in a.groupby("cls"):
    keep = g.merge(b[b.cls == cls], on=["s", "t", "cls"], how="left", indicator=True)
    out[cls] = {"v0.6_pairs": int(len(g)), "absent_from_v0.11": round(float((keep._merge == "left_only").mean()), 4)}
(RUN / "results" / "tables" / "turnover.json").write_text(json.dumps(out, indent=1))
print(out)
