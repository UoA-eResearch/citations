#!/usr/bin/env python
"""Figures for the report (results/figures/F*.png, each with a caption file)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import locations  # noqa: E402
from score import FC, TAB, truth  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
FIG = RUN / "results" / "figures"
BLUE, ORANGE, AQUA, INK, MUTED, GRID, NAVY, RED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#898781", "#e1e0d9", "#104281", "#c0392b"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})


def caption(name, text):
    (FIG / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1_coverage():
    c = pd.read_csv(TAB / "ww_coverage.csv")
    p = c.pivot(index="abbr", columns="season", values="coverage")
    p = p.loc[p.mean(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(12, 3.4))
    x = np.arange(len(p))
    for j, (s, col) in enumerate(zip(p.columns, (MUTED, BLUE, NAVY))):
        ax.bar(x + (j - 1) * 0.27, p[s], width=0.27, color=col, label=s)
    ax.axhline(0.5, color=RED, lw=1, ls="--")
    ax.axhline(0.2, color=ORANGE, lw=1, ls=":")
    ax.set_xticks(x)
    ax.set_xticklabels(p.index, fontsize=7)
    ax.set_xlim(-0.7, len(p) - 0.3)
    ax.set_ylabel("share of state population\nserved by active sites")
    ax.legend(ncol=3, fontsize=8, loc="upper right")
    fig.savefig(FIG / "F1_coverage.png")
    plt.close(fig)
    caption("F1_coverage", """F1. Wastewater coverage by state and season: the population served by sites that
reported influenza A in the two weeks before each forecast's data cut-off, as a share of the state population, averaged
over the season's forecast dates. Dashed red: the 50% threshold of the primary panel; dotted orange: the 20% threshold
of the secondary panel.""")


def f2_example():
    fc = pd.read_parquet(FC / "main_lag10.parquet")
    tr = truth()
    loc = locations()
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.6), sharey=False)
    for ax, (abbr, season_lo, season_hi) in zip(axes, (("CA", "2024-11-01", "2025-05-31"), ("IL", "2025-11-01", "2026-05-31"))):
        lc = loc.index[loc.abbreviation == abbr][0]
        d = fc[(fc.location == lc) & (fc.horizon == 1) & (fc.reference_date >= season_lo) & (fc.reference_date <= season_hi)].copy()
        d["target_end_date"] = d.reference_date + pd.Timedelta(weeks=1)
        t = tr.loc[lc]
        t = t[(t.index >= pd.Timestamp(season_lo) - pd.Timedelta(weeks=3)) & (t.index <= season_hi)]
        for model, col, off in (("base", MUTED, -1.2), ("ww", BLUE, 1.2)):
            m = d[d.model == model]
            xx = m.target_end_date + pd.Timedelta(days=off)
            ax.vlines(xx, m["q0.025"], m["q0.975"], color=col, lw=1, alpha=0.6)
            ax.vlines(xx, m["q0.25"], m["q0.75"], color=col, lw=3, alpha=0.9)
            ax.plot(xx, m["q0.5"], "o", ms=2.5, color=col, label={"base": "without wastewater", "ww": "with wastewater"}[model])
        ax.plot(t.index, t.values, "-", color=INK, lw=1.2, label="reported admissions (final)")
        ax.set_title(f"{loc.location_name[lc]}, 1 week ahead of the latest data")
        ax.set_ylabel("weekly confirmed influenza admissions")
        ax.legend(fontsize=7.5, loc="upper right")
        ax.tick_params(axis="x", labelsize=7.5)
    fig.savefig(FIG / "F2_example.png")
    plt.close(fig)
    caption("F2_example", """F2. Two example seasons: forecasts one week beyond the latest hospital data (hub horizon 1)
from the model without (grey) and with (blue) state wastewater features, made in real time each week. Thick bars: 50%
intervals; thin bars: 95% intervals; dots: medians. The two models are almost indistinguishable.""")


def f3_forest():
    rows = []
    add = lambda label, f, panel="primary (coverage >= 50%)": rows.append(
        (label, *pd.read_csv(TAB / f).set_index("panel").loc[panel, ["rel_wis", "lo", "hi"]].values))
    add("H1: with vs without wastewater (primary panel)", "relwis_main_lag10.csv")
    add("H2: secondary panel (coverage >= 20%)", "relwis_main_lag10.csv", "secondary (coverage >= 20%)")
    h4 = pd.read_csv(TAB / "h4.csv").set_index("panel").loc["primary"]
    rows.append(("H4: FluSight ensemble + wastewater model vs + base model", h4.rel_wis, h4.lo, h4.hi))
    for label, f in (("S1: lag 5 days", "relwis_main_lag5.csv"), ("S1: lag 17 days", "relwis_main_lag17.csv"),
                     ("S2: flow-normalised concentration", "relwis_flowpop_lag10.csv"), ("S3: level feature only", "relwis_level_lag10.csv"),
                     ("S4: base model trained on all rows", "relwis_basefull_lag10.csv"), ("S6: CDC activity levels (WVAL)", "relwis_wval_lag10.csv")):
        add(label, f)
    bg = pd.read_csv(TAB / "by_group.csv")
    s5 = bg[bg.group.str.startswith("S5")].iloc[0]
    rows.append(("S5: holiday weeks excluded", s5.rel_wis, s5.lo, s5.hi))
    add("V2 negative control: another state's wastewater", "relwis_derange_lag10.csv")
    add("V1 positive control: noisy next-week admissions", "relwis_oracle_lag10.csv")
    d = pd.DataFrame(rows, columns=["label", "est", "lo", "hi"])
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    y = np.arange(len(d))[::-1]
    cols = [NAVY] * 3 + [BLUE] * 7 + [MUTED, AQUA]
    for yy, (_, r), c in zip(y, d.iterrows(), cols):
        ax.errorbar(r.est, yy, xerr=[[r.est - r.lo], [r.hi - r.est]], fmt="o", color=c, ms=4, capsize=2)
    ax.axvline(1, color=INK, lw=0.8)
    ax.axvline(0.95, color=RED, lw=0.8, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels(d.label, fontsize=8)
    ax.set_xlabel("relative WIS (below 1 = wastewater model more accurate)")
    fig.savefig(FIG / "F3_relative_wis.png")
    plt.close(fig)
    caption("F3_relative_wis", """F3. Relative weighted interval score (WIS) of the forecast model with state
wastewater features against the identical model without them, with 95% two-way bootstrap intervals (states and 4-week
blocks of forecast dates resampled). Dashed red line: the preregistered 5% improvement. Primary panel unless stated;
wastewater usable 10 days after sample collection unless stated. Bottom: the pipeline's positive control (a noisy copy
of next week's admissions, which it detects) and negative control (another state's wastewater, which gives nothing).""")


def f4_timeliness():
    t = pd.read_csv(TAB / "timeliness.csv")
    t = t[t.panel == "primary"]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    a = t[t.horizon == "all"].sort_values("lag_days")
    ax.fill_between(a.lag_days, a.lo, a.hi, color=BLUE, alpha=0.15, lw=0)
    ax.plot(a.lag_days, a.rel_wis, "o-", color=NAVY, lw=2, label="all horizons (95% interval shaded)")
    for hz, col in zip(("0", "1", "2", "3"), (RED, ORANGE, AQUA, MUTED)):
        b = t[t.horizon.astype(str) == hz].sort_values("lag_days")
        ax.plot(b.lag_days, b.rel_wis, "--", color=col, lw=1, label=f"horizon {hz}")
    ax.axhline(1, color=INK, lw=0.8)
    ax.axvline(10, color=MUTED, lw=0.8, ls=":")
    ax.text(10.3, ax.get_ylim()[1] - 0.004, "preregistered assumption", fontsize=7, color=MUTED, va="top")
    ax.set_xlabel("days from sample collection until the result can be used")
    ax.set_ylabel("relative WIS (with / without wastewater)")
    ax.legend(fontsize=7.5, loc="upper left")
    fig.savefig(FIG / "F4_timeliness.png")
    plt.close(fig)
    caption("F4_timeliness", """F4. Exploratory (not preregistered): the value of wastewater appears to depend on how quickly results arrive. Relative
WIS of the with-wastewater model in the primary panel when samples become usable 0 to 17 days after collection
(forecasts are due on Wednesdays; the hospital data then run to the previous Saturday). At 0 days the latest sample is
from the due date itself, an unreachable bound. The gain is largest for the current and next week (horizons 0 and 1);
the all-horizon interval includes 1 except at 0 days.""")


def f5_leadlag():
    ll = pd.read_csv(TAB / "leadlag.csv")
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    ax.plot(ll.lead_weeks, ll.corr_levels, "o-", color=NAVY, label="levels (state-season mean removed)")
    ax.plot(ll.lead_weeks, ll.corr_changes, "o-", color=ORANGE, label="week-to-week changes")
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_xlabel("weeks by which the wastewater week precedes the hospital week")
    ax.set_ylabel("correlation")
    ax.legend(fontsize=8)
    fig.savefig(FIG / "F5_leadlag.png")
    plt.close(fig)
    caption("F5_leadlag", """F5. Exploratory: how far the state wastewater signal leads hospital admissions, in final data
with no reporting delay, over the primary-panel state-seasons. Both correlations peak at a lead of 0-1 weeks, not the two
weeks reported in correlation studies (a bootstrap over state-seasons never puts the peak at 2 weeks).""")


def f6_benchmarks():
    c = pd.read_csv(TAB / "comparators.csv")
    c = c[c.panel == "primary"]
    pick = [("base", "FluSight-baseline"), ("ww", "FluSight-baseline"), ("FluSight-ensemble", "FluSight-baseline"),
            ("base", "FluSight-ensemble"), ("ww", "FluSight-ensemble"), ("ens+ww", "FluSight-ensemble")]
    names = {"base": "our model without wastewater", "ww": "our model with wastewater", "FluSight-ensemble": "FluSight ensemble",
             "ens+ww": "average of FluSight ensemble and our wastewater model"}
    fig, ax = plt.subplots(figsize=(8, 3.2))
    y = np.arange(len(pick))[::-1]
    for yy, (a, b) in zip(y, pick):
        r = c[(c.model == a) & (c.reference == b)].iloc[0]
        ax.errorbar(r.rel_wis, yy, xerr=[[r.rel_wis - r.lo], [r.hi - r.rel_wis]], fmt="o", color=NAVY, ms=4, capsize=2)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{names[a]}  vs  {b.replace('FluSight-', 'FluSight ')}" for a, b in pick], fontsize=8)
    ax.axvline(1, color=INK, lw=0.8)
    ax.set_xlabel("relative WIS (below 1 = more accurate than the reference)")
    fig.savefig(FIG / "F6_benchmarks.png")
    plt.close(fig)
    caption("F6_benchmarks", """F6. The forecasting model used here against FluSight's own forecasts on the same tasks
(primary panel, horizons 0-3). Without wastewater it is already about as accurate as the FluSight ensemble and a third
better than the FluSight baseline, so the wastewater test is against a strong model, not a straw man.""")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    for f in (f1_coverage, f2_example, f3_forest, f4_timeliness, f5_leadlag, f6_benchmarks):
        f()
    print("figures written")
