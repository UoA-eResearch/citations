"""Figures for the report (each PNG has a .txt caption).

  F1  every vintage's national gas production profile against realised production
  F2  the median field-level forecast error by horizon, with the preregistered thresholds and the sensitivities
  F3  how ultimate-recoverable reserves were revised between consecutive vintages, by category
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def rows(p):
    with open(p) as fh:
        return list(csv.DictReader(fh))


def main():
    p = json.load(open(T / "primary.json"))
    nat = rows(T / "national_pairs.csv")
    real = {int(y): v for y, v in p["validation"]["national_net_mbie_overview"].items()}

    # F1: profiles against reality
    prof = defaultdict(lambda: defaultdict(float))     # full 14-year profiles, not only the scored years
    keep = p["validation"]["kept_capture_per_vintage"]
    for r in rows(RUN / "data" / "profiles.csv"):
        if r["field"] == "Manufactured Production" or r["capture"] != keep[r["vintage_year"]]:
            continue
        prof[int(r["vintage_year"])][int(r["year"])] += float(r["pj"])
    prof = {v: sorted(d.items()) for v, d in prof.items()}
    vints = sorted(prof)
    cols = plt.cm.viridis(np.linspace(0.08, 0.85, len(vints)))
    fig, ax = plt.subplots(figsize=(7.6, 4.0)); fig.subplots_adjust(left=0.1, right=0.80, bottom=0.13, top=0.86)
    XMAX = 2032
    lab = []
    for c, v in zip(cols, vints):
        xy = [(a, b) for a, b in prof[v] if a <= XMAX]
        ax.plot([a for a, _ in xy], [b for _, b in xy], "-", color=c, lw=1.8)
        lab.append([xy[-1][1], xy[-1][0], f"{v} vintage", c])
    lab.sort()                                            # nudge labels apart so none overlaps
    for i in range(1, len(lab)):
        if lab[i][0] - lab[i - 1][0] < 11:
            lab[i][0] = lab[i - 1][0] + 11
    for y, x, t, c in lab:
        ax.annotate(t, (x, y), xytext=(6, 0), textcoords="offset points", fontsize=7.6, color=c, va="center",
                    annotation_clip=False)
    ry = sorted(y for y in real if y >= 2014)
    ax.plot(ry, [real[y] for y in ry], "-o", color=INK, lw=2.6, ms=4, mec=SURF, mew=1, zorder=5)
    ax.annotate("realised", (ry[-1], real[ry[-1]]), xytext=(6, -10), textcoords="offset points",
                fontsize=8.4, color=INK, fontweight="bold", annotation_clip=False)
    ax.set_xlim(2014, XMAX); ax.set_ylim(0, None)
    ax.set_ylabel("New Zealand gas production, PJ a year (net)"); ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Each year's official production profile, against what was produced", x=0.1, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F1_profiles_vs_realised.png", dpi=170); plt.close(fig)
    caption("F1_profiles_vs_realised", """Coloured lines: the national total of the field-by-field gas production
    profile that operators reported to MBIE in each vintage of the petroleum reserves workbook (the vintage is the
    'as at 1 January' date inside the workbook). Black: realised net production, from MBIE's energy overview, which
    reproduces the sum of the published field-level net production and whose 2025 value matches MBIE's published
    102 PJ. Profiles run 14 years ahead; the axis is cut at 2032.""")

    # F2: error by horizon
    hz = [r for r in rows(T / "by_horizon.csv") if r["basis"] == "net" and r["median_e"]]
    hs = [int(r["h"]) for r in hz]
    med = [100 * (np.exp(float(r["median_e"])) - 1) for r in hz]
    lo = [100 * (np.exp(float(r["lo"])) - 1) for r in hz]
    hi = [100 * (np.exp(float(r["hi"])) - 1) for r in hz]
    fig, ax = plt.subplots(figsize=(7.4, 3.8)); fig.subplots_adjust(left=0.11, right=0.97, bottom=0.15, top=0.82)
    for x, m, a, b, r in zip(hs, med, lo, hi, hz):
        ax.plot([x, x], [a, b], color="#2a78d6", lw=2.4)
        ax.plot(x, m, "o", color="#2a78d6", ms=7, mec=SURF, mew=1.2)
        ax.annotate(f"{m:+.0f}%", (x, b), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=7.6,
                    color=INK2)
        ax.annotate(f"{r['n_vintages']} vintage" + ("s" if int(r["n_vintages"]) != 1 else ""), (x, -14), ha="center", fontsize=6.8, color=INK2)
    ns = p["national"]["net"]
    ax.plot([int(h) for h in ns], [v["median_pct"] for v in ns.values()], "s--", color="#eb6834", lw=1.6, ms=5,
            label="national total")
    ax.axhline(0, color=INK2, lw=0.9)
    ax.axhline(5, color=GRID, lw=1, ls="--"); ax.axhline(15, color=GRID, lw=1, ls="--")
    ax.set_ylim(-22, None)
    ax.annotate("preregistered bars: +5% at 1 year, +15% at 3 years", (6.2, 2), fontsize=7.2, color=INK2, ha="right")
    ax.set_xlabel("years ahead of the vintage"); ax.set_ylabel("forecast over realised, %")
    ax.grid(axis="y", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0.0, 1.0))
    fig.suptitle("Gas production forecasts exceed what follows, and more so further out", x=0.1, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F2_error_by_horizon.png", dpi=170); plt.close(fig)
    caption("F2_error_by_horizon", """Blue: the median over (vintage, field) pairs of the forecast-to-realised ratio on
    the net basis, with field-cluster bootstrap 95% intervals (2,000 resamples); the label below each interval gives
    the number of vintages contributing. Orange squares: the same ratio for the national profile total, which is not
    sensitive to small fields and extends to 2025 because national realised production is published sooner than the
    field detail. Dashed lines: the preregistered thresholds.""")

    # F3: reserve revisions
    rv = p["revisions"]
    order = ["1P", "2P", "3P"]
    fig, ax = plt.subplots(figsize=(7.6, 3.0)); fig.subplots_adjust(left=0.33, right=0.95, bottom=0.21, top=0.79)
    for i, k in enumerate(order):
        r = rv[k]; y = len(order) - 1 - i
        ax.plot([100 * r["lo"], 100 * r["hi"]], [y, y], color="#1baf7a", lw=2.4)
        ax.plot(100 * r["share_down"], y, "o", color="#1baf7a", ms=7, mec=SURF, mew=1.2)
        ax.annotate(f"{100 * r['share_down']:.0f}%  ({r['n_down']} of {r['n_revised']})",
                    (100 * r["hi"], y), xytext=(8, 0), textcoords="offset points", va="center", fontsize=7.8,
                    color=INK2)
    ax.axvline(50, color=INK2, lw=1)
    ax.set_ylim(-0.7, 2.7)
    ax.annotate("50%: as often up as down", (50, 2.45), xytext=(5, 0), textcoords="offset points",
                fontsize=7.4, color=INK2)
    ax.annotate("10%", (10, 2.45), xytext=(4, 0), textcoords="offset points", fontsize=7.4, color=INK2)
    ax.axvline(10, color=GRID, lw=1, ls="--")
    ax.set_yticks(range(len(order))); ax.set_yticklabels(["proved (1P)", "proved + probable (2P)",
                                                          "proved + probable + possible (3P)"][::-1])
    ax.set_xlim(0, 85); ax.set_xlabel("share of field-years whose ultimate recoverable volume was revised down")
    ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("Reserve volumes are revised down about as often as up", x=0.33, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F3_reserve_revisions.png", dpi=170); plt.close(fig)
    caption("F3_reserve_revisions", """Among field-years whose ultimate recoverable gas volume changed by more than 1%
    between consecutive vintages, the share revised downward, with Wilson 95% intervals. A calibrated proved (1P)
    estimate should rarely be revised down (dashed line at 10%); a calibrated proved-plus-probable (2P) estimate
    should be revised down about half the time (solid line).""")
    print("figures written")


if __name__ == "__main__":
    main()
