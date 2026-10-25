"""Share of new releases carrying an agent-signed commit by month, with monorepo packages removed (descriptive; added
at the pre-review gate to qualify the headline 'a third of new releases'). -> results/tables/monthly_no_monorepos.json"""
import json
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT = RUN / "data" / "interim"
P = pd.read_parquet(INT / "packages.parquet")
F = pd.read_parquet(INT / "release_flags.parquet")
Pr = P.dropna(subset=["repo"])
mono = Pr.groupby("repo").name.transform("size") > 1                 # as analyse.py: repos hosting >1 top package
mono_keys = set(zip(Pr[mono].eco, Pr[mono].name))
F["month"] = pd.to_datetime(F.published).dt.strftime("%Y-%m")
out = {}
for eco, g in F.groupby("eco"):
    all_ = g.groupby("month").flagged.mean()
    keep = [(eco, n) not in mono_keys for n in g.name]
    nm = g[keep].groupby("month").flagged.agg(["mean", "size"])
    out[eco] = {m: {"all": round(float(all_[m]), 4), "no_monorepos": round(float(nm.loc[m, "mean"]), 4) if m in nm.index else None,
                    "no_monorepo_releases": int(nm.loc[m, "size"]) if m in nm.index else 0} for m in ("2025-01", "2026-03", "2026-09")}
(RUN / "results" / "tables" / "monthly_no_monorepos.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
