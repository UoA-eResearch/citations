"""Figures (each PNG has a .txt caption). Written after fit.py.

  F1  the ladder: eval loss against training tokens for every size and seed (fp32), with the 1B-2.8B targets
  F2  extrapolated Pythia-2.8B loss across single-seed ladders, against the actual loss
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
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
SIZES = ["14m", "31m", "70m", "160m", "410m"]
COL = dict(zip(SIZES, ["#9ecae1", "#6baed6", "#3182bd", "#08519c", "#08306b"]))
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1(p):
    L = pd.read_csv(T / "losses.csv")
    L = L[L.dtype == "float32"]
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    fig.subplots_adjust(left=0.1, right=0.86, bottom=0.13, top=0.88)
    for s in SIZES:
        for seed, g in L[L["size"] == s].groupby("seed"):
            g = g.sort_values("D")
            ax.plot(g.D, g.loss, color=COL[s], lw=0.9, alpha=0.8, marker="o", ms=2)
        last = L[(L["size"] == s) & (L.step == 143000)].loss.median()
        ax.annotate(s.upper(), (3.0e11, last), xytext=(6, 0), textcoords="offset points", color=COL[s], fontsize=8, va="center")
    for k, v in p["target"].items():
        ax.scatter([3.0e11], [v["loss"]], marker="D", s=22, color="#d6532a", zorder=5)
        ax.annotate(k.upper(), (3.0e11, v["loss"]), xytext=(6, 0), textcoords="offset points", color="#d6532a", fontsize=8, va="center")
    ax.set_xscale("log")
    ax.set_xlabel("training tokens D")
    ax.set_ylabel("eval loss (nats, Pile validation)")
    ax.grid(color=GRID, lw=0.5)
    fig.suptitle("Ten seeds per size: most runs agree closely, but a few jump late in training", x=0.02, ha="left",
                 fontsize=10, color=INK)
    fig.savefig(F / "F1_ladder.png", dpi=170); plt.close(fig)
    caption("F1_ladder", """PolyPythias (seeds 0-9) at sizes 14M-410M, eight checkpoints each (steps 2,000-143,000),
    evaluated in fp32 on 5.0M tokens of Pile validation (D1). Orange diamonds: the final Pythia-1B, 1.4B (fp32) and
    2.8B (fp16) losses, the extrapolation targets.""")


def f2(p):
    S = pd.read_csv(T / "ladders_single.csv")
    actual = p["target"]["2.8b"]["loss"]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.15, top=0.85)
    x = S.pred_2p8b.clip(upper=2.3)
    ax.hist(x, bins=80, color="#3182bd", alpha=0.85)
    lo, hi = np.percentile(S.pred_2p8b, [5, 95])
    for v in (lo, hi):
        ax.axvline(v, color=INK2, lw=0.8, ls="--")
    ax.axvline(actual, color="#d6532a", lw=2)
    ax.annotate(f"actual 2.8B\n{actual:.3f}", (actual, ax.get_ylim()[1] * 0.85), xytext=(-6, 0), textcoords="offset points",
                ha="right", color="#d6532a", fontsize=8)
    ax.annotate(f"5th–95th percentile\nW₁ = {p['W']['1']:.3f} nats", (hi, ax.get_ylim()[1] * 0.6), xytext=(-6, 0),
                textcoords="offset points", ha="right", color=INK2, fontsize=8)
    ax.set_xlabel("extrapolated Pythia-2.8B loss (nats)")
    ax.set_ylabel("single-seed ladders")
    ax.grid(axis="y", color=GRID, lw=0.5)
    above = (S.pred_2p8b > actual).mean()
    fig.suptitle(f"Which seed you train shifts the 2.8B forecast by {p['W']['1']:.2f} nats; {above:.0%} of fits overshoot",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F2_extrapolation.png", dpi=170); plt.close(fig)
    caption("F2_extrapolation", f"""Extrapolated loss of Pythia-2.8B (N of its config, D = 300B) from 2,000 single-seed
    ladders (one random seed per size, 40 points each), each fitted with the Chinchilla form by Huber loss on log L.
    Dashed: 5th and 95th percentiles. Orange: the actual 2.8B loss (seed 0, fp16). Values above 2.3 are clipped into
    the last bin. Three-seed averaging narrows the range only to {p['W']['3']:.3f}.""")


if __name__ == "__main__":
    p = json.load(open(T / "primary.json"))
    f1(p); f2(p)
    print("figures written")
