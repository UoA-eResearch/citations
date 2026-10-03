#!/usr/bin/env python
"""Matching, noise model and empirical-Bayes cliff confidence (plan.md sec 2-4, 7).

match():      benchmark molecules -> ChEMBL compounds by RDKit InChIKey (full key, else the 14-character connectivity
              block) within the same target and activity type; n_pre = entries in documents up to 2021 (>= 1),
              n_all = all entries, post-2021 mean.
sigma():      noise SD per activity type from inter-document replicate pairs (one random pair per compound, seed 0):
              sigma = 1.4826 * MAD(differences) / sqrt(2); validated on a random 20% of compounds held out.
npmle():      symmetric nonparametric prior on true differences (grid -5..5, step 0.05) by EM, heteroscedastic Gaussian
              (or Student-t) noise.
confidence(): P(|true difference| > 1 | observed difference).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from scipy import stats

RDLogger.DisableLog("rdApp.*")
GRID = np.round(np.arange(-5, 5.0001, 0.05), 4)


def inchikey(smi):
    m = Chem.MolFromSmiles(smi)
    return Chem.MolToInchiKey(m) if m is not None else None


def match(bench_df, chembl):
    """bench_df: one MoleculeACE dataset; chembl: that dataset's ChEMBL rows. Returns per-molecule match info."""
    keys = [inchikey(s) for s in bench_df.smiles]
    full = chembl.groupby("inchikey")
    conn = chembl.assign(conn=chembl.inchikey.str[:14]).groupby("conn")
    rows = []
    for k in keys:
        if k is not None and k in full.groups:
            g, how = full.get_group(k), "full"
        elif k is not None and k[:14] in conn.groups:
            g, how = conn.get_group(k[:14]), "connectivity"
        else:
            rows.append(dict(match="none", n_pre=1, n_all=1, n_post=0, post_mean=np.nan))
            continue
        v = g.pchembl_value.round(2)
        pre = v[g.year.fillna(0) <= 2021]
        post = v[(g.year.fillna(0) >= 2022) & ~v.isin(set(pre))]          # new, non-copied values only (D2)
        rows.append(dict(match=how, n_pre=max(pre.nunique(), 1), n_all=max(v.nunique(), 1), n_post=post.nunique(),
                         post_mean=float(post.drop_duplicates().mean()) if len(post) else np.nan))
    return pd.DataFrame(rows)


def replicate_pairs(chembl, intra=False, seed=0):
    """One random replicate pair per compound, from different documents (default) or the same document. Values identical
    to 2 decimals are collapsed first: they are re-reported copies, not independent replicates (deviations.md D2)."""
    rng = np.random.default_rng(seed)
    out = []
    for (mol, typ), g in chembl.groupby(["molregno", "standard_type"]):
        if intra:
            for doc, h in g.groupby("doc_id"):
                vals = h.pchembl_value.round(2).drop_duplicates()
                if len(vals) >= 2:
                    i, j = rng.choice(len(vals), 2, replace=False)
                    out.append((mol, typ, vals.iloc[i], vals.iloc[j]))
                    break
        else:
            docs = g.groupby("doc_id").pchembl_value.mean().round(2).drop_duplicates()
            if len(docs) >= 2:
                i, j = rng.choice(len(docs), 2, replace=False)
                out.append((mol, typ, docs.iloc[i], docs.iloc[j]))
    return pd.DataFrame(out, columns=["molregno", "standard_type", "x1", "x2"])


def robust_sigma(d):
    d = np.asarray(d)
    return 1.4826 * np.median(np.abs(d - np.median(d))) / np.sqrt(2)


def npmle(d, s, noise="normal", iters=2000, tol=1e-9):
    """Symmetric NPMLE prior weights on GRID for observations d with noise SD s."""
    d = np.concatenate([d, -d])
    s = np.concatenate([s, s])
    z = (d[:, None] - GRID[None, :]) / s[:, None]
    L = (stats.norm.pdf(z) if noise == "normal" else stats.t.pdf(z, 4)) / s[:, None]
    w = np.full(len(GRID), 1 / len(GRID))
    prev = -np.inf
    for _ in range(iters):
        num = L * w
        den = num.sum(1, keepdims=True)
        w = (num / den).mean(0)
        ll = np.log(den).sum()
        if ll - prev < tol:
            break
        prev = ll
    w = (w + w[::-1]) / 2
    return w / w.sum()


def confidence(d, s, w, noise="normal"):
    z = (np.asarray(d)[:, None] - GRID[None, :]) / np.asarray(s)[:, None]
    L = (stats.norm.pdf(z) if noise == "normal" else stats.t.pdf(z, 4)) / np.asarray(s)[:, None]
    post = L * w
    post /= post.sum(1, keepdims=True)
    return post[:, np.abs(GRID) > 1].sum(1)
