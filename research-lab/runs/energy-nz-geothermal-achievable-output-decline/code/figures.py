"""Figures for the report. Each PNG gets a .txt caption beside it.

  F1  every field's monthly achievable output (P95) indexed to its own segment mean, one shared axis, preregistered
      segments shaded and their fitted trends drawn
  F2  field trends with 95% intervals against the decision lines, the fleet estimate, and (post hoc, hollow) the
      Ohaaki run-down between drilling campaigns

Palette: the dataviz skill's reference slots; one series per panel in blue, fitted trends in orange, decision lines
in neutral ink. Text stays in neutral ink.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURF, BAND = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#eef3fb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1():
    fm = pd.read_csv(T / "field_monthly.csv")
    mem = pd.read_csv(T / "field_membership.csv")
    prim = json.load(open(T / "primary.json"))["primary"]["fields"]
    order = sorted(prim, key=lambda f: -prim[f]["mean_mw"])
    fig, axes = plt.subplots(4, 2, figsize=(8.4, 9.0), sharex=True, sharey=True)
    for ax, field in zip(axes.ravel(), order):
        ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
        ax.axhline(100, color=INK2, lw=0.6)
        for g in A.segments(fm, mem, field):
            d = g[g.ok]
            t = d.m.dt.year + (d.m.dt.month - 0.5) / 12
            ref = d.p95.mean()
            ax.axvspan(t.min(), t.max(), color=BAND, lw=0, zorder=0)
            ax.plot(t, 100 * d.p95 / ref, color=BLUE, lw=0.9)
            r = A.seg_trend(g)
            tt = np.array([t.min(), t.max()])
            ax.plot(tt, 100 * np.exp(r["b"] * (tt - t.mean())), color=ORANGE, lw=2)
        p = prim[field]
        ax.set_title(f"{field}  {p['pct_per_yr']:+.2f}%/yr  (mean {p['mean_mw']:.0f} MW)", loc="left", fontsize=9,
                     color=INK)
        ax.set_xlim(1999.5, 2027)
        ax.set_ylim(30, 175)
    for ax in axes[:, 0]:
        ax.set_ylabel("P95, % of segment mean")
    fig.tight_layout()
    fig.savefig(F / "F1_fields.png", dpi=200)
    caption("F1_fields", """F1. Achievable output for each field: the monthly 95th percentile of half-hourly generation,
    as a percentage of its own segment mean so that every field shares one axis (blue). Shaded spans are the
    preregistered segments, cut at plant entries and documented capacity changes; orange lines are their fitted
    trends (GLS with AR(1) errors, month-of-year effects removed - the line shows the trend only). The panel titles
    give each field's preregistered trend and mean P95. Ohaaki's 2008 jump and run-down are inside one segment;
    no capacity change was documented for it.""")


def f2():
    p = json.load(open(T / "primary.json"))["primary"]
    s = json.load(open(T / "supplementary.json"))
    fields = sorted(p["fields"], key=lambda f: p["fields"][f]["pct_per_yr"])
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    fig.subplots_adjust(left=0.20, right=0.97, bottom=0.14, top=0.95)
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    for x, lab in ((0, "flat"), (-1.5, "H1 line"), (-3, "H2 line\n(MBIE's 3%)")):
        ax.axvline(x, color=INK2, lw=0.8, ls="-" if x == 0 else ":")
        ax.text(x, len(fields) + 1.55, lab, ha="center", va="bottom", fontsize=8, color=INK2,
                bbox=dict(fc=SURF, ec="none", pad=1.5))
    ys = list(range(len(fields)))
    for y, f in zip(ys, fields):
        r = p["fields"][f]
        ax.plot(r["ci"], [y, y], color=BLUE, lw=2, solid_capstyle="round")
        ax.scatter([r["pct_per_yr"]], [y], color=BLUE, s=36, zorder=3)
    fy = len(fields) + 0.6
    lo, hi = p["H1"]["ci"]
    ax.plot([lo, hi], [fy, fy], color=INK, lw=2.4, solid_capstyle="round")
    ax.scatter([p["H1"]["fleet_pct_per_yr"]], [fy], color=INK, s=46, marker="D", zorder=3)
    oh = [r for r in s["rundowns_after_upward_steps"] if r["field"] == "Ohaaki" and r["start_year"] == 2008][0]
    oy = -1.2
    ax.plot(oh["ci"], [oy, oy], color=ORANGE, lw=2, solid_capstyle="round")
    ax.scatter([oh["pct_per_yr"]], [oy], facecolor=SURF, edgecolor=ORANGE, s=40, lw=1.5, zorder=3)
    ax.set_yticks(ys + [fy, oy])
    ax.set_yticklabels(fields + ["fleet (capacity-weighted)", "Ohaaki 2008-13, after\na step up (post hoc)"])
    ax.set_xlim(-13, 3.2)
    ax.set_ylim(-2.0, len(fields) + 2.3)
    ax.set_xlabel("trend in achievable output, % per year (95% interval)")
    fig.savefig(F / "F2_trends.png", dpi=200)
    caption("F2_trends", """F2. Preregistered trends in achievable output for the eight fields (blue) and the fleet
    (black diamond), with 95% intervals, against the decision lines: H1 asks whether the fleet declines more slowly
    than 1.5%/yr, H2 whether two or more fields decline faster than 3%/yr. The orange hollow marker is post hoc
    (deviations D3): Ohaaki's run-down over the five years after its 2008 step up, fitted with the same model.""")


if __name__ == "__main__":
    f1(); f2(); print("figures written")
