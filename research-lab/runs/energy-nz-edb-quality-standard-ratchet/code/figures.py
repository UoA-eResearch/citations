"""Figures for the report (each PNG has a .txt caption). Written after analysis.py.

  F1  national unplanned SAIDI 2014-2025: raw, and with IEEE major-event days excluded (rolling and frozen threshold)
  F2  DPP3 -> DPP4 change in each distributor's normalised target, split into boundary re-estimation and outcomes
  F3  H3: assessed unplanned SAIDI against the limit under the Commission's rule and the IEEE rule, 2021-2025
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
INK, INK2, GRID, SURF, BLUE, ORANGE, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317", "#9a9893"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1(p):
    n = p["national_index"]
    yrs = sorted(int(y) for y in n["raw"])
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.13, top=0.86)
    for k, col, lab, ls in (("raw", INK, "all unplanned interruptions", "-"),
                            ("excl_rolling", BLUE, "major-event days excluded, rolling 5-year threshold", "-"),
                            ("excl_frozen", ORANGE, "major-event days excluded, threshold frozen at 2009-2013", "--")):
        ax.plot(yrs, [n[k][str(y)] if str(y) in n[k] else n[k][y] for y in yrs], color=col, lw=2, ls=ls, marker="o", ms=4, label=lab)
    ax.set_ylabel("national unplanned SAIDI (minutes)"); ax.set_xticks(yrs); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.set_ylim(bottom=0); ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.annotate("Cyclone Gabrielle", (2023, n["raw"]["2023"]), xytext=(2020.3, n["raw"]["2023"] * 0.95), fontsize=8, color=INK2,
                arrowprops=dict(arrowstyle="-", color=GREY, lw=0.8))
    fig.suptitle("No rising trend to mask: storm years dominate raw outage minutes, which if anything fell", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_national.png", dpi=170); plt.close(fig)
    h = p["H1_H2"]
    tr = h["trend_pct_per_yr"]; c = h["cluster"]
    caption("F1_national", f"""ICP-weighted national unplanned SAIDI of the 16 non-exempt distributors, by disclosure year (April-March),
    from the Commerce Commission's interruption-level DPP model data. IEEE 1366 2.5-beta rule on calendar-day SAIDI; the rolling
    threshold for each year uses the previous five years. Top Energy 2025 is omitted (not separable). Trends 2014-2025: raw {tr['raw']:+.1f}% a year ({c['raw_ci'][0]:+.1f} to
    {c['raw_ci'][1]:+.1f}, distributor-cluster bootstrap), rolling-excluded {tr['excl_rolling']:+.1f}%, frozen-excluded {tr['excl_frozen']:+.1f}%.""")


def f2():
    d = pd.read_csv(T / "decomposition.csv").sort_values("d_target")
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    fig.subplots_adjust(left=0.27, right=0.97, bottom=0.12, top=0.88)
    y = np.arange(len(d))
    ax.barh(y - 0.18, d.d_outcome_part, height=0.34, color=BLUE, label="outcomes at the DPP3 boundary value")
    ax.barh(y + 0.18, d.d_boundary_part, height=0.34, color=ORANGE, label="boundary value re-estimated")
    ax.plot(d.d_target, y, "D", color=INK, ms=4, label="total change in target")
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(y); ax.set_yticklabels(d.edb, fontsize=8)
    ax.set_xlabel("change in normalised target (minutes), 2010-19 window to 2015-24 window")
    ax.grid(axis="x", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle("Where targets rose, outcomes did it, not the moving boundary", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_decomposition.png", dpi=170); plt.close(fig)
    caption("F2_decomposition", f"""Each distributor's normalised unplanned SAIDI target (mean annual SAIDI after capping
    major-event half-hours at boundary / 48) under the Commission's DPP3/DPP4 rule, recomputed on its 2010-2019 and 2015-2024
    reference windows. Blue: change at the fixed DPP3 boundary value; orange: the further change from re-estimating the
    boundary on the DPP4 window. Totals across distributors: {d.d_target.sum():+.0f} minutes, of which
    {d.d_boundary_part.sum():+.0f} from the boundary when outcomes change first; {d.d_boundary_first.sum():+.0f} when the
    boundary changes first (Shapley {d.d_boundary_shapley.sum():+.0f}).""")


def f3(p):
    rows = [r for r in p["H3"]["rows"] if r["a_exceed"] or r["b_exceed"]]
    fig, axes = plt.subplots(1, len(rows), figsize=(7.6, 3.2), sharey=False)
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.16, top=0.78, wspace=0.45)
    for ax, r in zip(np.atleast_1d(axes), rows):
        yrs = [int(y) for y in r["a_assessed"]]
        ax.plot(yrs, list(r["a_assessed"].values()), color=BLUE, marker="o", ms=3.5, lw=1.6)
        ax.axhline(r["a_limit"], color=BLUE, ls=":", lw=1)
        ax.plot(yrs, list(r["b_assessed"].values()), color=ORANGE, marker="s", ms=3.5, lw=1.6)
        ax.axhline(r["b_limit"], color=ORANGE, ls=":", lw=1)
        ax.set_title(r["edb"].replace(" Network", "").replace(" Electricity", "").replace("Electricity ", "") + (" *" if r["differs"] else ""),
                     fontsize=8.5, color=INK)
        ax.set_xticks(yrs); ax.set_xticklabels([str(y)[2:] for y in yrs], fontsize=7.5)
        ax.set_ylim(bottom=0); ax.grid(axis="y", color=GRID, lw=0.5); ax.tick_params(axis="y", labelsize=7.5)
    fig.text(0.02, 0.9, "solid: assessed unplanned SAIDI; dotted: limit.  blue: Commission's rule; orange: IEEE 2.5-beta daily. * outcome differs",
             fontsize=7.5, color=INK2)
    fig.suptitle("Which distributors exceed can depend on the major-event rule", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F3_compliance.png", dpi=170); plt.close(fig)
    caption("F3_compliance", f"""Assessment years 2021-2025 (2021-2024 for Top Energy; disclosure years, April-March) for the distributors that exceed
    a limit under either rule. Commission's rule: rolling 24-hour major events against the DPP3 boundary value, limit = target
    + 2 SD on 2010-2019. IEEE rule: daily SAIDI capped at the 2.5-beta threshold of 2010-2019, limit computed the same way.
    {p['H3']['differing']} of {p['H3']['distributors']} distributors have a different set of exceedance years; 2 with the
    determinations' limits, {p['H3']['variant_exclude_differing']} with IEEE major-event days excluded rather than capped.""")


if __name__ == "__main__":
    p = json.load(open(T / "primary.json"))
    f1(p); f2(); f3(p)
    print("figures written")
