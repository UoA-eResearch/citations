"""Figures for the report (each PNG has a .txt caption). Written after model.py.

  F1  AUROC by predictor, random vs temporal holdout, pooled and per interaction class
  F2  temporal holdout subsets (new vs existing source datasets, cold start) and degree-matched negatives
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
PRED = [("effort", "effort only", GREY), ("rdpg", "RDPG (structure)", BLUE), ("taxgb", "taxonomy + structure", ORANGE)]


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1(p):
    pc = pd.read_csv(T / "per_class.csv")
    groups = [("pooled", None), ("trophic", "trophic"), ("pollination", "pollination"), ("host-parasite", "host")]
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.5), sharey=True)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.17, top=0.8, wspace=0.08)
    for ax, mode, title in zip(axes, ("random", "temporal"), ("random 10% holdout within v0.6", "temporal: new in v0.11")):
        x = np.arange(len(groups))
        for k, (key, lab, col) in enumerate(PRED):
            vals = [p["auroc"][mode][key] if c is None else float(pc[(pc["mode"] == mode) & (pc.cls == c)][key].iloc[0])
                    for _, c in groups]
            ax.bar(x + (k - 1) * 0.26, vals, width=0.24, color=col, label=lab)
        ax.set_xticks(x); ax.set_xticklabels([g for g, _ in groups], fontsize=8)
        ax.set_ylim(0.6, 1.0); ax.set_title(title, fontsize=9, color=INK, loc="left"); ax.grid(axis="y", color=GRID, lw=0.5)
    axes[0].set_ylabel("AUROC (uniform negatives, 10 per positive)")
    axes[1].legend(frameon=False, fontsize=7.5, loc="lower right")
    fig.suptitle("Taxonomy-aware prediction keeps its edge over 'who gets studied' on future records", x=0.02, ha="left",
                 fontsize=10, color=INK)
    fig.savefig(F / "F1_auroc.png", dpi=170); plt.close(fig)
    caption("F1_auroc", f"""GloBI species-level interactions in three classes. Random holdout: 10% of v0.6 pairs hidden,
    predictors trained on the rest. Temporal holdout: pairs first present in v0.11 (2026-09-10) between species already in
    the v0.6 (2023-08-25) graph, predictors trained on all of v0.6. Advantage of the best structural predictor (taxonomy +
    structure, chosen on the random holdout) over effort: {p['A_random']:+.3f} random, {p['A_temporal']:+.3f} temporal;
    ratio {p['rho']:.2f} ({p['rho_ci'][0]:.2f} to {p['rho_ci'][1]:.2f}, cluster bootstrap over source datasets).""")


def f2(p):
    rows = [("all temporal", p["auroc"]["temporal"])] + [(k.replace("_", " "), v) for k, v in p["temporal_subsets"].items()] + \
           [("without trophiCH", p["without_trophiCH"]["auroc"]), ("degree-matched\nnegatives (D1)", p["degree_matched"]["temporal"])]
    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.25, top=0.83)
    x = np.arange(len(rows))
    for k, (key, lab, col) in enumerate(PRED):
        ax.bar(x + (k - 1) * 0.26, [r[1][key] for r in rows], width=0.24, color=col, label=lab)
    ax.set_xticks(x); ax.set_xticklabels([r[0] for r in rows], fontsize=8)
    ax.set_ylim(0.45, 1.0); ax.set_ylabel("AUROC, temporal holdout"); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3)
    fig.suptitle("The edge holds for new datasets, newly studied species and without trophiCH;\n"
                 "with degree-matched negatives effort falls to chance", x=0.02, ha="left", fontsize=9.5, color=INK)
    fig.savefig(F / "F2_subsets.png", dpi=170); plt.close(fig)
    s = p["temporal_subsets"]
    caption("F2_subsets", f"""Temporal holdout. New dataset: positives whose introducing source dataset was not in v0.6
    ({s['new_dataset']['pos']:,} of {p['n']['temporal']['pos']:,}). Cold start: an endpoint with a single v0.6 link
    ({s['cold_start']['pos']:,}). Without trophiCH: positives from the Swiss metaweb removed
    ({p['without_trophiCH']['trophiCH_positives']:,}; most of its species-level links are inferred). Degree-matched (D1):
    negatives drawn without replacement so every decile of the positives' log degree product holds ten negatives per
    positive.""")


if __name__ == "__main__":
    p = json.load(open(T / "primary.json"))
    f1(p); f2(p)
    print("figures written")
