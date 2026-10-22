"""Figures for the report (each PNG has a .txt caption). Written after analysis.py and analysis_slips.py.

  F1  newly bare share of land (200 m cells) and the 56 sites by exposure tercile
  F2  event study: top minus bottom tercile, site-demeaned mud content by year, with the placebo years
  F3  dose-response: each site's 2023 mud content minus its 2010-2022 mean, against exposure
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyproj  # noqa: E402
import rasterio  # noqa: E402

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, ORANGE, LAND = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317", "#f1f0eb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
TERC = {"bottom": "#9ec5f0", "middle": "#5a97dc", "top": "#d95926"}


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1():
    with rasterio.open(RUN / "data" / "bare20.tif") as ds:
        bare, valid, tf = ds.read(1).astype(float), ds.read(2).astype(float), ds.transform
    with rasterio.open(RUN / "data" / "sea20.tif") as ds:
        sea = ds.read(1).astype(bool)
    k = 10
    h, w = (bare.shape[0] // k) * k, (bare.shape[1] // k) * k
    agg = lambda a: a[:h, :w].reshape(h // k, k, w // k, k).sum((1, 3))
    B, V, S = agg(bare), agg(valid), agg(sea.astype(float))
    frac = np.where(V > 50, B / np.maximum(V, 1), np.nan)
    ex = pd.read_csv(T / "exposure.csv").merge(pd.read_csv(T / "sites.csv"), on="site_id")
    x, y = pyproj.Transformer.from_crs(4326, 2193, always_xy=True).transform(ex.lon.values, ex.lat.values)
    c, r = ~(tf * tf.scale(k)) * (x, y)
    fig, ax = plt.subplots(figsize=(7.2, 8.0))
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.04, top=0.92)
    ax.imshow(np.where(S > 50, 1.0, np.nan), cmap=matplotlib.colors.ListedColormap(["#dbe8f5"]))
    ax.imshow(np.where(np.isnan(frac) & (S <= 50), 1.0, np.nan), cmap=matplotlib.colors.ListedColormap([LAND]))
    im = ax.imshow(np.where(frac > 0, frac * 100, np.nan), cmap="Greys", vmin=0, vmax=5)
    for t in ("bottom", "middle", "top"):
        m = ex.tercile == t
        ax.scatter(c[m], r[m], s=26, color=TERC[t], edgecolor=INK, lw=0.4, label=f"{t} tercile", zorder=3)
    ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.legend(frameon=False, loc="lower left", fontsize=8)
    cb = fig.colorbar(im, ax=ax, shrink=0.35, pad=0.01); cb.set_label("newly bare, % of land per 200 m cell")
    fig.suptitle("Newly bare land after the 2023 storms, and the 56 monitoring sites", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_exposure_map.png", dpi=170); plt.close(fig)
    e = json.load(open(T / "exposure_summary.json")); sl = json.load(open(T / "exposure_slips_summary.json"))
    caption("F1_exposure_map", f"""Newly bare: median Sentinel-2 NDVI at least 0.5 in November-December 2022 and at
    most 0.3 in 15 February - 30 April 2023, with at least 2 clear observations in each window; shown as the share of
    valid 10 m pixels per 200 m cell, darker is more. Sites are coloured by the frozen tercile of exposure, the newly
    bare share of land draining to the coast within 5 km (median {100 * e['primary_E_quantiles']['0.5']:.2f}%,
    tercile cuts {100 * e['tercile_cutpoints'][0]:.3f}% and {100 * e['tercile_cutpoints'][1]:.3f}%).
    {100 * sl['share_of_bare_px_in_patches_gt_5ha']:.0f}% of newly bare area lies in patches over 5 ha, mostly
    market-garden and plantation harvest (south and west), and {100 * sl['share_of_bare_px_in_patches_le_1ha']:.0f}%
    in slip-sized patches of 1 ha or less.""")


def f2():
    es = pd.read_csv(T / "event_study.csv")
    p = json.load(open(T / "primary.json"))
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.15, top=0.84)
    ax.axhline(0, color=GRID, lw=0.9)
    ax.plot(es.year, es.top_minus_bottom, color=BLUE, lw=2, marker="o", ms=5, zorder=3)
    pl = p["placebo_beta"]
    ax.scatter([int(k) for k in pl], list(pl.values()), marker="s", s=22, facecolor=SURF, edgecolor=INK2, zorder=4,
               label="placebo-year estimates (pre-2023 data)")
    ax.axvspan(2022.6, 2023.4, color=ORANGE, alpha=0.18, lw=0)
    ax.text(2022.5, ax.get_ylim()[1] * 0.95, "storms Jan-Feb 2023;\nsurvey Oct-Nov", fontsize=7.5, color=INK2, va="top",
            ha="right")
    b = p["H1"]["top_2023"]
    ax.errorbar([2023.15], [b["estimate"]], yerr=[[b["estimate"] - b["wild_ci"][0]], [b["wild_ci"][1] - b["estimate"]]],
                fmt="D", color=ORANGE, ms=6, capsize=3, zorder=5, label="H1 estimate, 2023 (95% wild bootstrap)")
    ax.set_xticks(range(2010, 2025, 2)); ax.set_ylabel("top minus bottom tercile (pp mud)")
    ax.grid(axis="y", color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=7.5, loc="lower left")
    fig.suptitle("Most exposed minus least exposed sites, mud content relative to each site's 2010-2022 mean",
                 x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_event_study.png", dpi=170); plt.close(fig)
    caption("F2_event_study", f"""Line: mean deviation of mud content from each site's 2010-2022 mean, top-tercile
    sites minus bottom-tercile sites, by survey year ({p['H1']['sites']} sites). Squares: the same fixed-effects
    contrast with each of 2015-2021 treated as a fake event year, on pre-2023 data. Diamond: the preregistered H1
    estimate for 2023, {b['estimate']:+.2f} pp (95% wild cluster bootstrap {b['wild_ci'][0]:+.2f} to
    {b['wild_ci'][1]:+.2f}; {p['H1']['harbours']} harbours). 2022, before the storms, already sat at
    {es.set_index('year').top_minus_bottom[2022]:+.2f}.""")


def f3():
    d = A.load()
    base = d[d.year <= 2022].groupby("site_id").y.mean()
    x = d[d.year == 2023].assign(change=lambda z: z.y - z.site_id.map(base))
    p = json.load(open(T / "primary.json"))
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    fig.subplots_adjust(left=0.1, right=0.97, bottom=0.15, top=0.84)
    ax.axhline(0, color=GRID, lw=0.9)
    for t in ("bottom", "middle", "top"):
        m = x.tercile == t
        ax.scatter(100 * x.E_route_5[m], x.change[m], s=24, color=TERC[t], edgecolor=INK, lw=0.4, label=f"{t} tercile", zorder=3)
    ax.set_xscale("log"); ax.set_xlabel("exposure: newly bare share of contributing land (%, log scale)")
    ax.set_ylabel("2023 mud minus 2010-2022 mean (pp)"); ax.grid(color=GRID, lw=0.5); ax.legend(frameon=False, fontsize=8)
    h2 = p["H2"]
    fig.suptitle("No dose-response: 2023 mud change against storm exposure", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F3_dose_response.png", dpi=170); plt.close(fig)
    caption("F3_dose_response", f"""Each point is a site with a 2023 survey ({len(x)} sites): its 2023 mud content
    minus its own 2010-2022 mean, against its frozen exposure. The preregistered H2 slope, with site and year fixed
    effects, is {h2['delta_per_iqr']:+.2f} pp per interquartile range of exposure (95% wild cluster bootstrap
    {h2['delta_per_iqr_wild_ci'][0]:+.2f} to {h2['delta_per_iqr_wild_ci'][1]:+.2f}). The two most exposed sites
    (Auckland Airport and Clarks Beach, Manukau Harbour) sit beside the Pukekohe market-garden belt.""")


if __name__ == "__main__":
    f1(); f2(); f3()
    print("figures written")
