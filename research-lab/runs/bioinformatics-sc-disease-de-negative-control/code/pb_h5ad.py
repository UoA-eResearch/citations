"""Pseudobulk from the downloaded source H5ADs (plan sections 1-2; D1 data route): sum raw counts per
(tissue_general, cell type, donor) for the needed (tissue_general, cell type) pairs, primary cells only, genes in
Census var order. Consumes data/h5ad/<id>.complete files, then deletes the H5AD.

  pb_h5ad.py watch   -> data/pb/<id>.npz (CSR groups x Census genes), <id>.groups.parquet, <id>.cov.json
"""
import json
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import scipy.sparse as sp

RUN = Path(__file__).resolve().parents[1]
META, H5, PB = RUN / "data" / "meta", RUN / "data" / "h5ad", RUN / "data" / "pb"
VERSION = "2025-11-08"
CHUNK = 200_000
OBS = ["donor_id", "disease", "disease_ontology_term_id", "tissue_ontology_term_id", "cell_type",
       "cell_type_ontology_term_id", "assay", "suspension_type", "sex", "development_stage", "is_primary_data"]


def col(f, name):
    """One obs column of an AnnData H5AD (categorical or plain), as a NumPy array of str / bool."""
    g = f["obs"][name]
    if isinstance(g, h5py.Group):           # categorical
        cats = g["categories"][...].astype(str)
        return cats[g["codes"][...]]
    v = g[...]
    return v.astype(str) if v.dtype.kind in "SO" else v


def tissue_general_map(ds):
    import cellxgene_census as cc
    with cc.open_soma(census_version=VERSION) as census:
        t = census["census_data"]["homo_sapiens"].obs.read(value_filter=f"dataset_id == '{ds}'",
                                                           column_names=["tissue_ontology_term_id", "tissue_general"]).concat().to_pandas()
    t = t.astype(str).drop_duplicates()
    assert t.tissue_ontology_term_id.is_unique, "tissue term maps to more than one tissue_general"
    return dict(zip(t.tissue_ontology_term_id, t.tissue_general))


def one(ds):
    t0 = time.time()
    want = pd.concat([pd.read_csv(META / f) for f in ("contrasts_primary.csv", "contrasts_replication.csv")])
    want = set(map(tuple, want.loc[want.dataset_id == ds, ["tissue_general", "cell_type"]].to_numpy()))
    var = pd.read_parquet(META / "var.parquet")
    gpos = pd.Series(np.arange(len(var)), index=var.feature_id.astype(str))
    tg = tissue_general_map(ds)
    with h5py.File(H5 / f"{ds}.h5ad", "r") as f:
        obs = pd.DataFrame({c: col(f, c) for c in OBS})
        obs["tissue_general"] = obs.tissue_ontology_term_id.map(tg)
        raw = "raw" in f and "X" in f["raw"]
        Xg = f["raw/X"] if raw else f["X"]
        vg = f["raw/var"] if raw else f["var"]
        idx_key = vg.attrs.get("_index", "_index")
        genes = vg[idx_key][...].astype(str)
        assert Xg.attrs.get("encoding-type") == "csr_matrix", Xg.attrs.get("encoding-type")
        n_cells = len(obs)
        keep = (obs.is_primary_data.astype(str).isin(["True", "1", "true"])) & np.array([(a, b) in want for a, b in zip(obs.tissue_general, obs.cell_type)])
        sub = obs[keep]
        key = sub.tissue_general + "\t" + sub.cell_type + "\t" + sub.donor_id
        codes, uniq = pd.factorize(key, sort=True)
        cell_group = np.full(n_cells, -1, np.int64)
        cell_group[np.flatnonzero(keep)] = codes
        G = len(uniq)
        colmap = gpos.reindex(genes).to_numpy()
        in_census = ~np.isnan(colmap)
        acc = np.zeros((G, len(genes)), np.float64)
        indptr = Xg["indptr"][...]
        nonint, sampled = 0, 0
        for s in range(0, n_cells, CHUNK):
            e = min(n_cells, s + CHUNK)
            cg = cell_group[s:e]
            if (cg < 0).all():
                continue
            a, b = indptr[s], indptr[e]
            data = Xg["data"][a:b]
            if sampled < 1_000_000:
                nonint += int((data[:100_000] % 1 != 0).sum()); sampled += min(len(data), 100_000)
            X = sp.csr_matrix((data, Xg["indices"][a:b], indptr[s:e + 1] - a), shape=(e - s, len(genes)))
            k = cg >= 0
            M = sp.csr_matrix((np.ones(k.sum()), (cg[k], np.flatnonzero(k))), shape=(G, e - s))
            acc += (M @ X).toarray()
    groups = sub.assign(g=codes).groupby("g").agg(**{c: (c, "first") for c in ["tissue_general", "cell_type", "donor_id", "disease",
                                                                                 "disease_ontology_term_id", "cell_type_ontology_term_id",
                                                                                 "assay", "suspension_type", "sex", "development_stage"]},
                                                  n_cells=("donor_id", "size")).reset_index(drop=True)
    full = np.zeros((G, len(var)), np.float64)
    full[:, colmap[in_census].astype(int)] = acc[:, in_census]
    big = float(full.max()) >= 2 ** 24
    PB.mkdir(parents=True, exist_ok=True)
    groups.to_parquet(PB / f"{ds}.groups.parquet")
    cov = {"cells_h5ad": int(n_cells), "cells_kept": int(keep.sum()), "groups": int(G), "raw_layer": "raw.X" if raw else "X",
           "genes_h5ad": int(len(genes)), "genes_not_in_census_var": int((~in_census).sum()),
           "counts_dropped_not_in_census": float(acc[:, ~in_census].sum()), "total_counts": float(full.sum()),
           "nonint_share_sampled": round(nonint / max(sampled, 1), 6), "float64": big, "seconds": round(time.time() - t0, 1)}
    (PB / f"{ds}.cov.json").write_text(json.dumps(cov))
    tmp = PB / f"{ds}.tmp.npz"
    sp.save_npz(tmp, sp.csr_matrix(full if big else full.astype(np.float32)))
    tmp.rename(PB / f"{ds}.npz")
    return cov


def watch():
    need = set(pd.read_csv(META / "needed_datasets.csv").dataset_id)
    while True:
        done = {p.name[:-4] for p in PB.glob("*.npz")} if PB.exists() else set()
        if need <= done:
            break
        for c in sorted(H5.glob("*.complete")):
            ds = c.name[:-len(".complete")]
            try:
                cov = one(ds)
                print(time.strftime("%H:%M:%S"), ds, json.dumps(cov), flush=True)
            except Exception as e:  # counted in the log; the H5AD is kept for a rerun
                print(time.strftime("%H:%M:%S"), ds, "FAILED", repr(e)[:400], flush=True)
                c.rename(c.with_suffix(".failed"))
                continue
            (H5 / f"{ds}.h5ad").unlink(); c.unlink()
        time.sleep(20)
    print("== done", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "watch":
        watch()
    else:
        print(one(sys.argv[1]))
