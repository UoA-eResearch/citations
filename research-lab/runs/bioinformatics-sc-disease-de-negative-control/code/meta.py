"""Feasibility metadata (no expression values read): stream the Census LTS human obs table and aggregate cell counts
by dataset x donor x disease x tissue x cell type x assay x suspension x sex x stage x primary flag.
  meta.py -> data/meta/obs_counts.parquet, data/meta/datasets.parquet
"""
import time
from pathlib import Path

import cellxgene_census as cc
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "meta"
VERSION = "2025-11-08"   # Census LTS
COLS = ["dataset_id", "donor_id", "disease", "disease_ontology_term_id", "tissue_general", "cell_type",
        "cell_type_ontology_term_id", "assay", "suspension_type", "sex", "development_stage", "is_primary_data"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0, parts, n = time.time(), [], 0
    with cc.open_soma(census_version=VERSION) as census:
        census["census_info"]["datasets"].read().concat().to_pandas().to_parquet(OUT / "datasets.parquet")
        for tbl in census["census_data"]["homo_sapiens"].obs.read(column_names=COLS):
            df = tbl.to_pandas()
            n += len(df)
            parts.append(df.groupby(COLS, observed=True, dropna=False).size().rename("cells").reset_index())
            if len(parts) % 20 == 0:
                print(f"{time.time() - t0:.0f}s {n:,} cells", flush=True)
    agg = pd.concat(parts, ignore_index=True)
    for c in COLS:
        if agg[c].dtype == object or str(agg[c].dtype) == "category":
            agg[c] = agg[c].astype(str)
    agg = agg.groupby(COLS, dropna=False).cells.sum().reset_index()
    agg.to_parquet(OUT / "obs_counts.parquet")
    print(f"== done {n:,} cells, {len(agg):,} rows, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
