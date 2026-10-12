"""Figures (written before the matching finished): (1) pair scores by kind and layer; (2) the ratios against the 0.8
threshold (primary, per layer, other thresholds, decomposition); (3) the distribution of per-latent best correlations,
within against full; (4) decoder cosine raw and Procrustes-rotated; (5) match rate by firing-frequency tercile.
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
LAYERS = [4, 8]
FULL = ["p160m"] + [f"p160m-seed{i}" for i in range(1, 10)]
# labels for the decoupled kinds follow D6 (what the checkpoints show), not the preregistered names
KINDS = [("within", "within model\n(SAE seeds)", "#2e6f9e"), ("full", "full seeds\n(init + data)", "#c2412d"),
         ("init", "weight-seed\n(same init)", "#d9822b"), ("data", "data order\n(data-seed)", "#7a9e3b"),
         ("both_dc", "data order\n(weight- vs\ndata-seed)", "#8d6cab")]


def caption(name, text):
    (F / f"{name}.txt").write_text(text.strip() + "\n")


def per_pair(d, col="f0.7"):
    """Model-level scores: within -> one per model; cross kinds -> one per model pair (mean over SAE-seed combinations)."""
    w = d[d.kind == "within"].groupby("a")[col].mean().reset_index().assign(kind="within")
    x = d[d.kind != "within"].groupby(["a", "b", "kind"])[col].mean().reset_index()
    return pd.concat([w, x], ignore_index=True)


def scores(pairs, prim):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    rng = np.random.default_rng(0)
    for ax, L in zip(axes, LAYERS):
        s = per_pair(pairs[L])
        for j, (k, lab, col) in enumerate(KINDS):
            v = s[s.kind == k]
            if k == "within":  # full-seed models solid, decoupled variants hollow
                full = v.a.isin(FULL)
                ax.scatter(j + rng.uniform(-0.18, 0.18, full.sum()), v[full]["f0.7"], s=16, color=col, alpha=0.85, lw=0)
                ax.scatter(j + rng.uniform(-0.18, 0.18, (~full).sum()), v[~full]["f0.7"], s=16, facecolor="none",
                           edgecolor=col, lw=0.9)
            else:
                ax.scatter(j + rng.uniform(-0.18, 0.18, len(v)), v["f0.7"], s=12, color=col, alpha=0.7, lw=0)
            ax.plot([j - 0.3, j + 0.3], [v["f0.7"].mean()] * 2, color="black", lw=1.6)
        W = prim["W"][str(L)]
        ax.axhline(0.8 * W, color="#555555", ls="--", lw=0.9)
        ax.text(len(KINDS) - 0.5, 0.8 * W, "0.8 × W (full seeds)", ha="right", va="bottom", fontsize=7.5, color="#555555")
        ax.set_xticks(range(len(KINDS)))
        ax.set_xticklabels([k[1] for k in KINDS], fontsize=8)
        ax.set_title(f"Layer {L}", fontsize=10)
        ax.grid(axis="y", color="#e6e6e6", lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("pair score f (share of latents with a match at r ≥ 0.7)")
    fig.tight_layout()
    fig.savefig(F / "scores.png", dpi=160)
    plt.close(fig)
    caption("scores", """Pair scores at r >= 0.7, by kind of pair and layer (decoupled kinds labelled as in D6). Within: one point per model (mean of its
three SAE-seed pairs; filled = the 10 full-seed models that enter the primary statistic, hollow = the 6 decoupled
variants). Cross kinds: one point per model pair (mean of its three SAE-seed combinations). Black bars are means. The
dashed line is 0.8 times the mean within score of the 10 full-seed models: the hypothesis's threshold.""")


def ratios(prim, sec):
    rows = [("Primary: both layers, r ≥ 0.7", prim, True)]
    rows += [(f"Layer {L} only", sec["per_layer"][str(L)], False) for L in LAYERS]
    rows += [(f"Threshold r ≥ {c[1:]}", sec["thresholds"][c], False) for c in ["f0.5", "f0.9"]]
    if sec.get("drop_flagged"):
        rows += [("Flagged SAEs' models dropped", sec["drop_flagged"], False)]
    dec = sec["decomposition"]
    lab = {"init": "weight-seed (same init, perturbation unidentified)", "data": "data order (data-seed variants)",
           "both_dc": "data order (weight- vs data-seed)", "full": "full seeds (vs lineage within)"}
    rows += [(f"Decomposition: {lab[k]}", dict(R=dec[k]["ratio"], lower95=dec[k]["lower95"], upper95=dec[k]["upper95"]),
              False) for k in ["init", "data", "both_dc", "full"]]
    fig, ax = plt.subplots(figsize=(8.2, 0.42 * len(rows) + 1.2))
    for i, (lab_, r, p) in enumerate(rows):
        col = "black" if p else "#555555"
        ax.plot([r["lower95"], r["upper95"]], [i, i], color=col, lw=2.2 if p else 1.3)
        ax.plot(r["R"], i, "D" if p else "o", color=col, ms=7 if p else 5)
    ax.axvline(0.8, color="#c2412d", lw=0.9, ls="--")
    ax.axvline(1.0, color="grey", lw=0.9)
    lo = min(0.5, min(r["lower95"] for _, r, _ in rows) - 0.05)
    hi = max(1.1, max(r["upper95"] for _, r, _ in rows) + 0.05)
    ax.set_xlim(lo, hi)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("cross-seed matching ÷ within-model matching (95% interval)")
    ax.text(0.8, -0.9, "0.8 (H threshold)", ha="center", fontsize=7.5, color="#c2412d")
    ax.text(1.0, -0.9, "1 (no loss)", ha="center", fontsize=7.5, color="grey")
    fig.tight_layout()
    fig.savefig(F / "ratios.png", dpi=160)
    plt.close(fig)
    caption("ratios", """Cross-seed matching relative to within-model matching. Primary (diamond): R = (X4 + X8) / (W4 + W8)
over the 10 full-seed models, with the dyadic model bootstrap interval. Supported needs the whole interval below 0.8
(dashed); Refuted needs it at or above 0.8. The decomposition rows divide each kind's mean score by the mean within
score of the seed-0 lineage (original, weight-seed and data-seed variants); their intervals resample model pairs and
are descriptive (6-9 model pairs per kind, 45 for full). Labels follow D6: all seven lineage models were trained from
the original's initialisation, so the weight-seed pairs differ from each other and from the original in an
unidentified way, not in initialisation.""")


def best_corr(pairs):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    bins = np.linspace(-0.1, 1.0, 111)
    for ax, L in zip(axes, LAYERS):
        md = RUN / "data" / "match" / f"L{L}"
        for k, lab, col in KINDS[:2]:
            vals = []
            for _, p in pairs[L][(pairs[L].kind == k) & pairs[L].a.isin(FULL) & pairs[L].b.isin(FULL)].iterrows():
                z = np.load(md / f"pair_{p.id}.npz")
                for side in ("corr_a", "corr_b"):
                    v = z[side].astype(np.float32)
                    vals.append(v[np.isfinite(v)])
            v = np.concatenate(vals)
            ax.hist(v, bins=bins, density=True, histtype="step", color=col, lw=1.4, label=lab.replace("\n", " "))
        ax.axvline(0.7, color="#555555", ls="--", lw=0.9)
        ax.set_title(f"Layer {L}", fontsize=10)
        ax.set_xlabel("best correlation of a latent with any latent of the other SAE")
    axes[0].set_ylabel("density (assessable latents)")
    axes[0].legend(fontsize=8, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(F / "best_corr.png", dpi=160)
    plt.close(fig)
    caption("best_corr", """Distribution of each assessable latent's best activation correlation with the other SAE of
its pair, pooled over both directions and all pairs among the 10 full-seed models: within (same model, different SAE
seed) against full (different pretraining seed, different SAE seed). The dashed line is the matching threshold
r = 0.7.""")


def decoder(sec):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    ks = ["within", "full", "init", "data", "both_dc"]
    for ax, th in zip(axes, ["0.5", "0.7"]):
        x = np.arange(len(ks))
        for o, L in zip((-0.2, 0.2), LAYERS):
            raw = [sec["decoder"][f"L{L}|{k}"][f"cos{th}"] for k in ks]
            rot = [sec["decoder"][f"L{L}|{k}"][f"rcos{th}"] for k in ks]
            ax.bar(x + o, rot, width=0.38, color="#2e6f9e" if L == 4 else "#c2412d", alpha=0.35,
                   label=f"layer {L}, Procrustes-mapped")
            ax.bar(x + o, raw, width=0.38, color="#2e6f9e" if L == 4 else "#c2412d", label=f"layer {L}, raw")
        ax.set_xticks(x)
        ax.set_xticklabels([dict((k, l) for k, l, _ in KINDS)[k] for k in ks], fontsize=7.5)
        ax.set_title(f"best decoder cosine ≥ {th}", fontsize=10)
    axes[0].set_ylabel("share of latents")
    axes[0].legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(F / "decoder.png", dpi=160)
    plt.close(fig)
    caption("decoder", """Decoder geometry (plan 7.5): share of latents whose decoder direction has a cosine of at least
0.5 (left) or 0.7 (right) with some decoder direction of the other SAE, in the raw residual bases (solid) and after
an orthogonal Procrustes map of one model's residual basis onto the other's, fitted on 262,144 tokens of H (pale).
Within pairs share a basis, so their map is the identity. The lineage pairs (right three groups) share the
original's initialisation (D6), which explains their small raw alignment.""")


def frequency(sec):
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2), sharey=True)
    for ax, L in zip(axes, LAYERS):
        for k, lab, col in KINDS[:2]:
            ax.plot([1, 2, 3], [sec["by_frequency"][f"L{L}|{k}|t{t}"] for t in range(3)], "o-", color=col,
                    label=lab.replace("\n", " "))
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels(["rarest third", "middle", "most frequent"], fontsize=8)
        ax.set_title(f"Layer {L}", fontsize=10)
    axes[0].set_ylabel("share matched at r ≥ 0.7")
    axes[0].legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(F / "frequency.png", dpi=160)
    plt.close(fig)
    caption("frequency", """Directional match rate (r >= 0.7) by tercile of the source latent's firing count on H (plan
7.4), within against full pairs. Terciles are computed per SAE over its assessable latents. As preregistered, the
within line pools all 16 models; restricted to the 10 full-seed models it moves by at most 0.006 (report table).""")


def tiles(prim, sec):
    """Key-result tiles for report.html: [label, value, note], rounded once from the stored values."""
    W, X = prim["W"], prim["X"]
    t = [["Verdict", prim["verdict"], "the whole interval is at or above 0.8"],
         ["Cross ÷ within, R", f"{prim['R']:.3f}", f"95% interval {prim['lower95']:.3f}–{prim['upper95']:.3f}"],
         ["Within one model", f"{100 * W['4']:.0f}% · {100 * W['8']:.0f}%",
          "latents with a match at r ≥ 0.7 in another SAE seed, layer 4 · 8"],
         ["Across pretraining seeds", f"{100 * X['4']:.0f}% · {100 * X['8']:.0f}%", "same, in another model's SAE, layer 4 · 8"]]
    json.dump(t, open(T / "tiles.json", "w"), indent=1, ensure_ascii=False)


def main():
    F.mkdir(parents=True, exist_ok=True)
    pairs = {L: pd.read_csv(T / f"pairs_L{L}.csv") for L in LAYERS}
    prim, sec = json.load(open(T / "primary.json")), json.load(open(T / "secondary.json"))
    scores(pairs, prim)
    ratios(prim, sec)
    best_corr(pairs)
    decoder(sec)
    frequency(sec)
    tiles(prim, sec)
    print("figures written")


if __name__ == "__main__":
    main()
