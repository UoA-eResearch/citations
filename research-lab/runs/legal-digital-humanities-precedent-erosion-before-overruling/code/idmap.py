"""Data plumbing (no outcome is computed here).

  idmap.py opinions   stream CourtListener's opinions dump once -> data/interim/opinion_cluster.parquet (id, cluster_id)
  idmap.py clusters   clusters dump -> data/interim/clusters.parquet (id, docket_id, date_filed, scdb_id, case_name, ...)
  idmap.py dockets    dockets dump -> data/interim/dockets.parquet (id, court_id)

The dumps are the 2026-09-30 bulk files already downloaded for runs/legal-phantom-citations-judicial-opinions
(data/cl_raw). Parallel bz2 decompression (indexed_bzip2); csv parsing with an unlimited field size.
"""
import csv
import io
import sys
import time
from pathlib import Path

import indexed_bzip2 as ibz2
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "cl_raw"
INT = RUN / "data" / "interim"
csv.field_size_limit(sys.maxsize)


def stream(name, keep, every=1_000_000):
    t0 = time.time()
    f = ibz2.open(str(RAW / name), parallelization=6)
    # CourtListener's dumps escape quotes with a backslash (PostgreSQL CSV), not by doubling them
    r = csv.reader(io.TextIOWrapper(f, encoding="utf-8", errors="replace", newline=""), escapechar="\\", doublequote=False)
    head = next(r)
    ix = [head.index(k) for k in keep]
    rows = []
    for n, row in enumerate(r, 1):
        if len(row) == len(head):
            rows.append([row[i] for i in ix])
        if n % every == 0:
            print(name, n, round(time.time() - t0), "s", flush=True)
    print(name, "done", n, "rows", round(time.time() - t0), "s", flush=True)
    return pd.DataFrame(rows, columns=keep)


def opinions():
    d = stream("opinions.csv.bz2", ["id", "cluster_id"])
    d = d.apply(pd.to_numeric, errors="coerce").dropna().astype("int64")
    d.to_parquet(INT / "opinion_cluster.parquet", index=False)


def clusters():
    d = stream("opinion-clusters.csv.bz2", ["id", "docket_id", "date_filed", "scdb_id", "case_name", "precedential_status",
                                             "citation_count"])
    d.to_parquet(INT / "clusters.parquet", index=False)


def dockets():
    d = stream("dockets.csv.bz2", ["id", "court_id"])
    d.to_parquet(INT / "dockets.parquet", index=False)


if __name__ == "__main__":
    INT.mkdir(parents=True, exist_ok=True)
    {"opinions": opinions, "clusters": clusters, "dockets": dockets}[sys.argv[1]]()
