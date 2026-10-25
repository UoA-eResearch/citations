"""Snapshot records -> SAGE species x 1 km cell support (plan sections 1 and 3).

  cells.py records   per snapshot file: SAGE's basisOfRecord and coordinate-uncertainty filters, species assignment
                     (GBIF species key from species_keys.csv, else exact species name), EPSG:6933 1 km cell
                     (floor(x/1000), floor(y/1000), as SAGE's geo_utils), provenance tier from provenance_flags.csv
                     -> data/work/rec/<part>.parquet; core records also keep coordinates and date -> data/work/core/
  cells.py support   species x cell counts by tier and the cell's majority country -> data/work/support.parquet
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RUN = Path(__file__).resolve().parents[1]
S3, W = RUN / "data" / "gbif_s3", RUN / "data" / "work"
(W / "rec").mkdir(parents=True, exist_ok=True)
(W / "core").mkdir(parents=True, exist_ok=True)
BOR = {"HUMAN_OBSERVATION", "OBSERVATION", "PRESERVED_SPECIMEN"}


def _maps():
    sk = pd.read_csv(RUN / "data" / "registry" / "species_keys.csv")
    by_key = {str(int(k)): int(i) for k, i in zip(sk.specieskey, sk["index"]) if pd.notna(k)}
    by_name = dict(zip(sk.name, sk["index"]))
    fl = pd.read_csv(RUN / "results" / "tables" / "provenance_flags.csv")
    tier = {k: (1 if f == "core" else 2) for k, f in zip(fl.datasetKey, fl.flag)}
    return by_key, by_name, tier


def one(path):
    out = W / "rec" / path.name
    if out.exists():
        return 0
    from pyproj import Transformer
    by_key, by_name, tier = _maps()
    t = pq.read_table(path).to_pandas()
    t = t[t.basisofrecord.isin(BOR) & (t.coordinateuncertaintyinmeters.isna() | (t.coordinateuncertaintyinmeters <= 1000))]
    sp = t.specieskey.map(by_key)
    sp = sp.fillna(t.species.map(by_name))
    t = t[sp.notna()].assign(sp=sp[sp.notna()].astype(np.int16))
    tr = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    x, y = tr.transform(t.decimallongitude.to_numpy(float), t.decimallatitude.to_numpy(float))
    ok = np.isfinite(x) & np.isfinite(y)
    t = t[ok]
    t["gx"] = np.floor_divide(x[ok], 1000).astype(np.int32)
    t["gy"] = np.floor_divide(y[ok], 1000).astype(np.int32)
    t["tier"] = t.datasetkey.map(tier).fillna(0).astype(np.int8)
    rec = t[["sp", "gx", "gy", "tier", "countrycode"]]
    pq.write_table(pa.Table.from_pandas(rec, preserve_index=False), out, compression="zstd")
    core = t[t.tier == 1][["sp", "gx", "gy", "datasetkey", "decimallatitude", "decimallongitude", "year", "month", "day"]]
    if len(core):
        pq.write_table(pa.Table.from_pandas(core, preserve_index=False), W / "core" / path.name, compression="zstd")
    return len(rec)


def records():
    files = sorted(S3.glob("*.parquet"))
    n = 0
    with ProcessPoolExecutor(20) as ex:
        for k, m in enumerate(ex.map(one, files, chunksize=8), 1):
            n += m
            if k % 500 == 0:
                print(k, "of", len(files), "records", n, flush=True)
    print("== records done", n)


def support():
    import duckdb
    con = duckdb.connect()
    con.execute("SET threads TO 24; SET memory_limit = '48GB'")
    rec = str(W / "rec" / "*.parquet")
    con.execute(f"""
        COPY (
          SELECT sp, gx, gy,
                 count(*) FILTER (WHERE tier = 1) AS n_core,
                 count(*) FILTER (WHERE tier = 2) AS n_broad,
                 count(*) FILTER (WHERE tier = 0) AS n_other
          FROM read_parquet('{rec}') GROUP BY sp, gx, gy
        ) TO '{W / "support.parquet"}' (FORMAT parquet, COMPRESSION zstd)""")
    con.execute(f"""
        COPY (
          SELECT gx, gy, arg_max(countrycode, n) AS country FROM (
            SELECT gx, gy, countrycode, count(*) AS n FROM read_parquet('{rec}') GROUP BY gx, gy, countrycode)
          GROUP BY gx, gy
        ) TO '{W / "cell_country.parquet"}' (FORMAT parquet, COMPRESSION zstd)""")
    s = con.execute(f"SELECT count(*), sum(n_core > 0), sum(n_core > 0 AND n_other = 0) FROM read_parquet('{W / 'support.parquet'}')").fetchone()
    print("species-cells", s[0], "with core", s[1], "core-only", s[2])


if __name__ == "__main__":
    {"records": records, "support": support}[sys.argv[1]]()
