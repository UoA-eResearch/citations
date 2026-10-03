#!/usr/bin/env python
"""Figures for the report (results/figures/F*.png, each with a caption file)."""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import noise_eb as NE  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
INK, MUTED, GRID = "#0b0b0b", "#898781", "#e1e0d9"
BLUE, ORANGE, AQUA, NAVY, RED = "#2a78d6", "#eb6834", "#1baf7a", "#104281", "#c0392b"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})


def caption(name, text):
    (FIG / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1_noise():
    ch = pd.read_parquet(RUN / "data" / "chembl_bench.parquet")
    nm = pd.read_csv(TAB / "noise_model.csv").set_index("standard_type")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, typ in zip(axes, ("Ki", "EC50")):
        pr = NE.replicate_pairs(ch[ch.standard_type == typ])
        d = (pr.x1 - pr.x2).values
        d = np.r_[d, -d]
        ax.hist(d, bins=np.arange(-4, 4.01, 0.1), density=True, color=BLUE, alpha=0.55, label="independent replicate differences")
        sig = nm.sigma[typ]
        x = np.linspace(-4, 4, 400)
        ax.plot(x, stats.norm.pdf(x, 0, np.sqrt(2) * sig), color=INK, lw=1.2, label=f"Gaussian, sigma = {sig:.2f}")
        dens = np.convolve(stats.t.pdf(x / sig, 4) / sig, stats.t.pdf(x / sig, 4) / sig, mode="same") * (x[1] - x[0])
        ax.plot(x, dens, color=ORANGE, lw=1.2, ls="--", label="Student-t (4 df), same scale")
        ax.set_yscale("log")
        ax.set_ylim(1e-3, 2)
        ax.set_xlabel("difference between two independent measurements (log units)")
        ax.set_title(f"{typ}: {len(pr)} compounds with distinct values from 2+ documents")
    axes[0].set_ylabel("density (log scale)")
    axes[0].legend(fontsize=7, loc="upper left")
    fig.savefig(FIG / "F1_noise.png")
    plt.close(fig)
    caption("F1_noise", """F1. How much do two independent measurements of the same compound on the same target disagree?
Differences between distinct values reported in different ChEMBL documents for the 30 benchmark targets (identical,
re-reported values removed; deviations D2), with the fitted Gaussian and Student-t noise models. The tails are heavier
than Gaussian, which is why the t model is primary (D3).""")


def f2_confidence():
    cp = pd.read_parquet(TAB / "cliff_pairs_conf.parquet")
    cl = cp[cp.cliff]
    # Gaussian-arm confidence recomputed for display
    w = NE.npmle(cp.d.values, cp.sd.values, "normal")
    cg = NE.confidence(cl.d.values, cl.sd.values, w, "normal")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    ax = axes[0]
    bins = np.linspace(0, 1, 41)
    ax.hist(cl.conf, bins=bins, color=ORANGE, alpha=0.6, label="t noise (primary)")
    ax.hist(cg, bins=bins, color=BLUE, alpha=0.5, label="Gaussian noise")
    ax.axvline(0.8, color=INK, lw=0.8, ls="--")
    ax.set_xlabel("probability that the cliff is a true >= 10-fold difference")
    ax.set_ylabel("cliff pairs")
    ax.legend(fontsize=7)
    ax.set_title(f"{len(cl):,} MoleculeACE cliff pairs")
    ax = axes[1]
    order = np.argsort(np.abs(cl.d.values))
    ax.scatter(np.abs(cl.d.values), cl.conf, s=2, color=ORANGE, alpha=0.3, label="t noise")
    ax.scatter(np.abs(cl.d.values), cg, s=2, color=BLUE, alpha=0.3, label="Gaussian noise")
    ax.set_xlabel("observed potency difference (log units; > 1 defines a cliff)")
    ax.set_ylabel("cliff confidence")
    ax.legend(fontsize=7, markerscale=4)
    fig.savefig(FIG / "F2_confidence.png")
    plt.close(fig)
    caption("F2_confidence", """F2. Left: the posterior probability that each benchmark cliff is a real 10-fold difference,
given measured replicate noise (empirical-Bayes deconvolution over all similar pairs). Dashed: the 0.8 line of H1.
Right: confidence against the observed difference. Under heavy-tailed noise no cliff is confidently real; under
Gaussian noise only cliffs with very large observed differences are.""")


def f3_null():
    st = pd.read_csv(TAB / "summary_by_target.csv")
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    ax.scatter(st.gap, st.null_gap_t, color=ORANGE, s=18, label="noise-only world, t noise")
    ax.scatter(st.gap, st.null_gap_normal, color=BLUE, s=18, label="noise-only world, Gaussian noise")
    lim = [-0.2, 0.55]
    ax.plot(lim, lim, color=INK, lw=0.8)
    ax.plot(lim, [0.5 * v for v in lim], color=MUTED, lw=0.8, ls="--")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("observed cliff gap (RMSE cliff minus non-cliff)")
    ax.set_ylabel("gap in a world with no real cliffs")
    ax.legend(fontsize=7, loc="upper left")
    fig.savefig(FIG / "F3_null.png")
    plt.close(fig)
    caption("F3_null", """F3. One point per benchmark target: the cliff gap observed with real labels against the gap in a
simulated world with a smooth activity landscape (no real cliffs) plus measured noise, averaged over 20 noise draws and
four models. Solid line: equal; dashed: half (the H3 threshold). Noise and the way cliffs are selected reproduce the
whole gap. The t world is over-dispersed (more cliffs than real); the better-calibrated Gaussian world reproduces 115%.""")


def f4_restricted():
    bt = pd.read_csv(TAB / "gaps_by_target_normal.csv")
    nv = pd.read_csv(TAB / "null_v2.csv")
    nr = nv[nv.world == "normal"].groupby(["dataset", "draw"]).gap_restricted.mean().groupby("dataset").mean()
    nf = nv[nv.world == "normal"].groupby(["dataset", "draw"]).gap.mean().groupby("dataset").mean()
    bt = bt.assign(null_restricted=bt.dataset.map(nr), null_full=bt.dataset.map(nf)).sort_values("gap")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(bt))
    ax.plot(x, bt.gap.values, "o", color=NAVY, ms=4, label="real data: all benchmark cliff molecules")
    ax.plot(x, bt.gap_restricted.values, "o", color=RED, ms=4, label="real data: high-confidence cliff molecules only")
    ax.plot(x, bt.null_restricted.values, "x", color=MUTED, ms=5, label="noise-only world: same high-confidence rule")
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks([])
    ax.set_xlabel("benchmark targets (ordered by the full real gap)")
    ax.set_ylabel("cliff gap (RMSE, log units)")
    ax.legend(fontsize=7)
    fig.savefig(FIG / "F4_restricted.png")
    plt.close(fig)
    caption("F4_restricted", """F4. Gaussian-noise arm. Restricting the cliff set to molecules in at least one cliff with
confidence >= 0.9 roughly triples the gap in the real data (red). A simulated world with no real cliffs, given the same
high-confidence rule, shows the same increase (grey crosses): confidently real-looking cliffs are those with the most
extreme observed differences, and selecting them is itself what enlarges the gap.""")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    targets = sys.argv[1:] or ['f1_noise', 'f2_confidence', 'f3_null', 'f4_restricted']
    for name in targets:
        globals()[name]()
    print("figures written")
