"""Reviewer check (independent of code/analysis.py): recompute W, X, R, the dyadic bootstrap interval and the verdict
from results/tables/pairs_L*.csv; the per-layer and other-threshold ratios; the decomposition; the per-model ratios and
separation ranges quoted in report.md; the SAE-seed sharing check; the D7 conditional-replication table from the
released per-latent arrays (and the same table stratified by firing-frequency tercile, to probe the selection
question); the frequency-tercile table; the modes of the best-correlation distributions; and the quality/reference
numbers. Prints everything; writes review/reviewer_checks/recompute_stats.json."""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[2]
TAB = RUN / "results" / "tables"
OUT = Path(__file__).resolve().parent
FULL = ["p160m"] + [f"p160m-seed{i}" for i in range(1, 10)]
LINEAGE = ["p160m"] + [f"p160m-weight-seed{i}" for i in range(1, 4)] + [f"p160m-data-seed{i}" for i in range(1, 4)]
LAYERS = [4, 8]
res = {}

pairs = {L: pd.read_csv(TAB / f"pairs_L{L}.csv") for L in LAYERS}

# ---- design checks
for L in LAYERS:
    d = pairs[L]
    cross = d[d.kind != "within"]
    assert (cross.sa != cross.sb).all(), "a cross-model pair shares an SAE seed"
    assert (cross.a != cross.b).all()
    w = d[d.kind == "within"]
    assert (w.a == w.b).all() and (w.sa != w.sb).all()
    assert len(d) == 246 and d.id.is_unique
    # every full-seed model pair appears with exactly the 3 seed combos (0,1),(1,2),(2,0)
    f = d[d.kind == "full"]
    combos = f.groupby(["a", "b"]).apply(lambda t: sorted(zip(t.sa, t.sb)), include_groups=False)
    assert len(combos) == 45 and all(c == [(0, 1), (1, 2), (2, 0)] for c in combos)
print("design checks passed: no cross pair shares an SAE seed; 246 pairs; 45 full model pairs x 3 combos")


# ---- primary statistic, re-implemented from scratch (matrix form)
def model_level(L, col):
    d = pairs[L]
    w = d[d.kind == "within"].groupby("a")[col].mean()
    x = d[d.kind == "full"].groupby(["a", "b"])[col].mean()
    n = len(FULL)
    Xm = np.full((n, n), np.nan)
    for (a, b), v in x.items():
        i, j = FULL.index(a), FULL.index(b)
        Xm[i, j] = Xm[j, i] = v
    return np.array([w[m] for m in FULL]), Xm


def ratio(ws, Xs, idx=None):
    """ws: list over layers of per-model within (n,), Xs: list of (n,n) cross matrices. idx: bootstrap draw."""
    num = den = 0.0
    for w, X in zip(ws, Xs):
        if idx is None:
            den += w.mean()
            num += X[np.triu_indices(len(w), 1)].mean()
        else:
            den += w[idx].mean()
            ii, jj = np.triu_indices(len(idx), 1)
            a, b = idx[ii], idx[jj]
            keep = a != b
            num += X[a[keep], b[keep]].mean()
    return num / den


def primary(col="f0.7", layers=LAYERS, seed=20261012, B=2000):
    ws, Xs = zip(*[model_level(L, col) for L in layers])
    R = ratio(ws, Xs)
    rng = np.random.default_rng(seed)
    bs = np.array([ratio(ws, Xs, rng.integers(0, 10, 10)) for _ in range(B)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    verdict = "Supported" if hi < 0.8 else "Refuted" if lo >= 0.8 else "Inconclusive"
    return dict(R=float(R), lo=float(lo), hi=float(hi), verdict=verdict,
                W={L: float(w.mean()) for L, w in zip(layers, ws)},
                X={L: float(X[np.triu_indices(10, 1)].mean()) for L, X in zip(layers, Xs)}, sd_boot=float(bs.std()))


res["primary"] = primary()
res["primary_other_seed"] = primary(seed=1)
res["primary_B20000"] = primary(seed=7, B=20000)
res["per_layer"] = {L: primary(layers=[L]) for L in LAYERS}
res["thresholds"] = {c: primary(col=c) for c in ["f0.5", "f0.9"]}
print("PRIMARY", json.dumps(res["primary"], indent=None))
print("other seed", res["primary_other_seed"]["lo"], res["primary_other_seed"]["hi"])
print("B=20000", res["primary_B20000"]["lo"], res["primary_B20000"]["hi"])
for L in LAYERS:
    print("layer", L, res["per_layer"][L])
for c in ["f0.5", "f0.9"]:
    print("threshold", c, res["thresholds"][c])

# a simpler, model-level interval for comparison: per-model ratio (its mean cross / its within, pooled layers)
ws, Xs = zip(*[model_level(L, "f0.7") for L in LAYERS])
per_model = {}
for i, m in enumerate(FULL):
    num = sum(np.nanmean(X[i]) for X in Xs)
    den = sum(w[i] for w in ws)
    per_model[m] = dict(pooled=num / den, **{f"L{L}": float(np.nanmean(X[i]) / w[i]) for L, w, X in zip(LAYERS, ws, Xs)})
pm = pd.DataFrame(per_model).T
print("per-model ratios:\n", pm.round(4).to_string())
res["per_model_ratio_range"] = {k: [float(pm[k].min()), float(pm[k].max())] for k in pm.columns}
print("per-model ratio ranges", res["per_model_ratio_range"])
# naive t-interval on the 10 per-model pooled ratios
x = pm.pooled.values
print("mean of per-model pooled ratios", x.mean(), "t-interval", x.mean() - 2.262 * x.std(ddof=1) / np.sqrt(10), x.mean() + 2.262 * x.std(ddof=1) / np.sqrt(10))

# separation ranges quoted in the report
for L, w, X in zip(LAYERS, ws, Xs):
    xs = X[np.triu_indices(10, 1)]
    res[f"separation_L{L}"] = dict(cross=[float(xs.min()), float(xs.max())], within=[float(w.min()), float(w.max())],
                                   all_cross_below_all_within=bool(xs.max() < w.min()))
    print("separation", L, res[f"separation_L{L}"])

# ---- decomposition (plan 7.2), re-implemented
den = sum(pairs[L][(pairs[L].kind == "within") & pairs[L].a.isin(LINEAGE)]["f0.7"].mean() for L in LAYERS)
res["decomposition"] = {"lineage_within_mean": den / 2}
rng = np.random.default_rng(20261013)
for kind in ["init", "data", "both_dc", "full"]:
    g = [pairs[L][pairs[L].kind == kind].groupby(["a", "b"])["f0.7"].mean() for L in LAYERS]
    keys = sorted(set(g[0].index) & set(g[1].index))
    pp = np.array([g[0][k] + g[1][k] for k in keys])
    bs = [pp[rng.integers(0, len(pp), len(pp))].mean() / den for _ in range(4000)]
    res["decomposition"][kind] = dict(ratio=float(pp.mean() / den), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)),
                                      n=len(keys), by_layer={L: float(g[i].mean() / pairs[L][(pairs[L].kind == "within") & pairs[L].a.isin(LINEAGE)]["f0.7"].mean()) for i, L in enumerate(LAYERS)})
    print("decomposition", kind, res["decomposition"][kind])
# how different are the lineage kinds from full, pooled: a permutation-free look at the model-pair values
for L in LAYERS:
    d = pairs[L]
    print(f"L{L} model-pair means by kind:", d[d.kind != "within"].groupby(["kind", "a", "b"])["f0.7"].mean().groupby("kind").agg(["mean", "std", "min", "max"]).round(4).to_dict("index"))

# ---- assessable counts and dead fractions
q = {L: pd.read_csv(TAB / f"sae_quality_L{L}.csv") for L in LAYERS}
for L in LAYERS:
    qq = q[L][q[L].model != "eai_reference"]
    res[f"quality_L{L}"] = dict(assessable=[int(qq.assessable.min()), int(qq.assessable.max())],
                                not_assessable_frac=[float(1 - qq.assessable.max() / 32768), float(1 - qq.assessable.min() / 32768)],
                                dead=[float(qq.dead.min()), float(qq.dead.max())], fvu_median=float(qq.fvu.median()),
                                fvu_range=[float(qq.fvu.min()), float(qq.fvu.max())],
                                flagged=int(((qq.fvu > 2 * qq.fvu.median()) | (qq.dead > 0.5)).sum()),
                                ref_fvu=float(q[L][q[L].model == "eai_reference"].fvu.iloc[0]))
    r = pd.read_csv(TAB / f"reference_L{L}.csv")
    res[f"quality_L{L}"]["ref_f07"] = float(r["f0.7"].mean())
    print("quality", L, res[f"quality_L{L}"])
    # Spearman score vs FVU
    fv = q[L].set_index(["model", "seed"]).fvu
    d = pairs[L][pairs[L].kind.isin(["within", "full"])].copy()
    d["fvu"] = [(fv[(a, sa)] + fv[(b, sb)]) / 2 for a, sa, b, sb in zip(d.a, d.sa, d.b, d.sb)]
    for kind, g in d.groupby("kind"):
        rho = g["f0.7"].rank().corr(g.fvu.rank())
        n = len(g)
        t = rho * np.sqrt((n - 2) / (1 - rho ** 2))
        print(f"  spearman L{L} {kind}: rho={rho:.3f} n={n} t={t:.2f}")

# ---- per-latent arrays: D7 conditional replication (own implementation) + stratified by frequency; tercile table; modes
arr = {L: np.load(RUN / "results" / f"match_arrays_L{L}.npz") for L in LAYERS}
res["conditional"], res["conditional_by_tercile"], res["tercile"], res["modes"] = {}, {}, {}, {}
for L in LAYERS:
    d = pairs[L]
    z = arr[L]
    side = {}  # (model, seed) -> list of (kind, best array)
    for _, p in d.iterrows():
        side.setdefault((p.a, p.sa), []).append((p.kind, p.b, z[f"pair{p.id}_a"].astype(np.float32)))
        side.setdefault((p.b, p.sb), []).append((p.kind, p.a, z[f"pair{p.id}_b"].astype(np.float32)))
    counts = np.zeros(3)
    hits = np.zeros(3)
    tot = np.zeros((3, 3))
    tot_hits = np.zeros((3, 3))
    for m in FULL:
        for s in range(3):
            lst = side[(m, s)]
            w = [b for k, _, b in lst if k == "within"]
            x = [b for k, _, b in lst if k == "full"]
            assert len(w) == 2 and len(x) == 9, (m, s, len(w), len(x))
            ok = np.isfinite(w[0])
            assert all((np.isfinite(b) == ok).all() for b in w + x), "assessability differs between pairs"
            wc = (w[0] >= 0.7).astype(int) + (w[1] >= 0.7).astype(int)
            xr = np.mean([(b >= 0.7) for b in x], axis=0)
            fired = z[f"fired_{m}_s{s}"]
            qs = np.quantile(fired[ok], [1 / 3, 2 / 3])
            terc = np.digitize(fired, qs)
            for c in range(3):
                sel = ok & (wc == c)
                counts[c] += sel.sum()
                hits[c] += xr[sel].sum()
                for t in range(3):
                    st = sel & (terc == t)
                    tot[c, t] += st.sum()
                    tot_hits[c, t] += xr[st].sum()
    res["conditional"][L] = dict(share=(counts / counts.sum()).round(4).tolist(), cross_rate=(hits / counts).round(4).tolist(),
                                 overall=float(hits.sum() / counts.sum()))
    res["conditional_by_tercile"][L] = dict(share_within_tercile=(tot / tot.sum(0, keepdims=True)).round(3).tolist(),
                                            cross_rate=(tot_hits / tot).round(3).tolist())
    print(f"D7 L{L}: share by within-count {res['conditional'][L]['share']} cross rate {res['conditional'][L]['cross_rate']} overall {res['conditional'][L]['overall']:.4f}")
    print(f"D7 L{L} by tercile (rows: within-count 0,1,2; cols: rarest, middle, most frequent):")
    print("   share of tercile:", res["conditional_by_tercile"][L]["share_within_tercile"])
    print("   cross rate      :", res["conditional_by_tercile"][L]["cross_rate"])
    # frequency terciles (plan 7.4), within (16 models) vs full (10)
    agg = {}
    for _, p in d[d.kind.isin(["within", "full"])].iterrows():
        for model, seed, best in ((p.a, p.sa, z[f"pair{p.id}_a"]), (p.b, p.sb, z[f"pair{p.id}_b"])):
            best = best.astype(np.float32)
            fired = z[f"fired_{model}_s{seed}"]
            ok = np.isfinite(best)
            qs = np.quantile(fired[ok], [1 / 3, 2 / 3])
            terc = np.digitize(fired, qs)
            for t in range(3):
                sel = ok & (terc == t)
                a = agg.setdefault((p.kind, t), [0, 0])
                a[0] += sel.sum()
                a[1] += (best[sel] >= 0.7).sum()
    res["tercile"][L] = {f"{k}|t{t}": round(v[1] / v[0], 4) for (k, t), v in sorted(agg.items())}
    print(f"tercile L{L}:", res["tercile"][L])
    # modes of the best-correlation distributions (within vs full, 10 full-seed models, both sides)
    for kind in ["within", "full"]:
        vals = []
        for _, p in d[(d.kind == kind) & d.a.isin(FULL) & d.b.isin(FULL)].iterrows():
            for s_ in ("a", "b"):
                v = z[f"pair{p.id}_{s_}"].astype(np.float32)
                vals.append(v[np.isfinite(v)])
        v = np.concatenate(vals)
        h, e = np.histogram(v, bins=np.linspace(-0.1, 1.0, 111))
        res["modes"][f"L{L}|{kind}"] = float((e[h.argmax()] + e[h.argmax() + 1]) / 2)
        print(f"mode L{L} {kind}: {res['modes'][f'L{L}|{kind}']:.3f}  (median {np.median(v):.3f}, share>=0.7 {np.mean(v >= 0.7):.4f})")

json.dump(res, open(OUT / "recompute_stats.json", "w"), indent=1, default=float)
print("written", OUT / "recompute_stats.json")
