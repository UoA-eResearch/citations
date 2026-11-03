"""D3 (review finding 6): was each primary-rule emergence already observable at the cutoff in real time?

The isolate table dates isolates by collection year; the metadata also records when each isolate was deposited
(target_creation_date). A pair counts as already observable at the 2022 cutoff if at least one carrier isolate
collected by 2022 had been deposited by the end of 2022.

  hindsight.py -> results/tables/hindsight.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"

dep = []
for f in sorted((D / "raw").glob("*.metadata.tsv")):
    x = pd.read_csv(f, sep="\t", usecols=lambda c: c in ("biosample_acc", "target_creation_date"), dtype=str, low_memory=False)
    dep.append(x)
dep = pd.concat(dep).dropna().drop_duplicates("biosample_acc")
dep["dep_year"] = pd.to_numeric(dep.target_creation_date.str[:4], errors="coerce")
iso = pd.read_parquet(D / "isolates.parquet", columns=["biosample", "year", "species", "genes"]).drop_duplicates("biosample")
iso = iso.merge(dep[["biosample_acc", "dep_year"]], left_on="biosample", right_on="biosample_acc", how="left")
pre = iso[iso.year <= 2022]
te = pd.read_parquet(D / "task_test.parquet", columns=["gene", "species", "y"])
pos = te[te.y == 1][["gene", "species"]].astype(str)
ex = pre.explode("genes").rename(columns={"genes": "gene"})
ex = ex.merge(pos, on=["gene", "species"])
seen_collected = ex.groupby(["gene", "species"]).size()
seen_deposited = ex[ex.dep_year <= 2022].groupby(["gene", "species"]).size()
out = {"isolates_with_deposit_year": int(iso.dep_year.notna().sum()), "isolates": len(iso),
       "collected_by_2022": len(pre), "collected_by_2022_deposited_after_2022": int((pre.dep_year > 2022).sum()),
       "share_deposited_after_2022": round(float((pre.dep_year > 2022).mean()), 4),
       "primary_positives": len(pos), "positives_with_a_carrier_collected_by_2022": int(len(seen_collected)),
       "positives_with_a_carrier_deposited_by_2022": int(len(seen_deposited))}
(T / "hindsight.json").write_text(json.dumps(out, indent=1) + "\n")
print(out)
