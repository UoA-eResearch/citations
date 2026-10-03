#!/usr/bin/env python
"""Model panel and the cliff gap (plan.md sec 5).

ECFP4 (radius 2, 2,048 bits). Models with fixed default settings, identical across datasets:
  RF  random forest, 500 trees (10 seeds)
  SVR support vector regression with a Tanimoto kernel (deterministic)
  GBM LightGBM regressor, library defaults (10 seeds)
  KNN k-nearest neighbours, k = 5, Tanimoto distance (deterministic)
Gap = RMSE(test cliff molecules) - RMSE(test non-cliff molecules).

Usage: models.py  -> results/tables/predictions.parquet (dataset, idx, model, seed, y, pred) on the test sets
"""
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR

RDLogger.DisableLog("rdApp.*")
RUN = Path(__file__).resolve().parents[1]
BENCH = RUN / "data" / "moleculeace" / "MoleculeACE" / "Data" / "benchmark_data"
SEEDS = list(range(10))
MODELS = ["RF", "SVR", "GBM", "KNN"]


def ecfp(smiles):
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)   # created per call: RDKit objects do not pickle
    return np.array([gen.GetFingerprintAsNumPy(Chem.MolFromSmiles(s)) for s in smiles], dtype=np.float32)


def tanimoto(A, B):
    inter = A @ B.T
    return inter / (A.sum(1)[:, None] + B.sum(1)[None, :] - inter + 1e-9)


def fit_predict(model, Xtr, ytr, Xte, seed=0):
    if model == "RF":
        m = RandomForestRegressor(n_estimators=500, random_state=seed, n_jobs=1).fit(Xtr, ytr)
        return m.predict(Xte)
    if model == "GBM":
        m = lgb.LGBMRegressor(random_state=seed, verbose=-1, n_jobs=1).fit(Xtr, ytr)
        return m.predict(Xte)
    if model == "SVR":
        m = SVR(kernel="precomputed").fit(tanimoto(Xtr, Xtr), ytr)
        return m.predict(tanimoto(Xte, Xtr))
    if model == "KNN":
        S = tanimoto(Xte, Xtr)
        nn = np.argsort(-S, axis=1)[:, :5]
        return ytr[nn].mean(1)
    raise ValueError(model)


def runs_for(model):
    return SEEDS if model in ("RF", "GBM") else [0]


def gap(y, pred, cliff):
    cliff = np.asarray(cliff, bool)
    rm = lambda m: float(np.sqrt(np.mean((y[m] - pred[m]) ** 2))) if m.any() else np.nan
    return rm(cliff) - rm(~cliff), rm(cliff), rm(~cliff)


def load(name):
    df = pd.read_csv(BENCH / f"{name}.csv")
    return df, ecfp(df.smiles.tolist())


def _job(name, model, seed):
    df, X = load(name)
    tr, te = (df.split == "train").values, (df.split == "test").values
    y = df["y [pEC50/pKi]"].values
    p = fit_predict(model, X[tr], y[tr], X[te], seed)
    return pd.DataFrame(dict(dataset=name, idx=np.where(te)[0], model=model, seed=seed, y=y[te], pred=p))


def main():
    names = sorted(p.stem for p in BENCH.glob("*.csv"))
    jobs = [(n, m, s) for n in names for m in MODELS for s in runs_for(m)]
    parts = Parallel(n_jobs=28, verbose=0)(delayed(_job)(*j) for j in jobs)
    out = pd.concat(parts, ignore_index=True)
    out.to_parquet(RUN / "results" / "tables" / "predictions.parquet", index=False)
    print(len(jobs), "fits;", len(out), "test predictions")


if __name__ == "__main__":
    main()
