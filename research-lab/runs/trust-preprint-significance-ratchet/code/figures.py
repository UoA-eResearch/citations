"""Figures for the report. Each PNG gets a .txt caption beside it.

  F1  blind alignment precision by stratum: automated crossings are mostly artefacts (0.12 with the preregistered
      aligner, 0.66 with the strict exploratory rule), while aligned non-crossings are mostly right
  F2  share of significance crossings that go up (non-significant in the preprint, significant when published), from
      the preregistered primary through to the verified crossings, against 0.5 (no ratchet) and 0.67 (a 2:1 ratchet)

Palette: the dataviz skill's reference blue ramp; filled marks for verified estimates, hollow for automated ones.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis_v2 import clopper  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
BLUE, LIGHT, ORANGE = "#123d72", "#5f99df", "#eb6834"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1():
    v1, v2 = pd.read_csv(T / "alignment_validation.csv"), pd.read_csv(T / "alignment_validation_v2.csv")
    rows = [("Preregistered aligner: crossings", v1[v1.stratum == "crossing"], True),
            ("Preregistered aligner: other aligned pairs", v1[v1.stratum == "other"], False),
            ("Strict rule (exploratory): crossings, all 64", v2[v2.stratum == "crossing"], True),
            ("Strict rule (exploratory): non-crossings", v2[v2.stratum == "other"], False)]
    fig, ax = plt.subplots(figsize=(8.4, 2.9))
    fig.subplots_adjust(left=0.44, right=0.97, bottom=0.2, top=0.9)
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    for k, (lab, g, cross) in enumerate(rows):
        y = len(rows) - 1 - k
        n, c = len(g), int(g.correct.sum())
        lo, hi = clopper(c, n)
        ax.plot([lo, hi], [y, y], color=BLUE if cross else LIGHT, lw=2, solid_capstyle="round")
        ax.scatter([c / n], [y], s=42, color=BLUE if cross else LIGHT, zorder=3, edgecolor=SURF, lw=1.5)
    ax.axvline(0.90, color=ORANGE, lw=1, ls="--")
    ax.text(0.895, len(rows) - 0.45, "preregistered\nthreshold 0.90", color=INK2, fontsize=7.5, ha="right", va="top")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{r[0]} ({int(r[1].correct.sum())}/{len(r[1])})" for r in rows][::-1])
    ax.set_xlim(0, 1.05); ax.set_ylim(-0.6, len(rows) - 0.3)
    ax.set_xlabel("share judged the same statistic in both versions (exact 95% interval)")
    fig.savefig(F / "F1_alignment_precision.png", dpi=200); plt.close(fig)
    caption("F1_alignment_precision", """Blind adjudication of aligned statistic pairs, with version order and stratum
    hidden. With the preregistered aligner, 12 of 100 sampled significance crossings were the same statistic in both
    versions, far below the 0.90 the plan required, so the primary test fell back to exact tuple matches. The strict
    exploratory rule (abstract and results text only, near-identical sentences, same position) reached 42 of all 64
    crossings in the version-1 population. Aligned pairs that do not cross are mostly right in both cases.""")


def f2():
    p = json.load(open(T / "primary.json")); e = json.load(open(T / "exploratory_v2.json"))
    s = json.load(open(T / "supplementary.json"))["verified"]
    ex = p["exact_tuples_only"]; k = round(ex["share_up"] * ex["n_crossings"])
    rows = [("Preregistered primary: exact tuple matches", ex["share_up"], clopper(k, ex["n_crossings"]), ex["n_crossings"], False),
            ("All automated crossings (precision 0.12)", p["primary_all_crossings"]["share_up"], p["primary_all_crossings"]["ci"],
             p["primary_all_crossings"]["n_crossings"], False),
            ("Strict automated crossings (precision 0.66)", e["strict_v1"]["share_up"], e["strict_v1"]["ci_read"], e["strict_v1"]["n"], False),
            ("Verified strict crossings (census)", s["v2_census"]["share_up"], s["v2_census"]["exact_ci"], s["v2_census"]["n"], True),
            ("All verified crossings (both samples)", s["combined"]["share_up"], s["combined"]["exact_ci"], s["combined"]["n"], True)]
    fig, ax = plt.subplots(figsize=(8.4, 3.2))
    fig.subplots_adjust(left=0.44, right=0.97, bottom=0.18, top=0.9)
    ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    for x, lab in ((0.5, "no ratchet"), (0.67, "2:1 ratchet")):
        ax.axvline(x, color=ORANGE if x > 0.6 else INK2, lw=1, ls="--")
        ax.text(x + 0.008, len(rows) - 0.35, lab, color=INK2, fontsize=7.5, va="top")
    for i, (lab, est, ci, n, ver) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot(ci, [y, y], color=BLUE, lw=2, solid_capstyle="round")
        ax.scatter([est], [y], s=42, zorder=3, color=BLUE if ver else SURF, edgecolor=BLUE, lw=1.5)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{r[0]} (n = {r[3]:,})" for r in rows][::-1])
    ax.set_xlim(0, 1.0); ax.set_ylim(-0.6, len(rows) - 0.2)
    ax.set_xlabel("share of crossings that go up, preprint → published (95% interval)")
    fig.savefig(F / "F2_share_up.png", dpi=200); plt.close(fig)
    caption("F2_share_up", """Share of statistics that move from non-significant in the preprint to significant in the
    published version, among those whose significance changes. Hollow marks are automated estimates; filled marks are
    crossings a blind adjudication confirmed. The preregistered primary rests on 4 crossings (exact interval). The
    automated estimates sit near one half but are made mostly of artefacts. The 42 verified strict crossings and the
    52 verified crossings overall lean up (0.57 and 0.60) with intervals that include both one half and a 2:1
    ratchet.""")


if __name__ == "__main__":
    f1(); f2()
    print(sorted(p.name for p in F.iterdir()))
