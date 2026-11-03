"""D3 (review finding 7): the year each (gene, species) pair reached three isolates, for the preregistered
"at least three" outcome variant. Adds first_year_3 to data/pairs.parquet (other columns unchanged).
"""
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
iso = pd.read_parquet(D / "isolates.parquet", columns=["biosample", "year", "species", "genes"]).drop_duplicates("biosample")
iso = iso.explode("genes").rename(columns={"genes": "element"}).dropna(subset=["element"])
iso = iso.drop_duplicates(["biosample", "element"]).sort_values("year", kind="stable").reset_index(drop=True)
third = iso.groupby(["element", "species"]).year.nth(2)
t3 = iso.loc[third.index].groupby(["element", "species"]).year.first().rename("first_year_3").reset_index().rename(columns={"element": "gene"})
p = pd.read_parquet(D / "pairs.parquet").drop(columns=["first_year_3"], errors="ignore").merge(t3, on=["gene", "species"], how="left")
p.to_parquet(D / "pairs.parquet")
print(len(p), "pairs;", int(p.first_year_3.notna().sum()), "reached three isolates")
