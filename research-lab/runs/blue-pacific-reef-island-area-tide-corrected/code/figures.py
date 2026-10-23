"""Figures for the report (each PNG has a .txt caption). Written after rates.py, h2_diag.py and dep_compare.py.

  F1  H2: uncorrected against tide-corrected Sentinel-2 rates per islet, and the bias against tide slope x the trend
      in overpass-time water level
  F2  the sensor-step guard (Landsat Collection 1 vs Sentinel-2 at 30 m, 2017-2021) and the H1 epochs
  F3  the D5 land screen: share of clear Sentinel-2 scenes in which dry land covers at least 10% of the OSM feature
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
INK, INK2, GRID, SURF, BLUE, ORANGE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def one_to_one(ax, lim):
    ax.plot(lim, lim, color=INK2, lw=0.8, ls="--", zorder=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.axhline(0, color=GRID, lw=0.8, zorder=0); ax.axvline(0, color=GRID, lw=0.8, zorder=0)


def f1():
    x = pd.read_csv(T / "h2_diagnostics_islets.csv")
    h = json.load(open(T / "h2_diagnostics.json"))
    r = pd.read_csv(T / "islet_rates.csv")
    r = r[(r.family == "E2") & (r.series == "area_otsu") & (r.robust_slope == 0)].set_index("islet")
    x = x.join(r[["rate_corr", "rate_uncorr"]], on="islet")
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 4.0))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.14, top=0.86, wspace=0.28)
    one_to_one(ax[0], (-12, 12))
    ax[0].scatter(x.rate_corr, x.rate_uncorr, s=14, color=BLUE, alpha=0.75, edgecolor=SURF, lw=0.5, zorder=2)
    ax[0].set_xlabel("tide-corrected rate (%/yr of OSM area)"); ax[0].set_ylabel("uncorrected rate (%/yr)")
    ax[0].set_title("a  Sentinel-2 epoch, 2017-2026", loc="left", fontsize=9.5, color=INK)
    lim = (-8, 12)
    one_to_one(ax[1], lim)
    ax[1].scatter(x.beta_pct_per_m * x.level_trend_m_yr, x.bias, s=14, color=BLUE, alpha=0.75, edgecolor=SURF,
                  lw=0.5, zorder=2)
    ax[1].set_xlabel("tide slope x overpass water-level trend (%/yr)"); ax[1].set_ylabel("uncorrected minus corrected (%/yr)")
    ax[1].set_title("b  the difference is tide slope x sampled-level trend (an identity)", loc="left",
                    fontsize=9.5, color=INK)
    for a in ax:
        a.grid(color=GRID, lw=0.5)
    fig.suptitle("Tide correction changes Sentinel-2-era islet rates by about 1%/yr", x=0.02, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F1_tide_bias.png", dpi=170); plt.close(fig)
    caption("F1_tide_bias", f"""Each point is a retained, non-engineered islet of at least 1 ha with a Sentinel-2
    rate ({h['islets']} islets in 6 atolls). (a) Theil-Sen rate of uncorrected area against the rate after removing
    each islet's tide response; the dashed line is equality. The mean absolute difference is
    {h['mean_abs_bias']:.2f}%/yr (H2, preregistered); with water levels permuted within each islet it is
    {h['mean_abs_bias_under_permuted_levels']:.2f}%/yr (post hoc noise floor). (b) The difference against the islet's
    tide slope (% of area per metre) times the Theil-Sen trend of the gauge water level at that islet's own usable
    images. This relation is an identity of the correction, not evidence of a mechanism: each islet's finite sample of
    overpass tide levels has a chance trend, and the uncorrected rate carries it.
    {int(((x.rate_corr.abs() > 12) | (x.rate_uncorr.abs() > 12)).sum())} islets lie outside the axes of (a).""")


def f2():
    r = pd.read_csv(T / "islet_rates.csv")
    r = r[(r.engineered == 0) & (r.area_ha >= 5) & (r.robust_slope == 0) & (r.possible_loss == 0)]
    gl = r[(r.family == "guard_ls") & (r.series == "area_otsu")].set_index("islet")
    gs = r[(r.family == "guard_s2_30m") & (r.series == "area_otsu_30m")].set_index("islet")
    g = gl[["rate_corr"]].join(gs[["rate_corr"]], rsuffix="_s2", how="inner")
    e1 = r[(r.family == "E1") & (r.series == "area_otsu")].set_index("islet")
    e2 = r[(r.family == "E2") & (r.series == "area_otsu")].set_index("islet")
    e = e1[["rate_corr"]].join(e2[["rate_corr"]], rsuffix="_e2", how="inner")
    h = json.load(open(T / "h1_h2.json"))
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 4.0))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.14, top=0.86, wspace=0.28)
    one_to_one(ax[0], (-6, 6))
    ax[0].scatter(g.rate_corr_s2, g.rate_corr, s=22, color=ORANGE, edgecolor=SURF, lw=0.5, zorder=2)
    ax[0].set_xlabel("Sentinel-2 at 30 m (%/yr)"); ax[0].set_ylabel("Landsat 8 Collection 1 (%/yr)")
    gd = h["guard"]
    ax[0].set_title(f"a  guard, 2017-2021: Landsat minus S2 {gd['mean_diff']:+.2f} ({gd['ci'][0]:.2f} to "
                    f"{gd['ci'][1]:.2f})", loc="left", fontsize=9.5, color=INK)
    one_to_one(ax[1], (-6, 6))
    ax[1].scatter(e.rate_corr, e.rate_corr_e2, s=22, color=BLUE, edgecolor=SURF, lw=0.5, zorder=2)
    ax[1].set_xlabel("1999-2015, Landsat (%/yr)"); ax[1].set_ylabel("2017-2026, Sentinel-2 (%/yr)")
    hd = h["H1"]
    ax[1].set_title(f"b  H1 epochs: D = {hd['D']:+.2f} ({hd['ci'][0]:.2f} to {hd['ci'][1]:.2f})", loc="left",
                    fontsize=9.5, color=INK)
    for a in ax:
        a.grid(color=GRID, lw=0.5)
    fig.suptitle("The two sensors are not shown to agree in the overlap, so the cross-epoch test is not licensed", x=0.02, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F2_guard_and_epochs.png", dpi=170); plt.close(fig)
    caption("F2_guard_and_epochs", f"""Non-engineered islets of at least 5 ha, tide-corrected rates as % of OSM area
    per year; dashed lines are equality. (a) The preregistered sensor-step guard: the same {gd['islets']} islets
    measured with Landsat 8 Collection 1 and with Sentinel-2 resampled to 30 m within each islet's Sentinel-2 window
    (2017-2021). The interval of the mean difference is not inside the +/-0.2%/yr band (it includes zero, so the sensors
    are not shown to disagree either), so H1 is not testable by the plan's rule. (b) The H1 comparison it would have
    licensed: {hd['islets']} islets in {hd['atolls']} atolls with rates in both epochs.""")


def f3():
    t = pd.read_csv(T / "land_screen.csv")
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.17, top=0.84)
    bins = np.linspace(0, 1, 21)
    pen, oth = t[t.atoll == "penrhyn"].land_share, t[t.atoll != "penrhyn"].land_share
    ax.hist([oth, pen], bins=bins, stacked=True, color=[BLUE, ORANGE], edgecolor=SURF, lw=0.6,
            label=[f"other atolls ({len(oth)})", f"Penrhyn ({len(pen)})"])
    ax.axvline(0.5, color=INK2, lw=0.8, ls="--"); ax.text(0.51, ax.get_ylim()[1] * 0.92, "kept at or above 0.5",
                                                         fontsize=8, color=INK2)
    ax.set_xlabel("share of clear Sentinel-2 scenes with dry land (MNDWI < 0) over at least 10% of the feature")
    ax.set_ylabel("OSM features"); ax.legend(frameon=False, fontsize=8); ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Most of Penrhyn's mapped 'islets' are never dry: submerged lagoon knolls", x=0.02, ha="left",
                 fontsize=10.5, color=INK)
    fig.savefig(F / "F3_land_screen.png", dpi=170); plt.close(fig)
    caption("F3_land_screen", f"""All {len(t)} measured OSM features of at least 1 ha (D5). Dry land is MNDWI below
    0, which no water depth gives. {int(t.retained.sum())} features are kept as islets; {int((~t.retained).sum())}
    are not, {int(((~t.retained) & (t.atoll == 'penrhyn')).sum())} of them at Penrhyn, where imagery shows
    submerged coral knolls in the lagoon that OSM maps as islets.""")


if __name__ == "__main__":
    f1(); f2(); f3()
    print("figures written")
