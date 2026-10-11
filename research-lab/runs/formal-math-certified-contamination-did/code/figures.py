"""Figures: (1) certified leak rates by corpus and benchmark; (2) pass@32 by statement version, leaked vs clean items,
for each prover; (3) the reformulation-drop difference-in-differences per prover and pooled (one-sided 95% bounds).
Writes results/figures/*.png with .txt captions."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
NAMES = {"stp": "STP_Lean_0320", "goedel_pset": "Goedel-Pset-v1", "sft_v2": "Goedel SFT v2", "numina_lean": "NuminaMath-LEAN",
         "dsp_v1": "DeepSeek-Prover-V1", "goedel_lwproofs": "Goedel LW proofs", "lean_workbook": "Lean Workbook", "any corpus": "any corpus"}
BENCH = {"bench_minif2f": "miniF2F", "bench_minif2f_v2c": "miniF2F-v2c", "bench_proofnet": "ProofNet#", "bench_putnam": "PutnamBench"}
PROV = {"dsp_v2": "DeepSeek-Prover-V2", "goedel_v2": "Goedel-Prover-V2", "kimina": "Kimina-Distill", "stp": "STP (secondary)"}


def leaks():
    r = pd.read_csv(T / "leak_rates.csv")
    r = r.pivot_table(index="corpus", columns="bench", values="share_any").reindex(list(NAMES)).rename(index=NAMES)[list(BENCH)].rename(columns=BENCH)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    x = np.arange(len(r))
    for k, col in enumerate(r.columns):
        ax.bar(x + (k - 1.5) * 0.2, 100 * r[col], 0.2, label=col)
    ax.set_xticks(x); ax.set_xticklabels(r.index, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("benchmark items with a certified\nequivalent or stronger statement (%)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(F / "leak_rates.png", dpi=150)
    (F / "leak_rates.txt").write_text("Share of benchmark items with a Lean-certified identical (L0), equivalent (L1) or stronger (L2) statement in each open training corpus, after the informativeness and explosion guards (D3-D3b, D9).")


def pass_rates():
    g = pd.read_csv(T / "statement_changes.csv")
    fig, axes = plt.subplots(2, 4, figsize=(11, 5.6), sharey="row")
    for row, (col_, lab_) in enumerate((("pass32", "items solved (pass@32, %)"), ("rate", "samples correct (%)"))):
        for ax, p in zip(axes[row], PROV):
            d = g[g.prover == p]
            for leaked, col, lab in ((True, "#b5452c", "leaked"), (False, "#2e5e8c", "clean")):
                x = d[d.leaked == leaked].set_index("version").reindex(["orig", "R1", "R2"])
                ax.plot(range(3), 100 * x[col_], "o-", color=col, label=lab)
            ax.set_xticks(range(3)); ax.set_xticklabels(["original", "R1", "R2"], fontsize=8)
            if row == 0:
                ax.set_title(PROV[p], fontsize=9)
            ax.set_ylim(0, 105)
        axes[row][0].set_ylabel(lab_)
    axes[0][0].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(F / "pass_by_version.png", dpi=150)
    (F / "pass_by_version.txt").write_text("Top: pass@32 on the original statement and its kernel-certified reformulations (R1: renamed and reordered; R2: also equalities flipped), for items leaked in the prover's own training corpora and for clean items. Bottom: the share of the 32 samples that are correct. For DeepSeek-Prover-V2 and STP, pass@32 on leaked items sits at 100%, so it cannot register a drop; the per-sample rate on those items falls with each reformulation. R1 versions identical to the original are excluded (D9); each version is averaged over the items where it exists (paired differences are in did_by_version.csv).")


def forest():
    s = pd.read_csv(T / "secondary.csv").set_index("analysis")
    prim = json.load(open(T / "primary.json"))
    rows = [("Pooled (H1)", (prim["DiD"], prim["lower95_one_sided"], prim["upper95_one_sided"]),
             tuple(s.loc["per-sample pass rate (pooled)", ["DiD", "lower95_one_sided", "upper95_one_sided"]]))]
    for p in PROV:
        rows.append((PROV[p], tuple(s.loc[f"prover {p}", ["DiD", "lower95_one_sided", "upper95_one_sided"]]),
                     tuple(s.loc[f"per-sample, prover {p}", ["DiD", "lower95_one_sided", "upper95_one_sided"]])))
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    for i, (lab, a, b) in enumerate(rows):
        for off, (e, lo, hi), col, mk, name in ((-0.15, a, "black", "o", "pass@32 (preregistered)"), (0.15, b, "#b5452c", "s", "per-sample solve rate")):
            ax.plot([100 * lo, 100 * hi], [i + off, i + off], color=col, lw=1.6 if i == 0 else 1.1)
            ax.plot(100 * e, i + off, mk, color=col, label=name if i == 0 else None)
    ax.axvline(0, color="grey", lw=0.8); ax.axvline(10, color="#b5452c", lw=0.8, ls="--")
    ax.text(10.3, -0.45, "preregistered\n10 pp threshold", fontsize=7, color="#b5452c", va="top")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("extra drop on reformulation for leaked items (pp; 90% interval)")
    ax.legend(frameon=False, fontsize=7, loc="center right")
    fig.tight_layout(); fig.savefig(F / "did.png", dpi=150)
    (F / "did.txt").write_text("Difference-in-differences: (drop from original to certified reformulation on leaked items) minus (the same drop on clean items), for pass@32 (the preregistered metric, black) and the per-sample solve rate (red), pooled over the three preregistered provers and for each prover. Bars are 90% item-cluster bootstrap intervals; the verdict uses the upper one-sided 95% bound. STP is a pre-specified secondary.")


def main():
    F.mkdir(parents=True, exist_ok=True)
    leaks(); pass_rates(); forest()


if __name__ == "__main__":
    main()
