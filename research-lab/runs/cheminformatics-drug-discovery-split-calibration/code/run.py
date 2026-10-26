"""Splitters x models per target (plan sections 4-5). Written before any model was trained.

  run.py [WORKERS]  -> data/fits/<target>.json: retrospective metrics per splitter x repeat x model and prospective
                       metrics per model x prospective set; coverage.json stage fits (via analyse.py)
"""
import json
import os
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
OUT = D / "fits"
SEED, REPEATS, ACTIVE = 20261026, 5, 6.5
MODELS = ["rf", "lgbm", "svr", "knn", "mlp"]
SPLITTERS = ["random", "scaffold", "cluster", "document", "author", "assay", "time"]


def featurise(smiles):
    from rdkit import Chem, RDLogger
    from rdkit.Chem import AllChem, Descriptors
    RDLogger.DisableLog("rdApp.*")
    fps, desc, ok = [], [], []
    names = [n for n, _ in Descriptors.descList]
    for s in smiles:
        m = Chem.MolFromSmiles(s) if isinstance(s, str) else None
        if m is None:
            ok.append(False); fps.append(None); desc.append(None)
            continue
        fp = AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
        arr = np.zeros(2048, np.uint8)
        from rdkit import DataStructs
        DataStructs.ConvertToNumpyArray(fp, arr)
        fps.append(arr)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            desc.append(np.array([f(m) for _, f in Descriptors.descList], float))
        ok.append(True)
    return fps, desc, np.array(ok), names


def tanimoto(A, B):
    A, B = A.astype(np.float32), B.astype(np.float32)
    inter = A @ B.T
    return inter / (A.sum(1)[:, None] + B.sum(1)[None, :] - inter + 1e-9)


def fit_predict(model, Xf, Xd, y, tr, te_f, te_d):
    """Train on rows tr of the training matrices; predict for the given test feature matrices."""
    if model == "rf":
        from sklearn.ensemble import RandomForestRegressor
        m = RandomForestRegressor(n_estimators=500, n_jobs=1, random_state=SEED).fit(Xf[tr], y[tr])
        return m.predict(te_f)
    if model == "lgbm":
        import lightgbm as lgb
        m = lgb.LGBMRegressor(n_estimators=500, learning_rate=0.05, num_threads=1, random_state=SEED, verbose=-1)
        m.fit(Xd[tr], y[tr])
        return m.predict(te_d)
    if model == "svr":
        from sklearn.svm import SVR
        K = tanimoto(Xf[tr], Xf[tr])
        m = SVR(kernel="precomputed", C=1.0).fit(K, y[tr])
        return m.predict(tanimoto(te_f, Xf[tr]))
    if model == "knn":
        S = tanimoto(te_f, Xf[tr])
        idx = np.argsort(-S, axis=1)[:, :5]
        w = np.take_along_axis(S, idx, axis=1) + 1e-6
        return (w * y[tr][idx]).sum(1) / w.sum(1)
    if model == "mlp":
        from sklearn.neural_network import MLPRegressor
        m = MLPRegressor(hidden_layer_sizes=(512,), early_stopping=True, max_iter=200, random_state=SEED).fit(Xf[tr], y[tr])
        return m.predict(te_f)
    raise ValueError(model)


def metrics(y, p):
    from scipy.stats import spearmanr
    from sklearn.metrics import roc_auc_score
    out = {"rmse": float(np.sqrt(np.mean((y - p) ** 2))), "n": int(len(y))}
    out["spearman"] = float(spearmanr(y, p).statistic) if len(y) > 2 and np.std(y) > 0 else None
    lab = y >= ACTIVE
    out["auc"] = float(roc_auc_score(lab, p)) if 0 < lab.sum() < len(lab) else None
    return out


def group_split(groups, rng, lo=0.15, hi=0.25, tries=200):
    n = len(groups)
    ug, inv, counts = np.unique(groups, return_inverse=True, return_counts=True)
    for _ in range(tries):
        order = rng.permutation(len(ug))
        test, size = [], 0
        for g in order:
            if counts[g] > hi * n:
                continue
            if size + counts[g] <= hi * n:
                test.append(g); size += counts[g]
            if size >= lo * n:
                break
        if lo * n <= size <= hi * n:
            mask = np.isin(inv, test)
            return np.flatnonzero(~mask), np.flatnonzero(mask)
    return None


def author_groups(df):
    """Union documents that share an author (normalised surname + first initial); group = component of first doc."""
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    by_author = {}
    for doc, au in df[["first_doc", "authors"]].drop_duplicates().itertuples(index=False):
        find(doc)
        for a in str(au or "").split(","):
            a = a.strip()
            if not a or a.lower() == "none":
                continue
            parts = a.replace(".", " ").split()
            key = (parts[0].lower() + " " + (parts[1][0].lower() if len(parts) > 1 else "")).strip()
            if key in by_author:
                parent[find(doc)] = find(by_author[key])
            else:
                by_author[key] = doc
    return df.first_doc.map(lambda d: find(d)).to_numpy()


def splits(df, fps):
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold
    n = len(df)
    out = {}
    rng = np.random.default_rng(SEED)
    out["random"] = []
    for r in range(REPEATS):
        p = rng.permutation(n)
        k = int(round(0.2 * n))
        out["random"].append((np.sort(p[k:]), np.sort(p[:k])))
    scaf = []
    for s in df.smiles:
        try:
            scaf.append(MurckoScaffold.MurckoScaffoldSmiles(mol=Chem.MolFromSmiles(s)))
        except Exception:
            scaf.append(s)
    sims = tanimoto(fps, fps)
    # Butina at distance 0.65 (similarity >= 0.35), centroids by neighbour count
    nb = sims >= 0.35
    order = np.argsort(-nb.sum(1), kind="stable")
    cl, assigned = np.full(n, -1), np.zeros(n, bool)
    c = 0
    for i in order:
        if assigned[i]:
            continue
        members = np.flatnonzero(nb[i] & ~assigned)
        cl[members] = c; assigned[members] = True; c += 1
    groups = {"scaffold": np.array(scaf), "cluster": cl, "document": df.first_doc.to_numpy(),
              "author": author_groups(df), "assay": df.first_assay.to_numpy()}
    for name, g in groups.items():
        out[name] = []
        if name == "author":
            _, cnt = np.unique(g, return_counts=True)
            if cnt.max() > 0.8 * n:
                out[name] = "infeasible: largest author component holds more than 80% of compounds"
                continue
        rr = np.random.default_rng([SEED, len(out)])
        for r in range(REPEATS):
            s = group_split(g, rr)
            out[name].append(s if s is not None else "dropped: no group draw gave a 15-25% test set")
    yr = df.first_year.fillna(0).to_numpy() * 1e7 + df.first_doc.to_numpy()
    o = np.argsort(yr, kind="stable")
    k = int(round(0.2 * n))
    out["time"] = [(np.sort(o[:n - k]), np.sort(o[n - k:]))]
    return out


def one(target):
    f = OUT / f"{target}.json"
    if f.exists():
        return target, "done"
    t0 = time.time()
    tr = TRAIN[TRAIN.target == target].reset_index(drop=True)
    ps = PROS[PROS.target == target].reset_index(drop=True)
    fps, desc, ok, _ = featurise(tr.smiles)
    tr = tr[ok].reset_index(drop=True)
    Xf = np.stack([x for x, k in zip(fps, ok) if k]); Xd = np.stack([x for x, k in zip(desc, ok) if k])
    Xd = np.where(np.isfinite(Xd), Xd, np.nan)
    y = tr.pchembl.to_numpy(float)
    res = {"target": target, "n_train": int(len(tr)), "n_unparsed": int((~ok).sum()), "retro": [], "pros": [], "notes": {}}
    for name, lst in splits(tr, Xf).items():
        if isinstance(lst, str):
            res["notes"][name] = lst
            continue
        for r, s in enumerate(lst):
            if isinstance(s, str):
                res["notes"][f"{name}_{r}"] = s
                continue
            a, b = s
            for m in MODELS:
                p = fit_predict(m, Xf, Xd, y, a, Xf[b], Xd[b])
                res["retro"].append({"splitter": name, "repeat": r, "model": m, **metrics(y[b], p),
                                     "nn_sim_median": float(np.median(tanimoto(Xf[b], Xf[a]).max(1)))})
    allidx = np.arange(len(tr))
    for setname, g in ps.groupby("set"):
        pf, pdsc, pok, _ = featurise(g.smiles)
        if pok.sum() < 2:
            continue
        Pf = np.stack([x for x, k in zip(pf, pok) if k]); Pd = np.stack([x for x, k in zip(pdsc, pok) if k])
        Pd = np.where(np.isfinite(Pd), Pd, np.nan)
        py = g.pchembl.to_numpy(float)[pok]
        nn = float(np.median(tanimoto(Pf, Xf).max(1)))
        for m in MODELS:
            p = fit_predict(m, Xf, Xd, y, allidx, Pf, Pd)
            res["pros"].append({"set": setname, "model": m, **metrics(py, p), "nn_sim_median": nn})
    res["seconds"] = round(time.time() - t0, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(res))
    tmp.rename(f)
    return target, res["seconds"]


def main():
    global TRAIN, PROS
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    TRAIN = pd.read_parquet(D / "train.parquet")
    PROS = pd.read_parquet(D / "prospective.parquet")
    tg = pd.read_csv(T / "targets.csv").sort_values("n_train", ascending=False).target.tolist()
    print(len(tg), "targets", flush=True)
    with ProcessPoolExecutor(workers) as ex:
        for k, (t, s) in enumerate(ex.map(one, tg)):
            print(time.strftime("%H:%M:%S"), k + 1, t, s, flush=True)
    print("== done", flush=True)


if __name__ == "__main__":
    main()
