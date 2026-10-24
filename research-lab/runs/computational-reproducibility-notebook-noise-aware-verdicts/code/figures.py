"""Figure (PNG + .txt caption). Written after compare.py.

  F1  left: selection flow; right: completing notebooks by verdict (exact match / all mismatches intrinsic / other)
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")       # rendering this figure only; notebooks are never executed here
import matplotlib.pyplot as plt  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
p = json.load(open(T / "primary.json"))
flow = [("eligible in dataset", 340), ("sampled (<=2 per repo)", 192), ("repo ready (<=500 MB)", 149),
        ("AS-OF environment built", 71), ("ran to completion x3", p["completed_with_3_reps"]),
        ("exact mismatch", p["exact_mismatch"]), ("all mismatches intrinsic", p["all_intrinsic"])]
fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.0), gridspec_kw={"width_ratios": [1.5, 1]})
fig.subplots_adjust(left=0.27, right=0.97, bottom=0.36, top=0.86, wspace=0.45)
ax = axes[0]
y = range(len(flow))[::-1]
ax.barh(list(y), [v for _, v in flow], color=["#9a9893"] * 5 + ["#d6532a", "#2a78d6"], height=0.6)
ax.set_yticks(list(y)); ax.set_yticklabels([s for s, _ in flow], fontsize=8)
for yy, (_, v) in zip(y, flow):
    ax.annotate(str(v), (v, yy), xytext=(3, 0), textcoords="offset points", va="center", fontsize=8)
ax.set_xlabel("notebooks"); ax.grid(axis="x", color=GRID, lw=0.5)
ax = axes[1]
n = p["completed_with_3_reps"]; em = p["exact_mismatch"]; ai = p["all_intrinsic"]
parts = [("exact match", n - em, "#9a9893"), ("mismatch, all intrinsic", ai, "#2a78d6"), ("mismatch, not all intrinsic", em - ai, "#d6532a")]
left = 0
for lab, v, col in parts:
    ax.barh([0], [v], left=left, color=col, height=0.5, label=f"{lab} ({v})")
    left += v
ax.set_yticks([]); ax.set_xlim(0, n); ax.set_xlabel(f"of {n} completing notebooks")
ax.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.25))
fig.suptitle(f"Run-to-run noise explains all mismatches in {ai} of {em} irreproducible-looking notebooks ({ai/em:.0%})",
             x=0.02, ha="left", fontsize=10, color=INK)
fig.savefig(F / "F1_flow.png", dpi=170)
(F / "F1_flow.txt").write_text(" ".join(f"""Python notebooks from PubMed Central-linked repositories that Samuel and Mietchen's re-execution found
to complete but differ from stored outputs. Environments rebuilt with uv in Docker (AS-OF dependency date), executed
three times without network. A mismatching cell is intrinsic if its output varies across the three runs or the stored
numbers lie within the runs' envelope. H1 share {p['H1_share']:.0%} (Wilson {p['H1_wilson'][0]:.0%}-{p['H1_wilson'][1]:.0%}).""".split()) + "\n")
print("figure written")
