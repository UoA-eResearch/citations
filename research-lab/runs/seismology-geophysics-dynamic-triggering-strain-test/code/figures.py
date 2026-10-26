"""Figures (PNG + .txt caption). Written after analyse.py.

  F1  left: excess significant rate (observed - matched null) by quintile of estimated peak dynamic strain, with
      two-way bootstrap 95% intervals: preregistered, triggers <= M8, and post hoc exposure-corrected; right: observed
      significant station x trigger pairs against the expected number of false positives, per trigger
  F2  station map: observed significant rate minus p0 per station (population pairs), with geothermal areas marked
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
INK, INK2, GRID, SURF, BLUE, ORANGE, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#d6532a", "#8a8984"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
p = json.load(open(T / "primary.json"))


def f1():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), gridspec_kw={"width_ratios": [1.15, 1]})
    fig.subplots_adjust(left=0.09, right=0.93, bottom=0.14, top=0.84, wspace=0.3)
    ax = axes[0]
    specs = [("primary", "preregistered", INK, -0.18), ("no_m8", "triggers <= M8", BLUE, 0.0),
             ("exposure", "post hoc: exposure-corrected", ORANGE, 0.18)]
    for k, lab, c, dx in specs:
        if k not in p:
            continue
        v = p[k]
        x = np.arange(1, 6) + dx
        e = [v["E"][str(q)] for q in range(1, 6)]
        lo = [v["E_ci95"][str(q)][0] for q in range(1, 6)]
        hi = [v["E_ci95"][str(q)][1] for q in range(1, 6)]
        ax.errorbar(x, e, yerr=[np.subtract(e, lo), np.subtract(hi, e)], fmt="o", ms=4.5, capsize=2, color=c,
                    label=f"{lab} (H1 {v['H1']}, H2 {v['H2']})")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks(range(1, 6)); ax.set_xticklabels(["1 (lowest)", "2", "3", "4", "5 (highest)"])
    ax.set_xlabel("quintile of estimated peak dynamic strain"); ax.set_ylabel("excess share of significant pairs\n(observed - matched null)")
    ax.legend(frameon=False, fontsize=7.2, loc="lower left")
    ax.set_title(f"{p['primary']['pairs']:,} station x trigger pairs; {p['primary']['triggers']} triggers; "
                 f"{p['primary']['stations']:,} stations", fontsize=8.5, color=INK, loc="left")
    ax = axes[1]
    pr = pd.read_parquet(T / "pairs_primary.parquet")
    pr = pr[pr.in_population]
    g = pr.groupby("trigger").agg(observed=("sig", "sum"), expected=("p0", "sum"), mag=("mag", "first"))
    sc = ax.scatter(g.expected, g.observed, c=g.mag, cmap="viridis", s=14, alpha=0.85, edgecolors="none")
    m = max(g.expected.max(), g.observed.max()) * 1.05
    ax.plot([0, m], [0, m], color=INK2, lw=0.8, ls="--")
    ax.set_xlabel("expected false positives (sum of station p0)"); ax.set_ylabel("observed significant pairs")
    cb = fig.colorbar(sc, ax=ax, fraction=0.04, pad=0.02); cb.set_label("trigger magnitude", color=INK2)
    ax.set_title(f"per trigger: {int(g.observed.sum()):,} observed vs {g.expected.sum():,.0f} expected", fontsize=8.5, color=INK, loc="left")
    fig.suptitle("No excess of local-event rises after distant M7+ earthquakes, and none that grows with strain",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F1_excess_by_strain.png", dpi=170); plt.close(fig)
    (F / "F1_excess_by_strain.txt").write_text(" ".join("""Station x trigger pairs: global M >= 7.0 earthquakes 2002-2025 at least
1,000 km from every analysed station, against western-US stations of the QuakeScope 2026 PhaseNet catalogue. A pair is
significant when the station's 3-station-coincident P-S pairs in the 24 h after the surface-wave train exceed its 7-day
baseline at beta >= 2; the excess subtracts the station's own significant rate at 500 matched pseudo-trigger times.
Left: mean excess by quintile of strain estimated from magnitude and distance, with two-way (trigger, station)
bootstrap 95% intervals. Right: per trigger, observed significant pairs against the expected number of false
positives.""".split()) + "\n")


def f2():
    pr = pd.read_parquet(T / "pairs_primary.parquet")
    pr = pr[pr.in_population]
    s = pr.groupby("tid").agg(n=("sig", "size"), obs=("sig", "mean"), p0=("p0", "first"))
    s = s[s.n >= 20]
    st = pd.read_parquet(RUN / "data" / "raw" / "stations.parquet", columns=["id", "latitude", "longitude"]).groupby("id").median()
    s = s.join(st)
    s["ex"] = s.obs - s.p0
    fig, ax = plt.subplots(figsize=(6.4, 6.8))
    fig.subplots_adjust(left=0.12, right=0.84, bottom=0.08, top=0.9)
    lim = np.nanpercentile(np.abs(s.ex), 98)
    sc = ax.scatter(s.longitude, s.latitude, c=s.ex, cmap="RdBu_r", vmin=-lim, vmax=lim, s=10, edgecolors="none")
    geo = {"The Geysers": (38.79, -122.76), "Coso": (36.03, -117.80), "Salton Sea": (33.17, -115.60),
           "Long Valley": (37.65, -118.90), "Yellowstone": (44.60, -110.50)}
    for n, (la, lo) in geo.items():
        ax.add_patch(plt.Rectangle((lo - 0.3, la - 0.3), 0.6, 0.6, fill=False, ec=INK, lw=0.9))
        right = lo < -112
        ax.text(lo + 0.4 if right else lo - 0.4, la, n, fontsize=7, color=INK, va="center", ha="left" if right else "right")
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude"); ax.set_aspect(1 / np.cos(np.radians(40)))
    cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02); cb.set_label("observed significant rate - station null rate", color=INK2)
    ax.set_title(f"{len(s):,} stations with at least 20 population pairs", fontsize=8.5, color=INK, loc="left")
    fig.suptitle("Station-level excess after distant M7+ earthquakes", x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F2_station_map.png", dpi=170); plt.close(fig)
    (F / "F2_station_map.txt").write_text(" ".join(f"""Per station (at least 20 population pairs): share of its station x trigger
pairs that are significant, minus its significant rate at matched pseudo-triggers. Boxes: the geothermal and volcanic
areas excluded in the robustness check ({', '.join(geo)}). Colour limits at the 98th percentile of absolute
excess.""".split()) + "\n")


if __name__ == "__main__":
    f1(); f2()
    print("figures written")
