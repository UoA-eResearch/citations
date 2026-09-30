#!/usr/bin/env python
"""Figures for the report (results/figures/F*.png, with a caption file each)."""
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
from analyze import E1, E2, YEARS, stage1  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB, FIG, PROC = RUN / "results" / "tables", RUN / "results" / "figures", RUN / "data" / "processed"
BLUE, ORANGE, AQUA, INK, MUTED, GRID, NAVY, RED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#898781", "#e1e0d9", "#104281", "#c0392b"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})


def caption(name, text):
    (FIG / f"{name}.txt").write_text(text.strip() + "\n")


def f1_map(df):
    ex = (df.obs_E2_gt1 - df.stat_E2_gt1) / df.elig_E2
    fig, ax = plt.subplots(figsize=(10, 4.6))
    sc = ax.scatter(df.lon, df.lat, c=100 * ex, s=7, cmap="RdBu_r", vmin=-8, vmax=8, linewidths=0)
    ax.set(xlim=(-180, 180), ylim=(-60, 80), xlabel="longitude", ylabel="latitude")
    cb = fig.colorbar(sc, ax=ax, shrink=0.8)
    cb.set_label("excess record-shattering years, 2003–2025\n(% of years, observed minus no-warming null)")
    ax.set_title(f"{len(df):,} qualifying GHCN-Daily stations (validated analysis)")
    fig.savefig(FIG / "F1_station_map.png")
    plt.close(fig)
    caption("F1_station_map", """F1. The qualifying stations (at least 60 valid warm seasons in 1951-2025 and near-complete
coverage in both eras). Colour: the station's excess of record-shattering years in 2003-2025 (years whose hottest day
beat the hottest of the previous 30 years by more than one standard deviation of year-to-year variability), observed
minus the expectation under a no-warming (stationary) null, in percent of years.""")


def f2_yearly(df):
    m = np.array(df.m_obs.tolist())                      # (stations, 75) margins in sigma units
    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    yrs = YEARS[YEARS >= 1981]
    idx = np.isin(YEARS, yrs)
    for k, col, lab in ((1.0, RED, "record-shattering (> 1σ)"), (0.0, ORANGE, "any new 30-year record")):
        n = np.array([np.isfinite(m[:, i]).sum() for i in np.where(idx)[0]])
        f = np.where(n > 100, np.array([np.nansum(m[:, i] > k) for i in np.where(idx)[0]]) / np.maximum(n, 1), np.nan)
        ax.plot(yrs, 100 * f, "o-", ms=3, lw=1.2, color=col, label=f"observed: {lab}")
    for (a, b), era in ((E1, "E1"), (E2, "E2")):
        for pref, col, ls, lab in (("stat", MUTED, "--", "no-warming null"), ("trend", NAVY, ":", "trend-preserving null")):
            v = 100 * df[f"{pref}_{era}_gt1"].sum() / df[f"elig_{era}"].sum()
            ax.plot([a, b], [v, v], color=col, ls=ls, lw=1.6, label=f"{lab} (> 1σ)" if era == "E1" else None)
    ax.set(xlabel="year", ylabel="% of station-years")
    ax.legend(fontsize=7.5, loc="upper left")
    ax.set_title("how often a year's hottest day beats the previous 30 years")
    fig.savefig(FIG / "F2_yearly.png")
    plt.close(fig)
    caption("F2_yearly", """F2. Percentage of qualifying stations whose hottest day of the warm season beat the hottest
of the previous 30 years (orange) and beat it by more than one standard deviation of year-to-year variability
(record-shattering, red), per year. Horizontal lines: expected record-shattering frequency per era under the
no-warming null (grey dashed) and under the station's own smooth warming trend with unchanged variability (blue
dotted).""")


def f3_forest():
    p = pd.read_csv(TAB / "pooled_hinge_permute.csv")
    pre = pd.read_csv(TAB / "pooled.csv").iloc[[0]].copy()
    pre["analysis"] = "preregistered null (flawed; D3-D4)"
    for col in ("R1_obs_over_stationary", "R2_obs_over_trend", "R4_E2_over_E1"):    # it has only a cell-only interval
        pre[col + "_lo_cell"], pre[col + "_hi_cell"], pre[col + "_lo"], pre[col + "_hi"] = pre[col + "_lo"], pre[col + "_hi"], np.nan, np.nan
    p = pd.concat([p, pre], ignore_index=True)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
    for ax, (col, title) in zip(axes, (("R1_obs_over_stationary", "H1: observed / no-warming null (2003–25)"),
                                        ("R2_obs_over_trend", "H2: observed / trend-preserving null (2003–25)"),
                                        ("R4_E2_over_E1", "H4: 2003–25 / 1981–2002 (observed)"))):
        y = np.arange(len(p))[::-1]
        ax.errorbar(p[col], y + 0.18, xerr=[p[col] - p[col + "_lo_cell"], p[col + "_hi_cell"] - p[col]], fmt="none",
                    ecolor="#9aa3ad", lw=1, capsize=1.5)
        ax.errorbar(p[col], y, xerr=[p[col] - p[col + "_lo"], p[col + "_hi"] - p[col]], fmt="o", color=NAVY, ms=4, capsize=2)
        ax.axvline(1, color=INK, lw=0.8)
        ax.set_title(title, fontsize=8.5)
        ax.set_xscale("log")
        ax.set_xticks([0.5, 0.7, 1, 1.5, 2, 3])
        ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%g"))
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axes[0].set_yticks(np.arange(len(p))[::-1])
    axes[0].set_yticklabels(p.analysis, fontsize=8)
    fig.savefig(FIG / "F3_ratios.png")
    plt.close(fig)
    caption("F3_ratios", """F3. Ratios with 95% intervals: dark, the two-way bootstrap (5x5-degree grid cells and 3-year
blocks of years both resampled; deviations.md D6), which allows for heatwave years shared by many stations; thin grey,
the preregistered cell-only bootstrap, which ignores that dependence and is too narrow. For the validated analysis (hinge trend, block-permutation nulls; top) and the preregistered robustness variants. Bottom
row: the preregistered null models, which the synthetic validation showed to be biased (F6). Record-shattering = a year's hottest day beats the
previous 30 years' hottest by more than one standard deviation (thresholds 0 and 2 in two variants; TX7x uses the hottest
7-day mean).""")


def f4_h3(df):
    r = pd.read_parquet(PROC / "station_rates.parquet").merge(df[["station", "obs_E2_gt1", "stat_E2_gt1", "elig_E2"]], on="station")
    r["excess"] = 100 * (r.obs_E2_gt1 - r.stat_E2_gt1) / r.elig_E2
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.scatter(r.rate_berkeley, r.excess, s=4, color=MUTED, alpha=0.4, linewidths=0)
    bins = np.quantile(r.rate_berkeley.dropna(), np.linspace(0, 1, 11))
    c = pd.cut(r.rate_berkeley, bins, include_lowest=True)
    g = r.groupby(c, observed=True).agg(x=("rate_berkeley", "mean"), y=("excess", "mean"), se=("excess", "sem"))
    ax.errorbar(g.x, g.y, yerr=1.96 * g.se, fmt="o-", color=RED, ms=5, capsize=2, label="decile means")
    ax.axhline(0, color=INK, lw=0.7)
    ax.set(xlabel="local warming 1981–2024 (°C per decade, Berkeley Earth)", ylabel="excess record-shattering years (%)")
    ax.legend(fontsize=8)
    fig.savefig(FIG / "F4_rate.png")
    plt.close(fig)
    caption("F4_rate", """F4 (H3). Each station's excess of record-shattering years in 2003-2025 (observed minus the
no-warming null, percent of years) against the local warming rate of its 1-degree grid cell in Berkeley Earth
(1981-2024). Red: means by decile of warming rate with 95% intervals.""")


def f6_validation():
    files = [("preregistered: LOESS + bootstrap", "null_validation.csv"), ("hinge + bootstrap", "null_validation_hinge_bootstrap.csv"),
             ("LOESS + permutation", "null_validation_loess_permute.csv"), ("hinge + permutation (used)", "null_validation_hinge_permute.csv"),
             ("hinge + permutation, curved truth", "null_validation_hinge_permute_truth-loess.csv")]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.4), sharey=True)
    for ax, (world, col, title) in zip(axes, (("no_trend", "R1", "no-warming world: H1 ratio should be 1"),
                                              ("trend", "R2", "steady-warming world: H2 ratio should be 1"))):
        for k, (lab, f) in enumerate(files):
            v = pd.read_csv(TAB / f)
            for thr, mk, off in ((0.0, "s", -0.12), (1.0, "o", 0.12)):
                r = v[(v.world == world) & (v.threshold == thr)].iloc[0]
                ax.errorbar(r[col], k + off, xerr=[[r[col] - r[col + "_lo"]], [r[col + "_hi"] - r[col]]], fmt=mk, ms=5,
                            color=NAVY if "used" in lab else MUTED, capsize=2, label=(f"threshold {int(thr)}" if k == 0 else None))
        ax.axvline(1, color=RED, lw=1)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("ratio in synthetic data with a known answer")
    axes[0].set_yticks(range(len(files)))
    axes[0].set_yticklabels([f[0] for f in files], fontsize=8)
    axes[0].invert_yaxis()
    axes[0].legend(fontsize=7.5, loc="lower right")
    fig.savefig(FIG / "F6_null_validation.png")
    plt.close(fig)
    caption("F6_null_validation", """F6. Validating the null models on synthetic station series with a known answer: each
qualifying station's own trend (or no trend) plus stationary noise matched to its variability, run through the full
pipeline (3 replicates of 2,013 stations). A calibrated method gives ratio 1. The preregistered nulls (LOESS trend,
resampling with replacement) are biased by 10-25%; resampling with replacement under-produces records because duplicated
extreme values cannot be strictly beaten. Hinge detrending with block permutation (blue) is calibrated, including when
the true trend is curved (bottom row).""")


def f5_margins(df):
    m = np.array(df.m_obs.tolist())
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    bins = np.linspace(-6, 4, 51)
    for (a, b), col, lab in ((E1, BLUE, "1981–2002"), (E2, RED, "2003–2025")):
        sel = (YEARS >= a) & (YEARS <= b)
        v = m[:, sel].ravel()
        v = v[np.isfinite(v)]
        ax.hist(v, bins=bins, density=True, histtype="step", lw=1.8, color=col, label=f"{lab} (n = {len(v):,})")
    ax.axvline(0, color=INK, lw=0.7)
    ax.axvline(1, color=INK, lw=0.7, ls=":")
    ax.set(xlabel="margin over the previous 30 years' hottest day (standard deviations)", ylabel="density", yscale="log")
    ax.legend(fontsize=8)
    fig.savefig(FIG / "F5_margins.png")
    plt.close(fig)
    caption("F5_margins", """F5. Distribution of the 30-year record margin (a year's hottest day minus the hottest of
the previous 30 years, in units of the station's year-to-year standard deviation) in the two eras, pooled over
stations. Positive values are new 30-year records; values above 1 (dotted) are record-shattering.""")


def f7_coverage():
    v = pd.read_csv(TAB / "coverage_validation_kernel.csv")
    fig, axes = plt.subplots(1, 4, figsize=(12, 4.2), sharey=True)
    for ax, ((kind, thr), g) in zip(axes, v.groupby(["kind", "threshold"], sort=False)):
        g = g.sort_values("est").reset_index(drop=True)
        y = np.arange(len(g))
        ax.errorbar(g.est, y + 0.25, xerr=[g.est - g.cell_lo, g.cell_hi - g.est], fmt="none", ecolor="#9aa3ad", lw=1)
        ax.errorbar(g.est, y, xerr=[g.est - g.two_lo, g.two_hi - g.est], fmt="o", color=NAVY, ms=3, lw=1)
        ax.axvline(1, color=RED, lw=1)
        ax.set_xscale("log")
        ax.set_xticks([0.5, 0.7, 1, 1.5, 2])
        ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%g"))
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        name = "H2 ratio, steady-warming world" if kind == "trend" else "H1 ratio, no-warming world"
        ax.set_title(f"{name}, threshold {int(thr)}\ncovers 1: two-way {g.two_covers.mean():.0%}, cell-only {g.cell_covers.mean():.0%}", fontsize=8.5)
    axes[0].set_ylabel("synthetic world (sorted by estimate)")
    axes[0].set_yticks([])
    fig.savefig(FIG / "F7_interval_coverage.png")
    plt.close(fig)
    caption("F7_interval_coverage", """F7. Do the 95% intervals contain the true answer? Thirty synthetic worlds per panel in
which the true ratio is exactly 1, with year-to-year noise correlated between stations as in the data (correlation
falling with distance: about 0.56 within 500 km, 0.18 at 1,000-1,500 km). Dark: the two-way bootstrap (grid cells and
3-year blocks of years resampled) used in this report. Thin grey: the preregistered cell-only bootstrap. The red line is
the truth. The cell-only intervals miss it far more often than the nominal 5%.""")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    df = stage1("txx", 3, "hinge", "permute")
    for f in (lambda: f1_map(df), lambda: f2_yearly(df), f3_forest, lambda: f4_h3(df), lambda: f5_margins(df), f6_validation, f7_coverage):
        try:
            f()
        except FileNotFoundError as e:
            print("skip", e)
    print("figures written")
