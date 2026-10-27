"""Figures for the report (each PNG has a .txt caption). Written after analyse.py.

  F1  memorization and the rest, by how much analog leakage the split allows, in both benchmarks
  F2  foundation-model embeddings against ECFP4 + random forest, per target (H2)
  F3  method ranking agreement with the LIT consensus, against the split-half noise ceiling (H3)
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
NAMES = {"nn": "1-NN memorization", "rf": "ECFP4 + RF", "gbm": "descriptors + LightGBM",
         "cb": "ChemBERTa + LR", "mf": "MoLFormer + LR"}


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1(M, folds):
    order = [("random", "random"), ("audit06", "analog-disjoint\nat 0.6"), ("audit04", "analog-disjoint\nat 0.4")]
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.1), sharey=True)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.17, top=0.78, wspace=0.07)
    for ax, (ev, title) in zip(axes, (("new", "PCBA-2026 (28 targets)"), ("lit_cv", "LIT-PCBA, same procedure (15)"))):
        g = M[M["eval"] == ev]
        for k, meth in enumerate(("nn", "rf")):
            y = [g[(g.variant == v) & (g.method == meth)].ef1.median() for v, _ in order]
            ax.plot(range(3), y, marker="o", ms=6, lw=2, color=ORANGE if meth == "nn" else BLUE, label=NAMES[meth])
            for i, v in enumerate(y):
                ax.annotate(f"{v:.1f}", (i, v), xytext=(0, 7), textcoords="offset points", fontsize=7.5,
                            color=ORANGE if meth == "nn" else BLUE, ha="center")
        ax.set_xticks(range(3)); ax.set_xticklabels([t for _, t in order], fontsize=8)
        ax.set_xlim(-0.35, 2.35)
        ax.set_title(title, fontsize=9, color=INK, loc="left")
        ax.grid(axis="y", color=GRID, lw=0.5)
    axes[0].set_ylabel("median EF1% over targets")
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    nn_new = folds[folds.bench == "new"].nn_sim_sample_share_above_0_4.median()
    nn_lit = folds[folds.bench == "lit"].nn_sim_sample_share_above_0_4.median()
    fig.suptitle(f"Memorization's advantage is a property of the split\nAnalog leakage reaches {nn_lit * 100:.0f}% of "
                 f"LIT-PCBA evaluation compounds and {nn_new * 100:.0f}% of PCBA-2026's",
                 x=0.02, y=0.98, ha="left", va="top", fontsize=9.5, color=INK)
    fig.savefig(F / "F1_splits.png", dpi=170); plt.close(fig)
    caption("F1_splits", """Median enrichment factor in the top 1% across targets, for the parameter-free
    1-nearest-neighbour memorization baseline and for ECFP4 + random forest, under three splits of the same data: a
    random 5-fold split, and analog-disjoint 5-fold splits in which any evaluation compound with a training
    neighbour above Tanimoto 0.6 or 0.4 is removed from scoring. Both benchmarks are capped at 50,000 compounds per
    target with the hit rate preserved (D3).""")


def f2(P):
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.16, top=0.82)
    for k, (emb, col) in enumerate((("cb", BLUE), ("mf", ORANGE))):
        g = P[P.embedding == emb].sort_values("delta")
        x = np.arange(len(g)) + (k - 0.5) * 0.35
        ax.errorbar(x, g.delta, yerr=[g.delta - g.ci_lo, g.ci_hi - g.delta], fmt="o", ms=3.5, lw=0.8,
                    color=col, ecolor=col, alpha=0.75, label=f"{NAMES[emb]} − {NAMES['rf']}")
    ax.axhline(0, color=INK, lw=1)
    ax.set_xlabel("targets, sorted by difference (each embedding separately)")
    ax.set_ylabel("ΔEF1% against ECFP4 + RF")
    ax.grid(axis="y", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Neither pretrained embedding beats a fingerprint random forest on any target",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F2_embeddings.png", dpi=170); plt.close(fig)
    caption("F2_embeddings", f"""Per target and embedding, the difference in EF1% against ECFP4 + random forest on the
    analog-disjoint (0.4) split of PCBA-2026, with 95% paired bootstrap intervals over evaluation compounds (2,000
    resamples). Above zero means the embedding is better. The embedding's interval excludes zero on 0 of
    {len(P)} target-embedding pairs; the random forest's does on {int(P.rf_beats_emb.sum())}.""")


def f3(tau, p):
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.16, top=0.82)
    ax.hist(tau.tau, bins=np.linspace(-1, 1, 21), color=GREY, edgecolor=SURF)
    m, ci = p["H3"]["mean_tau"], p["H3"]["ci"]
    ax.axvline(m, color=BLUE, lw=2, label=f"mean τ = {m:.2f} [{ci[0]:.2f}, {ci[1]:.2f}]")
    nc = p["noise_ceiling"]["mean_tau_split_half"]
    ax.axvline(nc, color=ORANGE, lw=2, ls="--", label=f"split-half ceiling = {nc:.2f}")
    ax.axvline(0.4, color=INK2, lw=0.8, ls=":", label="H3 bar = 0.4")
    ax.set_xlabel("Kendall τ between a target's method ranking and the LIT-PCBA consensus")
    ax.set_ylabel("targets"); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Method rankings transfer weakly — but they barely replicate within a target either",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F3_ranking.png", dpi=170); plt.close(fig)
    caption("F3_ranking", f"""For each PCBA-2026 target, the Kendall τ between its ranking of the five methods by
    EF1% and the consensus ranking on LIT-PCBA as published. Orange: the mean τ between rankings computed on two
    random halves of the same target's evaluation set, which bounds how much agreement is achievable
    ({p['noise_ceiling']['targets_used']} targets; {p['noise_ceiling']['targets_skipped_tied_or_missing']} skipped
    for tied rankings).""")


if __name__ == "__main__":
    p = json.loads((T / "primary.json").read_text())
    M = pd.read_csv(T / "metrics.csv")
    folds = pd.concat([pd.read_csv(T / f"folds_{b}.csv").assign(bench=b) for b in ("new", "lit")])
    f1(M, folds); f2(pd.read_csv(T / "pairs_h2.csv")); f3(pd.read_csv(T / "tau_h3.csv"), p)
    print("figures written")
