#!/usr/bin/env python
"""Figures for the report (results/figures/F*.png, each with a caption file)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import nibabel as nb  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
INK, MUTED, GRID = "#0b0b0b", "#898781", "#e1e0d9"
COL = {"S": "#0b0b0b", "EB-Q": "#2a78d6", "EB-W": "#eb6834", "EB-0": "#1baf7a"}
LABEL = {"S": "standard (mean map)", "EB-Q": "shrunk toward matched NeuroQuery map",
         "EB-W": "shrunk toward mismatched map", "EB-0": "shrunk toward a flat prior"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})


def caption(name, text):
    (FIG / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1_maps():
    keys = [k for k, v in A.CONTRASTS.items() if v[3]]
    grid = nb.load(RUN / "data" / "grid" / "mask.nii.gz")
    gm = np.asarray(grid.get_fdata()) > 0
    pri = np.load(RUN / "results" / "priors" / "priors.npz")
    fig, axes = plt.subplots(2, len(keys), figsize=(13, 4.6))
    for j, k in enumerate(keys):
        Y, gmask, _ = A.load(k)
        dom, q, _, _ = A.CONTRASTS[k]
        full = np.full(gm.sum(), np.nan)
        full[gmask] = Y.mean(0)
        prior = pri[q].astype(float)
        for i, (vec, ttl) in enumerate(((full, f"{dom}\nall {Y.shape[0]} subjects"), (prior, f'NeuroQuery: "{q}"'))):
            vol = np.full(gm.shape, np.nan)
            vol[gm] = vec
            sl = np.nanmax(vol, axis=2).T                                 # maximum-intensity projection, axial
            v = np.nanpercentile(np.abs(vec[np.isfinite(vec)]), 99)
            ax = axes[i, j]
            ax.imshow(sl, origin="lower", cmap="RdBu_r", vmin=-v, vmax=v)
            ax.set_title(ttl, fontsize=8.5)
            ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
            r = np.corrcoef(prior[gmask], full[gmask])[0, 1]
            if i == 1:
                ax.set_xlabel(f"spatial r with data = {r:.2f}", fontsize=8)
    fig.savefig(FIG / "F1_maps.png")
    plt.close(fig)
    caption("F1_maps", """F1. Top: each domain's group map from all included subjects (contrast estimate, maximum-intensity
projection, axial view). Bottom: the NeuroQuery prediction for the matched query. The number under each prior is its
spatial correlation with the full-sample map.""")


def f2_curves():
    keys = list(A.CONTRASTS)
    fig, axes = plt.subplots(2, 4, figsize=(13, 6), sharex=True)
    for ax, k in zip(axes.flat, keys):
        d = pd.read_parquet(TAB / f"draws_{k}.parquet")
        s = d.groupby(["method", "n"]).r.mean().unstack(0)
        for m in ("S", "EB-0", "EB-W", "EB-Q"):
            ax.plot(s.index, s[m], "o-", ms=3, color=COL[m], label=LABEL[m])
        ax.axvline(15, color=MUTED, lw=0.8, ls=":")
        ax.set_xscale("log")
        ax.set_xticks([10, 15, 20, 30, 50, 80]); ax.set_xticklabels([10, 15, 20, 30, 50, 80])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_title(A.CONTRASTS[k][0], fontsize=9)
        ax.set_xlabel("subjects in the small study")
        ax.set_ylabel("spatial r with ground truth")
    h, l = axes.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=4, fontsize=8)
    fig.savefig(FIG / "F2_curves.png")
    plt.close(fig)
    caption("F2_curves", """F2. Mean spatial correlation between a small study's group map and the ground-truth map from
a separate set of subjects (N - 80), over 500 random draws per sample size. Black: the standard mean map. Blue: shrunk
toward the matched NeuroQuery map. Orange: toward a mismatched map. Green: toward a flat prior. The dotted line marks
n = 15, the preregistered comparison point.""")


def f3_gain():
    g = pd.read_csv(TAB / "gains.csv")
    g = g[(g.metric == "r") & (g.n0 == 15) & (g.method != "S")]
    keys = list(A.CONTRASTS)
    fig, ax = plt.subplots(figsize=(8.5, 4))
    for i, m in enumerate(("EB-Q", "EB-W", "EB-0")):
        x = g[g.method == m].set_index("key").reindex(keys)
        y = np.arange(len(keys)) + (i - 1) * 0.22
        floor = (x.flag == "<").values
        ax.errorbar(x.G[~floor], y[~floor], xerr=[(x.G - x.G_lo)[~floor], (x.G_hi - x.G)[~floor]], fmt="o", ms=4,
                    color=COL[m], label=LABEL[m], capsize=0)
        ax.plot(x.G[floor], y[floor], "<", ms=5, color=COL[m])
    ax.axvline(1, color=INK, lw=0.8)
    ax.axvline(2, color=MUTED, lw=0.8, ls="--")
    ax.set_yticks(np.arange(len(keys)))
    ax.set_yticklabels([A.CONTRASTS[k][0] for k in keys])
    ax.invert_yaxis()
    ax.set_xlabel("effective sample-size gain at n = 15 (1 = no gain; dashed: the predicted doubling)")
    ax.legend(fontsize=7, loc="lower right")
    fig.savefig(FIG / "F3_gain.png")
    plt.close(fig)
    caption("F3_gain", """F3. How many subjects each method is worth at n = 15, as a multiple of 15: the sample size at
which the standard analysis reaches the same mean spatial correlation, divided by 15 (95% intervals from a bootstrap over
draws). Triangles at 0.67 mark the floor of the grid: the method at n = 15 is worse than the standard analysis at
n = 10. H1 predicted at least 2 (dashed line) in at least five of the six primary domains.""")


def f4_fpr():
    keys = list(A.CONTRASTS)
    rows = []
    for k in keys:
        d = pd.read_parquet(TAB / f"draws_{k}.parquet")
        f = d[d.n == 15].groupby("method").fpr.mean()
        rows.append(f.rename(k))
    t = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    w = 0.2
    for i, m in enumerate(("S", "EB-Q", "EB-W", "EB-0")):
        ax.bar(np.arange(len(keys)) + (i - 1.5) * w, t[m] * 100, w, color=COL[m], label=LABEL[m])
    ax.set_xticks(np.arange(len(keys)))
    ax.set_xticklabels([A.CONTRASTS[k][0].replace(" (PIOP2 replication)", "\n(PIOP2)") for k in keys], fontsize=7.5,
                       rotation=25, ha="right")
    ax.set_ylabel("false-positive rate (%)")
    ax.legend(fontsize=7)
    fig.savefig(FIG / "F4_fpr.png")
    plt.close(fig)
    caption("F4_fpr", """F4. False-positive rate at n = 15: the share of voxels with no detectable effect in the
ground-truth set (|z| < 1.96) that each method declares active at z > 3.09, averaged over 500 draws.""")


def f5_explore():
    g = pd.read_csv(TAB / "explore_gains.csv")
    keys = list(A.CONTRASTS)
    spec = (("HEB-Q", "#2a78d6", "uniform-weight shrinkage toward the matched map (E1)"),
            ("ORACLE-Q", "#104281", "oracle: best uniform mix with the matched map (E2)"),
            ("ORACLE-W", "#eb6834", "oracle: best uniform mix with the mismatched map (E2)"))
    fig, ax = plt.subplots(figsize=(8.5, 4))
    for i, (m, c, lab) in enumerate(spec):
        x = g[g.method == m].set_index("key").reindex(keys)
        y = np.arange(len(keys)) + (i - 1) * 0.22
        floor = (x.flag == "<").values
        ax.errorbar(x.G[~floor], y[~floor], xerr=[(x.G - x.G_lo)[~floor], (x.G_hi - x.G)[~floor]], fmt="o", ms=4,
                    color=c, label=lab, capsize=0)
        ax.plot(x.G[floor], y[floor], "<", ms=5, color=c)
    ax.axvline(1, color=INK, lw=0.8)
    ax.axvline(2, color=MUTED, lw=0.8, ls="--")
    ax.set_yticks(np.arange(len(keys)))
    ax.set_yticklabels([A.CONTRASTS[k][0] for k in keys])
    ax.invert_yaxis()
    ax.set_xlabel("effective sample-size gain at n = 15")
    ax.legend(fontsize=7, loc="lower right")
    fig.savefig(FIG / "F5_explore.png")
    plt.close(fig)
    caption("F5_explore", """F5. Exploratory, defined after the primary results. Blue: the same empirical-Bayes model with one
noise level for all voxels, so every voxel is shrunk by the same weight. Dark blue and orange: the best possible uniform
mix of the small-study map with the matched or mismatched NeuroQuery map, with the mixing weight chosen by looking at the
ground truth (an upper bound, not a usable method). Even the oracle stays far below the predicted doubling (dashed).""")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    for f in (f1_maps, f2_curves, f3_gain, f4_fpr, f5_explore):
        f()
    print("figures written")
