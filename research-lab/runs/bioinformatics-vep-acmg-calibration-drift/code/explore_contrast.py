#!/usr/bin/env python
"""EXPLORATORY (deviations.md D6): did the pooled >= +3 LR of REVEL rise more than that of ESM1b (clinically less
used, thresholds published only in 2024) between 2021-2022 and 2024-2026? Joint gene-cluster bootstrap over variants
scored by both tools. Output: results/tables/explore_contrast.json"""
import json
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import load, pooled  # noqa: E402
from calib import gene_counts, interval_lr  # noqa: E402

TAB = Path(__file__).resolve().parents[1] / "results" / "tables"
df = load()
df = df[df.primary_new & df.revel.notna() & df.esm1b.notna()]
genes = np.unique(df.gene.astype(str))
idx = {g: i for i, g in enumerate(genes)}


def counts(d, tool):
    p = pooled(d, tool)
    gi = p.gene.astype(str).map(idx).values
    cnt = np.zeros((len(genes), 3, 2))
    isb = (p.label.values == "B").astype(int)
    iv = np.where(p.pts_pool.values >= 3, 1, np.where(p.pts_pool.values <= -3, 0, -1))
    np.add.at(cnt, (gi, np.full(len(p), 2), isb), 1)
    m = iv >= 0
    np.add.at(cnt, (gi[m], iv[m], isb[m]), 1)
    return cnt


pre, post = df[df.year.isin([2021, 2022])], df[df.year.isin([2024, 2025, 2026])]
C = {(t, w): counts(d, t) for t in ("revel", "esm1b") for w, d in (("pre", pre), ("post", post))}


def stat(w):
    lr = {k: interval_lr(np.tensordot(w, c, axes=(0, 0)))[1] for k, c in C.items()}
    dr = np.log(lr[("revel", "post")]) - np.log(lr[("revel", "pre")])
    de = np.log(lr[("esm1b", "post")]) - np.log(lr[("esm1b", "pre")])
    return dr, de, dr - de


rng = np.random.default_rng(5)
est = stat(np.ones(len(genes)))
bs = np.array([stat(np.bincount(rng.integers(0, len(genes), len(genes)), minlength=len(genes)).astype(float)) for _ in range(2000)])
bs = bs[np.all(np.isfinite(bs), axis=1)]
out = {name: dict(estimate=float(e), lo5=float(np.percentile(bs[:, i], 5)), hi95=float(np.percentile(bs[:, i], 95)),
                  p_le_0=float(np.mean(bs[:, i] <= 0)))
       for i, (name, e) in enumerate(zip(("revel_log_ratio", "esm1b_log_ratio", "difference"), est))}
out["n_variants"] = int(len(df))
json.dump(out, open(TAB / "explore_contrast.json", "w"), indent=2)
print(json.dumps(out, indent=1))
