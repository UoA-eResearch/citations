#!/usr/bin/env python
"""EXPLORATORY (deviations.md D5): transparent keyword detectors, fixed before being run against outcomes.
K1 (narrow): explicit replication-failure language.
K2 (broad): K1 plus general doubt language (controversy, criticism, contradiction, mixed / inconsistent results).
A citing paper is flagged if any of its contexts matches. Reported: precision / recall against the analyst's 300
validation labels, and the plan's H1 and V1 AUCs (plus eligibility >= 1) with these flags in place of a classifier.
Replication papers listed in FLoRA or FReD are excluded from the citing sets (deviations.md D7).
Output: results/tables/keywords_validation.csv, results/tables/results_keywords.csv
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import BASE, PROC, TAB, auc_boot, covariates, incremental, outcomes, replication_dois, window_features  # noqa: E402

K1 = re.compile(r"(fail\w*|unable|could\s?n[o']t|did\s?n[o']t|not\s+been\s+able|have\s+not)\W+(?:\w+\W+){0,3}?(replicat|reproduc)"
                r"|non-?replicat|replication\s+failure|failed\s+replication|unsuccessful\s+(?:\w+\s+)?replicat|not\s+(?:been\s+)?replicat"
                r"|(replicat\w*|reproduc\w*)\W+(?:\w+\W+){0,4}?(fail|unsuccessful|did\s?n[o']t\s+hold|not\s+(?:been\s+)?(?:found|confirmed|supported))",
                re.I)
K2_EXTRA = re.compile(r"controvers|criticiz|criticis|questioned|called\s+into\s+question|challenged|contradict|inconsistent\s+(?:results|findings|evidence)"
                      r"|mixed\s+(?:results|findings|evidence)|conflicting\s+(?:results|findings|evidence)|questionable|flaw|confound", re.I)


def main():
    reps = replication_dois()
    ctx = pd.read_parquet(PROC / "contexts.parquet", columns=["ctx_id", "doi_o", "citing_id", "citing_doi", "year", "text"])
    ctx_all = ctx
    ctx = ctx[~ctx.citing_doi.isin(reps)]                                 # D7: replication papers excluded
    ctx["k1"] = ctx.text.str.contains(K1.pattern, flags=re.I, regex=True)
    ctx["k2"] = ctx.k1 | ctx.text.str.contains(K2_EXTRA.pattern, flags=re.I, regex=True)
    lab = pd.read_csv(PROC / "validation_labels.csv").merge(pd.read_parquet(PROC / "validation_key.parquet"), on="val_id")
    ctx_all = ctx_all.assign(k1=ctx_all.text.str.contains(K1.pattern, flags=re.I, regex=True))
    ctx_all["k2"] = ctx_all.k1 | ctx_all.text.str.contains(K2_EXTRA.pattern, flags=re.I, regex=True)
    v = lab.merge(ctx_all[["ctx_id", "k1", "k2"]].drop_duplicates("ctx_id"), on="ctx_id")
    rows = []
    for k in ("k1", "k2"):
        tp = int((v[k] & (v.label == "Negative")).sum())
        rows.append(dict(detector=k, flagged=int(v[k].sum()), true_negative=int((v.label == "Negative").sum()), tp=tp,
                         precision=tp / max(1, v[k].sum()), recall=tp / max(1, (v.label == "Negative").sum()),
                         share_of_all_contexts=float(ctx[k].mean())))
    pd.DataFrame(rows).to_csv(TAB / "keywords_validation.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    o = outcomes()
    cit = pd.read_parquet(PROC / "citing.parquet", columns=["doi_o", "citing_id", "citing_doi", "year"])
    cit = cit[~cit.citing_doi.isin(reps)].drop(columns="citing_doi")
    res = []
    for k in ("k1", "k2"):
        per = ctx.groupby(["doi_o", "citing_id"]).agg(year=("year", "first"), neg=(k, "max"), pos=(k, "size"),
                                                      n_ctx=(k, "size"), n_ctx_neg=(k, "sum")).reset_index()
        per["pos"] = False
        df = window_features(per, cit, o)
        df = df[df.outcome.isin(["failed", "successful"])]
        df["failed"] = (df.outcome == "failed").astype(int)
        pr = df[df.n_ctxpapers_pre >= 5]
        v1 = pr[pr.n_ctxpapers_post >= 5]
        est, lo, hi, n, nf = auc_boot(v1.failed.values, v1.neg_share_post.values)
        res.append(dict(detector=k, analysis="V1 post-replication share, primary originals with >= 5 post citing papers", auc=est,
                        lo=lo, hi=hi, n=n, n_failed=nf, share_flagged=float((v1.n_neg_post > 0).mean())))
        res.append(dict(detector=k, analysis="any flagged pre-replication citing paper: failed / successful originals",
                        auc=float((pr[pr.failed == 1].n_neg_pre > 0).mean()), lo=float((pr[pr.failed == 0].n_neg_pre > 0).mean()),
                        hi=np.nan, n=len(pr), n_failed=int(pr.failed.sum()), share_flagged=float((pr.n_neg_pre > 0).mean())))
        for label, col, ncol, mn in (("pre-replication window ending 2 years before", "neg_share_pre_m2", "n_ctxpapers_pre_m2", 5),
                                     ("H1 pre-replication share", "neg_share_pre", "n_ctxpapers_pre", 5),
                                     ("V1 post-replication share", "neg_share_post", "n_ctxpapers_post", 5),
                                     ("H1 pre-replication, any flagged citing paper", "n_neg_pre", "n_ctxpapers_pre", 5),
                                     ("V1 post-replication, any flagged citing paper", "n_neg_post", "n_ctxpapers_post", 5)):
            d = df[df[ncol] >= mn].copy()
            x = d[col].values if "any" not in label else (d[col].values > 0).astype(float)
            est, lo, hi, n, nf = auc_boot(d.failed.values, x)
            res.append(dict(detector=k, analysis=label, auc=est, lo=lo, hi=hi, n=n, n_failed=nf,
                            share_flagged=float((d[col] > 0).mean())))
        prim = covariates(df[df.n_ctxpapers_pre >= 5].copy())
        r2 = incremental(prim, BASE, "neg_share_pre")
        res.append(dict(detector=k, analysis="H2-style incremental CV AUC over baseline (delta)", auc=r2["delta"], lo=r2["lo"],
                        hi=r2["hi"], n=r2["n"], n_failed=r2["n_failed"], share_flagged=np.nan))
    r = pd.DataFrame(res)
    r.to_csv(TAB / "results_keywords.csv", index=False)
    print(r.round(3).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
