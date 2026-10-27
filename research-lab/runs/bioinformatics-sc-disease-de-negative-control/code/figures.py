"""Figures for the report (each PNG has a .txt caption). Written after analyse.py.

  F1  per contrast: the real statistic against its matched-null distribution, and the share indistinguishable
  F2  what a practitioner would find (DE genes at full size) against whether the contrast beats its own null
  F3  replication between cross-collection pairs against donor count, with the null-pair baseline
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, ORANGE, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317", "#9a9893"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1(d, p):
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), gridspec_kw={"width_ratios": [1.35, 1]})
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.16, top=0.80, wspace=0.28)
    ax = axes[0]
    x = d.n_de_null_q95.to_numpy() + 1
    y = d.n_de_real.to_numpy() + 1
    sig = (d.n_de_q < 0.05).to_numpy()
    ax.scatter(x[~sig], y[~sig], s=7, color=GREY, alpha=0.45, lw=0, label="indistinguishable from its null")
    ax.scatter(x[sig], y[sig], s=9, color=ORANGE, alpha=0.75, lw=0, label="exceeds its null (BH q < 0.05)")
    lim = [1, max(x.max(), y.max()) * 1.3]
    ax.plot(lim, lim, color=INK2, lw=0.8, ls="--")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("DE genes, 95th percentile of the matched healthy-vs-healthy nulls (+1)")
    ax.set_ylabel("DE genes, real contrast (+1)")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.grid(color=GRID, lw=0.5)
    ax = axes[1]
    labels = ["DE genes\n(87% power)", "π1\n(8% power)", "mean |logFC|\ntop 100"]
    vals = [p["H1"]["by_n_de_power_selected"]["S1"], p["H1"]["S1"], p["H1"]["share_indistinguishable_by_stat"]["mean_abs_lfc_top100"]]
    cis = [p["H1"]["by_n_de_power_selected"]["ci95"], p["H1"]["ci95"], None]
    for i, (v, ci) in enumerate(zip(vals, cis)):
        ax.bar(i, v * 100, width=0.6, color=BLUE if i == 0 else GREY)
        if ci:
            ax.plot([i, i], [ci[0] * 100, ci[1] * 100], color=INK, lw=1)
        ax.text(i, v * 100, f"{v * 100:.0f}%", ha="center", va="bottom", fontsize=8, color=INK)
    ax.axhline(50, color=ORANGE, lw=0.8, ls="--")
    ax.text(2.4, 50, "H1 bar", fontsize=7, color=INK2, ha="right", va="bottom")
    ax.set_xticks(range(3)); ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("% of contrasts indistinguishable"); ax.set_ylim(0, 100); ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Most disease contrasts in the atlas do not exceed a matched healthy-vs-healthy null",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F1_exceedance.png", dpi=170); plt.close(fig)
    caption("F1_exceedance", f"""Left: for each of the {p['H1']['contrasts_evaluable']} primary contrasts (one disease x
    tissue x cell type within one dataset), the number of differentially expressed genes (BH FDR < 0.05, limma-voom on
    donor pseudobulk) in the real comparison against the 95th percentile of 500 matched healthy-donor-only
    comparisons from the same dataset, tissue and cell type, matched on sex and age bin and on group sizes. Orange:
    exceeds its own null at BH q < 0.05 across contrasts. Right: share indistinguishable under each statistic, with
    95% intervals from a cluster bootstrap over the {p['H1']['datasets']} datasets, and each statistic's power
    against a synthetic twofold change in 5% of genes.""")


def f2(d):
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.16, top=0.82)
    bins = [-0.5, 0.5, 10.5, 100.5, 1000.5, 1e9]
    names = ["0", "1-10", "11-100", "101-1,000", "> 1,000"]
    cut = pd.cut(d.n_de_full, bins, labels=names)
    tot = cut.value_counts().reindex(names)
    exc = d.assign(b=cut).groupby("b", observed=False).apply(lambda g: (g.n_de_q < 0.05).sum(), include_groups=False).reindex(names)
    ax.bar(range(5), tot, width=0.62, color=GREY, label="all contrasts")
    ax.bar(range(5), exc, width=0.62, color=ORANGE, label="of those, exceed their own null")
    for i, (t, e) in enumerate(zip(tot, exc)):
        if t:
            ax.text(i, t, f"{100 * e / t:.0f}%", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks(range(5)); ax.set_xticklabels(names, fontsize=8)
    ax.set_xlabel("DE genes a practitioner would report (all donors, BH FDR < 0.05)")
    ax.set_ylabel("contrasts"); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.suptitle("Finding differentially expressed genes is not evidence of disease signal", x=0.02, ha="left",
                 fontsize=10, color=INK)
    fig.savefig(F / "F2_practitioner.png", dpi=170); plt.close(fig)
    caption("F2_practitioner", """Grey: contrasts by the number of DE genes the full-size comparison reports, as a
    practitioner would run it. Orange: how many of those also exceed their own matched healthy-vs-healthy null
    (BH q < 0.05). The percentage above each bar is the share that does.""")


def f3(pr, p):
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.16, top=0.82)
    ax.scatter(2 ** pr.d, pr.rho, s=14, color=BLUE, alpha=0.6, lw=0, label="cross-collection pair")
    nb = pr.dropna(subset=["null_rho_median"])
    if len(nb):
        ax.scatter(2 ** nb.d, nb.null_rho_median, s=14, color=GREY, alpha=0.6, lw=0, marker="x",
                   label="same pair, null signatures")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("donors in the smaller group of the pair")
    ax.set_ylabel("Spearman ρ between the two studies' t statistics")
    ax.grid(color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="upper left")
    b = p["H2"]["bootstrap"]["group"]
    ax.set_title(f"β(log2 donors) = {p['H2']['beta']['d']:.3f} [{b['beta_d_ci'][0]:.3f}, {b['beta_d_ci'][1]:.3f}]; "
                 f"β(log2 cells) = {p['H2']['beta']['c']:.3f} [{b['beta_c_ci'][0]:.3f}, {b['beta_c_ci'][1]:.3f}]",
                 fontsize=8.5, color=INK2, loc="left")
    fig.suptitle("Replication across studies rises with donors, but not detectably more than with cells",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F3_replication.png", dpi=170); plt.close(fig)
    caption("F3_replication", f"""Each point is a pair of contrasts for the same disease, tissue and cell type from
    datasets in different Census collections ({p['H2']['pairs']} pairs, {p['H2']['groups']} groups,
    {p['H2']['diseases']} diseases): the Spearman correlation of their moderated t statistics over shared genes,
    against the smallest donor group in the pair. Crosses: the same pairs' matched-null signatures, where both sides
    have null draws.""")


if __name__ == "__main__":
    p = json.loads((T / "primary.json").read_text())
    d = pd.read_csv(T / "contrasts.csv")
    pr = pd.read_csv(T / "pairs.csv")
    f1(d, p); f2(d); f3(pr, p)
    print("figures written")
