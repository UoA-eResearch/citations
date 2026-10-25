"""Figure (PNG + .txt caption). Written after analyse.py.

  F1  left: share of source-cell test presences with a core-flagged training record in the same 1 km cell, by source
      database (H2); right: per-species DiD (random removal minus provenance removal, AUROC on source cells), overall
      and by source database (H1)
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, ORANGE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#d6532a"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
a = json.load(open(T / "audit.json"))
p = json.load(open(T / "primary.json"))
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1, 1]})
fig.subplots_adjust(left=0.17, right=0.98, bottom=0.13, top=0.86, wspace=0.62)
ax = axes[0]
bys = sorted(a["H2_by_source"].items(), key=lambda kv: kv[1]["share"])
ax.barh([k for k, _ in bys], [100 * v["share"] for _, v in bys], color=BLUE)
for i, (k, v) in enumerate(bys):
    ax.text(100 * v["share"] + 1, i, f"{100 * v['share']:.1f}% (n={v['presences']:,})", va="center", fontsize=7, color=INK2)
ax.axvline(10, color=INK2, lw=0.8, ls="--")
ax.axvline(100 * a["H2"]["share_with_core_record_same_cell"], color=ORANGE, lw=1.2)
ax.set_xlim(0, 125); ax.set_xlabel("% of source-cell test presences with a flagged training record in the same 1 km cell")
ax.set_title(f"H2 audit: {100 * a['H2']['share_with_core_record_same_cell']:.1f}% overall (orange); 10% bar dashed",
             fontsize=8.5, color=INK, loc="left")
ax = axes[1]
rows = [("all source cells", p["H1_source_cells"])] + [(k, v) for k, v in sorted(p["by_source_db"].items())] + \
       [("non-source cells", p["other_cells"])]
y = np.arange(len(rows))[::-1]
for yy, (name, r) in zip(y, rows):
    ax.errorbar(r["did"], yy, xerr=[[r["did"] - r["ci"][0]], [r["ci"][1] - r["did"]]], fmt="o",
                color=ORANGE if name == "all source cells" else BLUE, ms=5, capsize=2)
ax.axvline(0, color=INK2, lw=0.8); ax.axvline(0.02, color=INK2, lw=0.8, ls="--")
ax.set_yticks(y); ax.set_yticklabels([f"{name} ({r['species']})" for name, r in rows], fontsize=7.5)
ax.set_xlabel("AUROC: random removal minus provenance removal")
ax.set_title(f"H1: DiD {p['H1_source_cells']['did']:+.3f} ({p['H1_source_cells']['ci'][0]:+.3f} to "
             f"{p['H1_source_cells']['ci'][1]:+.3f}); 0.02 bar dashed", fontsize=8.5, color=INK, loc="left")
fig.suptitle(f"Provenance leakage in SAGE: H2 {a['H2']['verdict']}, H1 {p['H1_source_cells']['verdict']}", x=0.02,
             ha="left", fontsize=10, color=INK)
fig.savefig(F / "F1_provenance.png", dpi=170)
(F / "F1_provenance.txt").write_text(" ".join(f"""Left: SAGE test cells holding plots from sPlotOpen source databases that have a
core-flagged GBIF republication; share of their range-masked presences whose species has a core-flagged GBIF record
(2026-02-01 snapshot, SAGE's basis-of-record and uncertainty filters) in the same EPSG:6933 1 km cell. Right: SAGE's
Random Forest baseline retrained per species after removing provenance-only training presences (C1) and after five
matched random removals (same species and country, C2-C6); mean per-species AUROC difference (random minus
provenance) on range-masked source test cells, with species-bootstrap 95% intervals; by source database where at
least 50 species qualify, and on non-source test cells as a check.""".split()) + "\n")
print("figure written")
