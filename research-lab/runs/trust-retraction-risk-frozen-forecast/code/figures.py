"""Figures for the report (each PNG has a .txt caption). Written after the results.

  F1  enrichment in the top 1% (E@1%) with publisher-clustered 95% intervals: every frozen model, and the primary
      model refitted without each of the three publishers with the most test-period retractions
  F2  bias audit: share of the cohort, of test-period retractions and of each model's top 1%, by first-author country
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
BLUE, ORANGE, GREY = "#2a78d6", "#e8a317", "#8a8984"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})
PUB = {"4310319869": "Hindawi", "4310320990": "Elsevier", "4310319900": "Springer"}


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1():
    r = json.loads((T / "h1_h2.json").read_text())
    rows = [("full model (H1)", r["models"]["hgb_full.pkl"]["E@0.01"], BLUE),
            ("without venue block (H2)", r["models"]["hgb_no_A.pkl"]["E@0.01"], ORANGE),
            ("venue block only", r["models"]["hgb_A_only.pkl"]["E@0.01"], GREY),
            ("author block only", r["models"]["hgb_B_only.pkl"]["E@0.01"], GREY),
            ("reference block only", r["models"]["hgb_C_only.pkl"]["E@0.01"], GREY),
            ("logistic regression", r["models"]["lr_full.pkl"]["E@0.01"], GREY)]
    rows += [(f"full model without {PUB.get(h, h)}", {"enrichment": v["E@0.01"], "ci": v["ci"]}, BLUE)
             for h, v in r["lopo"].items()]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    fig.subplots_adjust(left=0.3, right=0.97, bottom=0.14, top=0.88)
    for i, (lab, v, col) in enumerate(rows):
        ax.plot(v["ci"], [i, i], color=col, lw=1.6)
        ax.plot(v["enrichment"], i, "o", color=col, ms=5)
    ax.axvline(5, color=INK2, lw=0.8, ls="--"); ax.text(5.1, -0.7, "H1 bar: 5x", fontsize=7.5, color=INK2)
    ax.axvline(3, color=INK2, lw=0.8, ls=":"); ax.text(3.1, -0.7, "H2 bar: 3x", fontsize=7.5, color=INK2)
    ax.axvline(1, color=GRID, lw=0.8)
    ax.set_yticks(range(len(rows)), [x[0] for x in rows]); ax.set_ylim(len(rows) - 0.5, -1.1)
    ax.set_xscale("log"); ax.set_xticks([1, 2, 3, 5, 10, 20], ["1", "2", "3", "5", "10", "20"])
    ax.set_xlabel("enrichment of retractions in the top 1% of risk scores (x base rate, log scale)")
    ax.grid(axis="x", color=GRID, lw=0.5)
    fig.suptitle("Retraction risk, 2021-22 biomedical articles: enrichment in the top 1%", x=0.02, ha="left", fontsize=10,
                 color=INK)
    fig.savefig(F / "F1_enrichment.png", dpi=170)
    plt.close(fig)
    caption("F1_enrichment", f"""Models fitted only on 2015-2019 articles with retractions known by the end of 2020,
    applied to {r['test_articles']:,} biomedical articles from 2021-2022 ({r['test_retracted']:,} retracted by
    2026-10-21; base rate {100 * r['base_rate']:.2f}%). Dots: share of retracted articles among the top 1% of scores
    divided by the base rate; lines: 95% intervals from a publisher-clustered bootstrap. The last three rows refit
    the full model without the publisher with the most test-period retractions (Hindawi, 57% of them) and the next
    two.""")


def f2():
    a = json.loads((T / "posthoc_complete_metadata.json").read_text())["country_audit_with_retraction_shares"]
    full, noa = a["hgb_full.pkl"], a["hgb_no_A.pkl"]
    cs = [c for c in full if c][:8]
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    fig.subplots_adjust(left=0.1, right=0.98, bottom=0.14, top=0.86)
    w = 0.2
    for j, (lab, vals, col) in enumerate([("share of cohort", [full[c]["cohort_share"] for c in cs], GREY),
                                          ("share of test retractions", [full[c]["retraction_share"] for c in cs], INK2),
                                          ("share of top 1%, full model", [full[c]["top1_share"] for c in cs], BLUE),
                                          ("share of top 1%, authors + references", [noa[c]["top1_share"] for c in cs],
                                           ORANGE)]):
        ax.bar([i + (j - 1.5) * w for i in range(len(cs))], [100 * v for v in vals], width=w, color=col, label=lab)
    ax.set_xticks(range(len(cs)), cs)
    ax.set_ylabel("%"); ax.grid(axis="y", color=GRID, lw=0.5)
    ax.legend(frameon=False, fontsize=7.5)
    fig.suptitle("Who the risk scores point at: first-author country", x=0.02, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F2_country_audit.png", dpi=170)
    plt.close(fig)
    caption("F2_country_audit", """Aggregate bias audit on the 2021-2022 test cohort, by the first author's country
    (the eight largest with a known country). Country is not a model feature. Articles with a China-based first author
    are 12% of the cohort, 67% of retractions detected by October 2026, and about half of each model's top 1%.""")


if __name__ == "__main__":
    f1(); f2(); print("figures written")
