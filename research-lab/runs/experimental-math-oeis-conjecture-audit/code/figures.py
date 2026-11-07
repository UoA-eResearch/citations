"""Figure (PNG + .txt caption). Written after analyse.py.

  F1  the audit funnel: candidate lines -> parsed -> consistent with own data -> screened by LODA -> disagree -> confirmed
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, RED = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#d6532a"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
p = json.load(open(T / "primary.json"))
steps = [("candidate 'conjecture'/'empirical' lines", p["candidate_lines"]),
         ("parsed C/G/D (recurrence, g.f., D-finite)", sum(v for k, v in p["parsed_by_class"].items() if k != "P")),
         ("consistent with own data (>= 5 terms)", p["cgd_data_status"]["consistent"]),
         ("screened against a LODA program", p["screened"]["n"]),
         ("LODA disagrees beyond the data", p["screened"]["k"]),
         ("confirmed by the b-file (all already noted)", p["confirmed_falsifications_all"])]
fig, ax = plt.subplots(figsize=(7.6, 3.4))
fig.subplots_adjust(left=0.38, right=0.95, bottom=0.18, top=0.86)
y = range(len(steps))[::-1]
vals = [v for _, v in steps]
ax.barh(list(y), vals, color=[BLUE] * 4 + [RED, RED], height=0.62)
ax.set_xscale("log")
ax.set_yticks(list(y)); ax.set_yticklabels([s for s, _ in steps], fontsize=8)
for yy, v in zip(y, vals):
    ax.annotate(f"{v:,}", (v, yy), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color=INK)
ax.axvline(100, color=INK2, lw=0.8, ls="--")
ax.annotate("H1 bar: 100", (100, len(steps) - 0.6), xytext=(4, 0), textcoords="offset points", fontsize=7.5, color=INK2)
ax.set_xlabel("count (log scale)"); ax.grid(axis="x", color=GRID, lw=0.5)
fig.suptitle(f"Of {p['screened']['n']:,} screened OEIS conjectures, {p['screened']['k']} disagree with LODA; {p['confirmed_falsifications_all']} lines are confirmed false, all already noted",
             x=0.02, ha="left", fontsize=9.5, color=INK)
fig.savefig(F / "F1_funnel.png", dpi=170)
(F / "F1_funnel.txt").write_text(" ".join(f"""OEIS formula lines marked "conjecture" or "empirical" (and members of "Conjectures
from ...: (Start)...(End)" blocks), parsed into linear recurrences, rational generating functions or P-recursive
relations; those consistent with the entry's own terms were run beyond the data against the entry's LODA program (median
{p['beyond_data_terms_checked']['median']:.0f} further terms) and disagreements checked against the entry's b-file. Revised after review (D2): at least 5 data terms checked; lines tagged [Wrong] excluded; polynomial closed forms excluded.""".split()) + "\n")
print("figure written")
