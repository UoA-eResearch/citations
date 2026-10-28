"""Figure (PNG + .txt caption). Written after analyse.py, posthoc.py and posthoc_b.py.

  F1  event-year profiles of exposed minus matched control log(1 + citations), relative to T-1, for the three designs
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
DESIGNS = [("event_profile.csv", "preregistered: matched to T−2, clean controls", "#9a9893"),
           ("event_profile_t1.csv", "post hoc A: matched to T−1, clean controls", "#d6532a"),
           ("event_profile_nyt.csv", "post hoc B: matched to T−1, not-yet-treated controls", "#2a78d6")]

fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), sharey=True)
fig.subplots_adjust(left=0.12, right=0.98, bottom=0.27, top=0.83, wspace=0.08)
for ax, depth, title in zip(axes, (1, 2), ("depth 1: citers of the retracted paper", "depth 2: citers of citers")):
    for f, lab, col in DESIGNS:
        p = pd.read_csv(T / f)
        p = p[p.depth == depth]
        ax.plot(p.k, p["mean"], marker="o", ms=3.5, lw=1.8, color=col, label=lab)
    ax.axhline(0, color=INK2, lw=0.6)
    ax.axvline(-0.5, color=INK2, lw=0.6, ls=":")
    ax.set_xticks(range(-4, 5)); ax.set_xlabel("years from retraction (T)")
    ax.set_title(title, fontsize=9, color=INK, loc="left"); ax.grid(axis="y", color=GRID, lw=0.5)
axes[0].set_ylabel("exposed − control, log(1 + citations)\nrelative to T−1")
axes[0].legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(0, -0.2), ncol=1)
fig.suptitle("Innocent citers show no post-retraction penalty once controls come from the same citation communities",
             x=0.02, ha="left", fontsize=10, color=INK)
fig.savefig(F / "F1_event_profiles.png", dpi=170)
(F / "F1_event_profiles.txt").write_text(" ".join("""Retraction Watch retractions 2000-2021 and works that cited them
before the retraction with no shared author or institution (depth 1), or cited such a work (depth 2; up to 20 per
retraction). Each line is the retraction-weighted mean of exposed minus matched-control log(1 + citations) by year,
relative to the year before the retraction. Grey (preregistered): controls from the same source and year citing no
retracted work, matched on citations to T-2; the gap steps up at T-1, the first year the match leaves free (regression
to the mean, not faster growth). Orange (post hoc A): the same controls matched on the trajectory to T-1; the same step
lands on T. Blue (post hoc B): controls that also cite retracted work, but only work retracted after T+4; no step. In A
and B the pre-period years are matched by construction, so flat pre-profiles there do not test parallel trends.""".split()) + "\n")
print("figure written")
