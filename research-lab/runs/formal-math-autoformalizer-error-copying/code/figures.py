"""Figures and key-result tiles: (1) the rate ratios (primary, by model, O vs P, sensitivities) against the decision
thresholds; (2) how outputs are classified, by model and condition; (3) per-item defect copies on originals against
analogous defects on twins. Writes results/figures/*.png with .txt captions and results/tables/tiles.json."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
T, F = RUN / "results" / "tables", RUN / "results" / "figures"
NAMES = {"kimina": "Kimina-Autoformalizer-7B", "goedel": "Goedel-Formalizer-V2-8B", "herald": "Herald_translator",
         "dsp_v2": "DeepSeek-Prover-V2-7B (secondary)", "qwen": "Qwen2.5-7B-Instruct (secondary)"}
COND = {"O": "original", "T": "twin", "P": "paraphrase"}
CLS = [("copy", "defect copy (≡ reference D)", "#c2412d"), ("correct", "correct (≡ corrected C)", "#2e6f9e"),
       ("other", "elaborates, equivalent to neither", "#b9b6ab"), ("noelab", "no statement or does not elaborate", "#e9e6dc")]


def forest(p, s):
    rows = [("Primary: 3 autoformalizers, O vs T", p, True)]
    rows += [(f"{NAMES[m]}, O vs T", s["by_model"][m], False) for m in NAMES if m in s["by_model"]]
    rows += [("Original vs paraphrase (3 primary)", s["O_vs_P"], False)]
    rows += [(f"{k}, O vs T", v, False) for k, v in s["by_source"].items()]
    rows += [("One-rater set added, O vs T", s["one_rater_set"], False)]
    if s.get("truth_certified_twins"):
        rows += [("Truth-certified twins only, O vs T", s["truth_certified_twins"], False)]
    fig, ax = plt.subplots(figsize=(8.2, 0.42 * len(rows) + 1.2))
    for i, (lab, r, prim) in enumerate(rows):
        col = "black" if prim else "#555555"
        ax.plot([r["lower95"], r["upper95"]], [i, i], color=col, lw=2.2 if prim else 1.3)
        ax.plot(r["RR"], i, "D" if prim else "o", color=col, ms=7 if prim else 5)
        ax.text(1.02, i, f"{r['x_O']} vs {r['x_T']}", transform=ax.get_yaxis_transform(), va="center", fontsize=7.5,
                color="#555555")
    for x, ls, lab in ((1, "-", "1 (no excess)"), (1.5, ":", "1.5"), (3, "--", "3 (H threshold)")):
        ax.axvline(x, color="#c2412d" if x == 3 else "grey", lw=0.9, ls=ls)
    ax.set_xscale("log")
    lo = min(0.2, min(r["lower95"] for _, r, _ in rows) * 0.8)
    hi = max(10, max(r["upper95"] for _, r, _ in rows) * 1.25)
    ax.set_xlim(lo, hi)
    ticks = [t for t in (0.1, 0.2, 0.5, 1, 1.5, 2, 3, 5, 10, 20, 50, 100) if lo <= t <= hi]
    ax.set_xticks(ticks); ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("rate ratio: defect copies on the first text / analogous defects on the second (95% item-cluster bootstrap)")
    ax.text(1.02, -0.9, "copies\nO vs T (P)", transform=ax.get_yaxis_transform(), fontsize=7, color="#555555", va="bottom")
    fig.tight_layout(); fig.savefig(F / "rate_ratios.png", dpi=150); plt.close(fig)
    (F / "rate_ratios.txt").write_text(
        "Rate ratio of defect copies (outputs certified equivalent to the defective reference) on the original informal "
        "statement against analogous defects on its number-perturbed twin (or, for the paraphrase row, against defect "
        "copies on a meaning-preserving paraphrase), with 95% item-cluster bootstrap intervals (2,000 draws). The "
        "primary estimate (diamond) pools the three dedicated autoformalizers' temperature samples on the included items "
        "with a valid twin. H is Supported if RR ≥ 3 with a lower bound above 1.5, and Refuted if the upper bound is "
        "below 3. The numbers at the right are the defect counts in the two conditions; 0.5 is added to each count.")


def classes():
    c = pd.read_csv(T / "classes_by_model_condition.csv").set_index(["model", "cond"])
    c = c.reindex(columns=[k for k, _, _ in CLS], fill_value=0)
    models = [m for m in NAMES if m in c.index.get_level_values(0)]
    fig, axes = plt.subplots(1, len(models), figsize=(2.1 * len(models) + 1.2, 3.6), sharey=True)
    for ax, m in zip(np.atleast_1d(axes), models):
        d = c.loc[m].reindex([k for k in COND if k in c.loc[m].index])
        share = d.div(d.sum(1), axis=0) * 100
        bottom = np.zeros(len(share))
        for k, lab, col in CLS:
            ax.bar(range(len(share)), share[k], bottom=bottom, color=col, label=lab, width=0.7, edgecolor="white", lw=0.5)
            bottom += share[k].to_numpy()
        ax.set_xticks(range(len(share))); ax.set_xticklabels([COND[x] for x in share.index], fontsize=8)
        ax.set_title(NAMES[m].replace(" (secondary)", "\n(secondary)"), fontsize=8)
        ax.set_ylim(0, 100)
    np.atleast_1d(axes)[0].set_ylabel("temperature samples (%)")
    h, l = np.atleast_1d(axes)[0].get_legend_handles_labels()
    fig.legend(h[::-1], l[::-1], loc="lower center", ncol=4, frameon=False, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.09, 1, 1)); fig.savefig(F / "classes.png", dpi=150); plt.close(fig)
    (F / "classes.txt").write_text(
        "How each model's temperature samples are classified in Lean, by condition: certified equivalent to the "
        "condition's defective reference (D for originals and paraphrases, D′ for twins), to its corrected reference (C or "
        "C′), elaborating but equivalent to neither, or no statement / does not elaborate. Items: the included items "
        "with a valid twin (originals and twins) and those with an accepted paraphrase.")


def items(p):
    d = pd.read_csv(T / "primary_by_item.csv")
    n = 3 * 16
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    rng = np.random.default_rng(1)
    jx, jy = rng.uniform(-0.25, 0.25, len(d)), rng.uniform(-0.25, 0.25, len(d))
    src = d.item.str.split("/").str[0]
    for s, col, lab in (("minif2f", "#2e6f9e", "miniF2F"), ("proofnet", "#c2412d", "ProofNet")):
        k = src == s
        ax.scatter(d.analog_T[k] + jx[k], d.copies_O[k] + jy[k], s=22, color=col, alpha=0.75, label=lab, edgecolor="none")
    m = max(d.copies_O.max(), d.analog_T.max(), 1) + 2
    ax.plot([0, m], [0, m], color="grey", lw=0.8)
    ax.plot([0, m / 3], [0, m], color="#c2412d", lw=0.8, ls="--")
    ax.set_xlim(-1, m); ax.set_ylim(-1, m)
    ax.set_xlabel(f"analogous defects on the twin (of {n})"); ax.set_ylabel(f"defect copies on the original (of {n})")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(F / "per_item.png", dpi=150); plt.close(fig)
    (F / "per_item.txt").write_text(
        f"Each point is one of the {len(d)} included items with a valid twin: defect copies among the three primary "
        "models' 48 temperature samples on the original informal statement against analogous defects among the 48 on "
        "its twin (jittered). The grey line is equality; the dashed red line a ratio of 3.")


def tiles(p, s):
    f = lambda v: f"{v:.2f}" if v < 10 else f"{v:.1f}"  # noqa: E731
    out = [["Verdict (preregistered rule)", p["verdict"].split(" (")[0], f"RR ≥ 3 with lower bound > 1.5 needed"],
           ["Rate ratio, original vs twin", f(p["RR"]), f"95% CI {f(p['lower95'])}–{f(p['upper95'])}"],
           ["Defect copies, originals", f"{p['x_O']} / {p['n_O']:,}", f"{100 * p['rate_O']:.1f}% of samples"],
           ["Analogous defects, twins", f"{p['x_T']} / {p['n_T']:,}", f"{100 * p['rate_T']:.1f}% of samples; {p['items']} items"]]
    json.dump(out, open(T / "tiles.json", "w"), ensure_ascii=False, indent=1)


def main():
    F.mkdir(parents=True, exist_ok=True)
    p = json.load(open(T / "primary.json"))
    s = json.load(open(T / "secondary.json"))
    forest(p, s); classes(); items(p); tiles(p, s)


if __name__ == "__main__":
    main()
