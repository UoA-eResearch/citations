"""Figures (PNG + .txt caption). Written after classify.py run.
  F1  share of classified advisories whose lower bound is over-approximated, by ecosystem and lower-bound kind
  F2  how far declared lower bounds sit before the corrected ones (years), over-approximated advisories
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
INK, INK2, GRID, SURF, BLUE, ORANGE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#d6532a"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.facecolor": SURF, "figure.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False})
p = json.load(open(T / "primary.json"))
C = pd.read_csv(T / "classes.csv")
groups = [("all", p["H1"]["over_approximated"], p["H1"]["classified"], p["H1"]["wilson"])]
for k, v in p["by_ecosystem"].items():
    groups.append((k, v["over"], v["classified"], v["wilson"]))
for k, v in p["by_lower_bound"].items():
    groups.append((k, v["over"], v["classified"], v["wilson"]))
fig, ax = plt.subplots(figsize=(6.4, 3.4))
fig.subplots_adjust(left=0.24, right=0.97, bottom=0.16, top=0.85)
y = np.arange(len(groups))[::-1]
for yy, (lab, k, n, ci) in zip(y, groups):
    ax.plot([ci[0], ci[1]], [yy, yy], color=BLUE, lw=2)
    ax.plot(k / n, yy, "o", color=BLUE, ms=6)
    ax.annotate(f"{k}/{n}", (ci[1], yy), xytext=(5, 0), textcoords="offset points", va="center", fontsize=8, color=INK)
ax.axvline(0.25, color=ORANGE, lw=1, ls="--")
ax.annotate("H1 bar 25%", (0.25, -0.45), xytext=(4, 0), textcoords="offset points", fontsize=8, color=ORANGE)
ax.set_yticks(y); ax.set_yticklabels([g[0] for g in groups])
ax.set_xlim(0, 1); ax.set_xlabel("share over-approximated among classified advisories (95% Wilson)")
ax.grid(axis="x", color=GRID, lw=0.5)
fig.suptitle("Pipeline flags: lower bounds the code-presence test calls too early (not confirmed by the audit)", x=0.02, ha="left", fontsize=10, color=INK)
fig.savefig(F / "F1_share.png", dpi=170); plt.close(fig)
(F / "F1_share.txt").write_text("Share of classified (tight or over-approximated) GHSA advisories for npm and PyPI whose declared lower bound "
                                "starts before the first release containing the code the fix removes or guards, with Wilson 95% intervals; "
                                f"{p['H1']['undetermined_share']:.0%} of the 800 sampled advisories are undetermined and excluded.\n")
ov = C[C.cls == "over-approximated"].dropna(subset=["gap_years"])
fig, ax = plt.subplots(figsize=(6.2, 3.2))
fig.subplots_adjust(left=0.11, right=0.97, bottom=0.17, top=0.85)
ax.hist(ov.gap_years.clip(upper=15), bins=np.arange(0, 15.5, 0.5), color=BLUE, edgecolor=SURF)
ax.set_xlabel("years from the declared lower bound's first release to the first release with the vulnerable code (clipped at 15)")
ax.set_ylabel("advisories"); ax.grid(axis="y", color=GRID, lw=0.5)
fig.suptitle(f"Pipeline flags (unaudited): flagged lower bounds sit a median {ov.gap_years.median():.1f} years before the test finds the code", x=0.02, ha="left", fontsize=10, color=INK)
fig.savefig(F / "F2_gap.png", dpi=170); plt.close(fig)
(F / "F2_gap.txt").write_text(f"For the {len(ov)} over-approximated advisories with publish dates, the time between the earliest release inside "
                              "the declared range and the first release containing the vulnerable code.\n")
print("figures written")
