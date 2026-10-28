"""H1 and H2 (plan section 0). Committed before it was run on the test task.

The model is a HistGradientBoostingClassifier trained on the earlier task (cutoff 2019, horizon 2020-2022) and
applied to the test task (cutoff 2022, horizon 2023-2025). Hyperparameters are chosen inside the training task by
gene-grouped 2-fold cross-validation (D2). The null ranks candidates by the sampling-effort probability alone.

  analyse.py -> results/tables/primary.json, secondary.json, top100.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
SEED, B = 20261028, 2000
EFFORT = ["log_n_hor", "log_n_cut", "null_p"]
COOC = ["log_n_species_g", "log_freq_g", "growth_g", "log_n_genes_s", "jaccard_max", "jaccard_top5"]
TAX = ["genus_count", "genus_has", "family_count", "family_has"]
EMB = ["emb_cos_max"]
FULL = EFFORT + COOC + TAX + EMB
GRID = [{"max_leaf_nodes": 31, "learning_rate": 0.1}, {"max_leaf_nodes": 63, "learning_rate": 0.05},
        {"max_leaf_nodes": 15, "learning_rate": 0.1}]


def fit_predict(tr, te, feats, rng_seed=SEED):
    """Hyperparameters by gene-grouped 2-fold CV inside the training task, then refit on all of it (D2)."""
    g = tr.gene.cat.codes.to_numpy() if hasattr(tr.gene, "cat") else pd.factorize(tr.gene)[0]
    half = (g % 2) == 0
    best, best_ap = None, -1
    for kw in GRID:
        aps = []
        for m in (half, ~half):
            mdl = HistGradientBoostingClassifier(max_iter=300, early_stopping=False, random_state=rng_seed, **kw)
            mdl.fit(tr.loc[m, feats], tr.y[m])
            aps.append(average_precision_score(tr.y[~m], mdl.predict_proba(tr.loc[~m, feats])[:, 1]))
        if np.mean(aps) > best_ap:
            best, best_ap = kw, float(np.mean(aps))
    mdl = HistGradientBoostingClassifier(max_iter=300, early_stopping=False, random_state=rng_seed, **best)
    mdl.fit(tr[feats], tr.y)
    return mdl.predict_proba(te[feats])[:, 1], best, best_ap


def precision_at(score, y, k):
    idx = np.argsort(-score, kind="stable")[:k]
    return float(y[idx].mean())


def boot_indices(genes, rng, n):
    """Resample candidate rows by gene."""
    codes, uniq = pd.factorize(genes)
    order = np.argsort(codes, kind="stable")
    starts = np.searchsorted(codes[order], np.arange(len(uniq)))
    ends = np.r_[starts[1:], len(order)]
    for _ in range(n):
        pick = rng.integers(0, len(uniq), len(uniq))
        yield np.concatenate([order[starts[p]:ends[p]] for p in pick])


def main():
    tr = pd.read_parquet(D / "task_train.parquet")
    te = pd.read_parquet(D / "task_test.parquet")
    y = te.y.to_numpy()
    rng = np.random.default_rng(SEED)
    p_model, best, best_ap = fit_predict(tr, te, FULL)
    p_null = te.null_p.to_numpy()

    out = {"train": {"candidates": len(tr), "positives": int(tr.y.sum())},
           "test": {"candidates": len(te), "positives": int(y.sum())},
           "hyperparameters": best, "cv_average_precision": round(best_ap, 5),
           "precision_at_100": {"model": precision_at(p_model, y, 100), "null": precision_at(p_null, y, 100)}}
    pm, pn = out["precision_at_100"]["model"], out["precision_at_100"]["null"]
    out["ratio"] = round(pm / pn, 4) if pn > 0 else None
    ratios = []
    for idx in boot_indices(te.gene.to_numpy(), rng, B):
        a, b = precision_at(p_model[idx], y[idx], 100), precision_at(p_null[idx], y[idx], 100)
        ratios.append(a / b if b > 0 else np.nan)
    ratios = np.array(ratios, float)
    out["ratio_ci"] = [float(np.nanpercentile(ratios, 2.5)), float(np.nanpercentile(ratios, 97.5))]
    out["ratio_ci_undefined_draws"] = int(np.isnan(ratios).sum())
    lo, hi = out["ratio_ci"]
    out["H1"] = ("Supported" if (out["ratio"] or 0) >= 2 and lo > 1 else "Refuted" if hi < 2 else "Inconclusive")

    # H2: the embedding feature's contribution, paired over the same gene resamples
    p_noemb, _, _ = fit_predict(tr, te, EFFORT + COOC + TAX)
    ap_full, ap_noemb = average_precision_score(y, p_model), average_precision_score(y, p_noemb)
    out["auprc"] = {"full": round(float(ap_full), 6), "no_embedding": round(float(ap_noemb), 6),
                    "difference": round(float(ap_full - ap_noemb), 6)}
    rng2 = np.random.default_rng(SEED + 1)
    diffs = []
    for idx in boot_indices(te.gene.to_numpy(), rng2, B):
        if y[idx].sum() == 0:
            diffs.append(np.nan); continue
        diffs.append(average_precision_score(y[idx], p_model[idx]) - average_precision_score(y[idx], p_noemb[idx]))
    diffs = np.array(diffs, float)
    out["auprc"]["difference_ci"] = [float(np.nanpercentile(diffs, 2.5)), float(np.nanpercentile(diffs, 97.5))]
    dlo, dhi = out["auprc"]["difference_ci"]
    out["H2"] = ("Supported" if dlo > 0 else "Refuted" if dhi < 0.005 else "Inconclusive")
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out, indent=1, default=float))

    sec = {"precision_at_k": {}, "ablations": {}}
    for k in (50, 100, 500):
        sec["precision_at_k"][k] = {"model": precision_at(p_model, y, k), "null": precision_at(p_null, y, k)}
    sec["auprc_null"] = float(average_precision_score(y, p_null))
    for nm, feats in (("effort_only", EFFORT), ("no_taxonomy", EFFORT + COOC + EMB), ("no_cooccurrence", EFFORT + TAX + EMB),
                      ("no_embedding", EFFORT + COOC + TAX)):
        p, _, _ = fit_predict(tr, te, feats)
        sec["ablations"][nm] = {"precision_at_100": precision_at(p, y, k=100), "auprc": float(average_precision_score(y, p))}
    q = pd.qcut(pd.Series(p_model).rank(method="first"), 10, labels=False)
    sec["calibration_decile"] = pd.DataFrame({"q": q, "p": p_model, "y": y}).groupby("q").agg(
        mean_p=("p", "mean"), observed=("y", "mean"), n=("y", "size")).round(6).to_dict("index")
    (T / "secondary.json").write_text(json.dumps(sec, indent=1, default=float) + "\n")
    top = te.assign(p_model=p_model, p_null=p_null).nlargest(100, "p_model")[
        ["gene", "species", "p_model", "p_null", "y", "genus_count", "family_count", "jaccard_max", "emb_cos_max", "log_n_hor"]]
    top.to_csv(T / "top100.csv", index=False)
    print(json.dumps({k: v for k, v in sec.items() if k != "calibration_decile"}, indent=0, default=float))


if __name__ == "__main__":
    main()
