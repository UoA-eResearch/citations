"""D3: fixes after the independent review (verdict: fix first). See deviations.md D3.

1. The preregistered null, 1 - Binomial(<=1; n_s,horizon, f_g), ranked by -log P(<=1) (binom.logcdf; D3b - logsf of
   P(>=2) still saturated at 0.0). In double
   precision the probability saturates at 1.0 for thousands of candidates, so precision@100 depended on row order.
   The log-space value is the same quantity without saturation. The old null's expectation under random tie order is
   also reported.
2. Seed stability: the preregistered hyperparameters (primary.json) refitted with ten seeds (the preregistered seed
   first), full model and without the embedding, on the primary and first-appearance tasks.
   Even in log space, genes with equal counts tie within a species, so every precision@k here is the exact
   expectation under random order within ties (topk).
3. H1 recomputed with the log-space null at the preregistered seed. Bootstrap draws where the model scores above zero
   and the null scores zero count as an infinite ratio (they favour the model); 0/0 draws are dropped.
4. Secondary analyses the plan promised: recall at matched list sizes, the >=3-isolate variant, and the D1
   sensitivity with all genes (KEEP_ALL_GENES).
5. The null's calibration by decile (G3).

  d3_fixes.py -> results/tables/d3.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyse as A  # noqa: E402

HP = json.loads((A.T / "primary.json").read_text())["hyperparameters"]
SEEDS = [A.SEED] + list(range(1, 10))
KS, RK = (50, 100, 500), (100, 500, 1000, 5000)


def log_null(te, C, H):
    iso = pd.read_parquet(A.D / "isolates.parquet", columns=["biosample", "year", "species", "genes"]).drop_duplicates("biosample")
    pre = iso[iso.year <= C]
    f = pd.Series([g for gs in pre.genes for g in gs]).value_counts() / len(pre)
    nh = iso[(iso.year > C) & (iso.year <= H)].species.value_counts()
    n = te.species.map(nh).fillna(0).to_numpy(); fg = te.gene.astype(str).map(f).fillna(0).to_numpy()
    # D3b (confirmation finding C1): log P(>=2) = logsf rounds to exactly 0.0 wherever P(>=2) is within 1e-16 of 1,
    # the same saturation as before. The same order, without saturation, is P(<=1) ascending: score = -log P(<=1),
    # which binom.logcdf computes accurately deep into the tail.
    sc = -binom.logcdf(1, n, fg)
    fin = np.isfinite(sc)
    return np.where(fin, sc, sc[fin].max() + 1.0)


def topk(score, y, k, rng=None):
    """Precision@k. Without rng: the exact expectation under random order within tied scores (all of a tied group
    straddling rank k contributes its positive share to the remaining slots). With rng: one random tie order."""
    if rng is None:
        o = np.argsort(-score, kind="stable"); kth = score[o[k - 1]]
        above = score > kth; tied = score == kth
        n_above = int(above.sum()); slots = k - n_above
        return float((y[above].sum() + slots * y[tied].mean()) / k)
    o = np.lexsort((rng.random(len(score)), -score))          # random order within ties
    return float(y[o[:k]].mean())


def recall(score, y, k):
    return float(y[np.argsort(-score, kind="stable")[:k]].sum() / max(y.sum(), 1))


def fit(tr, te, feats, seed):
    m = HistGradientBoostingClassifier(max_iter=300, early_stopping=False, random_state=seed, **HP)
    m.fit(tr[feats], tr.y)
    return m.predict_proba(te[feats])[:, 1]


def metrics(p, y):
    return {**{f"p@{k}": topk(p, y, k) for k in KS}, "auprc": float(average_precision_score(y, p)), **{f"recall@{k}": recall(p, y, k) for k in RK}}


def main():
    out = {"hyperparameters": HP, "seeds": SEEDS}
    rng = np.random.default_rng(A.SEED)
    for task, (trn, ten) in {"primary": ("train", "test"), "first_appearance": ("train_any", "test_any"),
                             "three_isolates": ("train_3", "test_3"), "all_genes": ("train_allgenes", "test_allgenes")}.items():
        f_tr, f_te = A.D / f"task_{trn}.parquet", A.D / f"task_{ten}.parquet"
        if not (f_tr.exists() and f_te.exists()):
            out[task] = "task table missing"; continue
        tr, te = pd.read_parquet(f_tr), pd.read_parquet(f_te)
        y = te.y.to_numpy(); ln = log_null(te, 2022, 2025)
        old = te.null_p.to_numpy()
        r = {"candidates": len(te), "positives": int(y.sum()), "null_log": metrics(ln, y),
             "null_old_saturated_at_1": int((old >= 1.0).sum()),
             "null_old_p@100_row_order": float(y[np.argsort(-old, kind="stable")[:100]].mean())}
        tie = [topk(old, y, 100, rng) for _ in range(1000)]
        r["null_log_p@100_row_order"] = float(y[np.argsort(-ln, kind="stable")[:100]].mean())
        r["null_old_p@100_expected"] = topk(old, y, 100)
        r["null_old_p@100_random_ties"] = {"mean": float(np.mean(tie)), "q025": float(np.quantile(tie, 0.025)), "q975": float(np.quantile(tie, 0.975))}
        seeds = SEEDS if task in ("primary", "first_appearance") else SEEDS[:1]
        runs = []
        for s in seeds:
            pf = fit(tr, te, A.FULL, s); pn = fit(tr, te, A.EFFORT + A.COOC + A.TAX, s)
            runs.append({"seed": s, "full": metrics(pf, y), "no_embedding": metrics(pn, y),
                         "auprc_diff": float(average_precision_score(y, pf) - average_precision_score(y, pn))})
            if task == "primary" and s == A.SEED:
                p_pre = pf
            print(task, s, runs[-1]["full"]["p@100"], runs[-1]["no_embedding"]["p@100"], flush=True)
        r["runs"] = runs
        r["full_p@100_by_seed"] = [x["full"]["p@100"] for x in runs]
        r["no_embedding_p@100_by_seed"] = [x["no_embedding"]["p@100"] for x in runs]
        r["auprc_diff_by_seed"] = [x["auprc_diff"] for x in runs]
        out[task] = r
        if task == "primary":
            # H1 with the log-space null at the preregistered seed
            pm, pn0 = topk(p_pre, y, 100), topk(ln, y, 100)
            rb = np.random.default_rng(A.SEED); ratios = []
            for idx in A.boot_indices(te.gene.to_numpy(), rb, A.B):
                a, b = topk(p_pre[idx], y[idx], 100), topk(ln[idx], y[idx], 100)
                ratios.append(np.inf if (b == 0 and a > 0) else (np.nan if b == 0 else a / b))
            ratios = np.array(ratios, float); lo, hi = np.nanpercentile(ratios, [2.5, 97.5])
            ratio = pm / pn0 if pn0 > 0 else None
            out["H1_d3"] = {"model_p@100": pm, "null_log_p@100": pn0, "ratio": ratio, "ci": [float(lo), float(hi)],
                            "draws_0_over_0_dropped": int(np.isnan(ratios).sum()), "draws_model_over_zero": int(np.isinf(ratios).sum()),
                            "verdict": "Supported" if (ratio or 0) >= 2 and lo > 1 else "Refuted" if hi < 2 else "Inconclusive",
                            "ratio_by_seed": [x / pn0 if pn0 > 0 else None for x in r["full_p@100_by_seed"]]}
            # G3: null calibration by decile
            cal = {}
            for nm, sc in (("old", old), ("exact", -np.expm1(-ln))):
                q = pd.qcut(pd.Series(sc).rank(method="first"), 10, labels=False)
                cal[nm] = pd.DataFrame({"q": q, "p": sc, "y": y}).groupby("q").agg(mean_p=("p", "mean"), observed=("y", "mean")).round(5).to_dict("index")
            out["null_calibration"] = cal
    (A.T / "d3.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out.get("H1_d3", {}), indent=1, default=float))


if __name__ == "__main__":
    main()
