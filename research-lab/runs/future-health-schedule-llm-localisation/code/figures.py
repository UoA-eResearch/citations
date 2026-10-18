"""Figures for the report (each PNG has a .txt caption).

  F1  accuracy by family, jurisdiction and condition (zero-shot, retrieval), with Wilson 95% intervals; family (a) is
      marked as resting on a key that failed its check (D5)
  F2  the NZ - AU accuracy gap, zero-shot and with retrieval, for family (b) (confirmatory, D5) and families (a)+(b)
      pooled (preregistered form), with chemical-cluster bootstrap intervals
  F3  how often the model affirms a criterion: NZ and AU counterfactuals (absent criteria; NZ also after the screen)
      and true criteria (controls), zero-shot and with retrieval
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
COL = {"NZ": "#2a78d6", "AU": "#eb6834"}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def wilson(k, n, z=1.959964):
    p = k / n; c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def scored():
    it = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "items.jsonl")])
    rn = pd.DataFrame([json.loads(l) for l in open(RUN / "data" / "runs.jsonl")]).drop_duplicates(["id", "condition"], keep="last")
    d = rn.merge(it[["id", "family", "jurisdiction", "answer"]].rename(columns={"answer": "truth"}), on="id")
    d["ok"] = (d.answer == d.truth).astype(float)
    return d


def main():
    p = json.load(open(T / "primary.json"))
    d = scored()
    # F1
    fams = [("a", "(a) listed presentation*"), ("b", "(b) restriction (SA / Authority)"), ("d", "(d) criterion (true + absent)")]
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.3), sharey=True); fig.subplots_adjust(left=0.27, right=0.98, bottom=0.17, top=0.80, wspace=0.08)
    lows = []
    for ax, (cond, lab) in zip(axes, (("zero", "zero-shot"), ("retrieval", "with retrieval"))):
        for i, (f, fl) in enumerate(fams):
            for j, (jur, off) in enumerate((("NZ", 0.15), ("AU", -0.15))):
                x = d[(d.condition == cond) & (d.family == f) & (d.jurisdiction == jur)]
                k, n = x.ok.sum(), len(x); lo, hi = wilson(k, n); lows.append(lo)
                y = len(fams) - 1 - i + off
                ax.plot([lo, hi], [y, y], color=COL[jur], lw=2)
                ax.plot(k / n, y, "o", color=COL[jur], ms=6.5, mec=SURF, mew=1.2, label=jur if i == 0 else None)
                ax.text(hi + 0.015, y, f"{k / n:.0%}", va="center", fontsize=7.5, color=INK2)
        ax.axvline(0.5, color=GRID, lw=1, ls="--"); ax.set_title(lab, fontsize=9, color=INK2, loc="left")
        ax.set_xlabel("accuracy"); ax.grid(axis="x", color=GRID, lw=0.5)
    axes[0].set_yticks(range(len(fams))); axes[0].set_yticklabels([f[1] for f in fams][::-1])
    for ax in axes:
        ax.set_xlim(max(0, min(lows) - 0.05), 1.08)
    axes[1].legend(frameon=False, fontsize=8, loc="lower right", bbox_to_anchor=(1, 1.06), ncol=2)
    fig.suptitle("Accuracy by question family and jurisdiction", x=0.27, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_accuracy.png", dpi=170); plt.close(fig)
    caption("F1_accuracy", """Share of items answered correctly by Nemotron 3 Nano Omni (temperature 0, yes/no), New Zealand
    (blue) and Australia (orange), with Wilson 95% intervals. The dashed line is 50%, the score of a coin flip on a
    balanced family. *Family (a) is descriptive only: its answer key failed the check on negatives (D5).""")
    # F2
    rows = [("(b) alone: confirmatory", p["H1"], p["H2"]), ("(a)+(b) pooled: preregistered", p["H1_pooled_ab"], p["H2_pooled_ab"])]
    fig, ax = plt.subplots(figsize=(7.2, 2.7)); fig.subplots_adjust(left=0.33, right=0.97, bottom=0.2, top=0.8)
    for i, (lab, h1, h2) in enumerate(rows):
        y = len(rows) - 1 - i
        for dy, g, ci, c, nm in ((0.12, h1["gap"], h1["ci"], INK, "zero-shot"), (-0.12, h2["gap_retrieval"], h2["gap_retrieval_ci"], "#1baf7a", "with retrieval")):
            ax.plot(ci, [y + dy] * 2, color=c, lw=2)
            ax.plot(g, y + dy, "o", color=c, ms=6.5, mec=SURF, mew=1.2, label=nm if i == 0 else None)
            ax.text(ci[1] + 0.006, y + dy, f"{g:+.3f}", va="center", fontsize=7.5, color=INK2)
    ax.axvline(0, color=INK2, lw=0.8)
    ends = [v for _, h1, h2 in rows for v in h1["ci"] + h2["gap_retrieval_ci"]]
    ax.set_xlim(min(ends + [0]) - 0.02, max(ends + [0]) + 0.05)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1]); ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("NZ accuracy − AU accuracy (below 0: worse on New Zealand)"); ax.grid(axis="x", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1, 1.22), ncol=2)
    fig.suptitle("The localisation gap (H1, H2)", x=0.33, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_gap.png", dpi=170); plt.close(fig)
    caption("F2_gap", """New Zealand minus Australian accuracy, zero-shot (black) and with the top three passages retrieved
    from the jurisdiction's own document (green). Intervals: chemical-cluster bootstrap, 2,000 resamples. The family (b)
    row carries the verdict (D5); the pooled row is the preregistered form, flagged because family (a)'s key failed.""")
    # F3
    cf = d[(d.family == "d")]
    scr = pd.read_csv(T / "nz_counterfactual_screen.csv"); keep = set(scr[scr.screen == "distinct"].id)
    groups = [("NZ absent criteria, all 100", (cf.jurisdiction == "NZ") & (cf.truth == "no"), "NZ"),
              ("NZ absent criteria, screened (83)", (cf.jurisdiction == "NZ") & (cf.truth == "no") & cf.id.isin(keep), "NZ"),
              ("AU absent criteria (unscreened)", (cf.jurisdiction == "AU") & (cf.truth == "no"), "AU"),
              ("NZ true criteria", (cf.jurisdiction == "NZ") & (cf.truth == "yes"), "NZ"),
              ("AU true criteria", (cf.jurisdiction == "AU") & (cf.truth == "yes"), "AU")]
    fig, ax = plt.subplots(figsize=(7.4, 3.4)); fig.subplots_adjust(left=0.33, right=0.97, bottom=0.16, top=0.80)
    for i, (lab, m, jur) in enumerate(groups):
        for dy, cond, mk in ((0.13, "zero", "o"), (-0.13, "retrieval", "s")):
            x = cf[m & (cf.condition == cond)]; k, n = int((x.answer == "yes").sum()), len(x); lo, hi = wilson(k, n)
            y = len(groups) - 1 - i + dy
            ax.plot([lo, hi], [y, y], color=COL[jur], lw=2, alpha=1 if cond == "zero" else 0.55)
            ax.plot(k / n, y, mk, color=COL[jur], ms=6, mec=SURF, mew=1.2, alpha=1 if cond == "zero" else 0.55,
                    label=("zero-shot" if cond == "zero" else "with retrieval") if i == 0 else None)
            ax.text(hi + 0.012, y, f"{k / n:.0%}", va="center", fontsize=7.5, color=INK2)
    ax.axvline(0.2, color="#8a5cd1", lw=1.1, ls="--"); ax.text(0.2, len(groups) - 0.35, "H3 bar 20%", color="#8a5cd1", fontsize=8)
    ax.set_yticks(range(len(groups))); ax.set_yticklabels([g[0] for g in groups][::-1]); ax.set_xlim(0, 1.08)
    ax.set_xlabel("share answered \"yes, this is one of the criteria\""); ax.grid(axis="x", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=8, loc="lower right", bbox_to_anchor=(1, 1.04), ncol=2)
    fig.suptitle("Does the model affirm criteria that are not there?", x=0.33, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F3_fabrication.png", dpi=170); plt.close(fig)
    caption("F3_fabrication", """Share of criterion items the model affirms. Absent criteria are sentences taken from another
    chemical's restriction in the same therapeutic group; affirming one is a fabrication. The screened NZ row drops 17
    items that overlap the chemical's own criteria (D5). True criteria are controls: affirming them is correct. Circles:
    zero-shot; squares: with retrieval. Wilson 95% intervals.""")
    print("figures written")


if __name__ == "__main__":
    main()
