"""Analog-disjoint folds (plan section 2). Written before any outcome was read.

Per target: ECFP4 (radius 2, 2,048 bits); sparse neighbour lists of all pairs with Tanimoto >= 0.4 (chunked float32
matrix products, so no all-pairs distance list is held); Butina clustering at distance 0.6 on those lists (centroids
by neighbour count); clusters to 5 folds balancing actives, then compounds; evaluation compounds with any training-fold
neighbour above the threshold (0.4 primary, 0.6 sensitivity) are removed from evaluation and counted. The exact
nearest-neighbour similarity to training is computed for a random 2,000 evaluation compounds per target (audit, G4).
A random 5-fold split is the reference.

  folds.py new|lit [THREADS] -> data/folds_<bench>/<target>.npz (fold, eval_04, eval_06, random_fold), fp cache
"""
import json
import os
import sys
import zlib
from pathlib import Path

THREADS = sys.argv[2] if len(sys.argv) > 2 else "4"
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = THREADS
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
SEED, K, SIM = 20261027, 5, 0.4


def fingerprints(smiles):
    from rdkit import Chem, DataStructs, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    X = np.zeros((len(smiles), 2048), np.uint8)
    for i, s in enumerate(smiles):
        DataStructs.ConvertToNumpyArray(gen.GetFingerprint(Chem.MolFromSmiles(s)), X[i])
    return X


def neighbours(X, thr=SIM, chunk=1024):
    """All pairs (i, j), i != j, with Tanimoto >= thr, plus their similarity; chunked over rows."""
    A = X.astype(np.float32)
    cnt = A.sum(1)
    I, J, S = [], [], []
    for s in range(0, len(A), chunk):
        inter = A[s:s + chunk] @ A.T
        sim = inter / (cnt[s:s + chunk, None] + cnt[None, :] - inter + 1e-9)
        r, c = np.nonzero(sim >= thr)
        keep = (r + s) != c
        I.append(r[keep] + s); J.append(c[keep]); S.append(sim[r[keep], c[keep]].astype(np.float16))
    return np.concatenate(I), np.concatenate(J), np.concatenate(S)


def butina(n, I, J):
    """Butina on the sparse neighbour lists held as CSR arrays; centroids in order of neighbour count."""
    o = np.argsort(I, kind="stable")
    nbrs = J[o]
    ptr = np.concatenate([[0], np.cumsum(np.bincount(I, minlength=n))])
    order = np.argsort(-(ptr[1:] - ptr[:-1]), kind="stable")
    cl, assigned, c = np.full(n, -1), np.zeros(n, bool), 0
    for i in order:
        if assigned[i]:
            continue
        nb = nbrs[ptr[i]:ptr[i + 1]]
        mem = np.concatenate([[i], nb[~assigned[nb]]])
        cl[mem] = c; assigned[mem] = True; c += 1
    return cl


def assign_folds(cl, y, rng):
    """Clusters with actives first, balancing actives; then the rest, balancing compounds."""
    fold = np.empty(len(cl), int)
    n_act, n_all = np.zeros(K), np.zeros(K)
    ids, inv = np.unique(cl, return_inverse=True)
    act = np.bincount(inv, weights=y, minlength=len(ids)); size = np.bincount(inv, minlength=len(ids))
    perm = rng.permutation(len(ids))
    for c in sorted(perm, key=lambda c: (-int(act[c] > 0), -act[c], -size[c])):
        f = int(np.argmin(n_act * 1e6 + n_all)) if act[c] > 0 else int(np.argmin(n_all))
        fold[inv == c] = f; n_act[f] += act[c]; n_all[f] += size[c]
    return fold


def one(bench, target, g):
    out = D / f"folds_{bench}" / f"{target}.npz"
    if out.exists():
        return json.loads((D / f"folds_{bench}" / f"{target}.json").read_text())
    rng = np.random.default_rng([SEED, zlib.crc32(target.encode())])
    X = fingerprints(g.smiles.tolist())
    y = g.label.to_numpy()
    I, J, S = neighbours(X)
    cl = butina(len(g), I, J)
    fold = assign_folds(cl, y, rng)
    ev = {}
    for thr in (0.4, 0.6):
        bad = np.zeros(len(g), bool)
        m = (S > thr) & (fold[I] != fold[J])      # neighbour above threshold in a different fold = in that compound's training set
        bad[I[m]] = True
        ev[thr] = ~bad
    random_fold = rng.permutation(np.arange(len(g)) % K)
    # exact nearest-neighbour similarity to training for a random sample of evaluation compounds (audit)
    samp = rng.choice(len(g), min(2000, len(g)), replace=False)
    A = X.astype(np.float32); cnt = A.sum(1)
    nn = np.empty(len(samp))
    for f in range(K):                                # one product per fold: sampled compounds x all compounds
        k = np.flatnonzero(fold[samp] == f)
        if not len(k):
            continue
        inter = A[samp[k]] @ A.T
        sim = inter / (cnt[samp[k], None] + cnt[None, :] - inter + 1e-9)
        sim[:, fold == f] = -1                        # only that fold's training compounds count
        nn[k] = sim.max(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, fold=fold, eval_04=ev[0.4], eval_06=ev[0.6], random_fold=random_fold, cluster=cl)
    info = {"target": target, "compounds": int(len(g)), "actives": int(y.sum()), "clusters": int(cl.max() + 1),
            "neighbour_pairs_ge_0_4": int(len(I)), "eval_kept_04": int(ev[0.4].sum()), "eval_kept_06": int(ev[0.6].sum()),
            "actives_kept_04": int(y[ev[0.4]].sum()), "actives_kept_06": int(y[ev[0.6]].sum()),
            "nn_sim_sample_median": round(float(np.median(nn)), 3), "nn_sim_sample_share_above_0_4": round(float((nn > 0.4).mean()), 3),
            "nn_sim_sample_share_above_0_4_after_audit": round(float((nn[ev[0.4][samp]] > 0.4).mean()), 3) if ev[0.4][samp].any() else None}
    (D / f"folds_{bench}" / f"{target}.json").write_text(json.dumps(info))
    return info


def main(bench):
    df = pd.read_parquet(D / f"{bench}.parquet")
    if bench == "lit":
        df = df.drop_duplicates(["target", "smiles"])     # the LIT-PCBA control uses unique compounds per target
    infos = []
    for t, g in sorted(df.groupby("target"), key=lambda kv: len(kv[1])):
        infos.append(one(bench, t, g.reset_index(drop=True)))
        print(json.dumps(infos[-1]), flush=True)
    pd.DataFrame(infos).to_csv(T / f"folds_{bench}.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1])
