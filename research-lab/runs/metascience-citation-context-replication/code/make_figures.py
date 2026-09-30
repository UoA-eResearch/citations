#!/usr/bin/env python
"""Figures for the report (results/figures/F*.png, each with a caption file)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import PROC, TAB, outcomes  # noqa: E402
from explore_keywords import K1  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
FIG = RUN / "results" / "figures"
BLUE, ORANGE, AQUA, INK, MUTED, GRID, NAVY, RED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#898781", "#e1e0d9", "#104281", "#c0392b"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.labelcolor": INK, "axes.titlesize": 9.5, "legend.frameon": False,
                     "savefig.dpi": 160, "savefig.bbox": "tight", "figure.constrained_layout.use": True})


def caption(name, text):
    (FIG / f"{name}.txt").write_text(" ".join(text.split()) + "\n")


def f1_validation():
    m = pd.read_csv(TAB / "validation_metrics.csv").set_index("classifier")
    k = pd.read_csv(TAB / "keywords_validation.csv").set_index("detector")
    rows = [("C1: SciBERT trained on CC30k", m.loc["c1", "precision"], m.loc["c1", "recall"]),
            ("C2: local LLM, zero-shot", m.loc["c2", "precision"], m.loc["c2", "recall"]),
            ("K1: replication-failure keywords (exploratory)", k.loc["k1", "precision"], k.loc["k1", "recall"]),
            ("K2: broader doubt keywords (exploratory)", k.loc["k2", "precision"], k.loc["k2", "recall"])]
    fig, ax = plt.subplots(figsize=(8, 3))
    y = np.arange(len(rows))[::-1]
    ax.barh(y + 0.18, [r[1] for r in rows], 0.34, color=NAVY, label="precision")
    ax.barh(y - 0.18, [r[2] for r in rows], 0.34, color=ORANGE, label="recall")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.set_xlim(0, 1.05)
    ax.axvline(0.5, color=MUTED, lw=0.8, ls=":")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_xlabel("against 300 citation contexts labelled blind (9 express doubt about the cited findings)")
    fig.savefig(FIG / "F1_validation.png")
    plt.close(fig)
    caption("F1_validation", """F1. How well each detector finds citation contexts that express doubt about the cited
findings, judged against 300 contexts labelled blind by the analyst (150 that a classifier flagged, 150 others). The
CC30k-trained SciBERT flags almost every contrastive sentence (recall 1.0, precision 0.06); the LLM finds a third of the
true cases. Only 9 of the 300 contexts, about 3% of all contexts, express such doubt. The keyword detectors were
written afterwards (exploratory).""")


def f2_forest():
    rows = []
    for clf, name in (("c1", "C1 SciBERT"), ("c2", "C2 LLM")):
        p = TAB / f"results_{clf}.csv"
        if not p.exists():
            continue
        r = pd.read_csv(p).set_index("analysis")
        for a, lab in (("H1 primary: pre-replication negative share", "before replication"),
                       ("positive control V1: post-replication share, primary originals with >= 5 post citing papers",
                        "after replication (control)")):
            rows.append((f"{name}, {lab}", *r.loc[a, ["est", "lo", "hi"]].values))
    k = pd.read_csv(TAB / "results_keywords.csv")
    for det, name in (("k1", "K1 keywords"), ("k2", "K2 keywords")):
        kk = k[k.detector == det].set_index("analysis")
        rows.append((f"{name}, before replication", *kk.loc["H1 pre-replication share", ["auc", "lo", "hi"]].values))
        rows.append((f"{name}, after replication (control)",
                     *kk.loc["V1 post-replication share, primary originals with >= 5 post citing papers", ["auc", "lo", "hi"]].values))
    d = pd.DataFrame(rows, columns=["label", "est", "lo", "hi"])
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = np.arange(len(d))[::-1]
    for yy, (_, r) in zip(y, d.iterrows()):
        c = ORANGE if "after" in r.label else NAVY
        ax.errorbar(r.est, yy, xerr=[[r.est - r.lo], [r.hi - r.est]], fmt="o", color=c, ms=4, capsize=2)
    ax.axvline(0.5, color=INK, lw=0.8)
    ax.axvline(0.65, color=RED, lw=0.8, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels(d.label, fontsize=8)
    ax.set_xlabel("AUC for predicting replication failure (0.5 = no information)")
    fig.savefig(FIG / "F2_auc.png")
    plt.close(fig)
    caption("F2_auc", """F2. How well the share of negative citing papers predicts whether a finding later failed to
replicate (area under the ROC curve, 95% bootstrap intervals). Blue: citing papers published before the first
replication, for the 1,075 originals with at least 5 such citing papers with context (the hypothesis). Orange: citing
papers published at least a year after it, for the 851 of those originals with at least 5 such papers: the positive
control, which a detector that can see replication language should pass. Replication papers themselves are excluded
throughout. Dashed red: the preregistered AUC of 0.65. C1 and C2 fail the control; the exploratory keyword detectors
pass it.""")



def f3_eventstudy():
    """Original-weighted event study (deviations.md D7): for each original and year relative to its first replication,
    the share of its citing papers (with contexts) that use K1 replication-failure language; replication papers
    listed in FLoRA or FReD are excluded; the curve is the mean over originals with >= 3 such citing papers that year."""
    from analysis import replication_dois
    ctx = pd.read_parquet(PROC / "contexts.parquet", columns=["doi_o", "citing_id", "citing_doi", "year", "text"])
    ctx = ctx[~ctx.citing_doi.isin(replication_dois())]
    ctx["k1"] = ctx.text.str.contains(K1.pattern, flags=re.I, regex=True)
    per = ctx.groupby(["doi_o", "citing_id"]).agg(year=("year", "first"), k1=("k1", "max")).reset_index()
    o = outcomes()
    o = o[o.outcome.isin(["failed", "successful"])]
    per = per.merge(o[["doi_o", "yr1", "outcome"]], on="doi_o")
    per["rel"] = per.year - per.yr1
    per = per[per.rel.between(-10, 10)]
    oy = per.groupby(["doi_o", "outcome", "rel"]).k1.agg(["mean", "size"]).reset_index()
    oy = oy[oy["size"] >= 3]
    g = oy.groupby(["outcome", "rel"])["mean"].agg(["mean", "std", "size"]).reset_index()
    pw = per.groupby(["outcome", "rel"]).k1.mean().rename("paper_weighted").reset_index()
    g = g.merge(pw, on=["outcome", "rel"])
    g.to_csv(TAB / "eventstudy_k1.csv", index=False)
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for oc, col in (("failed", RED), ("successful", NAVY)):
        q = g[g.outcome == oc]
        se = q["std"] / np.sqrt(q["size"])
        ax.fill_between(q.rel, 100 * (q["mean"] - 1.96 * se), 100 * (q["mean"] + 1.96 * se), color=col, alpha=0.15, lw=0)
        ax.plot(q.rel, 100 * q["mean"], "o-", color=col, ms=3, label=f"originals whose first replication {oc}")
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_xlabel("year of the citing paper relative to the first replication")
    ax.set_ylabel("% of an original's citing papers\nusing replication-failure language")
    ax.legend(fontsize=8, loc="upper left")
    fig.savefig(FIG / "F3_eventstudy.png")
    plt.close(fig)
    caption("F3_eventstudy", """F3. Exploratory: the share of an original's citing papers whose citation context uses
explicit replication-failure language (keyword detector K1), by the citing paper's year relative to the original's
first replication, averaged over originals (each original with at least 3 citing papers with context that year counts
equally; replication papers themselves excluded). In the six years before the first recorded replication, findings
that went on to fail already draw such language at a somewhat higher, roughly flat rate (0.24-0.55% of citing papers,
against 0.01-0.26%), probably echoing earlier attempts; from the replication year on the rate is three to four times
higher (1.1-1.8%). Shaded: 95% intervals across originals.""")
    pre = g[g.rel.between(-6, -1)].groupby("outcome")["mean"].agg(["min", "max"]).mul(100).round(2)
    post = g[g.rel.between(0, 5)].groupby("outcome")["mean"].agg(["min", "max"]).mul(100).round(2)
    print("event study, original-weighted % (rel -6..-1):", pre.to_dict("index"), "(rel 0..5):", post.to_dict("index"))


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    for f in (f1_validation, f2_forest, f3_eventstudy):
        f()
    print("figures written")
