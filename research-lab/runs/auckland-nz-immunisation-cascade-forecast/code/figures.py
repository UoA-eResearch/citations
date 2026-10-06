"""Figures: (1) backtest error by horizon and period for the cascade (M1) and the two baselines; (2) national and
Auckland-region 24-month coverage, 2009-2026, with the 4-quarter-ahead cascade forecasts and the frozen prospective
forecasts; (3) frozen forecasts for 2026Q4 by district (Total, Maori, Pacific) against the 95% target.
Writes results/figures/*.png and .txt captions."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
COL = {"M1": "#1f6f8b", "B1": "#9a9a9a", "B2": "#c48a3a"}
LAB = {"M1": "cohort cascade (M1)", "B1": "persistence (B1)", "B2": "linear trend (B2)"}


def qx(label):
    y, q = label.split("Q")
    return int(y) + (int(q) - 0.5) / 4


def errors():
    d = pd.read_csv(T / "backtest_cells.csv")
    d = d[(d.district != "National total") & d.group.isin(["Total", "Maori", "Pacific"]) & d.M1.notna() & d.B1.notna() & d.B2.notna()]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
    for m in ("M1", "B1", "B2"):
        g = d.groupby("h")[f"ae_{m}"].mean()
        a1.plot(g.index, g.values, "o-", color=COL[m], label=LAB[m])
        e = d[d.h == 4].assign(yr=d.target // 4).groupby("yr")[f"ae_{m}"].mean()
        a2.plot(e.index, e.values, "o-", color=COL[m], ms=3.5, label=LAB[m])
    a1.set_xlabel("forecast horizon (quarters)"); a1.set_ylabel("mean absolute error (pp)"); a1.set_xticks([1, 2, 3, 4])
    a1.legend(frameon=False, fontsize=8)
    for x in (2020.75, 2023.75):
        a2.axvline(x, color="grey", lw=0.7, ls="--")
    a2.text(2020.8, a2.get_ylim()[1] * 0.92, "schedule\nchange", fontsize=7, color="grey")
    a2.text(2023.8, a2.get_ylim()[1] * 0.92, "AIR", fontsize=7, color="grey")
    a2.set_xlabel("target year (h = 4)"); a2.set_ylabel("mean absolute error (pp)")
    fig.tight_layout(); fig.savefig(F / "backtest_errors.png", dpi=150)
    (F / "backtest_errors.txt").write_text("Rolling-origin backtest, 20 districts x Total, Maori and Pacific. Left: mean absolute error by horizon. Right: at the 4-quarter horizon, by target year. Dashed lines: the October 2020 schedule change and the 2023-24 move to the Aotearoa Immunisation Register (AIR).")


def series():
    cov = pd.read_parquet(RUN / "data" / "coverage.parquet")
    cov = cov[(cov.milestone == 24) & (cov.group == "Total")]
    cov["x"] = [t.year + ((t.month - 1) // 3 + 0.5) / 4 for t in pd.to_datetime(cov.quarter_end)]
    cov["c"] = cov.immunised / cov.eligible
    bt = pd.read_csv(T / "backtest_cells.csv")
    bt = bt[(bt.h == 4) & (bt.group == "Total")]
    fr = pd.read_csv(RUN / "results" / "forecasts_frozen.csv")
    fr = fr[fr.group == "Total"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.4), sharex=True)
    for ax, dist in zip(axes.ravel(), ["National total", "Auckland", "Counties Manukau", "Waitematā"]):
        c = cov[cov.district == dist].sort_values("x")
        ax.plot(c.x, 100 * c.c, "-", color="black", lw=1.3, label="published")
        b = bt[bt.district == dist].sort_values("target")
        ax.plot(b.target_label.map(qx), 100 * b.M1, ".", color=COL["M1"], ms=4, label="cascade, 4 quarters ahead (backtest)")
        f = fr[fr.district == dist].sort_values("h")
        xs = f.target.map(qx)
        ax.fill_between(xs, 100 * f.lo80, 100 * f.hi80, color=COL["M1"], alpha=0.25, lw=0)
        ax.plot(xs, 100 * f.forecast, "o-", color=COL["M1"], ms=4, label="frozen forecast (80% interval)")
        ax.axhline(95, color="#b5452c", lw=0.8, ls=":")
        ax.set_title(dist, fontsize=9); ax.set_ylim(60, 100)
    axes[0, 0].legend(frameon=False, fontsize=7, loc="lower left")
    for ax in axes[:, 0]:
        ax.set_ylabel("24-month coverage (%)")
    fig.tight_layout(); fig.savefig(F / "series.png", dpi=150)
    (F / "series.txt").write_text("Published 24-month full-immunisation coverage (Total), 2009-2026, with the cascade's 4-quarter-ahead backtest forecasts (dots) and the forecasts frozen on 7 October 2026 for 2026Q3-2027Q2 (preregistered 80% intervals shaded). Dotted line: the 95% target.")


def districts():
    fr = pd.read_csv(RUN / "results" / "forecasts_frozen.csv")
    f = fr[(fr.target == "2026Q4") & (fr.district != "National total")]
    order = sorted(f[f.group == "Total"].district.unique(), reverse=True)  # D2: alphabetical, not a league table
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for k, (g, col, off) in enumerate([("Total", "#1f6f8b", 0), ("Maori", "#b5452c", 0.22), ("Pacific", "#6b8e23", -0.22)]):
        x = f[f.group == g].set_index("district").reindex(order)
        y = np.arange(len(order)) + off
        ax.errorbar(100 * x.forecast, y, xerr=[100 * (x.forecast - x.lo80), 100 * (x.hi80 - x.forecast)], fmt="o", ms=3.5, color=col, lw=0.8, label=g)
    ax.axvline(95, color="grey", ls=":", lw=0.8)
    ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=7.5)
    ax.set_xlabel("forecast 24-month coverage, Oct-Dec 2026 (%), with preregistered 80% interval")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(F / "districts_2026q4.png", dpi=150)
    (F / "districts_2026q4.txt").write_text("Frozen cascade forecasts of 24-month coverage for October-December 2026 (Q2 2026/27) by district, for Total, Maori and Pacific children where the inputs are published, with preregistered 80% intervals. Dotted line: the 95% target. Districts are listed alphabetically.")


def main():
    F.mkdir(parents=True, exist_ok=True)
    errors(); series(); districts()


if __name__ == "__main__":
    main()
