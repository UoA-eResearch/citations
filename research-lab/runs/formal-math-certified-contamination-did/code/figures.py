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
    (F / "leak_rates.txt").write_text("Share of benchmark items with a Lean-certified identical (L0), equivalent (L1) or stronger (L2) statement in each open training corpus, after the informativeness and explosion guards (D3-D3b).")


def pass_rates():
    g = pd.read_csv(T / "statement_changes.csv")
    fig, axes = plt.subplots(1, 4, figsize=(11, 3.2), sharey=True)
    for ax, p in zip(axes, PROV):
        d = g[g.prover == p]
        for leaked, col, lab in ((True, "#b5452c", "leaked"), (False, "#2e5e8c", "clean")):
            x = d[d.leaked == leaked].set_index("version").reindex(["orig", "R1", "R2"])
            ax.plot(range(3), 100 * x.pass32, "o-", color=col, label=lab)
        ax.set_xticks(range(3)); ax.set_xticklabels(["original", "R1", "R2"], fontsize=8)
        ax.set_title(PROV[p], fontsize=9); ax.set_ylim(0, 105)
    axes[0].set_ylabel("items solved (pass@32, %)"); axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(F / "pass_by_version.png", dpi=150)
    (F / "pass_by_version.txt").write_text("pass@32 on the original statement and its two kernel-certified reformulations (R1: renamed and reordered; R2: also equalities flipped), for items leaked in the prover's own training corpora and for clean items. Leaked items are solved more often, but rewording barely changes either group.")


def forest():
    s = pd.read_csv(T / "secondary.csv")
    prim = json.load(open(T / "primary.json"))
    rows = [("Pooled (H1)", prim["DiD"], prim["lower95_one_sided"], prim["upper95_one_sided"])]
    for p in PROV:
        x = s[s.analysis == f"prover {p}"].iloc[0]
        rows.append((PROV[p], x.DiD, x.lower95_one_sided, x.upper95_one_sided))
    fig, ax = plt.subplots(figsize=(7, 2.8))
    for i, (lab, e, lo, hi) in enumerate(rows):
        ax.plot([100 * lo, 100 * hi], [i, i], color="black" if i == 0 else "#555", lw=2 if i == 0 else 1.2)
        ax.plot(100 * e, i, "o", color="black" if i == 0 else "#555")
    ax.axvline(0, color="grey", lw=0.8); ax.axvline(10, color="#b5452c", lw=0.8, ls="--")
    ax.text(10.2, len(rows) - 0.6, "preregistered\n10 pp threshold", fontsize=7, color="#b5452c")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("extra drop in pass@32 on reformulation for leaked items (pp; one-sided 95% bounds)")
    fig.tight_layout(); fig.savefig(F / "did.png", dpi=150)
    (F / "did.txt").write_text("Difference-in-differences: (pass@32 drop from original to certified reformulation on leaked items) minus (the same drop on clean items), pooled over the three preregistered provers and for each prover, with item-cluster bootstrap one-sided 95% bounds. STP is a pre-specified secondary analysis.")


def main():
    F.mkdir(parents=True, exist_ok=True)
    leaks(); pass_rates(); forest()


if __name__ == "__main__":
    main()
