"""Figure (PNG + .txt caption). Written after score.py.

  F1  left: share of pairwise model orderings reversed by season; right: relative WIS under first-report vs finalised
      truth, 2024-25 horizon 1 (models covering >= 80% of cells)
"""
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, RED = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#d6532a"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
p = json.load(open(T / "primary.json"))
agg = defaultdict(lambda: [0, 0])
for k, v in p["per_season_horizon"].items():
    agg[k.split()[0]][0] += v["reversals"]; agg[k.split()[0]][1] += v["pairs"]
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.5), gridspec_kw={"width_ratios": [1, 1.2]})
fig.subplots_adjust(left=0.08, right=0.98, bottom=0.16, top=0.82, wspace=0.3)
ax = axes[0]
ss = sorted(agg)
vals = [agg[s][0] / agg[s][1] * 100 for s in ss]
ax.bar(ss, vals, color=BLUE, width=0.6)
for i, (s, v) in enumerate(zip(ss, vals)):
    ax.annotate(f"{v:.1f}%\n({agg[s][0]}/{agg[s][1]})", (i, v), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7.5)
ax.axhline(20, color=RED, lw=0.9, ls="--"); ax.annotate("H1 bar 20%", (2.3, 20), xytext=(0, 3), textcoords="offset points", ha="right", fontsize=7.5, color=RED)
ax.set_ylim(0, 25); ax.set_ylabel("pairwise orderings reversed (%)"); ax.grid(axis="y", color=GRID, lw=0.5)
ax.set_title("reversals by season (all horizons)", fontsize=9, color=INK, loc="left")
ax = axes[1]
rw = pd.read_csv(T / "relative_wis.csv")
r = rw[rw.season_h == "2024-25 h1"]
ax.scatter(r.rel_wis_final, r.rel_wis_first, s=16, color=INK2)
lim = [min(r.rel_wis_final.min(), r.rel_wis_first.min()) * 0.95, max(r.rel_wis_final.max(), r.rel_wis_first.max()) * 1.03]
ax.plot(lim, lim, color=GRID, lw=1)
for m in (p["best"]["2024-25 h1"]["first"], p["best"]["2024-25 h1"]["final"]):
    x = r[r.model == m]
    ax.scatter(x.rel_wis_final, x.rel_wis_first, s=30, color=RED)
    ax.annotate(m, (x.rel_wis_final.iloc[0], x.rel_wis_first.iloc[0]), xytext=(5, -3), textcoords="offset points", fontsize=7.5, color=RED)
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("relative WIS, finalised truth"); ax.set_ylabel("relative WIS, first-report truth")
ax.set_title("2024-25, 1 week ahead (largest revisions)", fontsize=9, color=INK, loc="left"); ax.grid(color=GRID, lw=0.5)
fig.suptitle("Scoring flu forecasts on first-reported data reorders few model pairs; the leader changes only in 2024-25",
             x=0.02, ha="left", fontsize=9.5, color=INK)
fig.savefig(F / "F1_reversals.png", dpi=170)
(F / "F1_reversals.txt").write_text(" ".join("""FluSight state and national weekly influenza hospital admission forecasts, 2022-23 to
2024-25, scored by WIS against the first-reported value of each location-week (earliest version of the hub's truth file
containing it) and against the finalised value. Left: share of model pairs (at least 100 common forecasts, within season
and horizon) whose mean-WIS ordering differs between the two scorings. Right: relative WIS (geometric mean of pairwise
WIS ratios) of well-covered models in 2024-25 at horizon 1 under both scorings; red, the best non-ensemble model under
each.""".split()) + "\n")
print("figure written")
