"""F3 (D4): the W3 penalty by calibration composition under each scoring variant, Whisper-small on EdAcc and on the
Common Voice replication (D5). Reads results/tables/robustness_small.json and robustness_small_cv.json."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
INK, INK2, GRID, SURF, BLUE, ORANGE, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317", "#9a9893"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
VARS = [("prereg", "preregistered"), ("capped", "capped at\n100%/utt"), ("no_loops", "looped utts\nremoved"),
        ("sub_del", "subs + dels\nonly")]
COMPS = [("gptq_w3_us", "US-only", GREY), ("gptq_w3_balanced", "balanced", BLUE), ("gptq_w3_worst", "worst-weighted", ORANGE)]


def panel(ax, r, title):
    x = np.arange(len(VARS))
    for k, (comp, lab, col) in enumerate(COMPS):
        vals, lo, hi = [], [], []
        for v, _ in VARS:
            p = r["variants"][v]["refixed"]["penalties"][comp]
            vals.append(100 * p["penalty"]); lo.append(100 * p["ci"][0]); hi.append(100 * p["ci"][1])
        vals, lo, hi = map(np.array, (vals, lo, hi))
        ax.errorbar(x + (k - 1) * 0.22, vals, yerr=[vals - lo, hi - vals], fmt="o", color=col, ms=5, capsize=2, lw=1.2, label=lab)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels([l for _, l in VARS], fontsize=7.5)
    ax.set_title(title, fontsize=9, color=INK, loc="left"); ax.grid(axis="y", color=GRID, lw=0.5)


def main():
    a = json.load(open(T / "robustness_small.json"))
    b = json.load(open(T / "robustness_small_cv.json"))
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.7), sharey=True)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.2, top=0.82, wspace=0.08)
    panel(axes[0], a, "EdAcc test (8,537 utterances)")
    panel(axes[1], b, "Common Voice replication (4,012 clips)")
    axes[0].set_ylabel("3-bit accent-gap penalty (WER points)")
    axes[1].legend(frameon=False, fontsize=8, loc="upper right")
    fig.suptitle("Most of the 3-bit accent penalty is runaway repetition loops, and calibration mix does not remove it",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F3_robust_w3.png", dpi=170); plt.close(fig)
    (F / "F3_robust_w3.txt").write_text(" ".join(f"""Whisper-small, GPTQ-W3 g128, three calibration draws per composition averaged;
    penalty = (pooled WER of the 3 worst FP16 groups minus the 3 best) minus the same in FP16, groups re-fixed from FP16 under
    each scoring; 95% speaker-clustered bootstrap (calibration draws not resampled). Capped: errors per utterance at most the
    reference length. Looped utterances removed: any utterance looped in any condition. Substitutions + deletions: insertions
    dropped. D4 and D5, after the independent review.""".split()) + "\n")
    print("F3 written")


if __name__ == "__main__":
    main()
