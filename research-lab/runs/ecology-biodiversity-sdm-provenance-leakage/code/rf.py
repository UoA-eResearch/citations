"""Retrain SAGE's single-species Random Forest under the removal conditions (plan section 4).

  rf.py removals          C1 (provenance-only presences) and C2-C6 (matched random removal per species and country,
                          seeds 1-5), applied to every species; cells left with no species are recorded
                          -> data/work/removals/<cond>.parquet (sp, cell) and <cond>_emptied.npy
  rf.py fit [WORKERS]     population species x {C0..C6}: per-species AUROC on range-masked test cells (source cells,
                          other cells, all) -> data/work/rf/<cond>_<sp>.json, then results/tables/rf_auroc.csv
  rf.py test SP           one species, all conditions, timed

Model and data follow SAGE (commit ce4a70e; sklearn_train.py, maxent_train.get_data): 1 km training targets restricted
to its occurrence subsample (train_indices_10000_1km.npy); presences capped at 10,000 at random; target-group
background = the species' in-range training cells (train_species_index) in the subsample minus the capped presences,
capped at 10,000; 52 environmental predictors with NaN imputed by SAGE's predictor means (z-scoring is irrelevant to
trees); imbalanced-learn BalancedRandomForestClassifier, 1,000 trees, max_features 7, sampling_strategy "all", no
replacement, seed 0. Per-species random draws use seed 0 + species index (SAGE uses one global stream).
"""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import h5py
import hdf5plugin  # noqa: F401
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
B, W, T = Path("/mnt/sage/bench"), RUN / "data" / "work", RUN / "results" / "tables"
(W / "removals").mkdir(parents=True, exist_ok=True)
(W / "rf").mkdir(parents=True, exist_ok=True)
GROUPS = ["chelsa", "soilgrids", "topography", "human_footprint"]
CONDS = ["C0", "C1", "C2", "C3", "C4", "C5", "C6"]
CAP, BG_CAP = 10_000, 10_000
G = {}                                   # globals shared with forked workers


def means():
    """SAGE's predictor means, parsed (not executed) from its datamodule.py with ast."""
    import ast
    tree = ast.parse(Path("/mnt/sage/repo/src/data_modules/datamodule.py").read_text())
    node = next(n.value for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "predictors_means")
    vals = {ast.literal_eval(k): v for k, v in zip(node.keys, node.values)}
    return np.concatenate([np.asarray(ast.literal_eval(vals[g]), dtype=np.float32) for g in GROUPS])


def presences():
    with h5py.File(B / "targets" / "train_targets_1km.h5") as h:
        idx, lk = h["target_location_indices"][:], h["target_location_indices_lookup"][:]
    return idx, lk


def removals():
    import audit
    rng0 = 20261025
    idx, lk = presences()
    sp = np.repeat(np.arange(len(lk) - 1, dtype=np.int16), np.diff(lk))
    P = pd.DataFrame({"sp": sp, "cell": idx})
    po = pd.read_parquet(W / "prov_only.parquet")
    po["po"] = True
    P = P.merge(po, on=["sp", "cell"], how="left").fillna({"po": False}).astype({"po": bool})
    tc = audit.train_cells()
    cc = pd.read_parquet(W / "cell_country.parquet")
    country = tc.merge(cc, on=["gx", "gy"], how="left").sort_values("cell").country.fillna("??").to_numpy()
    P["country"] = country[P.cell.to_numpy()]
    n_cell = np.bincount(P.cell.to_numpy(), minlength=len(tc))

    def emptied(rem):
        r = np.bincount(rem.cell.to_numpy(), minlength=len(tc))
        return np.where((n_cell > 0) & (r >= n_cell))[0]
    r1 = P[P.po][["sp", "cell"]]
    r1.to_parquet(W / "removals" / "C1.parquet", index=False)
    np.save(W / "removals" / "C1_emptied.npy", emptied(r1))
    k = P[P.po].groupby(["sp", "country"]).size().rename("k")
    pool = P[~P.po].merge(k.reset_index(), on=["sp", "country"])
    short = {}
    for d in range(1, 6):
        rng = np.random.default_rng(rng0 + d)
        pool["u"] = rng.random(len(pool))
        pool["rank"] = pool.groupby(["sp", "country"]).u.rank(method="first")
        rd = pool[pool["rank"] <= pool.k][["sp", "cell"]]
        got = rd.merge(P[["sp", "cell", "country"]], on=["sp", "cell"]).groupby(["sp", "country"]).size()
        short[f"C{d + 1}"] = int((k - got.reindex(k.index).fillna(0)).clip(lower=0).sum())
        rd.to_parquet(W / "removals" / f"C{d + 1}.parquet", index=False)
        np.save(W / "removals" / f"C{d + 1}_emptied.npy", emptied(rd))
    summ = {"C1_removed": int(len(r1)), "C1_emptied_cells": int(len(np.load(W / "removals" / "C1_emptied.npy"))),
            "random_shortfall_presences": short,
            "random_emptied_cells": {f"C{d + 1}": int(len(np.load(W / "removals" / f"C{d + 1}_emptied.npy"))) for d in range(1, 6)}}
    (T / "removals.json").write_text(json.dumps(summ, indent=1))
    print(summ)


def load():
    if G:
        return
    mu = means()
    X = np.concatenate([h5py.File(B / "predictors" / f"train_{g}_1km.h5")["predictor_data"][:] for g in GROUPS], axis=1)
    X = np.where(np.isnan(X), mu, X).astype(np.float32)
    test = np.load(B / "test_indices.npy")
    Xe = np.concatenate([h5py.File(B / "predictors" / f"eval_{g}.h5")["predictor_data"][:] for g in GROUPS], axis=1)[test]
    Xe = np.where(np.isnan(Xe), mu, Xe).astype(np.float32)
    idx, lk = presences()
    with h5py.File(B / "targets" / "eval_targets.h5") as h:
        eptr, eidx = h["csr"]["indptr"][:], h["csr"]["indices"][:]
    with h5py.File(B / "range_masks_1km" / "eval_range_mask.h5") as h:
        cl, si = h["cumulative_lengths"][:], h["species_index"][:]
    meta = pd.read_csv(RUN / "data" / "raw" / "eval_plot_metadata.csv", usecols=["cell_row", "GIVD_ID"])
    flags = pd.read_csv(T / "provenance_flags.csv")
    src = set(meta[meta.GIVD_ID.isin(set(flags[flags.flag == "core"].givd_source))].cell_row)
    import scipy.sparse as sp_
    nsp = len(lk) - 1
    rm_rows = np.repeat(np.arange(len(test)), [cl[c + 1] - cl[c] for c in test])
    rm_cols = np.concatenate([si[cl[c]:cl[c + 1]] for c in test])
    RM = sp_.csc_matrix((np.ones(len(rm_rows), bool), (rm_rows, rm_cols)), shape=(len(test), nsp))
    y_rows = np.repeat(np.arange(len(test)), [eptr[c + 1] - eptr[c] for c in test])
    y_cols = np.concatenate([eidx[eptr[c]:eptr[c + 1]] for c in test])
    Y = sp_.csc_matrix((np.ones(len(y_rows), np.int8), (y_rows, y_cols)), shape=(len(test), nsp))
    G.update(RM=RM, Y=Y)
    G.update(X=X, Xe=Xe, test=test, idx=idx, lk=lk, eptr=eptr, eidx=eidx, cl=cl, si=si,
             sub=np.isin(np.arange(len(X)), np.load(B / "targets" / "subsample_indices" / "train_indices_10000_1km.npy")),
             src=np.array([c in src for c in test]))
    G["rem"] = {}
    for c in CONDS[1:]:
        r = pd.read_parquet(W / "removals" / f"{c}.parquet")
        G["rem"][c] = {int(s): g.cell.to_numpy() for s, g in r.groupby("sp")}
        G["rem"][c + "_emptied"] = np.load(W / "removals" / f"{c}_emptied.npy")


def eval_labels(s):
    """Test-cell labels and native-range mask for species s."""
    m = G["RM"][:, s].toarray().ravel().astype(bool)
    y = G["Y"][:, s].toarray().ravel().astype(np.int8)
    return y, m


def fit_one(args):
    s, cond = args
    out = W / "rf" / f"{cond}_{s}.json"
    if out.exists():
        return json.loads(out.read_text())
    from imblearn.ensemble import BalancedRandomForestClassifier
    from sklearn.metrics import roc_auc_score
    load()
    t0 = time.time()
    pres = G["idx"][G["lk"][s]:G["lk"][s + 1]]
    emptied = np.array([], dtype=np.int64)
    if cond != "C0":
        pres = np.setdiff1d(pres, G["rem"][cond].get(s, np.array([], dtype=np.int32)))
        emptied = G["rem"][cond + "_emptied"]
    pres = pres[G["sub"][pres]]
    rng = np.random.default_rng(s)
    if len(pres) > CAP:
        pres = rng.choice(pres, CAP, replace=False)
    with h5py.File(B / "range_masks_1km" / "train_species_index.h5") as h:
        lk = h["target_location_indices_lookup"]
        tgb = h["target_location_indices"][int(lk[s]):int(lk[s + 1])]
    bg = np.setdiff1d(tgb, pres)
    bg = bg[G["sub"][bg]]
    if len(emptied):
        bg = np.setdiff1d(bg, emptied)
    if len(bg) > BG_CAP:
        bg = np.random.default_rng(1_000_003 + s).choice(bg, BG_CAP, replace=False)
    import hashlib
    key = hashlib.sha1(np.sort(pres).astype(np.int64).tobytes() + b"|" + np.sort(bg).astype(np.int64).tobytes()).hexdigest()[:20]
    cache = W / "rf" / f"hash_{s}_{key}.json"          # identical inputs give identical fits (seeded): reuse
    if cache.exists():
        res = dict(json.loads(cache.read_text()), cond=cond, reused=True)
        out.write_text(json.dumps(res))
        return res
    X = np.concatenate([G["X"][pres], G["X"][bg]])
    y = np.r_[np.ones(len(pres), dtype=int), np.zeros(len(bg), dtype=int)]
    m = BalancedRandomForestClassifier(n_estimators=1000, max_features=7, sampling_strategy="all", replacement=False,
                                       bootstrap=True, n_jobs=int(G.get("n_jobs", 2)), random_state=0)
    m.fit(X, y)
    ye, mask = eval_labels(s)
    p = m.predict_proba(G["Xe"][mask])[:, 1]
    ye, src = ye[mask], G["src"][mask]
    res = {"sp": s, "cond": cond, "n_pres": int(len(pres)), "n_bg": int(len(bg)), "secs": round(time.time() - t0, 1)}
    for name, sel in (("src", src), ("other", ~src), ("all", np.ones(len(ye), bool))):
        ok = sel & True
        res[f"auroc_{name}"] = float(roc_auc_score(ye[ok], p[ok])) if 0 < ye[ok].sum() < ok.sum() else None
        res[f"n_{name}"] = int(ok.sum()); res[f"pos_{name}"] = int(ye[ok].sum())
    out.write_text(json.dumps(res))
    cache.write_text(json.dumps(res))
    return res


def fit(workers=12):
    load()
    G["n_jobs"] = 2
    pop = pd.read_csv(T / "population.csv").sp.tolist()
    jobs = [(int(s), c) for s in pop for c in CONDS]          # C0 first per species, so unchanged conditions reuse it
    done = 0
    with ProcessPoolExecutor(int(workers)) as ex:          # fork: workers share the loaded arrays copy-on-write
        for r in ex.map(fit_one, jobs, chunksize=1):
            done += 1
            if done % 100 == 0:
                print(time.strftime("%H:%M:%S"), done, "of", len(jobs), flush=True)
    rows = [json.loads(f.read_text()) for f in (W / "rf").glob("C*.json")]
    pd.DataFrame(rows).sort_values(["sp", "cond"]).to_csv(T / "rf_auroc.csv", index=False)
    print("== fit done", len(rows))


def test(s):
    load()
    G["n_jobs"] = 8
    for c in CONDS:
        r = fit_one((int(s), c)); print(r)


if __name__ == "__main__":
    a = sys.argv
    {"removals": removals, "fit": lambda: fit(*(a[2:3] or [12])), "test": lambda: test(a[2])}[a[1]]()
