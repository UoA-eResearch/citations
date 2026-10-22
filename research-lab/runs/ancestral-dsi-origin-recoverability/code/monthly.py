"""Monthly counts of country-field classes (care filter applied), for the limb-1 figure. Written after the results."""
import glob
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
parts = []
for f in sorted(glob.glob(str(RUN / "data" / "samples" / "*.parquet"))):
    d = pd.read_parquet(f, columns=["submission_date", "organism", "host", "country_class"])
    d = d[(d.submission_date >= "2019-01-01") & (d.submission_date <= "2026-09-30")]
    d = d[~(d.organism.str.contains("metagenome", case=False, na=False)
            & d.host.str.contains(r"homo sapiens|\bhuman\b", case=False, na=False))]
    parts.append(d.assign(month=d.submission_date.str[:7]).groupby(["month", "country_class"]).size())
m = pd.concat(parts).groupby(level=[0, 1]).sum().unstack(fill_value=0)
m.to_csv(RUN / "results" / "tables" / "monthly_class_counts.csv")
print(m.tail(3))
