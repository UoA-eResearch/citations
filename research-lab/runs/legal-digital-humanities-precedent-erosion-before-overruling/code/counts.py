"""Yearly lower-court citations to every Supreme Court cluster (plan section 1).

Reads data/interim/{opinion_cluster,clusters,dockets}.parquet (idmap.py), the courts table and the citation map.
A citation (citing opinion -> cited opinion) is kept if the cited opinion's cluster is a Supreme Court cluster
(docket court_id == "scotus") and the citing cluster's court is not; citing clusters are counted once per cited
cluster. Writes
  data/interim/cites_scotus.parquet   (cited_cluster, citing_cluster, year, juris)   one row per citing-cited cluster pair
  results/tables/scotus_cites_by_year.csv   (year, all lower-court citations to Supreme Court clusters; federal; state)
"""
import csv
import io
import sys
import time
from pathlib import Path

import indexed_bzip2 as ibz2
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT = RUN / "data" / "interim"
RAW = RUN / "data" / "raw"
T = RUN / "results" / "tables"
csv.field_size_limit(sys.maxsize)


def courts():
    f = ibz2.open(str(RAW / "courts-2026-09-30.csv.bz2"))
    r = csv.reader(io.TextIOWrapper(f, encoding="utf-8", newline=""), escapechar="\\", doublequote=False)
    h = next(r)
    i, j = h.index("id"), h.index("jurisdiction")
    return {row[i]: row[j] for row in r if len(row) == len(h)}


def main():
    t0 = time.time()
    oc = pd.read_parquet(INT / "opinion_cluster.parquet")
    cl = pd.read_parquet(INT / "clusters.parquet", columns=["id", "docket_id", "date_filed"])
    dk = pd.read_parquet(INT / "dockets.parquet")
    cl["id"] = pd.to_numeric(cl.id, errors="coerce")
    cl["docket_id"] = pd.to_numeric(cl.docket_id, errors="coerce")
    cl = cl.dropna(subset=["id", "docket_id"]).astype({"id": "int64", "docket_id": "int64"})
    dk["id"] = pd.to_numeric(dk.id, errors="coerce")
    dk = dk.dropna(subset=["id"]).astype({"id": "int64"})
    cl = cl.merge(dk.rename(columns={"id": "docket_id"}), on="docket_id", how="left")
    jur = courts()
    cl["juris"] = cl.court_id.map(jur).fillna("")
    cl["scotus"] = cl.court_id == "scotus"
    cl["year"] = pd.to_numeric(cl.date_filed.str[:4], errors="coerce").fillna(0).astype(int)
    # dense lookup arrays indexed by id
    op2cl = np.full(int(oc.id.max()) + 1, -1, dtype=np.int64)
    op2cl[oc.id.to_numpy()] = oc.cluster_id.to_numpy()
    n = int(cl.id.max()) + 1
    is_sc = np.zeros(n, bool); is_sc[cl.id.to_numpy()] = cl.scotus.to_numpy()
    yr = np.zeros(n, np.int16); yr[cl.id.to_numpy()] = cl.year.to_numpy()
    jcode = {"": 0}
    for j in sorted(set(cl.juris)):
        jcode.setdefault(j, len(jcode))
    jc = np.zeros(n, np.int16); jc[cl.id.to_numpy()] = cl.juris.map(jcode).to_numpy()
    print("lookups", round(time.time() - t0), "s; scotus clusters", int(is_sc.sum()), flush=True)
    parts, seen = [], 0
    reader = pd.read_csv(ibz2.open(str(RAW / "citation-map-2026-09-30.csv.bz2"), parallelization=4),
                         usecols=["citing_opinion_id", "cited_opinion_id"], chunksize=5_000_000, dtype="int64")
    for ch in reader:
        seen += len(ch)
        a = ch.citing_opinion_id.to_numpy(); b = ch.cited_opinion_id.to_numpy()
        ok = (a < len(op2cl)) & (b < len(op2cl))
        ca = np.where(ok, op2cl[np.minimum(a, len(op2cl) - 1)], -1)
        cb = np.where(ok, op2cl[np.minimum(b, len(op2cl) - 1)], -1)
        ok &= (ca >= 0) & (cb >= 0) & (ca < n) & (cb < n)
        ca, cb = ca[ok], cb[ok]
        keep = is_sc[cb] & ~is_sc[ca]
        parts.append(pd.DataFrame({"cited_cluster": cb[keep], "citing_cluster": ca[keep]}))
        print(seen, "rows", round(time.time() - t0), "s", flush=True)
    d = pd.concat(parts).drop_duplicates()
    d["year"] = yr[d.citing_cluster.to_numpy()]
    inv = {v: k for k, v in jcode.items()}
    d["juris"] = pd.Series(jc[d.citing_cluster.to_numpy()]).map(inv).to_numpy()
    d.to_parquet(INT / "cites_scotus.parquet", index=False)
    fed = d.juris.str.startswith("F")
    state = d.juris.isin(["S", "SA", "ST", "SS"])
    tot = pd.DataFrame({"all": d.groupby("year").size(), "federal": d[fed].groupby("year").size(),
                        "state": d[state].groupby("year").size()}).fillna(0).astype(int)
    tot.to_csv(T / "scotus_cites_by_year.csv")
    print("citation map rows", seen, "lower-court citing-cited pairs to scotus", len(d), round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
