#!/usr/bin/env python
"""Hypotheses H1-H3, positive control V1 and robustness (plan.md sec 2, 4-6; deviations.md D2-D3).

Usage: analysis.py CLASSIFIER [capped] [dry]
  CLASSIFIER: c1 (SciBERT on all contexts) or c2 (local LLM on capped analysis contexts)
  capped:     restricts C1 to the same capped citing papers as C2 (like-for-like comparison)
  dry:        code test with outcomes randomly permuted (no real result is computed)
Output: results/tables/results_{clf}.csv (one row per analysis), results/tables/originals_{clf}.parquet (per-original
features and outcome, no context text)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_contexts import c2_selection  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW, PROC, TAB = RUN / "data" / "raw", RUN / "data" / "processed", RUN / "results" / "tables"
PSYCH = {"Psychology", "Neuroscience"}
ECON = {"Economics, Econometrics and Finance", "Business, Management and Accounting", "Decision Sciences"}


# ------------------------------------------------------------------------------------------------ outcome
def replication_dois() -> set:
    """DOIs of every replication paper in FLoRA and FReD (deviations.md D7): such papers are dropped from the citing
    sets, because a replication citing its own original (often dated a year early by its online-first date) would
    otherwise leak the outcome into the pre-replication window."""
    f = pd.read_csv(RAW / "flora_filtered.csv", low_memory=False)
    fr = pd.read_excel(RAW / "FReD.xlsx")
    d = pd.concat([f.doi_r, fr.doi_r]).dropna().astype(str).str.strip().str.lower()
    return set(d[d.str.startswith("10.")])


def outcomes() -> pd.DataFrame:
    f = pd.read_csv(RAW / "flora_filtered.csv", low_memory=False)
    f = f[(f.type == "replication") & f.doi_o.notna() & f.year_r.notna()].assign(doi_o=lambda d: d.doi_o.str.strip().str.lower())
    rows = []
    for doi, g in f.groupby("doi_o"):
        yr1 = g.year_r.min()
        codes = g[g.year_r == yr1].outcome.fillna("other").map(
            lambda o: o if o in ("failed", "successful", "mixed") else "other").value_counts()
        top = codes[codes == codes.max()].index.tolist()
        rows.append(dict(doi_o=doi, yr1=int(yr1), year_o=g.year_o.min(), outcome=top[0] if len(top) == 1 else "mixed",
                         n_replications=len(g), source1=";".join(sorted(g[g.year_r == yr1].source.astype(str).unique()))))
    o = pd.DataFrame(rows)
    return o[o.year_o.notna() & (o.year_o < o.yr1)]


# ------------------------------------------------------------------------------------------------ features
def citing_labels(clf: str, capped: bool) -> pd.DataFrame:
    ctx = pd.read_parquet(PROC / "contexts.parquet", columns=["ctx_id", "doi_o", "citing_id", "citing_doi", "year", "text"])
    if clf == "c2" or capped:
        ctx = c2_selection(ctx.drop(columns="citing_doi")).merge(ctx[["ctx_id", "citing_doi"]], on="ctx_id")
    ctx = ctx[~ctx.citing_doi.isin(replication_dois())]
    sc = pd.read_parquet(PROC / ("scores_c1.parquet" if clf == "c1" else "scores_c2_analysis.parquet"), columns=["ctx_id", "label"])
    ctx = ctx.drop(columns="text").merge(sc.drop_duplicates("ctx_id"), on="ctx_id", how="inner")
    ctx["neg"], ctx["pos"] = ctx.label.eq("Negative"), ctx.label.eq("Positive")
    per = ctx.groupby(["doi_o", "citing_id"]).agg(year=("year", "first"), neg=("neg", "max"), pos=("pos", "max"),
                                                  n_ctx=("neg", "size"), n_ctx_neg=("neg", "sum"))
    return per.reset_index()


def window_features(per: pd.DataFrame, cit: pd.DataFrame, o: pd.DataFrame) -> pd.DataFrame:
    """Per original and window: citing papers (all, with contexts), negative / positive citing papers and shares."""
    wins = {"pre": lambda d: (d.year >= d.year_o) & (d.year < d.yr1),
            "first3": lambda d: (d.year >= d.year_o) & (d.year <= d.year_o + 3) & (d.year < d.yr1),
            "post": lambda d: d.year >= d.yr1 + 1,
            "pre_m2": lambda d: (d.year >= d.year_o) & (d.year <= d.yr1 - 2)}
    p = per.merge(o[["doi_o", "yr1", "year_o"]], on="doi_o")
    c = cit.merge(o[["doi_o", "yr1", "year_o"]], on="doi_o")
    out = o.set_index("doi_o").copy()
    for w, sel in wins.items():
        pw, cw = p[sel(p)], c[sel(c)]
        g = pw.groupby("doi_o").agg(n=("neg", "size"), neg=("neg", "sum"), pos=("pos", "sum"),
                                    ctx=("n_ctx", "sum"), ctx_neg=("n_ctx_neg", "sum"))
        out[f"n_ctxpapers_{w}"] = g.n.reindex(out.index).fillna(0)
        out[f"n_neg_{w}"] = g.neg.reindex(out.index).fillna(0)
        out[f"neg_share_{w}"] = out[f"n_neg_{w}"] / out[f"n_ctxpapers_{w}"].replace(0, np.nan)
        out[f"pos_share_{w}"] = g.pos.reindex(out.index) / out[f"n_ctxpapers_{w}"].replace(0, np.nan)
        out[f"neg_ctx_share_{w}"] = g.ctx_neg.reindex(out.index) / g.ctx.reindex(out.index)
        out[f"n_citing_{w}"] = cw.groupby("doi_o").size().reindex(out.index).fillna(0)
        out[f"neg_per100_{w}"] = 100 * out[f"n_neg_{w}"] / out[f"n_citing_{w}"].replace(0, np.nan)
    return out.reset_index()


def covariates(df: pd.DataFrame) -> pd.DataFrame:
    oa = pd.read_parquet(PROC / "openalex_originals.parquet")
    df = df.merge(oa[["doi_o", "field", "venue_citedness"]], on="doi_o", how="left")
    df["psych"] = df.field.isin(PSYCH).astype(float)
    df["econ"] = df.field.isin(ECON).astype(float)
    v = np.log(df.venue_citedness + 0.1)
    df["venue_missing"] = v.isna().astype(float)
    df["log_venue"] = v.fillna(v.median())
    df["log_citing_pre"] = np.log1p(df.n_citing_pre)
    df["years_to_rep"] = df.yr1 - df.year_o
    fred = pd.read_excel(RAW / "FReD.xlsx").assign(doi_o=lambda d: d.doi_o.astype(str).str.strip().str.lower())
    fs = fred.groupby("doi_o").agg(n_o=("n_o", "median"), p_o=("pval_value_o", "median"))
    df = df.merge(fs, left_on="doi_o", right_index=True, how="left")
    df["in_fred"] = df.doi_o.isin(fs.index)
    df["log_n_o"] = np.log(df.n_o)
    df["p_cat"] = pd.cut(df.p_o, [-1, 0.001, 0.01, 0.05, 2], labels=["<.001", "<.01", "<.05", ">=.05"]).astype(str)
    df.loc[df.p_o.isna(), "p_cat"] = "not reported"
    return df


BASE = ["log_citing_pre", "year_o", "psych", "econ", "log_venue", "venue_missing", "years_to_rep"]


# ------------------------------------------------------------------------------------------------ statistics
def auc_boot(y, x, nboot=2000, seed=0):
    ok = np.isfinite(x)
    y, x = y[ok], x[ok]
    est = roc_auc_score(y, x)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(nboot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            bs.append(roc_auc_score(y[i], x[i]))
    return est, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), int(len(y)), int(y.sum())


def cv_auc(X, y, groups, n_splits, n_rep, seed):
    aucs = []
    for r in range(n_rep):
        oof = np.zeros(len(y))
        for tr, te in StratifiedGroupKFold(n_splits, shuffle=True, random_state=seed + r).split(X, y, groups):
            m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(X[tr], y[tr])
            oof[te] = m.predict_proba(X[te])[:, 1]
        aucs.append(roc_auc_score(y, oof))
    return float(np.mean(aucs))


def incremental(df, base_cols, add_col, nboot=200, seed=0):
    d = df.dropna(subset=base_cols + [add_col])
    y = d.failed.values
    Xb, Xf = d[base_cols].values.astype(float), d[base_cols + [add_col]].values.astype(float)
    g = np.arange(len(d))
    b, f = cv_auc(Xb, y, g, 10, 20, seed), cv_auc(Xf, y, g, 10, 20, seed)
    rng = np.random.default_rng(seed + 1)
    bs = []
    for k in range(nboot):
        i = rng.integers(0, len(d), len(d))
        if y[i].sum() < 10 or (1 - y[i]).sum() < 10:
            continue
        bs.append(cv_auc(Xf[i], y[i], i, 5, 2, 100 + k) - cv_auc(Xb[i], y[i], i, 5, 2, 100 + k))
    return dict(auc_base=b, auc_full=f, delta=f - b, lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)),
                n=len(d), n_failed=int(y.sum()))


def verdict_h1(est, lo, hi):
    return "supported" if (est >= 0.65 and lo > 0.5) else ("contradicted" if hi < 0.65 else "inconclusive")


def verdict_h2(r):
    return "supported" if (r["delta"] >= 0.05 and r["lo"] > 0) else ("contradicted" if r["hi"] < 0.05 else "inconclusive")


# ------------------------------------------------------------------------------------------------ main
def main():
    clf = sys.argv[1] if len(sys.argv) > 1 else "c1"
    capped = "capped" in sys.argv[2:]
    dry = "dry" in sys.argv[2:]
    tag = clf + ("_capped" if capped else "") + ("_DRYRUN" if dry else "")
    o = outcomes()
    cit = pd.read_parquet(PROC / "citing.parquet", columns=["doi_o", "citing_id", "citing_doi", "year"])
    cit = cit[~cit.citing_doi.isin(replication_dois())].drop(columns="citing_doi")
    df = covariates(window_features(citing_labels(clf, capped), cit, o))
    hs = pd.read_csv(TAB / "harvest_summary.csv")
    df["truncated"] = df.doi_o.isin(hs[(hs.status == 400) & (hs.n_citing > 0)].doi_o)
    df.to_parquet(TAB / f"originals_{tag}.parquet", index=False)
    rows = []

    def h1(label, d, col="neg_share_pre", min_n=5, ncol="n_ctxpapers_pre"):
        d = d[d.outcome.isin(["failed", "successful"]) & (d[ncol] >= min_n)] if "mixed as failed" not in label else d
        est, lo, hi, n, nf = auc_boot(d.failed.values, d[col].values)
        rows.append(dict(analysis=label, predictor=col, stat="AUC", est=est, lo=lo, hi=hi, n=n, n_failed=nf,
                         verdict=verdict_h1(est, lo, hi) if label.startswith("H1") else ""))
        return d

    if dry:                                                              # code test only: outcomes permuted at random
        df["outcome"] = np.random.default_rng(99).permutation(df.outcome.values)
    df["failed"] = (df.outcome == "failed").astype(int)
    prim = h1("H1 primary: pre-replication negative share", df)
    v1 = prim[prim.n_ctxpapers_post >= 5]
    est, lo, hi, n, nf = auc_boot(v1.failed.values, v1.neg_share_post.values)
    rows.append(dict(analysis="positive control V1: post-replication share, primary originals with >= 5 post citing papers",
                     predictor="neg_share_post", stat="AUC", est=est, lo=lo, hi=hi, n=n, n_failed=nf,
                     verdict="passes" if lo > 0.5 else "fails"))
    v1_fail = lo <= 0.5
    h1("positive control V1 (all originals with >= 5 post-replication citing papers)", df, "neg_share_post", 5, "n_ctxpapers_post")
    h1("excluding originals whose first replication came from OpenAlex-sourced FLoRA entries",
       df[~df.source1.str.contains("openalex", na=False)])
    h1("excluding the 6 originals with truncated harvests", df[~df.truncated])
    h1("first 3 years after publication", df, "neg_share_first3", 5, "n_ctxpapers_first3")
    h1("window ending 2 years before replication", df, "neg_share_pre_m2", 5, "n_ctxpapers_pre_m2")
    h1("positive share (higher = success expected; AUC < 0.5 if so)", df, "pos_share_pre")
    h1("negative citing papers per 100 citing papers", df, "neg_per100_pre", 5)
    h1("context-level negative share", df, "neg_ctx_share_pre")
    h1("eligibility >= 1 citing paper", df, min_n=1)
    h1("eligibility >= 10 citing papers", df, min_n=10)
    h1("psychology originals only", df[df.psych == 1])
    h1("originals from 2000 onward", df[df.year_o >= 2000])
    mf = df[df.outcome.isin(["failed", "successful", "mixed"]) & (df.n_ctxpapers_pre >= 5)].copy()
    mf["failed"] = mf.outcome.isin(["failed", "mixed"]).astype(int)
    h1("mixed as failed", mf)
    # H2 / H3
    r2 = incremental(prim, BASE, "neg_share_pre")
    rows.append(dict(analysis="H2: incremental CV AUC over baseline", predictor="neg_share_pre", stat="delta AUC",
                     est=r2["delta"], lo=r2["lo"], hi=r2["hi"], n=r2["n"], n_failed=r2["n_failed"], verdict=verdict_h2(r2),
                     auc_base=r2["auc_base"], auc_full=r2["auc_full"]))
    fr = prim[prim.in_fred].copy()
    for cat in ("<.001", "<.01", "<.05", ">=.05"):
        fr[f"p_{cat}"] = (fr.p_cat == cat).astype(float)
    base3 = BASE + ["log_n_o"] + [f"p_{c}" for c in ("<.001", "<.01", "<.05", ">=.05")]
    if len(fr) >= 60:
        r3 = incremental(fr, base3, "neg_share_pre")
        rows.append(dict(analysis="H3: incremental CV AUC over baseline + original n and p (FReD subset)", predictor="neg_share_pre",
                         stat="delta AUC", est=r3["delta"], lo=r3["lo"], hi=r3["hi"], n=r3["n"], n_failed=r3["n_failed"],
                         verdict=verdict_h2(r3), auc_base=r3["auc_base"], auc_full=r3["auc_full"]))
    out = pd.DataFrame(rows)
    if v1_fail:                                                          # plan sec 5: a failed V1 makes a null uninformative
        for pre in ("H1", "H2", "H3"):
            m = out.analysis.str.startswith(pre)
            out.loc[m, "verdict"] = "uninformative (positive control failed; mechanical rule: " + out.loc[m, "verdict"] + ")"
    out.to_csv(TAB / f"results_{tag}.csv", index=False)
    pd.set_option("display.width", 220)
    print(out[["analysis", "stat", "est", "lo", "hi", "n", "n_failed", "verdict"]].round(3).to_string(index=False))
    print("outcome counts among originals with year_o < first replication:", o.outcome.value_counts().to_dict(),
          "| truncated originals in primary:", int(prim.truncated.sum()))
    print("primary sample: originals", len(prim), "failed", int(prim.failed.sum()), "| median pre-window citing papers with contexts",
          prim.n_ctxpapers_pre.median(), "| share with any negative", round(float((prim.n_neg_pre > 0).mean()), 3))


if __name__ == "__main__":
    sys.exit(main())
