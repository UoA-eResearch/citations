"""Plan sections 5-7: the primary ratio R with its dyadic bootstrap, the decision rule, and the secondary analyses.

Inputs: results/tables/pairs_L{4,8}.csv, sae_quality_L{4,8}.csv, reference_L{4,8}.csv and the per-latent arrays in
data/match/L*/. Outputs: results/tables/primary.json, secondary.json, model_scores.csv."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"
LAYERS, B, SEED = [4, 8], 2000, 20261012
FULL = ["p160m"] + [f"p160m-seed{i}" for i in range(1, 10)]
LINEAGE = ["p160m"] + [f"p160m-weight-seed{i}" for i in range(1, 4)] + [f"p160m-data-seed{i}" for i in range(1, 4)]


def load():
    return {L: pd.read_csv(TAB / f"pairs_L{L}.csv") for L in LAYERS}


def scores(pairs, col="f0.7", drop=()):
    """Per layer: within score per model and cross score per unordered model pair (means over SAE-seed combinations)."""
    W, X = {}, {}
    for L, d in pairs.items():
        d = d[~d.a.isin(drop) & ~d.b.isin(drop)]
        w = d[d.kind == "within"].groupby("a")[col].mean()
        x = d[d.kind != "within"].groupby(["a", "b", "kind"])[col].mean().reset_index()
        W[L] = w.to_dict()
        X[L] = {frozenset((r.a, r.b)): (r.kind, r[col]) for _, r in x.iterrows()}
    return W, X


def ratio_full(W, X, models, layers=LAYERS):
    num = sum(np.mean([X[L][frozenset((a, b))][1] for i, a in enumerate(models) for b in models[i + 1:]]) for L in layers)
    den = sum(np.mean([W[L][m] for m in models]) for L in layers)
    return num / den, {L: np.mean([W[L][m] for m in models]) for L in layers}, \
        {L: np.mean([X[L][frozenset((a, b))][1] for i, a in enumerate(models) for b in models[i + 1:]]) for L in layers}


def boot(W, X, models, layers=LAYERS, seed=SEED):
    """Dyadic bootstrap over models: resample models; pairs of draws that are the same model are skipped."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(B):
        draw = [models[i] for i in rng.integers(0, len(models), len(models))]
        num = den = 0.0
        for L in layers:
            den += np.mean([W[L][m] for m in draw])
            xs = [X[L][frozenset((a, b))][1] for i, a in enumerate(draw) for b in draw[i + 1:] if a != b]
            num += np.mean(xs)
        out.append(num / den)
    lo, hi = np.percentile(out, [2.5, 97.5])
    return float(lo), float(hi)


def verdict(lo, hi):
    return "Supported" if hi < 0.8 else "Refuted" if lo >= 0.8 else "Inconclusive"


def primary_block(pairs, col="f0.7", layers=LAYERS, drop=()):
    W, X = scores(pairs, col, drop)
    models = [m for m in FULL if m not in drop]
    R, Wl, Xl = ratio_full(W, X, models, layers)
    lo, hi = boot(W, X, models, layers)
    return dict(R=float(R), lower95=lo, upper95=hi, verdict=verdict(lo, hi), any_loss=hi < 1,
                W={str(L): float(Wl[L]) for L in layers}, X={str(L): float(Xl[L]) for L in layers}, models=len(models))


def decomposition(pairs, col="f0.7"):
    """Plan 7.2: mean pair score by kind relative to the mean within score of the seed-0 lineage (pooled layers)."""
    rng = np.random.default_rng(SEED + 1)
    out = {}
    den = sum(pairs[L][(pairs[L].kind == "within") & pairs[L].a.isin(LINEAGE)][col].mean() for L in LAYERS)
    for kind in ["init", "data", "both_dc", "full"]:
        per_pair = []  # model-pair scores, pooled over layers (sum over layers of the mean over SAE-seed combinations)
        g = [pairs[L][pairs[L].kind == kind].groupby(["a", "b"])[col].mean() for L in LAYERS]
        keys = sorted(set(g[0].index) & set(g[1].index))
        per_pair = np.array([sum(x[k] for x in g) for k in keys])
        est = per_pair.mean() / den
        bs = [per_pair[rng.integers(0, len(per_pair), len(per_pair))].mean() / den for _ in range(B)]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        out[kind] = dict(ratio=float(est), lower95=float(lo), upper95=float(hi), model_pairs=len(keys))
    out["lineage_within_mean"] = float(den / len(LAYERS))
    return out


def by_frequency(pairs):
    """Plan 7.4: directional match rate (r >= 0.7) by tercile of the source latent's firing count on H."""
    rows = []
    for L in LAYERS:
        md = RUN / "data" / "match" / f"L{L}"
        for _, p in pairs[L][pairs[L].kind.isin(["within", "full"])].iterrows():
            z = np.load(md / f"pair_{p.id}.npz")
            for side, model, seed, best in (("a", p.a, p.sa, z["corr_a"]), ("b", p.b, p.sb, z["corr_b"])):
                fired = np.load(md / f"fired_{model}_s{seed}.npy")
                ok = np.isfinite(best.astype(np.float32))
                q = np.quantile(fired[ok], [1 / 3, 2 / 3])
                terc = np.digitize(fired, q)
                for t in range(3):
                    sel = ok & (terc == t)
                    rows.append(dict(layer=L, kind=p.kind, tercile=t, n=int(sel.sum()),
                                     matched=int((best[sel].astype(np.float32) >= 0.7).sum())))
    d = pd.DataFrame(rows).groupby(["layer", "kind", "tercile"])[["n", "matched"]].sum()
    d["rate"] = d.matched / d.n
    return {f"L{L}|{k}|t{t}": float(r) for (L, k, t), r in d.rate.items()}


def main():
    pairs = load()
    prim = primary_block(pairs)
    json.dump(prim, open(TAB / "primary.json", "w"), indent=1)
    sec = {}
    sec["per_layer"] = {str(L): primary_block(pairs, layers=[L]) for L in LAYERS}
    sec["thresholds"] = {c: primary_block(pairs, col=c) for c in ["f0.5", "f0.9"]}
    sec["decomposition"] = decomposition(pairs)
    sec["decomposition_by_layer"] = {}
    for L in LAYERS:
        d = pairs[L]
        den = d[(d.kind == "within") & d.a.isin(LINEAGE)]["f0.7"].mean()
        sec["decomposition_by_layer"][str(L)] = {k: float(d[d.kind == k]["f0.7"].mean() / den)
                                                 for k in ["init", "data", "both_dc", "full"]}
    sec["by_frequency"] = by_frequency(pairs)
    # 7.5 decoder geometry
    sec["decoder"] = {}
    for L in LAYERS:
        d = pairs[L]
        for kind in ["within", "full", "init", "data", "both_dc"]:
            s = d[d.kind == kind]
            sec["decoder"][f"L{L}|{kind}"] = {c: float(s[c].mean()) for c in ["cos0.5", "cos0.7", "rcos0.5", "rcos0.7"]}
    # 7.6 SAE quality and flagging
    q = pd.concat([pd.read_csv(TAB / f"sae_quality_L{L}.csv").assign(layer=L) for L in LAYERS])
    q = q[q.model != "eai_reference"]
    med = q.groupby("layer").fvu.transform("median")
    q["flag"] = (q.fvu > 2 * med) | (q.dead > 0.5)
    sec["quality"] = dict(fvu_median={str(L): float(q[q.layer == L].fvu.median()) for L in LAYERS},
                          fvu_range={str(L): [float(q[q.layer == L].fvu.min()), float(q[q.layer == L].fvu.max())] for L in LAYERS},
                          dead_max=float(q.dead.max()), flagged=q[q.flag][["model", "seed", "layer"]].to_dict("records"))
    flagged_models = sorted(set(q[q.flag].model))
    sec["drop_flagged"] = primary_block(pairs, drop=flagged_models) if flagged_models else None
    # does pair score track SAE quality? (Spearman between pair score and the pair's mean FVU)
    fv = q.set_index(["layer", "model", "seed"]).fvu
    rho = {}
    for L in LAYERS:
        d = pairs[L][pairs[L].kind.isin(["within", "full"])].copy()
        d["fvu"] = [(fv[(L, a, sa)] + fv[(L, b, sb)]) / 2 for a, sa, b, sb in zip(d.a, d.sa, d.b, d.sb)]
        for kind, g in d.groupby("kind"):
            rho[f"L{L}|{kind}"] = float(g["f0.7"].rank().corr(g.fvu.rank()))
    sec["score_vs_fvu_spearman"] = rho
    # 7.7 reference
    sec["reference"] = {}
    for L in LAYERS:
        r = pd.read_csv(TAB / f"reference_L{L}.csv")
        qq = pd.read_csv(TAB / f"sae_quality_L{L}.csv")
        sec["reference"][str(L)] = dict(f07_with_ours=float(r["f0.7"].mean()) if len(r) else None,
                                        fvu_reference=float(qq[qq.model == "eai_reference"].fvu.iloc[0]) if (qq.model == "eai_reference").any() else None)
    json.dump(sec, open(TAB / "secondary.json", "w"), indent=1, default=float)
    # per-model and per-pair scores (pooled layers)
    W, X = scores(pairs)
    pd.DataFrame([dict(model=m, **{f"within_L{L}": W[L].get(m) for L in LAYERS}) for m in W[LAYERS[0]]]).to_csv(
        TAB / "model_scores.csv", index=False)
    print(json.dumps(prim, indent=1))


if __name__ == "__main__":
    main()
