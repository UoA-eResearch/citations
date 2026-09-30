#!/usr/bin/env python
"""Figures for the report (results/figures/F*.png, with a caption file each)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from calib import TOOLS, lr_target  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB, FIG = RUN / "results" / "tables", RUN / "results" / "figures"
BLUE, ORANGE, AQUA, INK, MUTED, GRID, NAVY = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#898781", "#e1e0d9", "#104281"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})
PTS_LABEL = {-4: "−4\nStrong", -3: "−3", -2: "−2\nMod.", -1: "−1\nSupp.", 1: "+1\nSupp.", 2: "+2\nMod.", 3: "+3", 4: "+4\nStrong"}


def caption(name, text):
    (FIG / f"{name}.txt").write_text(text.strip() + "\n")


def f1_cohorts():
    c = pd.read_csv(TAB / "cohort_sizes_rare.csv")
    fig, ax = plt.subplots(figsize=(7.5, 3.0))
    x = np.arange(len(c))
    ax.bar(x - 0.2, c.P, 0.4, color=ORANGE, label="pathogenic / likely pathogenic")
    ax.bar(x + 0.2, c.B, 0.4, color=BLUE, label="benign / likely benign")
    ax.set_xticks(x)
    ax.set_xticklabels(c.cohort, fontsize=8)
    ax.set_ylabel("rare missense variants")
    ax.legend(fontsize=8)
    ax.set_title("calibration-era set and yearly cohorts of newly classified variants")
    fig.savefig(FIG / "F1_cohorts.png")
    plt.close(fig)
    caption("F1_cohorts", """F1. Variants per cohort (rare missense SNVs, gnomAD AF < 0.01, ClinVar >= 1 star, not
conflicting). C2019: confidently classified in the December-2019 release (the calibration era). N_2020 ... N_2026:
variants first confidently classified in each later release (N_2026: December 2025 to September 2026).""")


def f2_h1():
    h = pd.read_csv(TAB / "h1_interval_lr.csv")
    tools = [t for t in TOOLS]
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.2), sharey=True)
    for ax, t in zip(axes.flat, tools):
        d = h[h.tool == t]
        pts = sorted(d.points.unique())
        xs = {p: i for i, p in enumerate(pts)}
        for c, col, off, lab in (("C2019", MUTED, -0.22, "calibration era (2019)"), ("N_2020", AQUA, 0.0, "new in 2020 (published check)"),
                                 ("N_new", NAVY, 0.22, "new in 2021–2026 (this study)")):
            e = d[d.cohort == c].set_index("points")
            for p in pts:
                if p not in e.index:
                    continue
                r = e.loc[p]
                if not np.isfinite(r.lr) or r.lr <= 0:
                    continue
                lo = r.lr_lo5 if np.isfinite(r.lr_lo5) and r.lr_lo5 > 0 else r.lr
                hi = r.lr_hi95 if np.isfinite(r.lr_hi95) else r.lr
                ax.errorbar(xs[p] + off, r.lr, yerr=[[max(r.lr - lo, 0)], [max(hi - r.lr, 0)]], fmt="o", ms=4,
                            color=col, capsize=2, lw=1, label=lab if p == pts[0] else None)
        for p in pts:
            ax.plot([xs[p] - 0.38, xs[p] + 0.38], [lr_target(p)] * 2, color=ORANGE, lw=1.6)
        ax.set_yscale("log")
        ax.set_xticks(range(len(pts)))
        ax.set_xticklabels([PTS_LABEL.get(p, str(p)) for p in pts], fontsize=7)
        ax.set_title(TOOLS[t]["label"])
        ax.axhline(1, color=INK, lw=0.6)
    axes[0, 0].set_ylabel("likelihood ratio in interval")
    axes[1, 0].set_ylabel("likelihood ratio in interval")
    axes[0, 0].legend(fontsize=7, loc="upper left")
    fig.suptitle("H1: realised likelihood ratio per published evidence interval (orange bar = target the interval must reach)", fontsize=10)
    fig.savefig(FIG / "F2_h1_interval_lr.png")
    plt.close(fig)
    caption("F2_h1_interval_lr", """F2 (H1). For each tool and each published evidence interval (x axis, ACMG points;
negative = benign evidence BP4, positive = pathogenic evidence PP3), the likelihood ratio realised in each cohort:
fraction of pathogenic variants in the interval divided by the fraction of benign variants in it. Points: estimate;
bars: 5th-95th percentile over 2,000 gene-cluster bootstrap resamples. Orange bars: the likelihood ratio each
interval must reach (2.406 per point; benign intervals must fall below the reciprocal). An interval holds when its
pathogenic-side lower bound is above the orange bar (benign side: upper bound below it).""")


def f3_h2():
    h = pd.read_csv(TAB / "h2_trend.csv")
    order = ["C2019", "N_2020"] + [f"N_{y}" for y in range(2021, 2027)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    for ax, side in zip(axes, (">= +3", "<= -3")):
        for t, col in (("revel", NAVY), ("am", ORANGE), ("esm1b", AQUA), ("bayesdel", MUTED)):
            d = h[(h.tool == t) & (h.side == side)].set_index("cohort").reindex(order)
            x = np.arange(len(order)) + {"revel": -0.15, "am": -0.05, "esm1b": 0.05, "bayesdel": 0.15}[t]
            ok = np.isfinite(d.lr) & (d.lr > 0)
            lo = np.where(np.isfinite(d.lr_lo5) & (d.lr_lo5 > 0), d.lr_lo5, d.lr)
            hi = np.where(np.isfinite(d.lr_hi95), d.lr_hi95, d.lr)
            ax.errorbar(x[ok], d.lr[ok], yerr=[np.maximum(d.lr[ok] - lo[ok], 0), np.maximum(hi[ok] - d.lr[ok], 0)],
                        fmt="o-", ms=3.5, lw=1, capsize=2, color=col, label=TOOLS[t]["label"])
        tgt = lr_target(3) if side == ">= +3" else lr_target(-3)
        ax.axhline(tgt, color=ORANGE, lw=1, ls="--")
        ax.set_yscale("log")
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([o.replace("N_", "") for o in order], fontsize=8)
        ax.axvline(order.index("N_2022") + 0.5, color=INK, lw=0.7, ls=":")
        ax.text(order.index("N_2022") + 0.55, ax.get_ylim()[1], " REVEL thresholds\n published", fontsize=7, va="top")
        ax.set_title(f"pooled strongest {'pathogenic' if side == '>= +3' else 'benign'} intervals ({side} points)")
        ax.set_xlabel("cohort (year first confidently classified)")
    axes[0].set_ylabel("likelihood ratio")
    axes[0].legend(fontsize=7.5, loc="lower right")
    fig.savefig(FIG / "F3_h2_trend.png")
    plt.close(fig)
    caption("F3_h2_trend", """F3 (H2). Likelihood ratio of the pooled strongest evidence intervals (pathogenic: +3 and +4
points; benign: -3 and -4) among variants first confidently classified in each year. Bars: 5th-95th gene-bootstrap
percentiles. Dashed orange line: the +3 / -3 target. Dotted line: publication of the REVEL/BayesDel thresholds
(AJHG, December 2022); AlphaMissense and ESM1b thresholds followed in September 2024 (bioRxiv).""")


def f4_h3():
    by = pd.read_csv(TAB / "h3_missense_by_year.csv")
    fig, ax = plt.subplots(figsize=(7, 3.3))
    for side, col, lab in (("P", ORANGE, "pathogenic / likely pathogenic"), ("B", BLUE, "benign / likely benign")):
        d = by[(by.side == side) & (by.n >= 10)]
        ax.errorbar(d.year + (0.08 if side == "B" else -0.08), 100 * d.frac,
                    yerr=[np.clip(100 * (d.frac - d.lo95), 0, None), np.clip(100 * (d.hi95 - d.frac), 0, None)], fmt="o-", ms=4, lw=1.2, capsize=2, color=col, label=lab)
    ax.axvline(2022.9, color=INK, lw=0.7, ls=":")
    ax.set(xlabel="expert-panel approval year", ylabel="% of labels that need PP3/BP4")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("H3: ClinGen expert-panel missense classifications that would be VUS without computational evidence")
    fig.savefig(FIG / "F4_h3_tool_dependence.png")
    plt.close(fig)
    caption("F4_h3_tool_dependence", """F4 (H3). Share of ClinGen expert-panel (VCEP) missense classifications whose
pathogenic or benign category depends on the computational criteria: recounting the panel's own applied criteria on
the ACMG points scale without the PP3/BP4 points moves the variant into VUS. Bars: Wilson 95% intervals; years with
fewer than 10 classifications on a side are omitted. Dotted line: publication of the calibrated thresholds.""")


def f5_composition():
    c = pd.read_csv(TAB / "explore_composition.csv")
    order = ["C2019", "N_2020"] + [f"N_{y}" for y in range(2021, 2027)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.5))
    for (lab, strat), col, ls in (((("B", "1-star")), BLUE, "-"), (("B", "2+star"), BLUE, "--"),
                                  (("P", "1-star"), ORANGE, "-"), (("P", "2+star"), ORANGE, "--")):
        d = c[(c.label == lab) & (c.stratum == strat)].set_index("cohort").reindex(order)
        name = ("benign" if lab == "B" else "pathogenic") + (", single submitter" if strat == "1-star" else ", multi-submitter / panel")
        a1.plot(range(len(order)), d.median_revel, "o" + ls, color=col, ms=4, lw=1.4, label=name)
        if lab == "B":
            a2.bar(np.arange(len(order)) + (-0.2 if strat == "1-star" else 0.2), d.n, 0.4, color=col,
                   alpha=1.0 if strat == "1-star" else 0.45, label=name)
    for a in (a1, a2):
        a.set_xticks(range(len(order)))
        a.set_xticklabels([o.replace("N_", "") for o in order], fontsize=8)
        a.axvline(order.index("N_2022") + 0.5, color=INK, lw=0.7, ls=":")
        a.set_xlabel("cohort (year first confidently classified)")
    a1.set_ylabel("median REVEL score of new labels")
    a1.legend(fontsize=7, loc="center right")
    a1.set_title("new benign labels from single submitters shift to low scores")
    a2.set_ylabel("new benign labels (rare missense)")
    a2.legend(fontsize=7, loc="upper left")
    a2.set_title("and their number jumps")
    fig.savefig(FIG / "F5_benign_composition.png")
    plt.close(fig)
    caption("F5_benign_composition", """F5 (exploratory). Left: median REVEL score of newly classified labels by year, for
single-submitter (1-star) and multi-submitter or expert-panel (>= 2-star) classifications. Pathogenic labels (orange)
do not change; benign labels from single submitters (solid blue) move to lower scores from 2023, while benign labels
from multiple submitters or panels (dashed blue) do not. Right: the number of newly classified benign rare missense
variants per year. The shift is mostly one laboratory's bulk submission of likely-benign calls in genes without earlier
benign labels (report section 4.3). Dotted line: publication of the calibrated thresholds (December 2022).""")


def f6_without_bulk():
    w = pd.read_csv(TAB / "explore_without_bulk.csv")
    order = ["C2019", "N_2020"] + [f"N_{y}" for y in range(2021, 2027)]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4), sharey=True)
    for ax, t in zip(axes, ("revel", "am", "esm1b")):
        for sub, col, lab in (("all", MUTED, "all new labels"), ("without_single_lab_bulk", NAVY, "without one laboratory's bulk benign submissions")):
            d = w[(w.tool == t) & (w.subset == sub)].set_index("cohort").reindex(order)
            ax.errorbar(range(len(order)), d.lr_ge3, yerr=[np.clip(d.lr_ge3 - d.lo5, 0, None), np.clip(d.hi95 - d.lr_ge3, 0, None)],
                        fmt="o-", ms=3.5, lw=1.2, capsize=2, color=col, label=lab)
        ax.axhline(lr_target(3), color=ORANGE, lw=1, ls="--")
        ax.axvline(order.index("N_2022") + 0.5, color=INK, lw=0.7, ls=":")
        ax.set_yscale("log")
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([o.replace("N_", "") for o in order], fontsize=7.5)
        ax.set_title(TOOLS[t]["label"])
    axes[0].set_ylabel("pooled >= +3 likelihood ratio")
    axes[0].legend(fontsize=7, loc="upper left")
    fig.savefig(FIG / "F6_without_bulk.png")
    plt.close(fig)
    caption("F6_without_bulk", """F6 (exploratory). Likelihood ratio of the pooled strongest pathogenic intervals (+3 and +4
points) among newly classified variants each year, for all new labels (grey) and after removing variants whose only
ClinVar submitter is the laboratory that made 60% of the 2023-2026 single-submitter benign classifications (blue).
Without those bulk submissions the post-2022 rise disappears: REVEL is flat and AlphaMissense and ESM1b decline.
Dashed orange line: the +3 target (13.9). Bars: 5th-95th gene-bootstrap percentiles.""")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    for f in (f1_cohorts, f2_h1, f3_h2, f4_h3, f5_composition, f6_without_bulk):
        try:
            f()
        except FileNotFoundError as e:
            print("skip", f.__name__, e)
    print("figures written")
