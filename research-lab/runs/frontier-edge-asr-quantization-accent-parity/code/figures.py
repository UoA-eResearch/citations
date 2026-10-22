"""Figures for the report (each PNG has a .txt caption). Written after the results.

  F1  compression penalty on the pooled worst-3 vs best-3 accent gap, every condition and seed, with 95% intervals
  F2  WER by accent group: FP16, GPTQ-W3 with US-only calibration, GPTQ-W3 with worst-weighted calibration (seed means)
"""
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
COL = {"us": "#8a8984", "balanced": "#2a78d6", "worst": "#e8a317", "mp": "#b04a8b", "mp3": "#b04a8b", "rtn": "#52514e",
       "awq": "#6aa84f"}
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def kind(c):
    if c.startswith("rtn"):
        return "rtn"
    if c.startswith("awq"):
        return "awq"
    if c.startswith("mp3") or c.startswith("mp_"):
        return "mp"
    return c.split("_")[2]


def f1(model):
    a = json.loads((T / f"analysis_{model}.json").read_text())
    pc = a["per_condition"]
    order = []
    for bits in ("w8", "w4", "w3"):
        order += [c for c in sorted(pc) if c.startswith(f"rtn_{bits}")]
        for comp in ("us", "balanced", "worst"):
            order += sorted(c for c in pc if re.fullmatch(f"gptq_{bits}_{comp}_s\\d", c))
        if bits == "w4":
            order += sorted(c for c in pc if c.startswith("mp_")) + sorted(c for c in pc if c.startswith("awq"))
        if bits == "w3":
            order += sorted(c for c in pc if c.startswith("mp3"))
    fig, ax = plt.subplots(figsize=(7.4, 0.2 * len(order) + 1.2))
    fig.subplots_adjust(left=0.27, right=0.97, bottom=0.08, top=0.93)
    for i, c in enumerate(order):
        v = pc[c]
        ax.plot([100 * v["penalty_ci"][0], 100 * v["penalty_ci"][1]], [i, i], color=COL[kind(c)], lw=1.5)
        ax.plot(100 * v["penalty"], i, "o", color=COL[kind(c)], ms=4)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(range(len(order)), order)
    ax.invert_yaxis()
    ax.set_xlabel("penalty on the worst-3 vs best-3 accent gap (WER points, vs FP16)")
    ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle(f"Whisper-{model}: accent-gap penalty by condition and calibration seed", x=0.02, ha="left",
                 fontsize=10, color=INK)
    fig.savefig(F / f"F1_penalty_{model}.png", dpi=170)
    plt.close(fig)
    caption(f"F1_penalty_{model}", f"""Change in the pooled WER gap between the 3 accent groups with the highest and
    the 3 with the lowest FP16 WER ({', '.join(a['worst3_fp16'])} vs {', '.join(a['best3_fp16'])}), relative to FP16,
    for every decoded condition; dots are point estimates, lines 95% speaker-clustered bootstrap intervals. Grey: US-only
    calibration; blue: accent-balanced; orange: worst-weighted; purple: accent-aware mixed precision; green: AWQ-style;
    dark grey: round-to-nearest.""")


def f2(model):
    a = json.loads((T / f"analysis_{model}.json").read_text())
    pc = a["per_condition"]
    groups = sorted(a["fp16_group_wer"], key=lambda g: a["fp16_group_wer"][g])

    def mean(prefix):
        cs = [c for c in pc if re.fullmatch(prefix + r"_s\d", c)]
        return {g: np.mean([pc[c]["group_wer"][g] for c in cs]) for g in groups} if cs else None
    series = [("FP16", {g: a["fp16_group_wer"][g] for g in groups}, INK2),
              ("GPTQ-W3, US-only calibration", mean("gptq_w3_us"), COL["us"]),
              ("GPTQ-W3, worst-weighted calibration", mean("gptq_w3_worst"), COL["worst"])]
    series = [s for s in series if s[1]]
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    fig.subplots_adjust(left=0.27, right=0.97, bottom=0.12, top=0.86)
    w = 0.8 / len(series)
    for j, (lab, d, col) in enumerate(series):
        ax.barh([i + j * w for i in range(len(groups))], [100 * d[g] for g in groups], height=w, color=col, label=lab)
    ax.set_yticks([i + w for i in range(len(groups))], groups)
    ax.set_xlabel("WER (%)")
    ax.grid(axis="x", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    fig.suptitle(f"Whisper-{model}: WER by accent group (EdAcc test)", x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / f"F2_groups_{model}.png", dpi=170)
    plt.close(fig)
    caption(f"F2_groups_{model}", """Word error rate by EdAcc accent group (named groups: at least 2 test speakers and 10
    minutes), for FP16 and the mean over three calibration seeds of GPTQ-W3 with US-only and with worst-weighted
    calibration. Groups are ordered by FP16 WER.""")


if __name__ == "__main__":
    for m in sys.argv[1:] or ["small"]:
        f1(m)
        f2(m)
    print("figures written")
