"""Figures for the report (each PNG has a .txt caption).

  F1  pooled annual indices 2020-2025 under each policy: geometric mean across the included states, indexed to 2020
  F2  the pooled log-linear trends (% per year) with state-cluster bootstrap intervals, primary and coverage sensitivity
  F3  the rolling 2.5-beta threshold and the number of major event days per state-year, rolling vs frozen
  F4  Monte Carlo detection rates by scenario and policy (Wilson intervals)
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
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
POL = [("all", "all events (no normalisation)", "#52514e"), ("noMED_roll", "MED-excluded, rolling 2.5β (the standard)", "#2a78d6"),
       ("noMED_frozen", "MED-excluded, frozen 2.5β (2015-19)", "#eb6834"), ("noMED_q99", "MED-excluded, fixed 99th percentile", "#1baf7a")]
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def wilson(k, n, z=1.959964):
    p = k / n; c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def main():
    p = json.load(open(T / "primary.json")); pc = json.load(open(T / "primary_coverage_sensitivity.json"))
    sy = pd.read_csv(T / "state_year.csv")
    # F1
    fig, ax = plt.subplots(figsize=(7.2, 3.6)); fig.subplots_adjust(left=0.1, right=0.62, bottom=0.14, top=0.86)
    for col, lab, c in POL:
        g = sy.assign(l=np.log(sy[col] + 1)).groupby("year").l.mean()
        v = 100 * np.exp(g - g.iloc[0])
        ax.plot(v.index, v.values, "-o", color=c, lw=2, ms=4.5, mec=SURF, mew=1)
        ax.annotate(lab, (v.index[-1], v.values[-1]), xytext=(8, 0), textcoords="offset points", va="center", fontsize=7.8,
                    color=INK2, annotation_clip=False)
    ax.axhline(100, color=GRID, lw=1); ax.set_ylabel("index (2020 = 100, geometric mean of states)")
    ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle(f"Annual outage minutes per customer, {p['n_included']} states", x=0.1, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_indices.png", dpi=170); plt.close(fig)
    caption("F1_indices", f"""Annual SAIDI from EAGLE-I county outage snapshots, by normalisation policy, as the geometric mean
    across the {p['n_included']} included states of (index + 1 minute), set to 100 in 2020. The all-events line includes
    major event days (MEDs); the others exclude days above each policy's threshold.""")
    # F2
    rows = [(lab, p["trends"][col], pc["trends"][col]) for col, lab, _ in POL]
    fig, ax = plt.subplots(figsize=(7.2, 3.0)); fig.subplots_adjust(left=0.42, right=0.97, bottom=0.18, top=0.8)
    for i, (lab, a, b) in enumerate(rows):
        y = len(rows) - 1 - i
        for dy, t, c, nm in ((0.12, a, "#2a78d6", "primary"), (-0.12, b, "#8a5cd1", "coverage sensitivity")):
            ax.plot(t["ci"], [y + dy] * 2, color=c, lw=2)
            ax.plot(t["trend_pct"], y + dy, "o", color=c, ms=6, mec=SURF, mew=1.2, label=nm if i == 0 else None)
        ax.text(max(a["ci"][1], b["ci"][1]) + 0.3, y, f"{a['trend_pct']:+.1f}%", va="center", fontsize=7.8, color=INK2)
    ax.axvline(0, color=INK2, lw=0.8); ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1])
    hi = max(max(a_["ci"][1], b_["ci"][1]) for _, a_, b_ in rows); lo = min(min(a_["ci"][0], b_["ci"][0]) for _, a_, b_ in rows)
    ax.set_xlim(lo - 0.5, hi + 2.2)
    ax.set_xlabel("pooled trend 2020-2025, % per year (state fixed effects)"); ax.grid(axis="x", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=8, loc="lower right", bbox_to_anchor=(1, 1.02), ncol=2)
    fig.suptitle("Trends under each normalisation policy", x=0.42, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_trends.png", dpi=170); plt.close(fig)
    caption("F2_trends", """Pooled log-linear trend of each annual index over 2020-2025, with state-cluster bootstrap 95%
    intervals (2,000 resamples). Purple: the preregistered coverage sensitivity, normalising by covered customers.""")
    # F3
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.0)); fig.subplots_adjust(left=0.09, right=0.98, bottom=0.17, top=0.8, wspace=0.3)
    th = sy.groupby("year")[["t_roll", "t_frozen"]].median()
    a1.plot(th.index, th.t_roll, "-o", color="#2a78d6", lw=2, ms=4.5, label="rolling 2.5β")
    a1.plot(th.index, th.t_frozen, "--", color="#eb6834", lw=2, label="frozen 2.5β")
    a1.set_ylabel("threshold, minutes per customer-day"); a1.set_title("median state threshold", fontsize=9, color=INK2, loc="left")
    m = sy.groupby("year")[["n_MED_roll", "n_MED_frozen"]].mean()
    a2.plot(m.index, m.n_MED_roll, "-o", color="#2a78d6", lw=2, ms=4.5); a2.plot(m.index, m.n_MED_frozen, "--o", color="#eb6834", lw=2, ms=4.5)
    a2.set_ylabel("MEDs per state-year"); a2.set_title("mean major event days", fontsize=9, color=INK2, loc="left")
    for a in (a1, a2):
        a.grid(axis="y", color=GRID, lw=0.5)
    a1.legend(frameon=False, fontsize=8)
    fig.suptitle("The rolling threshold rose, so fewer days were excluded", x=0.09, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F3_thresholds.png", dpi=170); plt.close(fig)
    caption("F3_thresholds", """Left: the median across included states of the daily-SAIDI threshold exp(α + 2.5β), rolling (the
    previous five years) and frozen (2015-2019). Right: the mean number of major event days per state-year under each.""")
    # F4
    sp = T / "simulation.json"
    if sp.exists():
        s = json.load(open(sp))
        labs = [("oracle", "oracle (knows storm days)"), ("roll", "rolling 2.5β (standard)"), ("frozen", "frozen 2.5β"),
                ("q99", "fixed 99th percentile"), ("all", "all events")]
        scen = [("A", "A: normal operations +3%/yr", "#2a78d6"), ("B", "B: storms +5%/yr", "#eb6834"), ("C", "C: no trend", "#52514e")]
        fig, ax = plt.subplots(figsize=(7.4, 3.6)); fig.subplots_adjust(left=0.27, right=0.97, bottom=0.14, top=0.8)
        for i, (pol, lab) in enumerate(labs):
            y = len(labs) - 1 - i
            for j, (sc, sl, c) in enumerate(scen):
                r = s[sc][pol]; yy = y + (1 - j) * 0.22
                ax.plot(r["ci"], [yy, yy], color=c, lw=2)
                ax.plot(r["power"], yy, "o", color=c, ms=5.5, mec=SURF, mew=1, label=sl if i == 0 else None)
                ax.text(r["ci"][1] + 0.01, yy, f"{r['power']:.0%}", va="center", fontsize=7, color=INK2)
        ax.axvline(0.05, color=GRID, lw=1, ls="--")
        ax.set_yticks(range(len(labs))); ax.set_yticklabels([l for _, l in labs][::-1]); ax.set_xlim(0, 0.75)
        ax.set_xlabel("share of simulated systems with a detected upward trend (one-sided p < 0.05)")
        ax.grid(axis="x", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="lower right", bbox_to_anchor=(1, 1.02), ncol=3)
        fig.suptitle("Detection in simulated systems (H3)", x=0.27, ha="left", fontsize=10.5, color=INK)
        fig.savefig(F / "F4_power.png", dpi=170); plt.close(fig)
        caption("F4_power", """Monte Carlo, 2,000 systems per scenario, each calibrated to a randomly drawn included state's
        2015-2019 days (zero days, log-normal body, generalised Pareto tail above the 95th percentile). A: normal-operations
        severity grows 3% a year, storms unchanged. B: storm frequency and size grow 5% a year, normal operations
        unchanged. A "storm" here is any day above the 95th percentile of non-zero days, and most such days (57-66%) fall
        below the 2.5beta threshold, so under IEEE 1366 they count as normal operations: detection in B mostly reflects more
        sub-threshold bad-weather days entering every normalised index, not storm days slipping past the threshold. With
        storms defined at major-event scale, B detection falls to 8% (rolling) against 4% (oracle). C: no trend (the
        false-positive rate; dashed line 5%). Wilson 95% intervals.""")
    print("figures written")


if __name__ == "__main__":
    main()
