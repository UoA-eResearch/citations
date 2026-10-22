"""Figures for the report (each PNG has a .txt caption). Written after verification.

  F1  the screening funnel: citations -> candidates -> complete reporter-volumes -> verified phantoms (log scale)
  F2  opinions in which a court flags a nonexistent citation, by quarter filed (2019-2026)
"""
import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
S, T, F = RUN / "data" / "screen", RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF, BLUE, ORANGE = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb", "#2a78d6", "#e8a317"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def main():
    vol = json.load(open(S / "volumes.json"))
    prep = json.load(open(T / "prepare_summary.json"))
    ver = list(csv.DictReader(open(S / "verified.csv")))
    flag_ops = {(v["opinion_id"]) for v in ver if v["verdict"] == "phantom-flag"}          # D9 vocabulary
    rel_ops = {(v["opinion_id"]) for v in ver if v["verdict"] == "phantom" and v["type"] == "reliance"}
    steps = [("full case citations", vol["full_citations"]), ("phantom candidates", vol["candidates"]),
             ("in complete reporter-volumes", prep["kept"]),
             ("court-flagged phantom opinions", len(flag_ops)), ("judicial reliance (verified sample)", len(rel_ops))]
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    fig.subplots_adjust(left=0.36, right=0.9, bottom=0.18, top=0.84)
    ys = range(len(steps))[::-1]
    for y, (lab, n) in zip(ys, steps):
        ax.barh(y, max(n, 0.9), color=BLUE if n else GRID, height=0.55)
        ax.text(max(n, 1) * 1.15, y, f"{n:,}", va="center", fontsize=8, color=INK)
    ax.set_yticks(list(ys)); ax.set_yticklabels([s[0] for s in steps], fontsize=8)
    ax.set_xscale("log"); ax.set_xlim(0.8, 2e8); ax.set_xlabel("count (log scale)"); ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("From 24 million citations to zero verified judicial reliance", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F1_funnel.png", dpi=170); plt.close(fig)
    caption("F1_funnel", f"""US opinions dated 2019-01-01 to 2026-09-30 in the CourtListener 2026-09-30 snapshot
    ({vol['opinions']:,} documents). Candidates are citations that neither resolve to a matching case nor match any case
    name; only those in reporter-volumes with at least 98% page coverage can be phantoms. Court-flagged opinions were
    verified in full; reliance-type candidates in a seeded sample of 300 opinions (of 3,182), none of which was a
    phantom.""")
    ops = {r["opinion_id"]: r["date"] for r in csv.DictReader(open(S / "opinions.tsv"), delimiter="\t")
           if r["opinion_id"] in flag_ops}
    q = Counter(f"{d[:4]} Q{(int(d[4:6]) - 1) // 3 + 1}" for d in ops.values())
    quarters = [f"{y} Q{k}" for y in range(2019, 2027) for k in range(1, 5)][:31]
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.25, top=0.84)
    ax.bar(range(len(quarters)), [q.get(x, 0) for x in quarters], color=ORANGE, width=0.75)
    ax.set_xticks(range(0, len(quarters), 4)); ax.set_xticklabels([quarters[i][:4] for i in range(0, len(quarters), 4)])
    ax.axvline(15.5, color=INK2, lw=0.8, ls="--"); ax.text(15.7, ax.get_ylim()[1] * 0.9, "screened period from 2023", fontsize=7.5, color=INK2)
    ax.set_ylabel("opinions"); ax.grid(axis="y", color=GRID, lw=0.5)
    fig.suptitle("Opinions in which a court flags a nonexistent citation, by quarter", x=0.02, ha="left", fontsize=10.5, color=INK)
    fig.savefig(F / "F2_flagged_by_quarter.png", dpi=170); plt.close(fig)
    caption("F2_flagged_by_quarter", """Opinions on the flag sheets (context words such as sanction, fictitious,
    non-existent, AI) in complete reporter-volumes, verified in full: those in which the court itself identifies a cited
    case as nonexistent (D9). 43 from 2023 to September 2026, plus 2 in which the court only reports a party's
    assertion (not drawn). None in 2019-2022 among the 116 flag-sheet opinions verified; two placebo-period courts
    flagged litigants' miscited real cases. Counts are limited to citations into complete reporter-volumes, so they
    are a floor; all 43 are already in the AI Hallucination Cases database.""")
    print("figures written")


if __name__ == "__main__":
    main()
