"""POST HOC (after the primary result): why the trained model ranks worse than the sampling-effort null at the top.

  1. Ties: how many candidates share the top scores (an argsort artefact would make precision@100 meaningless).
  2. The model's top 100: what they look like, and whether they were already candidates one period earlier.
  3. Survivorship: test candidates split into those that were also candidates at the 2019 cutoff ("carried over",
     and so had three years in which they did not emerge) and those newly eligible. Precision and base rate in each.
  4. Within-period skill: the same model trained and evaluated inside the test task by gene-grouped 2-fold CV, to
     separate "the features carry no signal" from "the signal does not transfer across periods".

  posthoc.py -> results/tables/posthoc.json, results/tables/top100_annotated.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

sys.path.insert(0, str(Path(__file__).resolve().parent))      # python -I drops the script's own directory
import analyse as A  # noqa: E402

D, T = A.D, A.T


def main():
    tr = pd.read_parquet(D / "task_train.parquet")
    te = pd.read_parquet(D / "task_test.parquet")
    y = te.y.to_numpy()
    p_model, _, _ = A.fit_predict(tr, te, A.FULL)
    p_null = te.null_p.to_numpy()
    out = {}
    out["score_saturation"] = {"top100_min_score": float(np.sort(p_model)[-100:].min()),
                               "candidates_scored_above_0.999": int((p_model > 0.999).sum())}

    # the H1 statistic for the model without the embedding (the H2 comparison model, a preregistered ablation)
    p_noemb, _, _ = A.fit_predict(tr, te, A.EFFORT + A.COOC + A.TAX)
    rng = np.random.default_rng(A.SEED + 7)
    pn100, pe100 = A.precision_at(p_null, y, 100), A.precision_at(p_noemb, y, 100)
    ratios = []
    for idx in A.boot_indices(te.gene.to_numpy(), rng, A.B):
        a_, b_ = A.precision_at(p_noemb[idx], y[idx], 100), A.precision_at(p_null[idx], y[idx], 100)
        ratios.append(a_ / b_ if b_ > 0 else np.nan)
    ratios = np.array(ratios, float)
    out["no_embedding_vs_null"] = {"precision_at_100": pe100, "null_precision_at_100": pn100,
                                   "ratio": round(pe100 / pn100, 3) if pn100 else None,
                                   "ratio_ci": [float(np.nanpercentile(ratios, 2.5)), float(np.nanpercentile(ratios, 97.5))],
                                   "would_meet_H1_rule": bool(pe100 / pn100 >= 2 and np.nanpercentile(ratios, 2.5) > 1) if pn100 else None}

    s = np.sort(p_model)[::-1]
    out["ties"] = {"distinct_scores_in_top_1000": int(len(np.unique(s[:1000]))),
                   "candidates_sharing_the_top_score": int((p_model == s[0]).sum()),
                   "top_score": float(s[0]), "score_at_rank_100": float(s[99])}

    carried = set(zip(tr.gene.astype(str), tr.species))
    key = list(zip(te.gene.astype(str), te.species))
    is_carried = np.array([k in carried for k in key])
    for nm, m in (("carried_over_from_2019", is_carried), ("newly_eligible", ~is_carried)):
        out[nm] = {"candidates": int(m.sum()), "positives": int(y[m].sum()), "base_rate": round(float(y[m].mean()), 6),
                   "model_precision_at_100": A.precision_at(p_model[m], y[m], 100),
                   "null_precision_at_100": A.precision_at(p_null[m], y[m], 100),
                   "model_auprc": float(average_precision_score(y[m], p_model[m])) if y[m].sum() else None,
                   "null_auprc": float(average_precision_score(y[m], p_null[m])) if y[m].sum() else None}
    top = np.argsort(-p_model, kind="stable")[:100]
    out["top100_share_carried_over"] = round(float(is_carried[top].mean()), 3)
    nulltop = np.argsort(-p_null, kind="stable")[:100]
    out["null_top100_share_carried_over"] = round(float(is_carried[nulltop].mean()), 3)

    # within-period skill on the test task itself (not a forecast: it uses the horizon's own labels)
    g = te.gene.astype(str).to_numpy()
    half = (pd.factorize(g)[0] % 2) == 0
    preds = np.zeros(len(te))
    for m in (half, ~half):
        mdl = A.HistGradientBoostingClassifier(max_iter=300, early_stopping=False, random_state=A.SEED,
                                               max_leaf_nodes=63, learning_rate=0.05)
        mdl.fit(te.loc[m, A.FULL], te.y[m])
        preds[~m] = mdl.predict_proba(te.loc[~m, A.FULL])[:, 1]
    out["within_test_period_cv"] = {"precision_at_100": A.precision_at(preds, y, 100),
                                    "auprc": float(average_precision_score(y, preds))}
    (T / "posthoc.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out, indent=1, default=float))
    te.assign(p_model=p_model, p_null=p_null, carried_over=is_carried).iloc[top][
        ["gene", "species", "p_model", "p_null", "y", "carried_over", "log_n_hor", "genus_count", "jaccard_max", "emb_cos_max"]
    ].to_csv(T / "top100_annotated.csv", index=False)


if __name__ == "__main__":
    main()
