"""Figures for the report (each PNG has a .txt caption).

  F1  each run's simulated price band (10th-90th percentile) against the realised price, over time
  F2  the probability integral transform: where realised prices fell in their own simulated distributions
  F3  exceedance of the simulated 90th percentile, by forecast horizon and by storage state
"""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
BAND, LINE, HIT = "#9cc3ea", "#2a78d6", "#eb6834"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
S = 2  # the primary stage


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def main():
    p = json.load(open(T / "primary.json"))
    rows = [r for r in csv.DictReader(open(T / "runs.csv")) if r.get(f"s{S}_actual")]
    rows.sort(key=lambda r: r[f"s{S}_start"])
    x = np.arange(len(rows))
    num = lambda k: np.array([float(r[k]) if r[k] not in ("", None) else np.nan for r in rows])
    p10, p50, p90, act = num(f"s{S}_p10"), num(f"s{S}_p50"), num(f"s{S}_p90"), num(f"s{S}_actual")
    exceed = np.array([r[f"s{S}_exceed"] == "1" for r in rows])
    starts = [r[f"s{S}_start"] for r in rows]

    # F1: the band against what happened
    fig, ax = plt.subplots(figsize=(7.8, 3.9))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.14, top=0.83)
    ax.fill_between(x, p10, p90, color=BAND, alpha=0.55, lw=0, label="JADE 10th-90th percentile (91 inflow years)")
    ax.plot(x, p50, "-", color=LINE, lw=1.3, label="JADE median")
    ax.plot(x, act, "-", color=INK, lw=1.5, label="realised price at Haywards")
    ax.plot(x[exceed], act[exceed], "o", color=HIT, ms=5, mec=SURF, mew=0.8,
            label=f"above the 90th percentile ({int(exceed.sum())} of {len(rows)} weeks)")
    ks = [i for i, s in enumerate(starts) if s.endswith("-01-01") or s[5:7] in ("01", "07") and s[8:10] <= "07"]
    seen, ticks = set(), []
    for i in ks:
        lab = starts[i][:7]
        if lab not in seen:
            seen.add(lab); ticks.append((i, lab))
    ax.set_xticks([i for i, _ in ticks]); ax.set_xticklabels([l for _, l in ticks], fontsize=7.6)
    ax.set_ylabel("weekly average price, $/MWh")
    ax.set_yscale("log")
    ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=7.6, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    fig.suptitle("What the official model simulated, and what the market did", x=0.1, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F1_band_vs_actual.png", dpi=170); plt.close(fig)
    caption("F1_band_vs_actual", f"""For each published weekly JADE run, the simulated distribution of the average
    wholesale price at Haywards in the run's first fully out-of-sample week (stage 2), against the price actually
    settled in that week. The band spans the 10th to 90th percentile of the run's 91 historical inflow sequences.
    Orange markers are weeks when the realised price finished above the simulated 90th percentile, which a
    calibrated model would do about a tenth of the time; here it happens in {int(exceed.sum())} of {len(rows)}
    weeks. Log scale.""")

    # F2: PIT
    hist = np.array(p["pit"]["hist"], float)
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    fig.subplots_adjust(left=0.12, right=0.97, bottom=0.17, top=0.8)
    centres = np.arange(10) * 0.1 + 0.05
    ax.bar(centres, hist, width=0.088, color=BAND, edgecolor=SURF, lw=1.2)
    # both end bins are failures: the week finished outside the simulated 10th-90th range
    ax.bar(centres[[0, -1]], hist[[0, -1]], width=0.088, color=HIT, edgecolor=SURF, lw=1.2)
    ax.axhline(hist.sum() / 10, color=INK2, lw=1.2, ls="--")
    ax.annotate("what a calibrated model\nwould give in each bin", (0.5, hist.sum() / 10), xytext=(0, 16),
                textcoords="offset points", fontsize=7.4, color=INK2, ha="center")
    ax.annotate(f"{int(hist[-1])} weeks\nabove the band", (centres[-1], hist[-1]), xytext=(-6, -26),
                textcoords="offset points", fontsize=7.4, color="#8f3a12", ha="right")
    ax.annotate(f"{int(hist[0])} weeks\nbelow it", (centres[0], hist[0]), xytext=(8, 6),
                textcoords="offset points", fontsize=7.4, color="#8f3a12")
    ax.set_xlabel("where the realised price fell in its own simulated distribution")
    ax.set_ylabel("weekly runs")
    ax.set_xticks(np.arange(0, 1.01, 0.1))
    ax.set_xticklabels([f"{int(v * 100)}%" for v in np.arange(0, 1.01, 0.1)], fontsize=7.4)
    ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Almost every week finished outside the simulated range", x=0.12, ha="left", fontsize=10.5,
                 color=INK)
    fig.savefig(F / "F2_pit.png", dpi=170); plt.close(fig)
    caption("F2_pit", """The probability integral transform. For every weekly run, the share of its 91 simulated
    prices that were below the price actually realised. A calibrated model spreads these evenly across the ten
    bins (dashed line). Weight piled into the right-hand bin means the model's upper tail is too thin: the market
    repeatedly settled above almost everything the model simulated.""")

    # F3: by horizon and by storage
    bs = list(csv.DictReader(open(T / "by_stage.csv")))
    labels = [f"stage {r['stage']}" + (" (primary)" if int(r["stage"]) == S else "") for r in bs]
    rate = [float(r["rate"]) for r in bs]
    lo = [float(r["lo"]) for r in bs]; hi = [float(r["hi"]) for r in bs]
    h2 = p.get("H2", {})
    extra = []
    if h2.get("scored"):
        extra = [(f"lakes in the bottom fifth (n={h2['n_low']})", h2["rate_low"], None, None),
                 (f"other weeks (n={h2['n_high']})", h2["rate_high"], None, None)]
    fig, ax = plt.subplots(figsize=(7.6, 3.5))
    fig.subplots_adjust(left=0.33, right=0.96, bottom=0.17, top=0.8)
    allrows = [(labels[i], rate[i], lo[i], hi[i]) for i in range(len(bs))] + extra
    for k, (lab, v, l, h) in enumerate(allrows):
        c = HIT if "primary" in lab else INK2
        if l is not None:
            ax.plot([l, h], [k, k], color=c, lw=2.4)
        ax.plot(v, k, "o", color=c, ms=8 if "primary" in lab else 6, mec=SURF, mew=1.2)
        ax.annotate(f"{v * 100:.0f}%", (v, k), xytext=(0, 9), textcoords="offset points", ha="center",
                    fontsize=7.6, color=INK2)
    ax.axvline(0.10, color=INK2, lw=1.0, ls="--")
    ax.axvline(0.20, color=HIT, lw=1.0, ls=":")
    ax.set_ylim(-0.9, len(allrows) - 0.4)
    ax.annotate("what calibration would give: 10%", (0.10, -0.82), xytext=(4, 0),
                textcoords="offset points", fontsize=7.2, color=INK2, va="center")
    ax.annotate("H1 threshold: 20%", (0.20, -0.35), xytext=(4, 0), textcoords="offset points",
                fontsize=7.2, color=HIT, va="center")
    ax.set_yticks(range(len(allrows))); ax.set_yticklabels([a[0] for a in allrows])
    ax.set_xlabel("share of weeks above the simulated 90th percentile")
    ax.set_xlim(left=0)
    ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("Exceedance by forecast horizon, and by how full the lakes were", x=0.33, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F3_exceedance.png", dpi=170); plt.close(fig)
    caption("F3_exceedance", """The share of weekly runs whose realised price exceeded the simulated 90th
    percentile, by forecast horizon (stage 1 is the week the inputs were frozen, stage 2 the first fully
    out-of-sample week) and, where the hydrological record allows the split, by whether national energy storage
    was in the bottom fifth of its history for that week of the year. Bars are moving-block bootstrap 95%
    intervals. A calibrated model would sit on the dashed line.""")
    print("figures written")


if __name__ == "__main__":
    main()
