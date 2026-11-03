"""G4 (plan section 4; added in D3): first-observation years and BioProjects for 30 random pairs, recomputed from the
raw metadata by code independent of build.py (its own parsing of AMR_genotypes_core, scientific_name and
collection_date), and compared with data/pairs.parquet.

  g4_check.py -> results/tables/g4_check.csv
"""
import re
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
pairs = pd.read_parquet(D / "pairs.parquet")
s = pairs.sample(30, random_state=20261103)
want = set(s.species)
rows = []
for f in sorted((D / "raw").glob("*.metadata.tsv")):
    x = pd.read_csv(f, sep="\t", usecols=["biosample_acc", "scientific_name", "collection_date", "bioproject_acc", "AMR_genotypes_core"], dtype=str, low_memory=False)
    x["sp"] = x.scientific_name.fillna("").str.split().str[:2].str.join(" ")
    rows.append(x[x.sp.isin(want)])
x = pd.concat(rows).drop_duplicates("biosample_acc")
x["yr"] = pd.to_numeric(x.collection_date.fillna("").str.extract(r"((?:19|20)\d\d)")[0], errors="coerce")
x = x[x.yr.between(1990, 2025)]
out = []
for r in s.itertuples():
    sub = x[x.sp == r.species]
    pat = re.compile(r"(?:^|,)" + re.escape(r.gene) + r"(?:=[A-Z]+)?(?:,|$)")
    car = sub[sub.AMR_genotypes_core.fillna("").map(lambda v: bool(pat.search(v)))].sort_values("yr")
    first_any = car.yr.min() if len(car) else None
    first_2bp = None
    for yv in sorted(car.yr.unique()):
        if car[car.yr <= yv].bioproject_acc.nunique() >= 2:
            first_2bp = yv; break
    out.append((r.gene, r.species, r.first_year_any, first_any, r.first_year_2bp, first_2bp))
o = pd.DataFrame(out, columns=["gene", "species", "first_any_table", "first_any_raw", "first_2bp_table", "first_2bp_raw"])
o["any_match"] = o.first_any_table == o.first_any_raw
o["2bp_match"] = (o.first_2bp_table == o.first_2bp_raw) | (o.first_2bp_table.isna() & o.first_2bp_raw.isna())
o.to_csv(T / "g4_check.csv", index=False)
print(o.to_string(index=False)); print("first_any match", int(o.any_match.sum()), "/ 30; first_2bp match", int(o["2bp_match"].sum()), "/ 30")
