"""Pseudobulk extraction (plan sections 1-2): sum Census X["raw"] counts per (tissue_general, cell type, donor) for
every needed dataset, primary cells only.

  stream.py list            -> data/meta/needed_datasets.csv (primary contrasts + cross-collection replication pairs)
  stream.py run [WORKERS]   -> data/pb/<dataset_id>.npz (CSR groups x genes) + data/pb/<dataset_id>.groups.parquet
                               + data/pb/<dataset_id>.cov.json (cells read vs metadata count), data/meta/var.parquet
"""
import itertools
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

RUN = Path(__file__).resolve().parents[1]
META, PB = RUN / "data" / "meta", RUN / "data" / "pb"
VERSION = "2025-11-08"
# This host gets ~120 KB/s per S3 connection but scales with connections, so TileDB is told to keep many in flight.
TILEDB = {"vfs.s3.max_parallel_ops": 192, "sm.io_concurrency_level": 192, "vfs.s3.multipart_part_size": 4 * 2 ** 20,
          "soma.init_buffer_bytes": 2 ** 28, "vfs.s3.connect_max_tries": 10, "vfs.s3.request_timeout_ms": 600000}
KEYS = ["tissue_general", "cell_type", "donor_id"]
OBS_COLS = ["soma_joinid", "donor_id", "disease", "disease_ontology_term_id", "tissue_general", "cell_type",
            "cell_type_ontology_term_id", "assay", "suspension_type", "sex", "development_stage"]


def contrasts(min_d, min_h):
    """Contrasts from the metadata counts: donors with >= 10 cells of the type and a single disease label in the dataset."""
    o = pd.read_parquet(META / "obs_counts.parquet")
    o = o[o.is_primary_data.astype(str) == "True"]
    d = o.groupby(["dataset_id", "tissue_general", "cell_type", "donor_id", "disease"], observed=True).cells.sum().reset_index()
    labels = o.groupby(["dataset_id", "donor_id"]).disease.nunique()
    single = labels[labels == 1].index
    d = d[d.cells >= 10]
    d = d[pd.MultiIndex.from_frame(d[["dataset_id", "donor_id"]]).isin(single)]
    g = d.groupby(["dataset_id", "tissue_general", "cell_type", "disease"]).donor_id.nunique().unstack("disease", fill_value=0)
    rows = []
    for (ds, ti, ct), r in g.iterrows():
        nh = int(r.get("normal", 0))
        for dis, nd in r.items():
            if dis != "normal" and nd >= min_d and nh >= min_h:
                rows.append((ds, ti, ct, dis, int(nd), nh))
    return pd.DataFrame(rows, columns=["dataset_id", "tissue_general", "cell_type", "disease", "n_disease", "n_normal"])


def needed():
    col = pd.read_parquet(META / "datasets.parquet").set_index("dataset_id").collection_id
    prim = contrasts(8, 16)
    rep = contrasts(4, 4).assign(collection_id=lambda x: x.dataset_id.map(col))
    keep = []
    for _, g in rep.groupby(["disease", "tissue_general", "cell_type"]):
        idx = g.index.tolist()
        for a, b in itertools.combinations(idx, 2):
            if rep.collection_id[a] != rep.collection_id[b]:
                keep += [a, b]
    rep = rep.loc[sorted(set(keep))]
    prim.to_csv(META / "contrasts_primary.csv", index=False)
    rep.to_csv(META / "contrasts_replication.csv", index=False)
    ds = sorted(set(prim.dataset_id) | set(rep.dataset_id))
    pd.DataFrame({"dataset_id": ds}).to_csv(META / "needed_datasets.csv", index=False)
    print(f"primary {len(prim)} contrasts / {prim.dataset_id.nunique()} datasets; replication {len(rep)} contrasts; "
          f"{len(ds)} datasets needed", flush=True)


def one(ds):
    import cellxgene_census as cc
    out = PB / f"{ds}.npz"
    if out.exists():
        return ds, "done"
    t0 = time.time()
    with cc.open_soma(census_version=VERSION, tiledb_config=TILEDB) as census:
        exp = census["census_data"]["homo_sapiens"]
        obs = exp.obs.read(value_filter=f"dataset_id == '{ds}' and is_primary_data == True",
                           column_names=OBS_COLS).concat().to_pandas()
        for c in OBS_COLS[1:]:
            obs[c] = obs[c].astype(str)
        n_obs = len(obs)
        want = pd.concat([pd.read_csv(META / f) for f in ("contrasts_primary.csv", "contrasts_replication.csv")])
        want = set(map(tuple, want.loc[want.dataset_id == ds, ["tissue_general", "cell_type"]].to_numpy()))
        obs = obs[[t in want for t in zip(obs.tissue_general, obs.cell_type)]].reset_index(drop=True)
        grp = obs.groupby(KEYS, sort=True).ngroup().to_numpy()
        groups = (obs.assign(g=grp).groupby("g").agg(**{k: (k, "first") for k in OBS_COLS[1:]}, n_cells=("soma_joinid", "size"))
                  .reset_index(drop=True))
        jid = obs.soma_joinid.to_numpy()
        lo, hi = int(jid.min()), int(jid.max())
        lookup = np.full(hi - lo + 1, -1, np.int64)
        lookup[jid - lo] = grp
        n_genes = int(exp.ms["RNA"].var.count)
        acc = np.zeros((len(groups), n_genes), np.float64)   # dense; each batch touches few groups
        contiguous = (hi - lo + 1) == len(jid)
        coords = (slice(lo, hi),) if contiguous else (np.sort(jid),)
        nnz, cells_seen = 0, set()
        for tbl in exp.ms["RNA"].X["raw"].read(coords).tables():
            r = tbl["soma_dim_0"].to_numpy() - lo
            gi = lookup[r]
            k = gi >= 0
            if not k.all():
                r, gi = r[k], gi[k]
            cols = tbl["soma_dim_1"].to_numpy()[k]
            vals = tbl["soma_data"].to_numpy()[k].astype(np.float64)
            nnz += len(vals)
            rows = np.unique(gi)
            sub = sp.coo_matrix((vals, (np.searchsorted(rows, gi), cols)), shape=(len(rows), n_genes)).toarray()
            acc[rows] += sub
    PB.mkdir(parents=True, exist_ok=True)
    groups.to_parquet(PB / f"{ds}.groups.parquet")
    big = float(acc.max()) >= 2 ** 24
    (PB / f"{ds}.cov.json").write_text(json.dumps({"cells_obs": int(n_obs), "cells_kept": int(len(obs)), "groups": int(len(groups)),
                                                   "nnz": int(nnz), "float64": big,
                                                   "contiguous": bool(contiguous), "total_counts": float(acc.sum()),
                                                   "seconds": round(time.time() - t0, 1)}))
    tmp = PB / f"{ds}.tmp.npz"
    sp.save_npz(tmp, sp.csr_matrix(acc if big else acc.astype(np.float32)))
    tmp.rename(out)
    return ds, round(time.time() - t0, 1)


def run(workers):
    import cellxgene_census as cc
    if not (META / "var.parquet").exists():
        with cc.open_soma(census_version=VERSION, tiledb_config=TILEDB) as census:
            census["census_data"]["homo_sapiens"].ms["RNA"].var.read().concat().to_pandas().to_parquet(META / "var.parquet")
    ds = pd.read_csv(META / "needed_datasets.csv").dataset_id.tolist()
    o = pd.read_parquet(META / "obs_counts.parquet")
    size = o[o.is_primary_data.astype(str) == "True"].groupby("dataset_id").cells.sum()
    ds = sorted(ds, key=lambda d: -size.get(d, 0))
    print(len(ds), "datasets,", int(size[ds].sum()), "cells", flush=True)
    with ProcessPoolExecutor(workers) as ex:
        futs = {ex.submit(one, d): d for d in ds}
        for k, f in enumerate(as_completed(futs)):
            try:
                d, s = f.result()
                print(time.strftime("%H:%M:%S"), k + 1, d, s, flush=True)
            except Exception as e:  # counted; rerun resumes
                print(time.strftime("%H:%M:%S"), k + 1, futs[f], "FAILED", repr(e)[:300], flush=True)
    print("== done", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "list":
        needed()
    elif sys.argv[1] == "one":
        print(one(sys.argv[2]))
    else:
        run(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
