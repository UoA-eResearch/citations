"""Figures (PNG + .txt caption). Written after analyse.py.

  F1  left: per-species observed centroid velocity and the medians of the two nulls (log scale); right: the H1 ratio
      (null median / observed median) with 95% intervals, overall, by latitude band, by cells per period and for each
      robustness variant, against the preregistered 0.5 bar
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
nu = pd.read_parquet(T / "nulls_primary.parquet")
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.05, 1]})
fig.subplots_adjust(left=0.06, right=0.98, bottom=0.12, top=0.86, wspace=0.55)
ax = axes[0]
bins = np.logspace(-1.5, 2.5, 80)
for col, lab, c in (("v_sph", "observed", ORANGE), ("effort_med", "noise + effort null (median per species)", BLUE),
                    ("noise_med", "noise-only null (median per species)", GREY)):
    ax.hist(nu[col].clip(10 ** -1.5, 10 ** 2.5), bins=bins, histtype="step", lw=1.6, color=c,
            label=f"{lab}: median {nu[col].median():.1f}")
top = ax.get_ylim()[1]
ax.set_ylim(0, top * 1.45)
ax.axvline(5.6, color=INK2, lw=0.8, ls="--", ymax=1 / 1.45 * 1.08)
ax.text(6.2, top * 1.06, "Daru et al. 5.6 km/yr", fontsize=7, color=INK2, va="bottom")
ax.set_xscale("log"); ax.set_xlabel("centroid velocity, km/yr (5-arcmin thinning, 1970-2000 vs 2001-2024)")
ax.set_ylabel("species")
ax.legend(frameon=False, fontsize=7.5, loc="upper left")
ax.set_title(f"{p['H1']['species']:,} species with at least 10 thinned cells per period", fontsize=8.5, color=INK, loc="left")
ax = axes[1]
rows = [("all species (H1)", p["H1"]["ratio_effort"], p["H1"]["ci_effort"])]
rows += [(f"{k} |lat|", v["ratio_effort"], v["ci_effort"]) for k, v in p["by_latitude_band"].items()]
rows += [(f"{k} cells per period", v["ratio_effort"], v["ci_effort"]) for k, v in p["by_cells"].items()]
names = {"threshold_20": ">= 20 cells", "threshold_50": ">= 50 cells", "arithmetic_centroids": "arithmetic centroids",
         "thin30": "30-arcmin thinning", "eff30": "30-arcmin effort grid", "eff2deg": "2-degree effort grid",
         "no_r5": "no dense-point rule"}
rows += [(names[k], v["ratio_effort"], v["ci_effort"]) for k, v in p["robustness"].items()
         if isinstance(v, dict) and k != "threshold_50"]             # the same species as the ">=50 cells" class
y = np.arange(len(rows))[::-1]
for yy, (n, r, ci) in zip(y, rows):
    ax.errorbar(r, yy, xerr=[[r - ci[0]], [ci[1] - r]], fmt="o", ms=5, capsize=2, color=ORANGE if yy == y[0] else BLUE)
ax.axvline(0.5, color=INK2, lw=0.8, ls="--"); ax.axvline(1.0, color=GRID, lw=0.8)
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=7.5)
ax.set_xlim(0.3, 1.05); ax.set_xlabel("null median / observed median velocity")
ax.set_title(f"H1 {p['H1']['verdict']}: ratio {p['H1']['ratio_effort']:.2f} "
             f"({p['H1']['ci_effort'][0]:.2f}-{p['H1']['ci_effort'][1]:.2f}); 0.5 bar dashed", fontsize=8.5, color=INK, loc="left")
fig.suptitle("How much herbarium range velocity do sampling noise and collecting effort reproduce?", x=0.02, ha="left",
             fontsize=10, color=INK)
fig.savefig(F / "F1_velocity_null.png", dpi=170)
(F / "F1_velocity_null.txt").write_text(" ".join("""Left: per-species great-circle displacement of the spherical-mean
centroid of thinned 5-arcmin cells between 1970-2000 and 2001-2024, divided by 28 years, for GBIF Tracheophyta
preserved specimens (2026-07-01 snapshot, cleaned), against each species' median under 999 null replicates that keep
the range fixed: records reassigned between periods at their observed counts (noise only) or by Pareto order sampling
with leave-one-species-out 1-degree effort odds (noise + effort). Right: the ratio of the median null velocity to the
median observed velocity with species-bootstrap 95% intervals.""".split()) + "\n")
print("figure written")
