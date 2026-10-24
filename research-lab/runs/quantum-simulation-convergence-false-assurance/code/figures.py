"""Figure (PNG + .txt caption). Written after analyse.py.

  F1  per method: ladder spread of the two finest settings vs true error (log-log), false-assurance corner shaded;
      right: false-assurance share by family with bootstrap 95% intervals
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
INK, INK2, GRID, SURF, SHADE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#f6e1d8"
FAM = {"F": ("#d6532a", "Floquet mixed-field Ising"), "K": ("#2f6db5", "kicked Ising")}
NAME = {"bp": "BP-PEPS (χ 8 vs 16)", "pp": "Pauli propagation (ε 3e-4 vs 1e-4)"}
FLOOR = 1e-7
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
p = json.load(open(T / "primary.json"))
d = pd.read_csv(T / "instances.csv")
fig, axes = plt.subplots(1, 3, figsize=(11, 3.9), gridspec_kw={"width_ratios": [1, 1, 0.8]})
fig.subplots_adjust(left=0.06, right=0.98, bottom=0.16, top=0.8, wspace=0.32)
for ax, m in zip(axes[:2], ("bp", "pp")):
    g = d[d["method"] == m]
    ax.add_patch(plt.Rectangle((FLOOR / 2, 0.03), 0.01 - FLOOR / 2, 10, color=SHADE, zorder=0, lw=0))
    for fam, (c, lab) in FAM.items():
        h = g[g["family"] == fam]
        ax.scatter(h["spread"].clip(lower=FLOOR), h["err"].clip(lower=FLOOR), s=12, color=c, alpha=0.75, lw=0.4,
                   edgecolor=SURF, label=lab)
    ax.axvline(0.01, color=INK2, lw=0.8, ls="--"); ax.axhline(0.03, color=INK2, lw=0.8, ls="--")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(FLOOR / 2, 2); ax.set_ylim(FLOOR / 2, 2)
    s = p["methods"][m]
    ax.set_title(f"{NAME[m]}\nfalse assurance {s['n_fa']}/{s['n_conv']} = {s['share']:.0%} "
                 f"({s['ci'][0]:.0%}–{s['ci'][1]:.0%})", fontsize=8.5, color=INK, loc="left")
    ax.set_xlabel("spread of the two finest settings"); ax.set_ylabel("true error of the finest setting")
    ax.text(FLOOR, 0.6, "apparently converged\nbut wrong", fontsize=7, color=INK2, va="top")

ax = axes[2]
x = np.arange(2)
for j, fam in enumerate(("F", "K")):
    vals, lo, hi = [], [], []
    for m in ("bp", "pp"):
        s = p["methods"][m]["by_family"][fam]
        v = s["share"] if s["share"] is not None else np.nan
        vals.append(v); lo.append(v - (s["ci"][0] or 0) if s["share"] is not None else 0)
        hi.append((s["ci"][1] or 0) - v if s["share"] is not None else 0)
    ax.bar(x + (j - 0.5) * 0.36, np.nan_to_num(vals) * 100, width=0.34, color=FAM[fam][0], label=FAM[fam][1])
    ax.errorbar(x + (j - 0.5) * 0.36, np.nan_to_num(vals) * 100, yerr=[np.array(lo) * 100, np.array(hi) * 100],
                fmt="none", ecolor=INK2, lw=0.8, capsize=2)
ax.axhline(10, color=INK2, lw=0.8, ls="--"); ax.text(1.45, 10.5, "10% bar", fontsize=7, color=INK2, ha="right")
ax.set_xticks(x); ax.set_xticklabels(["BP-PEPS", "Pauli prop."]); ax.set_ylabel("false-assurance share (%)")
ax.set_title("by circuit family", fontsize=8.5, color=INK, loc="left"); ax.grid(axis="y", color=GRID, lw=0.5)
ax.legend(frameon=False, fontsize=7, loc="upper left"); ax.set_ylim(0, 110)
fig.suptitle(f"How often does agreement between the two finest truncation settings hide a large error? (H1 {p['H1']})",
             x=0.02, ha="left", fontsize=10, color=INK)
fig.savefig(F / "F1_false_assurance.png", dpi=170)
(F / "F1_false_assurance.txt").write_text(" ".join(f"""300 heavy-hex patch instances (20-26 qubits) with exact
magnetization from statevector simulation. Each point is one instance: the gap between the two finest truncation
settings (x) against the finest setting's true error (y); values below 1e-7 are drawn at 1e-7. The shaded corner holds
apparently converged estimates (gap at most 0.01) whose error exceeds 0.03. Right: share of apparently converged
instances that are wrong by more than 0.03, by family, with instance-bootstrap 95% intervals.""".split()) + "\n")
print("figure written")
