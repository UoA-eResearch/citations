"""Figures for the report (each PNG has a .txt caption).

  F1  the EU event study (S3): InScope x period coefficients relative to 2024-10, with 95% intervals; the Act applied
      from 2025-06-28
  F2  the difference-in-differences estimates as relative changes: H1 (EU), H2 (placebo), S1 (triple difference),
      S2 (UK), S5 (the lead's literal windows)
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
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def main():
    p = json.load(open(T / "primary.json"))
    ev = p["S3_event_study_eu"]
    per = sorted(list(ev) + ["202410"])
    b = np.array([ev.get(k, {"b": 0.0})["b"] for k in per]); se = np.array([ev.get(k, {"se": 0.0})["se"] for k in per])
    rel, lo, hi = np.expm1(b), np.expm1(b - 1.96 * se), np.expm1(b + 1.96 * se)
    lab = [f"{k[:4]}-{k[4:]}" for k in per]
    phase = {"202501": "#8a5cd1", "202504": "#8a5cd1", "202507": "#eb6834"}
    fig, ax = plt.subplots(figsize=(7.4, 3.4)); fig.subplots_adjust(left=0.12, right=0.97, bottom=0.2, top=0.84)
    for i, k in enumerate(per):
        c = phase.get(k, "#2a78d6" if k > "202507" else "#52514e")
        ax.plot([i, i], [lo[i] * 100, hi[i] * 100], color=c, lw=2)
        ax.plot(i, rel[i] * 100, "o", color=c, ms=6.5, mec=SURF, mew=1.2)
    ax.axhline(0, color=INK2, lw=0.8); ax.axhline(-15, color=GRID, lw=1, ls="--")
    ax.axvline(per.index("202507") - 0.5, color="#eb6834", lw=1, ls=":")
    ax.text(per.index("202507") - 0.45, ax.get_ylim()[1] * 0.9, "Act applies\n28 Jun 2025", fontsize=7.5, color="#eb6834", va="top")
    ax.set_xticks(range(len(per))); ax.set_xticklabels(lab, rotation=30)
    ax.set_ylabel("in-scope vs out-of-scope, % (ref. 2024-10)"); ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Accessibility violations of EU in-scope sites relative to out-of-scope sites", x=0.12, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_event_study.png", dpi=170); plt.close(fig)
    caption("F1_event_study", """Event study (S3): the relative difference in violation density (violation nodes per 1,000 DOM
    elements, frozen 19-rule axe subset) between EU sites offering in-scope consumer services and out-of-scope sites, by
    quarterly snapshot, relative to 2024-10, with site and period fixed effects and site-clustered 95% intervals. Grey:
    pre-period; purple: anticipation quarters; orange: the transition quarter; blue: post-period. Dashed line: the
    preregistered -15% bar.""")
    rows = [("H1: EU, in scope vs out (primary)", p["H1_eu"]), ("H2: placebo (.com.au, .co.nz, .ca)", p["H2_placebo"]),
            ("S1: triple difference, EU vs placebo", p["S1_triple_difference"]), ("S2: UK", p["S2_uk"]),
            ("S5: EU, the lead's literal windows", p["S5_lead_windows"]["eu"])]
    fig, ax = plt.subplots(figsize=(7.4, 3.0)); fig.subplots_adjust(left=0.4, right=0.97, bottom=0.18, top=0.84)
    for i, (l, r) in enumerate(rows):
        y = len(rows) - 1 - i; c = "#2a78d6" if i == 0 else "#52514e"
        ax.plot([r["ci"][0] * 100, r["ci"][1] * 100], [y, y], color=c, lw=2)
        ax.plot(r["rel"] * 100, y, "o", color=c, ms=6.5, mec=SURF, mew=1.2)
        ax.text(r["ci"][1] * 100 + 1.5, y, f"{r['rel'] * 100:+.0f}%", va="center", fontsize=7.8, color=INK2)
    ax.axvline(0, color=INK2, lw=0.8); ax.axvline(-15, color=GRID, lw=1, ls="--")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1]); ax.set_xlim(-55, 60)
    ax.set_xlabel("relative change in violation density after the Act, %"); ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("Difference-in-differences estimates", x=0.4, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_estimates.png", dpi=170); plt.close(fig)
    caption("F2_estimates", """exp(b) - 1 with site-clustered 95% intervals. Post-period: 2025-10, 2026-01, 2026-04; pre-period:
    2024-01 to 2024-10; anticipation and transition quarters excluded. Dashed line: the preregistered -15% bar for H1.""")
    print("figures written")


if __name__ == "__main__":
    main()
