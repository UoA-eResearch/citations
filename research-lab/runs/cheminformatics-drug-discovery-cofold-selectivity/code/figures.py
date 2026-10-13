"""Figures: (1) the selectivity axis against its baselines, with example ligands; (2) measured and
predicted panels as heatmaps, raw and with each ligand's mean removed; (3) the two-way variance
decomposition and the conventional axis; (4) the decoy-protein arm; (5) the sampling arm and the
training-support gradient. Writes results/figures/*.png with a .txt caption beside each.
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
BLUE, RED, ORANGE, GREEN, PURPLE, GREY = "#2e6f9e", "#c2412d", "#d9822b", "#7a9e3b", "#8d6cab", "#555555"
BASE_LABELS = [("B1_promiscuity", "promiscuity\n(no chemistry)", ORANGE),
               ("B2_neighbour", "neighbour\n(uses labels)", GREEN),
               ("B0_ligand_only", "ligand-only\n(zero)", GREY)]


def short_name(name, cid, limit=22):
    """Drug names make the example panels readable; the systematic names in the Davis release do not, so
    those fall back to the CID."""
    return name if len(str(name)) <= limit else f"CID {cid}"


def caption(name, text):
    (F / f"{name}.txt").write_text(text.strip() + "\n")


def load():
    prim = json.load(open(T / "primary.json"))
    sec = json.load(open(T / "secondary.json")) if (T / "secondary.json").exists() else {}
    pairs = pd.read_csv(T / "pairs_panel.csv")
    return prim, sec, pairs


def grid(pairs, value="pred_pic50"):
    """Ligand x kinase matrix from the tidy table, ordered by mean measured pKd."""
    m = pairs.pivot_table(index="cid", columns="kinase", values=value, aggfunc="last")
    y = pairs.pivot_table(index="cid", columns="kinase", values="pkd", aggfunc="last")
    ri = y.mean(1).sort_values(ascending=False).index
    ci = y.mean(0).sort_values(ascending=False).index
    return m.loc[ri, ci], y.loc[ri, ci]


def f1(prim, pairs):
    fig = plt.figure(figsize=(12, 4.6))
    ax = fig.add_axes([0.065, 0.19, 0.37, 0.72])
    rng = np.random.default_rng(0)
    series = [("boltz2", "Boltz-2", BLUE, prim["P1"]["per_ligand"])] + \
             [(k, lab, col, prim["baselines"][k]["P1"]["per_ligand"]) for k, lab, col in BASE_LABELS]
    for j, (_, lab, col, v) in enumerate(series):
        v = np.array(v, float)
        v = v[np.isfinite(v)]
        ax.scatter(j + rng.uniform(-0.17, 0.17, len(v)), v, s=16, color=col, alpha=0.8, lw=0)
        ax.plot([j - 0.3, j + 0.3], [np.median(v)] * 2, color="black", lw=1.8)
    ax.axhline(0.25, color=RED, ls="--", lw=1)
    ax.text(-0.42, 0.265, "hypothesis threshold 0.25", ha="left", va="bottom", fontsize=7.5, color=RED)
    ax.axhline(0, color="#bbbbbb", lw=0.8)
    ax.set_xticks(range(len(series)))
    ax.set_xticklabels([s[1] for s in series], fontsize=8)
    ax.set_xlim(-0.55, len(series) - 0.45)
    ax.set_ylabel("within-ligand Spearman across the 32 kinases", fontsize=9)
    # the floor matters as much as the median for a tool meant to nominate targets, and it is the one
    # place where the model and the baselines plainly differ (exploratory; see deviations D9)
    ax.set_title("One point per ligand; bar = median\nBoltz-2's worst ligand scores 0.03, the baselines' "
                 "worst score below zero", fontsize=9)
    ax.grid(axis="y", color="#ececec", lw=0.6)
    ax.set_axisbelow(True)

    # four example ligands: the ones with the most uncensored cells (deterministic)
    order = [str(c) for c in prim["cids"]]  # the order per_ligand follows
    unc = pairs.groupby("cid").censored.apply(lambda s: (~s).sum()).sort_values(ascending=False)
    names = pd.read_csv(T / "ligand_names.csv").set_index("cid").name.to_dict()
    gs = fig.add_gridspec(2, 2, left=0.53, right=0.99, top=0.88, bottom=0.14, wspace=0.42, hspace=0.62)
    for k, cid in enumerate(unc.index[:4]):
        a = fig.add_subplot(gs[k // 2, k % 2])
        d = pairs[pairs.cid == cid]
        a.scatter(d.pkd, d.pred_pic50, s=14, color=np.where(d.censored, "#cccccc", BLUE).tolist(), lw=0)
        r = prim["P1"]["per_ligand"][order.index(str(cid))]
        a.set_title(f"{short_name(names.get(cid, cid), cid)}   ρ = {r:.2f}", fontsize=8)
        a.tick_params(labelsize=7)
        if k // 2 == 1:
            a.set_xlabel("measured pKd", fontsize=8)
        if k % 2 == 0:
            a.set_ylabel("predicted", fontsize=8)
    fig.savefig(F / "F1_selectivity.png", dpi=160)
    plt.close(fig)
    caption("F1_selectivity",
            "Left: the selectivity axis. Each point is one ligand's Spearman correlation between Boltz-2's "
            "predicted affinity and the measured Davis pKd across the 32 panel kinases, with the same "
            "statistic for the chemistry-free target-promiscuity baseline, the nearest-chemical-neighbour "
            "baseline and the ligand-only baseline (exactly zero by construction). The dashed line is the "
            "preregistered threshold of 0.25. Right: four example ligands (the four with the most "
            "uncensored panel cells); grey points are cells at the 10 µM assay ceiling.")


def f2(pairs):
    pred, meas = grid(pairs, "pred_pic50")
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.4))
    for ax, (m, lab, cm) in zip(axes.ravel(), [
            (meas, "measured pKd", "viridis"), (pred, "predicted (6 − log10 IC50[µM])", "viridis"),
            (meas.sub(meas.mean(1), axis=0), "measured, ligand mean removed", "coolwarm"),
            (pred.sub(pred.mean(1), axis=0), "predicted, ligand mean removed", "coolwarm")]):
        v = m.to_numpy(float)
        lim = np.nanpercentile(np.abs(v), 98) if cm == "coolwarm" else None
        im = ax.imshow(v, aspect="auto", cmap=cm, vmin=-lim if lim else None, vmax=lim if lim else None)
        ax.set_title(lab, fontsize=10)
        ax.set_xticks(range(0, m.shape[1], 4))
        ax.set_xticklabels(m.columns[::4], rotation=90, fontsize=6)
        ax.set_yticks([])
        ax.set_ylabel("ligands (ordered by mean pKd)", fontsize=8)
        fig.colorbar(im, ax=ax, shrink=0.85)
    fig.tight_layout()
    fig.savefig(F / "F2_panels.png", dpi=150)
    plt.close(fig)
    caption("F2_panels",
            "The panel as measured and as predicted, ligands in rows (ordered by mean measured pKd) and "
            "kinases in columns (likewise). The lower row removes each ligand's own mean, which is what the "
            "selectivity question is about: horizontal banding in the lower-right panel would mean the "
            "model varies by ligand but not by target, while agreement between the two lower panels would "
            "mean it tracks the real selectivity profile.")


def f3(prim, pairs):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax = axes[0]
    for j, (key, lab) in enumerate([("P5_meas", "measured"), ("P5_pred", "Boltz-2")]):
        d = prim[key]
        bot = 0
        for part, col in [("ligand", BLUE), ("kinase", ORANGE), ("residual", "#cccccc")]:
            ax.bar(j, d[part], bottom=bot, color=col, width=0.6,
                   label=part if j == 0 else None)
            if d[part] > 0.04:
                ax.text(j, bot + d[part] / 2, f"{d[part]:.0%}", ha="center", va="center", fontsize=9)
            bot += d[part]
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["measured", "Boltz-2"])
    ax.set_ylabel("share of total variance")
    ax.set_title("Two-way decomposition of the panel", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    ax = axes[1]
    v = np.array(prim["P3"]["per_kinase"], float)
    v = v[np.isfinite(v)]
    ax.hist(v, bins=np.arange(-0.4, 1.01, 0.1), color=BLUE, alpha=0.85)
    ax.axvline(0.4, color=RED, ls="--", lw=1)
    ax.text(0.4, ax.get_ylim()[1] * 0.95, " hypothesis floor 0.4", color=RED, fontsize=8, va="top")
    ax.axvline(np.median(v), color="black", lw=1.6)
    ax.set_xlabel("within-kinase Spearman across the 32 ligands")
    ax.set_ylabel("kinases")
    ax.set_title(f"The conventional axis (median {np.median(v):.2f})", fontsize=10)
    fig.tight_layout()
    fig.savefig(F / "F3_decomposition.png", dpi=160)
    plt.close(fig)
    caption("F3_decomposition",
            "Left: how much of the variation in the panel belongs to the ligand, to the kinase and to the "
            "ligand-by-kinase interaction, for the measurements and for Boltz-2's predictions. A "
            "protein-blind predictor has a kinase share near zero. Right: the conventional axis — ranking "
            "ligands within one kinase — one correlation per kinase, against the hypothesis's floor of 0.4.")


def f4(sec, pairs):
    d = pd.DataFrame(sec["decoy"]["per_decoy"])
    names = {"P00918": "carbonic\nanhydrase 2", "P07477": "trypsin-1", "P09211": "GST P1-1",
             "P07900": "HSP90α\nN-domain"}
    dec = pd.read_csv(T / "pairs_decoy.csv")
    dec["acc"] = dec.protein.str.replace("_decoy", "", regex=False)
    kin = pairs.groupby("cid").pred_pic50.agg(["mean", "max", "std"])
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    ax = axes[0]
    rng = np.random.default_rng(1)
    for j, acc in enumerate(d.decoy):
        v = dec[dec.acc == acc].set_index("cid").pred_pic50.reindex(kin.index) - kin["mean"]
        ax.scatter(j + rng.uniform(-0.17, 0.17, len(v)), v, s=16, color=PURPLE, alpha=0.8, lw=0)
        ax.plot([j - 0.3, j + 0.3], [np.nanmedian(v)] * 2, color="black", lw=1.8)
    ax.axhline(0, color="#999999", lw=0.9)
    # drawn one SD *below* the mean, where the decoys actually are: at the top of the axis it collided
    # with the title and gave the reader nothing to compare against
    ax.axhline(-np.nanmedian(kin["std"]), color=BLUE, ls=":", lw=1)
    ax.text(-0.42, -np.nanmedian(kin["std"]), " one within-kinome SD below the ligand's kinase mean",
            fontsize=7.5, color=BLUE, ha="left", va="bottom")
    ax.set_xticks(range(len(d)))
    ax.set_xticklabels([names.get(a, a) for a in d.decoy], fontsize=8)
    ax.set_ylabel("predicted − the ligand's kinase mean (log units)")
    ax.set_title("Non-kinase decoy proteins, one point per ligand", fontsize=10)
    ax.grid(axis="y", color="#ececec", lw=0.6)
    ax.set_axisbelow(True)
    ax = axes[1]
    ax.scatter(pairs.prob_binary, pairs.pred_pic50, s=6, color=BLUE, alpha=0.3, lw=0, label="panel kinases")
    ax.scatter(dec.prob_binary, dec.pred_pic50, s=10, color=PURPLE, alpha=0.6, lw=0, label="decoy proteins")
    ax.set_xlabel("binary binder probability")
    ax.set_ylabel("predicted affinity (pIC50 scale)")
    ax.legend(fontsize=8, frameon=False)
    ax.set_title("The two affinity outputs, kinases and decoys", fontsize=10)
    fig.tight_layout()
    fig.savefig(F / "F4_decoys.png", dpi=160)
    plt.close(fig)
    caption("F4_decoys",
            "Left: each ligand re-scored against four non-kinase proteins, as the gap from that ligand's "
            "mean prediction over the 32 kinases; the dotted line is the median spread of a ligand's own "
            "predictions inside the kinome, so points inside that band are shifts no larger than the "
            "model's ordinary variation between kinases. HSP90's N-terminal domain is a nucleotide-binding "
            "non-kinase, included to see whether generic ATP-pocket character is what the head responds to. "
            "Right: the two affinity outputs against each other for panel and decoy complexes.")


def f5(sec):
    has_s = "sampling" in sec
    has_u = "support" in sec
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    if has_s:
        ax = axes[0]
        a = np.array(sec["sampling"]["panel"]["P1"]["per_ligand"], float)
        b = np.array(sec["sampling"]["sampling"]["P1"]["per_ligand"], float)
        for i in range(len(a)):
            ax.plot([0, 1], [a[i], b[i]], color="#bbbbbb", lw=0.8, zorder=1)
        ax.scatter(np.zeros(len(a)), a, s=22, color=BLUE, zorder=2, label="default (200 steps, 5 samples)")
        ax.scatter(np.ones(len(b)), b, s=22, color=RED, zorder=2, label="heavy (400 steps, 9 samples)")
        ax.plot([-0.15, 0.15], [np.nanmedian(a)] * 2, color="black", lw=1.8)
        ax.plot([0.85, 1.15], [np.nanmedian(b)] * 2, color="black", lw=1.8)
        ax.axhline(0.25, color=RED, ls="--", lw=0.9)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["default", "heavy"])
        ax.set_ylabel("within-ligand Spearman (8 × 12 sub-panel)")
        ax.set_title("Does more affinity sampling reveal the target?", fontsize=10)
        ax.legend(fontsize=7, frameon=False, loc="lower right")
    if has_u:
        ax = axes[1]
        t = pd.DataFrame(sec["support"]["per_kinase"])
        ax.scatter(t.log_support, t.within_kinase_rho, s=18, color=BLUE, lw=0)
        m = np.isfinite(t.within_kinase_rho)
        if m.sum() > 2:
            z = np.polyfit(t.log_support[m], t.within_kinase_rho[m], 1)
            xs = np.linspace(t.log_support.min(), t.log_support.max(), 10)
            ax.plot(xs, np.polyval(z, xs), color=RED, lw=1.2)
            ax.text(0.03, 0.03, f"Spearman {sec['support']['fits']['within_kinase_rho']['spearman']:.2f}",
                    transform=ax.transAxes, fontsize=9, color=RED)
        ax.set_xlabel("log10(1 + distinct compounds in pre-2024 ChEMBL)")
        ax.set_ylabel("within-kinase Spearman")
        ax.set_title("Accuracy against training support", fontsize=10)
    fig.tight_layout()
    fig.savefig(F / "F5_sampling_support.png", dpi=160)
    plt.close(fig)
    caption("F5_sampling_support",
            "Left: the same 8 × 12 sub-panel at the default affinity sampling and at the heavier setting "
            "that BoltzOmics reported to improve within-drug ranking across protein variants; lines join "
            "the same ligand. Right: per-kinase accuracy on the conventional axis against how much "
            "pre-2024 ChEMBL data exists for that kinase, a proxy for training support.")


def main():
    F.mkdir(parents=True, exist_ok=True)
    prim, sec, pairs = load()
    f1(prim, pairs)
    f2(pairs)
    f3(prim, pairs)
    if "decoy" in sec and (T / "pairs_decoy.csv").exists():
        f4(sec, pairs)
    if "sampling" in sec or "support" in sec:
        f5(sec)
    print("figures written to", F)


if __name__ == "__main__":
    main()
