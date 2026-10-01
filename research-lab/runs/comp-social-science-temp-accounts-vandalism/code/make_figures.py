#!/usr/bin/env python
"""Figures for the report (results/figures/F*.png, each with a caption file). Usage: make_figures.py [tag]"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
BLUE, ORANGE, AQUA, INK, MUTED, GRID, NAVY, RED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#898781", "#e1e0d9", "#104281", "#c0392b"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})


def caption(name, text):
    (FIG / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1_rollout(tag):
    p = pd.read_parquet(TAB / f"panel_{tag}.parquet")
    td = pd.read_csv(TAB / f"treatment_dates_{tag}.csv", parse_dates=["treatment_date"]).set_index("wiki")
    order = td.treatment_date.sort_values().index
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1.2, 1]})
    ax = axes[0]
    ax.scatter(td.loc[order, "treatment_date"], np.arange(len(order)), s=14, color=NAVY)
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels([w.replace("wiki", "") for w in order], fontsize=6.5)
    ax.set_xlabel("date temporary accounts reached 1% of logged-out edits")
    ax.tick_params(axis="x", rotation=30, labelsize=7.5)
    ax.set_title("rollout dates inferred from the edit data")
    ax = axes[1]
    for w in order:
        q = p[p.wiki == w].sort_values("month")
        ax.plot(q.month.astype(str).map(pd.Timestamp), q.temp_share * 100, color=BLUE, lw=0.8, alpha=0.5)
    ax.set_ylabel("% of logged-out edits by temporary accounts")
    ax.tick_params(axis="x", rotation=30, labelsize=7.5)
    ax.set_title("adoption within each wiki (monthly)")
    fig.savefig(FIG / "F1_rollout.png")
    plt.close(fig)
    caption("F1_rollout", """F1. The staggered switch from IP addresses to temporary accounts, as seen in the edit data. Left:
the first day on which temporary accounts made up at least 1% of each wiki's logged-out content edits (the treatment
date). Right: the monthly share of logged-out edits made from temporary accounts, one line per wiki.""")


def f2_events(tag):
    es = pd.read_csv(TAB / f"eventstudy_{tag}.csv")
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))
    for ax, (oc, title, col) in zip(axes, (("Y_LO", "logged-out edits reverted within 48 h", RED),
                                           ("Y_REG", "registered edits reverted within 48 h (placebo)", NAVY),
                                           ("GAP", "difference (logged-out minus registered)", INK))):
        s = es[es.outcome == oc].sort_values("e")
        ax.fill_between(s.e, s.lo * 100, s.hi * 100, color=col, alpha=0.15, lw=0)
        ax.plot(s.e, s.att * 100, "o-", color=col, ms=3)
        ax.axhline(0, color=INK, lw=0.8)
        ax.axvline(0, color=MUTED, lw=0.8, ls=":")
        ax.set_title(title)
        ax.set_xlabel("months since the switch")
        ax.set_ylabel("change (percentage points)")
    fig.savefig(FIG / "F2_eventstudy.png")
    plt.close(fig)
    caption("F2_eventstudy", """F2. Event study: change in the share of edits reverted within 48 hours, months before and after
each wiki switched to temporary accounts, relative to the month before the switch and to wikis that had not yet switched
(Callaway-Sant'Anna estimator; shaded: 95% intervals from a bootstrap over wikis). Months before the switch test
whether switching and not-yet-switched wikis were on parallel paths.""")


def f3_volume(tag):
    es = pd.read_csv(TAB / f"eventstudy_{tag}.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.3))
    for ax, (oc, title, col) in zip(axes, (("logN_LO", "logged-out edit volume", ORANGE),
                                           ("logACCT", "new registered accounts", AQUA))):
        s = es[es.outcome == oc].sort_values("e")
        ax.fill_between(s.e, (np.exp(s.lo) - 1) * 100, (np.exp(s.hi) - 1) * 100, color=col, alpha=0.15, lw=0)
        ax.plot(s.e, (np.exp(s.att) - 1) * 100, "o-", color=col, ms=3)
        ax.axhline(0, color=INK, lw=0.8)
        ax.axvline(0, color=MUTED, lw=0.8, ls=":")
        ax.set_title(title)
        ax.set_xlabel("months since the switch")
        ax.set_ylabel("change (%)")
    fig.savefig(FIG / "F3_volume.png")
    plt.close(fig)
    caption("F3_volume", """F3. Event study for logged-out edit volume and for new self-created registered accounts per month
(percentage change, same estimator and intervals as F2). Account creation is about as high in the months before the
switch as after it (relative to the month before the switch), so the post-switch level is not evidence of a change.""")


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "primary"
    FIG.mkdir(parents=True, exist_ok=True)
    for f in (f1_rollout, f2_events, f3_volume):
        f(tag)
    print("figures written")
