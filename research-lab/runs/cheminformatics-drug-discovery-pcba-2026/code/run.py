"""Methods and scores (plan sections 2-4). Written before any outcome was read.

Three evaluations:
  new      -- NEW benchmark, analog-disjoint 5-fold (primary), plus the 0.6 and random-split sensitivities
  lit_cv   -- LIT-PCBA under the same analog-disjoint procedure (benchmark vs split control)
  lit_pub  -- LIT-PCBA as published (AVE_unbiased training -> validation; D1)

Each writes data/scores_<eval>/<target>__<variant>.parquet with one row per evaluation compound and method, so the
metrics and their bootstraps are computed in analyse.py.

  run.py new|lit_cv|lit_pub [WORKERS] [THREADS_PER_WORKER]
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

THREADS = sys.argv[3] if len(sys.argv) > 3 else "1"
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = THREADS
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
SEED = 20261027
METHODS = ["nn", "rf", "gbm", "cb", "mf"]


def features(smiles):
    """ECFP4 bits, RDKit 2D descriptors, and the cached embedding rows for these SMILES."""
    from rdkit import Chem, DataStructs, RDLogger
    from rdkit.Chem import Descriptors, rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    X = np.zeros((len(smiles), 2048), np.uint8)
    desc = np.zeros((len(smiles), len(Descriptors.descList)), np.float64)
    for i, s in enumerate(smiles):
        m = Chem.MolFromSmiles(s)
        DataStructs.ConvertToNumpyArray(gen.GetFingerprint(m), X[i])
        desc[i] = [f(m) for _, f in Descriptors.descList]
    return X, np.where(np.isfinite(desc), desc, np.nan)


def embeddings(smiles):
    idx = pd.read_parquet(D / "smiles_unique.parquet").smiles
    pos = pd.Series(np.arange(len(idx)), index=idx.to_numpy())
    rows = pos.reindex(smiles).to_numpy()
    assert np.isfinite(rows).all(), "embedding cache is missing SMILES"
    return {m: np.load(D / f"emb_{m}.npy", mmap_mode="r")[rows.astype(int)] for m in ("cb", "mf")}


def tanimoto(A, B):
    A, B = A.astype(np.float32), B.astype(np.float32)
    inter = A @ B.T
    return inter / (A.sum(1)[:, None] + B.sum(1)[None, :] - inter + 1e-9)


def fit_score(method, X, desc, emb, y, tr, te):
    if method == "nn":
        act = tr[y[tr] == 1]
        return tanimoto(X[te], X[act]).max(1) if len(act) else np.zeros(len(te))
    if method == "rf":
        from sklearn.ensemble import RandomForestRegressor  # noqa: F401
        from sklearn.ensemble import RandomForestClassifier
        m = RandomForestClassifier(n_estimators=500, n_jobs=1, random_state=SEED, class_weight="balanced", max_features="sqrt")
        return m.fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    if method == "gbm":
        import lightgbm as lgb
        pos = max(1, int(y[tr].sum()))
        m = lgb.LGBMClassifier(n_estimators=500, learning_rate=0.05, num_threads=1, random_state=SEED, verbose=-1,
                               scale_pos_weight=(len(tr) - pos) / pos)
        return m.fit(desc[tr], y[tr]).predict_proba(desc[te])[:, 1]
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    E = emb[method]
    m = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000))
    return m.fit(E[tr], y[tr]).predict_proba(E[te])[:, 1]


def one(args):
    ev, target = args
    out_dir = D / f"scores_{ev}"
    out_dir.mkdir(parents=True, exist_ok=True)
    done = {p.name.split("__")[1][:-8] for p in out_dir.glob(f"{target}__*.parquet")}
    bench = "new" if ev == "new" else "lit"
    df = pd.read_parquet(D / f"{bench}.parquet")
    df = df[df.target == target].reset_index(drop=True)
    if ev == "lit_pub":
        df = df[df.split.isin(["training", "validation"])].drop_duplicates(["smiles", "split"]).reset_index(drop=True)
        variants = {"published": (df.split.to_numpy() == "training", df.split.to_numpy() == "validation")}
    else:
        if bench == "lit":
            df = df.drop_duplicates("smiles").reset_index(drop=True)
        z = np.load(D / f"folds_{bench}" / f"{target}.npz")
        variants = {}
        for name, fold, keep in (("audit04", z["fold"], z["eval_04"]), ("audit06", z["fold"], z["eval_06"]),
                                 ("random", z["random_fold"], np.ones(len(df), bool))):
            variants[name] = (fold, keep)
    if set(variants) <= done:
        return target, "done"
    X, desc = features(df.smiles.tolist())
    emb = embeddings(df.smiles.tolist())
    y = df.label.to_numpy()
    for name, v in variants.items():
        if name in done:
            continue
        rows = []
        if name == "published":
            tr_mask, te_mask = v
            folds = [(np.flatnonzero(tr_mask), np.flatnonzero(te_mask))]
        else:
            fold, keep = v
            folds = [(np.flatnonzero(fold != f), np.flatnonzero((fold == f) & keep)) for f in np.unique(fold)]
        for k, (tr, te) in enumerate(folds):
            if not len(te) or y[tr].sum() == 0:
                continue
            for meth in METHODS:
                rows.append(pd.DataFrame({"target": target, "variant": name, "fold": k, "method": meth,
                                          "idx": te, "y": y[te], "score": fit_score(meth, X, desc, emb, y, tr, te)}))
        if rows:
            pd.concat(rows, ignore_index=True).to_parquet(out_dir / f"{target}__{name}.parquet")
    return target, "ok"


def main(ev, workers):
    bench = "new" if ev == "new" else "lit"
    df = pd.read_parquet(D / f"{bench}.parquet")
    targets = sorted(df.target.unique(), key=lambda t: -int((df.target == t).sum()))
    print(len(targets), "targets", flush=True)
    with ProcessPoolExecutor(workers) as ex:
        for t, s in ex.map(one, [(ev, t) for t in targets]):
            print(t, s, flush=True)
    print("== done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8)
