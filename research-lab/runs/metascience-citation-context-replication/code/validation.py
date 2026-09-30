#!/usr/bin/env python
"""Validation of the two classifiers on psychology-literature contexts (plan.md sec 3; deviations.md D3).

  validation.py draw    -> data/processed/validation_blind.csv (val_id, text only; shuffled) and validation_key.parquet
                           300 contexts from the C2-scored pool: 150 that C1 or C2 calls Negative, 150 others,
                           restricted to eligible originals (>= 5 pre-replication citing papers with contexts)
  validation.py score   -> reads data/processed/validation_labels.csv (val_id, label: Negative/Positive/Neutral, by the
                           analyst, written before the classifier outputs are looked at) and reports per-classifier
                           precision / recall / F1 for Negative-vs-rest, and the primary-classifier decision rule.
Output: results/tables/validation_metrics.csv, results/tables/validation_labels.csv (val_id, ctx_id, labels; no text)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_contexts import windows  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PROC, TAB = RUN / "data" / "processed", RUN / "results" / "tables"


def draw():
    ctx = pd.read_parquet(PROC / "contexts.parquet")
    pool = pd.read_parquet(PROC / "scores_c2_pool.parquet").rename(columns={"label": "c2"}).drop_duplicates("ctx_id")
    c1 = pd.read_parquet(PROC / "scores_c1.parquet", columns=["ctx_id", "label"]).rename(columns={"label": "c1"})
    d = pool.merge(c1, on="ctx_id").merge(ctx[["ctx_id", "doi_o", "citing_id", "year", "text"]].drop_duplicates("ctx_id"), on="ctx_id")
    w = windows()
    pre = ctx.merge(w, left_on="doi_o", right_index=True)
    pre = pre[(pre.year >= pre.year_o) & (pre.year < pre.yr1)].groupby("doi_o").citing_id.nunique()
    d = d[d.doi_o.isin(pre[pre >= 5].index)]
    d = d[d.text.str.len().between(20, 1500)]
    neg = d[(d.c1 == "Negative") | (d.c2 == "Negative")]
    oth = d[~d.ctx_id.isin(neg.ctx_id)]
    s = pd.concat([neg.sample(150, random_state=21).assign(stratum="either negative"),
                   oth.sample(150, random_state=21).assign(stratum="other")])
    s = s.sample(frac=1, random_state=22).reset_index(drop=True)
    s["val_id"] = [f"v{i:03d}" for i in range(len(s))]
    s[["val_id", "text"]].to_csv(PROC / "validation_blind.csv", index=False)
    s[["val_id", "ctx_id", "doi_o", "stratum", "c1", "c2"]].to_parquet(PROC / "validation_key.parquet", index=False)
    pd.Series({"either negative": len(neg), "other": len(oth)}).to_json(PROC / "validation_pool_sizes.json")
    print("drawn", len(s), "from pool", len(d), "| stratum sizes in pool: either negative", len(neg), "other", len(oth))


def score():
    lab = pd.read_csv(PROC / "validation_labels.csv")
    key = pd.read_parquet(PROC / "validation_key.parquet")
    d = key.merge(lab, on="val_id")
    assert len(d) == 300 and d.label.isin(["Negative", "Positive", "Neutral"]).all()
    # the sample over-represents classifier negatives; weights restore each stratum's share of the pool (supplementary)
    ps = pd.read_json(PROC / "validation_pool_sizes.json", typ="series")
    d["w"] = d.stratum.map({"either negative": ps["either negative"] / 150, "other": ps["other"] / 150})
    rows = []
    y = (d.label == "Negative").values
    for clf in ("c1", "c2"):
        p = (d[clf] == "Negative").values
        pr, rc, f1, _ = precision_recall_fscore_support(y, p, average="binary", zero_division=0)
        wpr, wrc, wf1, _ = precision_recall_fscore_support(y, p, average="binary", zero_division=0, sample_weight=d.w.values)
        rows.append(dict(classifier=clf, precision=pr, recall=rc, f1=f1, weighted_precision=wpr, weighted_recall=wrc,
                         weighted_f1=wf1, n=len(d), n_true_negative=int(y.sum()), n_predicted_negative=int(p.sum()),
                         agreement_3class=float((d[clf] == d.label).mean())))
    m = pd.DataFrame(rows)
    # D7: bootstrap intervals (resampling the 300 within strata) and P(F1 >= 0.5)
    rng = np.random.default_rng(3)
    strata = [np.where(d.stratum.values == st)[0] for st in ("either negative", "other")]
    for clf in ("c1", "c2"):
        p = (d[clf] == "Negative").values
        bs = []
        for _ in range(4000):
            i = np.concatenate([idx[rng.integers(0, len(idx), len(idx))] for idx in strata])
            pr, rc, f1, _ = precision_recall_fscore_support(y[i], p[i], average="binary", zero_division=0)
            bs.append((pr, rc, f1))
        bs = np.array(bs)
        k = m.classifier == clf
        for j, name in enumerate(("precision", "recall", "f1")):
            m.loc[k, name + "_lo"], m.loc[k, name + "_hi"] = np.percentile(bs[:, j], [2.5, 97.5])
        m.loc[k, "p_f1_ge_0.5"] = float((bs[:, 2] >= 0.5).mean())
    # prevalence of true doubt in the pool: Wilson intervals per stratum, combined with the strata's pool shares
    from statsmodels.stats.proportion import proportion_confint
    share = {k: ps[k] / (ps["either negative"] + ps["other"]) for k in ("either negative", "other")}
    est = lo = hi = 0.0
    for st in ("either negative", "other"):
        g = d[d.stratum == st]
        x, n = int((g.label == "Negative").sum()), len(g)
        l, h = proportion_confint(x, n, method="wilson")
        est, lo, hi = est + share[st] * x / n, lo + share[st] * l, hi + share[st] * h
    pd.DataFrame([dict(quantity="share of pool contexts expressing doubt", est=est, lo=lo, hi=hi,
                       pool_contexts=int(ps["either negative"] + ps["other"]))]).to_csv(TAB / "validation_prevalence.csv", index=False)
    print(f"prevalence of doubt in the pool: {est:.4f} [{lo:.4f}, {hi:.4f}] (conservative sum of stratum Wilson bounds)")
    best = m.sort_values("f1", ascending=False).iloc[0]
    m["primary"] = (m.classifier == best.classifier) & (best.f1 >= 0.5)
    m.to_csv(TAB / "validation_metrics.csv", index=False)
    d[["val_id", "ctx_id", "stratum", "label", "c1", "c2"]].to_csv(TAB / "validation_labels.csv", index=False)
    print(m.round(3).to_string(index=False))
    print(pd.crosstab(d.label, [d.c1.rename("C1")]), "\n", pd.crosstab(d.label, [d.c2.rename("C2")]))
    print("by stratum:\n", d.groupby("stratum").apply(lambda g: pd.Series(dict(true_neg=(g.label == "Negative").mean(),
                                                                                 c1_neg=(g.c1 == "Negative").mean(),
                                                                                 c2_neg=(g.c2 == "Negative").mean()))).round(3))


if __name__ == "__main__":
    {"draw": draw, "score": score}[sys.argv[1]]()
