"""Figures for the report (each PNG has a .txt caption). Written after analyse.py was written, before it was run.

  F1  signed bias (retrospective - prospective RMSE) of the primary model by splitter, per target, with medians
  F2  mean Kendall tau between retrospective and prospective model rankings, by splitter
  F3  median signed bias by the prospective set's similarity to the training data (terciles), by splitter
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
SPLITTERS = ["random", "scaffold", "cluster", "document", "author", "assay", "time"]
# colour by hypothesis role, not by splitter: H1 splitters orange, H2 splitters blue, the rest grey
ROLE = {"random": ORANGE, "scaffold": ORANGE, "document": BLUE, "author": BLUE}


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1(p, L):
    P = L[(L.set == p["primary_set"]) & (L.model == "rf")]
    sp = [s for s in SPLITTERS if s in p["bias_rf"]]
    fig, ax = plt.subplots(figsize=(7.8, 3.8))
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.14, top=0.84)
    rng = np.random.default_rng(1)
    for i, s in enumerate(sp):
        y = P[P.splitter == s].bias.to_numpy()
        ax.scatter(i + rng.uniform(-0.28, 0.28, len(y)), y, s=6, color=ROLE.get(s, GREY), alpha=0.35, lw=0)
        r = p["bias_rf"][s]
        ax.plot([i - 0.34, i + 0.34], [r["median_bias"]] * 2, color=INK, lw=2)
        ax.plot([i, i], r["ci"], color=INK, lw=1)
        ax.text(i, r["median_bias"], f" {r['median_bias']:+.2f}", fontsize=7.5, color=INK, va="bottom", ha="left")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.axhline(-0.25, color=ORANGE, lw=0.8, ls="--")
    ax.text(len(sp) - 0.5, -0.25, "H1 bar (-0.25)", fontsize=7, color=INK2, va="bottom", ha="right")
    ax.set_xticks(range(len(sp))); ax.set_xticklabels(sp)
    ax.set_ylabel("retrospective - prospective RMSE (pChEMBL)")
    lo, hi = np.percentile(P.bias, [1, 99])
    ax.set_ylim(min(lo, -0.6), max(hi, 0.4))
    ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("How far each split's error estimate sits from the error on later chemistry (random forest, one dot per target)",
                 x=0.02, ha="left", fontsize=9.5, color=INK)
    fig.savefig(F / "F1_bias_by_splitter.png", dpi=170); plt.close(fig)
    caption("F1_bias_by_splitter", f"""Signed bias of the ECFP4 random forest's retrospective RMSE against its prospective RMSE
    on ChEMBL 37 compounds first measured in 2023+ documents, one dot per target ({P.target.nunique()} targets). Bars:
    medians with 95% bootstrap intervals over targets. Negative means the split understated the error. Orange: the
    H1 splitters; blue: the H2 provenance splitters. The y-axis is clipped to the 1st-99th percentiles.""")


def f2(p):
    mt = p["H3"]["mean_tau"]
    sp = [s for s in SPLITTERS if s in mt]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    fig.subplots_adjust(left=0.11, right=0.98, bottom=0.15, top=0.82)
    for i, s in enumerate(sp):
        ax.bar(i, mt[s]["mean"], width=0.6, color=ROLE.get(s, GREY))
        ax.plot([i, i], mt[s]["ci"], color=INK, lw=1)
        ax.text(i, mt[s]["mean"], f"{mt[s]['mean']:.2f}", fontsize=7.5, color=INK, ha="center", va="bottom")
    for y, lab in ((0.6, "H3: scaffold <= 0.6"), (0.8, "H3: document >= 0.8")):
        ax.axhline(y, color=INK2, lw=0.6, ls=":")
        ax.text(len(sp) - 0.5, y, lab, fontsize=7, color=INK2, ha="right", va="bottom")
    ax.set_xticks(range(len(sp))); ax.set_xticklabels(sp)
    ax.set_ylabel("mean Kendall tau (5 models)")
    ax.set_ylim(min(0, min(v["ci"][0] for v in mt.values()) - 0.05), 1)
    ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Does the split pick the same best model as later data?", x=0.02, ha="left", fontsize=9.5, color=INK)
    fig.savefig(F / "F2_ranking_tau.png", dpi=170); plt.close(fig)
    caption("F2_ranking_tau", """Per target, Kendall tau between the five model families' ranking by retrospective RMSE
    and by prospective RMSE, averaged over targets, with 95% bootstrap intervals. 1 means the split ranks the models
    exactly as the later data do.""")


def f3(p):
    b = p["bias_by_similarity_rf"]
    terc = ["low", "mid", "high"]
    sp = [s for s in SPLITTERS if all(s in b.get(t, {}) for t in terc)]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    fig.subplots_adjust(left=0.11, right=0.8, bottom=0.15, top=0.84)
    for s in sp:
        y = [b[t][s] for t in terc]
        ax.plot(range(3), y, marker="o", ms=4, lw=1.6 if s in ROLE else 1, color=ROLE.get(s, GREY))
        ax.text(2.06, y[-1], s, fontsize=7.5, color=INK2, va="center")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks(range(3)); ax.set_xticklabels(["low", "middle", "high"])
    ax.set_xlabel("prospective set's median nearest-neighbour similarity to the training set (tercile of targets)")
    ax.set_ylabel("median signed bias (RF)")
    ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Bias by how novel the later chemistry is", x=0.02, ha="left", fontsize=9.5, color=INK)
    fig.savefig(F / "F3_bias_by_similarity.png", dpi=170); plt.close(fig)
    caption("F3_bias_by_similarity", """Median signed bias of the random forest by tercile of targets ranked by the median
    Tanimoto similarity of their prospective compounds to the nearest training compound (ECFP4).""")


if __name__ == "__main__":
    p = json.loads((T / "primary.json").read_text())
    L = pd.read_csv(T / "bias_long.csv")
    f1(p, L); f2(p); f3(p)
    print("figures written")
