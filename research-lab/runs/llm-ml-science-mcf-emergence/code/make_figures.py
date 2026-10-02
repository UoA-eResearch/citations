#!/usr/bin/env python
"""Figures for the report (results/figures/F*.png, each with a caption file)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
INK, MUTED, GRID = "#0b0b0b", "#898781", "#e1e0d9"
GROUP_COL = {"pythia_scale": "#104281", "polypythia_410m": "#2a78d6", "floor_160m": "#9cc3ec", "olmo2": "#eb6834",
             "added_olmo": "#1baf7a"}
GROUP_LAB = {"pythia_scale": "Pythia 1B-6.9B", "polypythia_410m": "PolyPythias 410M (10 seeds)",
             "floor_160m": "Pythia 160M (10 seeds)", "olmo2": "OLMo-2 1B / 7B", "added_olmo": "OLMo-1B-0724 / 7B-0424"}
TASK_LAB = {"arc_easy": "ARC-Easy", "arc_challenge": "ARC-Challenge", "csqa": "CommonsenseQA", "piqa": "PIQA",
            "hellaswag": "HellaSwag", "mmlu": "MMLU"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})


def caption(name, text):
    (FIG / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1_all_runs(w):
    w = w.assign(excess=(w.acc_mcf5 - w.chance_mcf5) * 100)
    m = w.groupby(["group", "run", "tokens"]).agg(excess=("excess", "mean"), mass=("mass_mcf5", "mean")).reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for (group, run), g in m.groupby(["group", "run"]):
        g = g.sort_values("tokens")
        big = run in ("OLMo-2-1124-7B", "OLMo-7B-0424-hf", "pythia-6.9b")
        for ax, col in zip(axes, ("excess", "mass")):
            ax.plot(g.tokens / 1e9, g[col], color=GROUP_COL[group], lw=1.6 if big else 0.8, alpha=1 if big else 0.6)
    for g, c in GROUP_COL.items():
        axes[0].plot([], [], color=c, label=GROUP_LAB[g])
    axes[0].axhline(5, color=MUTED, ls="--", lw=0.8)
    axes[0].set_ylabel("five-shot MCF accuracy above chance (points, mean of 6 tasks)")
    axes[1].axhline(0.5, color=MUTED, ls="--", lw=0.8)
    axes[1].set_ylabel("five-shot letter mass (mean of 6 tasks)")
    for ax in axes:
        ax.set_xscale("log")
        ax.set_xlabel("training tokens (billions)")
    axes[0].legend(fontsize=7, loc="upper left")
    axes[0].set_title("accuracy in multiple-choice format")
    axes[1].set_title("probability on the answer letters")
    fig.savefig(FIG / "F1_all_runs.png")
    plt.close(fig)
    caption("F1_all_runs", """F1. All 28 training runs. Left: five-shot multiple-choice-format accuracy above chance,
averaged over the six tasks (dashed: the +5-point departure threshold). Right: mean probability the model puts on the
valid answer letters (dashed: the 0.5 threshold). Thick lines: the three 7B-class runs. Only the two OLMo 7B runs leave
chance; letter mass passes 0.5 by 21B tokens in 163 of the 168 run-task units, whether or not the format is ever learned.""")


def f2_olmo7b(w, u):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, run in zip(axes, ("OLMo-2-1124-7B", "OLMo-7B-0424-hf")):
        g = w[w.run == run]
        for i, (task, h) in enumerate(g.groupby("task")):
            h = h.sort_values("tokens")
            c = plt.cm.tab10(i)
            ax.plot(h.tokens / 1e9, (h.acc_mcf5 - h.chance_mcf5) * 100, "o-", ms=2.5, color=c, label=TASK_LAB[task])
            dep = u[(u.run == run) & (u.task == task)].departure_mcf5.values[0]
            if np.isfinite(dep):
                ax.axvline(dep / 1e9, color=c, lw=0.6, ls=":")
        ax.axhline(5, color=MUTED, ls="--", lw=0.8)
        ax.set_xscale("log")
        ax.set_title(run)
        ax.set_xlabel("training tokens (billions)")
    axes[0].set_ylabel("five-shot MCF accuracy above chance (points)")
    axes[0].legend(fontsize=7, loc="upper left")
    fig.savefig(FIG / "F2_olmo7b.png")
    plt.close(fig)
    caption("F2_olmo7b", """F2. The two runs that learn the format, task by task. Dotted lines mark each task's departure
(the first checkpoint above chance + 5 points that stays there). Departures cluster: three tasks at 307B tokens for
OLMo-2 7B and four at 490B for OLMo-7B-0424 (OLMES places this model's transition at about 400B).""")


def f3_timing(u):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for g, h in u.groupby("group"):
        x = h.masscross_mcf5 / 1e9
        dep = h.departure_mcf5 / 1e9
        never = dep.isna()
        last = h.last_tokens / 1e9
        if (~never).any():
            ax.scatter(x[~never], dep[~never], color=GROUP_COL[g], s=22, label=GROUP_LAB[g] + ": leaves chance", zorder=3)
        if never.any():
            ax.scatter(x[never], last[never] * 1.15, color=GROUP_COL[g], s=12, marker="^", alpha=0.6,
                       label=GROUP_LAB[g] + ": never (at last checkpoint)")
    lim = [1, 6000]
    ax.plot(lim, lim, color=MUTED, lw=0.8)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(1, 6000); ax.set_ylim(1, 6000)
    ax.set_xlabel("tokens when letter mass first passes 0.5 (billions)")
    ax.set_ylabel("tokens at departure from chance (billions)")
    ax.legend(fontsize=6.5, loc="lower right")
    fig.savefig(FIG / "F3_timing.png")
    plt.close(fig)
    caption("F3_timing", """F3. The candidate leading indicator against the event it should predict, one point per run and
task. Circles: units that leave chance. Triangles: units that never leave chance, plotted just above their run's last
checkpoint. Letter mass passes 0.5 early whether or not the format is ever learned; where the format is learned, it does so 31
to 244 times earlier (in tokens) than the departure from chance.""")


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    w = pd.read_csv(TAB / "checkpoint_metrics.csv")
    u = pd.read_csv(TAB / "units.csv")
    f1_all_runs(w)
    f2_olmo7b(w, u)
    f3_timing(u)
    print("figures written")


if __name__ == "__main__":
    main()
