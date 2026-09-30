#!/usr/bin/env python
"""EXPLORATORY (deviations.md D8, after independent review): is the H2 rise a within-gene change or a change in which
genes get newly classified?

For the pooled >= +3 interval of each tool, pre vs post window as in H2:
  raw          the preregistered H2 ratio (all variants);
  common       restricted to genes with labelled variants of both classes in both windows;
  standardised post within-gene class rates, re-weighted to the pre window's gene composition (direct
               standardisation, separately for pathogenic and benign labels; genes without post labels of a class are
               dropped from that class's weights).
Gene-cluster bootstrap (1,000) for the log ratios. Also counts of benign labels in the >= +3 interval per window, and
the genes contributing most post-window benign labels that had none before.
Output: results/tables/explore_gene_standardised.csv, results/tables/explore_new_benign_genes.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

TAB = Path(__file__).resolve().parents[1] / "results" / "tables"
WIN = {"revel": ([2021, 2022], [2024, 2025, 2026]), "am": ([2021, 2022, 2023], [2025, 2026]),
       "esm1b": ([2021, 2022], [2024, 2025, 2026])}


def gene_table(d, tool):
    d = d.dropna(subset=[tool])
    hi = d[f"pts_{tool}"] >= 3
    g = d.assign(hi=hi).groupby(["gene", "label"]).agg(n=("hi", "size"), k=("hi", "sum")).unstack("label", fill_value=0)
    g.columns = [f"{a}_{b}" for a, b in g.columns]
    for c in ("n_P", "n_B", "k_P", "k_B"):
        if c not in g:
            g[c] = 0
    return g


def lr_raw(t):
    return (t.k_P.sum() / t.n_P.sum()) / (t.k_B.sum() / t.n_B.sum())


def lr_std(pre, post):
    """post within-gene rates, weighted by the pre gene composition (per class)."""
    out = []
    for c in ("P", "B"):
        genes = pre.index[(pre[f"n_{c}"] > 0)].intersection(post.index[post[f"n_{c}"] > 0])
        w = pre.loc[genes, f"n_{c}"]
        r = post.loc[genes, f"k_{c}"] / post.loc[genes, f"n_{c}"]
        out.append(float((w * r).sum() / w.sum()))
    return out[0] / out[1]


def stats(pre, post):
    common = pre.index[(pre.n_P > 0) & (pre.n_B > 0)].intersection(post.index[(post.n_P > 0) & (post.n_B > 0)])
    with np.errstate(divide="ignore", invalid="ignore"):
        return (np.log(lr_raw(post)) - np.log(lr_raw(pre)),
                np.log(lr_raw(post.loc[common])) - np.log(lr_raw(pre.loc[common])),
                np.log(lr_std(pre, post)) - np.log(lr_raw(pre)))


def main():
    df = load()
    df = df[df.primary_new]
    rows = []
    for tool, (pw, qw) in WIN.items():
        pre = gene_table(df[df.year.isin(pw)], tool)
        post = gene_table(df[df.year.isin(qw)], tool)
        genes = pre.index.union(post.index)
        pre, post = pre.reindex(genes, fill_value=0), post.reindex(genes, fill_value=0)
        est = stats(pre, post)
        rng = np.random.default_rng(3)
        bs = []
        for _ in range(1000):
            s = rng.integers(0, len(genes), len(genes))
            ix = genes[s]
            pb = pre.loc[ix].groupby(level=0).sum()
            qb = post.loc[ix].groupby(level=0).sum()
            bs.append(stats(pb, qb))
        bs = np.array(bs)
        for i, name in enumerate(("raw", "common_genes", "standardised")):
            b = bs[:, i][np.isfinite(bs[:, i])]
            rows.append(dict(tool=tool, method=name, log_ratio=float(est[i]), ratio=float(np.exp(est[i])),
                             lo5=float(np.percentile(b, 5)), hi95=float(np.percentile(b, 95)),
                             n_genes_common=int(((pre.n_P > 0) & (pre.n_B > 0) & (post.n_P > 0) & (post.n_B > 0)).sum()),
                             benign_ge3_pre=int(pre.k_B.sum()), benign_ge3_post=int(post.k_B.sum()),
                             benign_pre=int(pre.n_B.sum()), benign_post=int(post.n_B.sum())))
    out = pd.DataFrame(rows)
    out.to_csv(TAB / "explore_gene_standardised.csv", index=False)
    print(out.round(3).to_string(index=False))
    # which genes carry the post-window benign wave (REVEL windows)?
    pre = gene_table(df[df.year.isin(WIN["revel"][0])], "revel")
    post = gene_table(df[df.year.isin(WIN["revel"][1])], "revel")
    new = post[~post.index.isin(pre.index[pre.n_B > 0])]
    share_new = new.n_B.sum() / post.n_B.sum()
    top = new.sort_values("n_B", ascending=False).head(15)[["n_B", "k_B"]]
    top.to_csv(TAB / "explore_new_benign_genes.csv")
    print(f"share of post-window benign labels in genes with no pre-window benign label: {share_new:.3f}")
    print(top.to_string())


if __name__ == "__main__":
    sys.exit(main())
