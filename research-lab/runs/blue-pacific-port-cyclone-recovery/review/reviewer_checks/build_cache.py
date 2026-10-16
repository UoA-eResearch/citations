"""Reviewer: cache the PortWatch daily-calls pivot (date x portid) so later checks do not re-read 649 MB."""
import sys, pickle
from pathlib import Path
import pandas as pd
RUN = Path(__file__).resolve().parents[2]
d = pd.read_csv(RUN / "data/raw/portwatch/daily.csv", usecols=["date", "portid", "portcalls"])
d["date"] = pd.to_datetime(d.date.str[:10])
calls = d.pivot_table(index="date", columns="portid", values="portcalls", aggfunc="sum").sort_index()
print(calls.shape, calls.index.min(), calls.index.max())
print("rows per port-day complete?", d.groupby("portid").size().describe().to_dict())
with open(Path(__file__).parent / "cache/calls.pkl", "wb") as f:
    pickle.dump(calls, f)
print("cached")
