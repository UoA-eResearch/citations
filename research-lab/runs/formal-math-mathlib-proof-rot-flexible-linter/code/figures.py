"""Figure (PNG + .txt caption). Written after analyse.py.

  F1  left: replay failure rate of flagged vs unflagged proofs for O+6, O+12 and the second pair; right: error classes
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F, W = RUN / "results" / "tables", RUN / "results" / "figures", RUN / "data" / "work"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, RED, GREY = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#d6532a", "#9a9893"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
p = json.load(open(T / "primary.json"))
groups = [("2025-03 → +6 mo", p["decay"]["O+6_gee"]), ("2025-03 → +12 mo\n(primary)", p["primary"]), ("2025-09 → +12 mo", p["secondary_pair"])]
fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), gridspec_kw={"width_ratios": [1.2, 1]})
fig.subplots_adjust(left=0.08, right=0.98, bottom=0.2, top=0.82, wspace=0.3)
ax = axes[0]
x = np.arange(len(groups))
ax.bar(x - 0.18, [g["fail_flagged"] * 100 for _, g in groups], width=0.34, color=RED, label="flagged by the flexible linter")
ax.bar(x + 0.18, [g["fail_unflagged"] * 100 for _, g in groups], width=0.34, color=GREY, label="not flagged")
for i, (_, g) in enumerate(groups):
    ax.annotate(f"OR {g['or']:.2f}\n({g['ci'][0]:.2f}–{g['ci'][1]:.2f})", (i, max(g["fail_flagged"], g["fail_unflagged"]) * 100),
                xytext=(0, 4), textcoords="offset points", ha="center", fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels([g for g, _ in groups], fontsize=8)
ax.set_ylabel("verbatim replay fails (%)"); ax.set_ylim(0, 60); ax.grid(axis="y", color=GRID, lw=0.5)
ax.legend(frameon=False, fontsize=7.5, loc="upper left")
ax = axes[1]
ec = pd.Series(p["error_classes"]).sort_values()
ax.barh(ec.index.str.replace("_", " "), ec.values, color=GREY)
ax.set_xlabel("failing primary-pair proofs, by first error class"); ax.grid(axis="x", color=GRID, lw=0.5)
fig.suptitle("Flagged proofs break more often on replay, but not reliably enough to clear the 1.5× bar", x=0.02, ha="left",
             fontsize=10, color=INK)
fig.savefig(F / "F1_rot.png", dpi=170)
(F / "F1_rot.txt").write_text(" ".join(f"""Mathlib theorem/lemma proofs containing a non-terminal unrestricted simp whose statement text is unchanged
later; each old proof body replayed verbatim into the later snapshot's file and compiled against its prebuilt cache.
Flag: a flexible-linter warning inside the declaration in the old snapshot. Odds ratios from a logistic GEE clustered by
file, adjusted for log tactic count and simp-call count. Right: first matching error class of failing proofs in the
primary pair (2025-03-31 to 2026-03-31).""".split()) + "\n")
print("figure written")
