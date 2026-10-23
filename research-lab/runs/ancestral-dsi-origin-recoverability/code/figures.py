"""Figures for the report (each PNG has a .txt caption). Written after the results.

  F1  monthly shares of usable, placeholder and absent country fields, 2019-2026, with the two rule dates
  F2  gold labels by stratum, and the recovery ceiling against each arm (test split; H2's 40% bar)
  F3  post hoc (D7): natural samples only - ceiling, and each arm's recovery and precision at any confidence
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
USABLE, PLACE, ABSENT = "#2a78d6", "#e8a317", "#8a8984"
INAPP, NOTST, CTRY = "#b9b7b0", "#e8a317", "#2a78d6"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF,
                     "axes.spines.top": False, "axes.spines.right": False})


def caption(name, text):
    (F / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1():
    m = pd.read_csv(T / "monthly_class_counts.csv", index_col=0)
    s = m.div(m.sum(axis=1), axis=0)
    x = pd.to_datetime(s.index + "-01")
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    fig.subplots_adjust(left=0.08, right=0.8, bottom=0.12, top=0.86)
    for col, c, lab in (("usable", USABLE, "usable country"), ("placeholder", PLACE, "placeholder"),
                        ("absent", ABSENT, "absent")):
        ax.plot(x, s[col] * 100, color=c, lw=2)
        ax.text(x[-1] + pd.Timedelta(days=25), s[col].iloc[-1] * 100, lab, color=INK2, va="center", fontsize=8)
    for d, lab in (("2023-06-01", "INSDC rule\n1 Jun 2023"), ("2025-01-01", "sequence-side\n1 Jan 2025")):
        ax.axvline(pd.Timestamp(d), color=INK2, lw=0.8, ls="--")
        ax.text(pd.Timestamp(d), 103, lab, ha="center", va="bottom", fontsize=7.5, color=INK2)
    ax.set_ylim(0, 100)
    ax.set_ylabel("share of non-human BioSamples (%)")
    ax.grid(axis="y", color=GRID, lw=0.6)
    fig.suptitle("Country field of new BioSamples by month of submission", x=0.08, ha="left", fontsize=10, color=INK)
    fig.savefig(F / "F1_monthly_shares.png", dpi=170)
    plt.close(fig)
    caption("F1_monthly_shares", """Monthly shares of non-human BioSamples (care filter applied) whose country field
    resolves to an INSDC country (usable), holds a missing-value term (placeholder) or is absent; malformed values are
    under 0.2% and not drawn. Dashed lines mark the INSDC rule (1 June 2023) and its sequence-side extension (1 January
    2025). The month-to-month swings around 2021 reflect SARS-CoV-2 surveillance volumes.""")


def f2():
    p = json.loads((T / "limb2_primary.json").read_text())
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3.5), gridspec_kw={"width_ratios": [1, 1.5]})
    fig.subplots_adjust(left=0.15, right=0.98, bottom=0.3, top=0.88, wspace=0.42)
    strata = [("with_publication", "with a linked\npublication"), ("without_publication", "without")]
    for i, (k, lab) in enumerate(strata):
        c = p["labels_by_stratum"][k]
        n = sum(c.values())
        left = 0
        for key, col in (("inapplicable", INAPP), ("not stated", NOTST), ("country", CTRY)):
            w = 100 * c.get(key, 0) / n
            a.barh(i, w, left=left, color=col, edgecolor=SURF, lw=2, height=0.6)
            if w > 6:
                a.text(left + w / 2, i, f"{w:.0f}%", ha="center", va="center", fontsize=8, color=INK)
            left += w
    a.set_yticks([0, 1], [s[1] for s in strata])
    a.invert_yaxis()
    a.set_xlim(0, 100)
    a.set_xlabel("gold-set records (%)")
    a.set_title("What the 497 untagged records are", fontsize=9, color=INK, loc="left")
    from matplotlib.patches import Patch
    a.legend(handles=[Patch(color=INAPP, label="lab material"), Patch(color=NOTST, label="origin not stated"),
                      Patch(color=CTRY, label="country found")], frameon=False, fontsize=7.5, ncol=1,
             loc="upper left", bbox_to_anchor=(-0.05, -0.2))
    test = p["test"]
    ceil = 100 * p["labels"]["test"]["country"] / test
    arms = ["gazetteer", "classifier", "llm"]
    at = [100 * p["arms"][k]["test"]["recovery"] for k in arms]
    anyc = [100 * p["arms"][k]["test_any_confidence"]["recovery"] for k in arms]
    xs = range(len(arms))
    b.bar([x - 0.18 for x in xs], at, width=0.34, color=USABLE, label="at tuned threshold (90% precision)")
    b.bar([x + 0.18 for x in xs], anyc, width=0.34, color="#9cc3ee", label="any confidence (correct calls)")
    b.axhline(40, color=INK2, lw=0.8, ls="--")
    b.text(2.45, 40.8, "H2 bar: 40%", ha="right", fontsize=7.5, color=INK2)
    b.axhline(ceil, color=PLACE, lw=1.5)
    b.text(2.45, ceil + 0.8, f"ceiling: {ceil:.0f}% have a findable country", ha="right", fontsize=7.5, color=INK2)
    b.set_xticks(list(xs), ["gazetteer", "classifier", "LLM"])
    b.set_ylim(0, 45)
    b.set_ylabel("test records recovered (%)")
    b.legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(0, -0.13))
    b.set_title("Recovery on the 300 test records", fontsize=9, color=INK, loc="left")
    fig.savefig(F / "F2_gold_and_recovery.png", dpi=170)
    plt.close(fig)
    caption("F2_gold_and_recovery", """Left: final gold labels of the 497 scored untagged records, by whether the
    sample's BioProject links a publication. Right: share of the 300 test records for which each arm names the correct
    country, at the confidence threshold tuned for 90% precision (after D10 no arm reaches 90% on the tuning split, so none makes calls) and at any confidence. The orange line is the ceiling set by the records that have a
    findable country at all; the dashed line is H2's 40% bar.""")


def f3():
    q = json.loads((T / "limb2_posthoc_natural.json").read_text())["all"]
    arms = ["gazetteer", "classifier", "llm"]
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    fig.subplots_adjust(left=0.12, right=0.97, bottom=0.17, top=0.82)
    rec = [100 * q["arms_any_confidence"][k]["recovery"] for k in arms]
    pre = [100 * q["arms_any_confidence"][k]["precision"] for k in arms]
    xs = range(len(arms))
    ax.bar([x - 0.18 for x in xs], rec, width=0.34, color=USABLE, label="recovered (% of natural records)")
    ax.bar([x + 0.18 for x in xs], pre, width=0.34, color="#9cc3ee", label="precision of its calls")
    for x, r, p_ in zip(xs, rec, pre):
        ax.text(x - 0.18, r + 1.5, f"{r:.0f}", ha="center", fontsize=7.5, color=INK2)
        ax.text(x + 0.18, p_ + 1.5, f"{p_:.0f}", ha="center", fontsize=7.5, color=INK2)
    ax.axhline(100 * q["ceiling"], color=PLACE, lw=1.5)
    ax.text(2.45, 100 * q["ceiling"] + 2, f"ceiling {100 * q['ceiling']:.0f}%", ha="right", fontsize=7.5, color=INK2)
    ax.axhline(90, color=INK2, lw=0.8, ls="--")
    ax.text(-0.45, 92, "90% precision", fontsize=7.5, color=INK2)
    ax.set_xticks(list(xs), ["gazetteer", "classifier", "LLM"])
    ax.set_ylim(0, 105)
    ax.set_ylabel("%")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(0, 0.84))
    ax.set_title(f"Post hoc: natural samples only (n = {q['natural_records']}, lab material removed)", fontsize=9,
                 color=INK, loc="left")
    fig.savefig(F / "F3_posthoc_natural.png", dpi=170)
    plt.close(fig)
    caption("F3_posthoc_natural", """Post hoc (D7, not preregistered). Among the 147 gold records that are not
    laboratory material, 19% have a findable country after D10 (orange). Bars give each arm's correct calls as a share of those
    records and the precision of its calls, at any confidence, across all 497 gold records' natural subset.""")


if __name__ == "__main__":
    f1(); f2(); f3()
