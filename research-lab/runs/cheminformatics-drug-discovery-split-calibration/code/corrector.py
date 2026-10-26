"""Bias corrector (plan section 6, secondary). Written before any model was trained.

Predicts the primary model's prospective RMSE per target from its retrospective RMSE under each splitter plus
computable dataset descriptors: median train-test nearest-neighbour similarity (scaffold split), activity-cliff density
(share of nearest-neighbour pairs with Tanimoto >= 0.8 and |delta pChEMBL| >= 1), document and assay entropy, label
variance and training size. Gradient boosting, 5-fold cross-validation over targets (seed 20261026); median absolute
error against the 0.10 log-unit bar; permutation feature importance.
-> results/tables/corrector.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
from run import featurise, tanimoto  # noqa: E402

SEED = 20261026


def entropy(x):
    p = pd.Series(x).value_counts(normalize=True).to_numpy()
    return float(-(p * np.log(p)).sum())


def descriptors():
    tr = pd.read_parquet(D / "train.parquet")
    rows = []
    for t, g in tr.groupby("target"):
        fps, _, ok, _ = featurise(g.smiles)
        X = np.stack([f for f, k in zip(fps, ok) if k])
        y = g.pchembl.to_numpy(float)[ok]
        S = tanimoto(X, X)
        np.fill_diagonal(S, -1)
        j = S.argmax(1)
        cliff = float(((S[np.arange(len(j)), j] >= 0.8) & (np.abs(y - y[j]) >= 1)).mean())
        rows.append({"target": t, "n_train": len(y), "label_var": float(np.var(y)), "cliff_density": cliff,
                     "doc_entropy": entropy(g.first_doc), "assay_entropy": entropy(g.first_assay)})
    return pd.DataFrame(rows)


def main():
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.inspection import permutation_importance
    from sklearn.model_selection import KFold
    sel = json.loads((T / "selection.json").read_text())
    L = pd.read_csv(T / "bias_long.csv")
    L = L[(L.set == sel["primary_definition"]) & (L.model == "rf")]
    w = L.pivot(index="target", columns="splitter", values="retro_rmse").add_prefix("retro_")
    sim = L[L.splitter == "scaffold"].set_index("target").nn_sim_median.rename("scaffold_nn_sim")
    yv = L.drop_duplicates("target").set_index("target").pros_rmse
    X = w.join(sim).join(descriptors().set_index("target")).loc[yv.index]
    X = X.fillna(X.median())
    pred = np.zeros(len(X))
    for a, b in KFold(5, shuffle=True, random_state=SEED).split(X):
        m = GradientBoostingRegressor(random_state=SEED).fit(X.iloc[a], yv.iloc[a])
        pred[b] = m.predict(X.iloc[b])
    m = GradientBoostingRegressor(random_state=SEED).fit(X, yv)
    imp = permutation_importance(m, X, yv, n_repeats=20, random_state=SEED)
    out = {"targets": int(len(X)), "median_abs_error": round(float(np.median(np.abs(pred - yv))), 4),
           "below_0_10_bar": bool(np.median(np.abs(pred - yv)) <= 0.10),
           "baseline_median_abs_error_best_single_splitter": {c: round(float(np.median(np.abs(X[c] - yv))), 4) for c in w.columns},
           "importance": dict(sorted({c: round(float(v), 4) for c, v in zip(X.columns, imp.importances_mean)}.items(), key=lambda kv: -kv[1]))}
    (T / "corrector.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
